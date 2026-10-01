import hashlib
import requests
from bs4 import BeautifulSoup
import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import urlparse

# Outcome kinds. The crawl worker schedules retries from these, so a 429
# ("slow down") is never handled like a 404 ("gone").
OK = 'ok'
RATE_LIMITED = 'rate_limited'   # wait as long as the site asks, then retry
TRANSIENT = 'transient'         # 5xx / timeout / network: retry with backoff
PERMANENT = 'permanent'         # 4xx / bad URL / empty page: retrying won't help

# Longest wait we accept from a site's Retry-After / rate-limit-reset header
MAX_RETRY_AFTER_SECONDS = 15 * 60


@dataclass
class FetchResult:
    kind: str
    content: Optional[str] = None
    error: Optional[str] = None           # human-readable, shown to admins
    status_code: Optional[int] = None
    retry_after: Optional[float] = None   # seconds, from the response headers


def url_host(url):
    """Lower-cased host a URL points at; the unit crawl pacing is keyed by."""
    try:
        return (urlparse(url).hostname or '').lower() or 'unknown'
    except ValueError:
        return 'unknown'


def parse_retry_after(headers, now=None):
    """
    Seconds the server asked us to wait, or None if it didn't say.

    Reads Retry-After (delta-seconds or HTTP-date) and falls back to
    X-RateLimit-Reset, which sites send either as epoch seconds (ReadMe,
    GitHub) or as seconds-until-reset. Clamped to [0, MAX_RETRY_AFTER_SECONDS].
    """
    now = time.time() if now is None else now

    def clamp(seconds):
        return max(0.0, min(float(seconds), MAX_RETRY_AFTER_SECONDS))

    retry_after = None
    value = headers.get('Retry-After')
    if value:
        value = value.strip()
        try:
            retry_after = clamp(float(value))
        except ValueError:
            try:
                when = parsedate_to_datetime(value)
                if when.tzinfo is None:  # "-0000" dates parse as naive; they're UTC
                    when = when.replace(tzinfo=timezone.utc)
                retry_after = clamp(when.timestamp() - now)
            except (TypeError, ValueError, IndexError, OverflowError):
                pass

    reset_after = None
    value = headers.get('X-RateLimit-Reset')
    if value:
        try:
            reset = float(value.strip())
            # Anything that looks like a Unix timestamp is absolute
            reset_after = clamp(reset - now if reset > 1_000_000_000 else reset)
        except ValueError:
            pass

    # A "Retry-After: 0" says nothing useful when the rate-limit window
    # itself resets later; wait for whichever is longer
    known = [v for v in (retry_after, reset_after) if v is not None]
    return max(known) if known else None


def _http_error_result(response, host):
    status = response.status_code
    if status == 429 or (status == 503 and 'Retry-After' in response.headers):
        return FetchResult(
            RATE_LIMITED, status_code=status,
            retry_after=parse_retry_after(response.headers),
            error=f"Rate-limited by {host} (HTTP {status})")
    if status >= 500 or status == 408:
        return FetchResult(TRANSIENT, status_code=status,
                           error=f"Server error at {host} (HTTP {status})")
    if status in (404, 410):
        return FetchResult(PERMANENT, status_code=status,
                           error=f"Page not found (HTTP {status}) — check the URL")
    if status in (401, 403):
        return FetchResult(PERMANENT, status_code=status,
                           error=f"Access denied by {host} (HTTP {status}) — the site may block "
                                 f"crawlers; use Paste Content instead")
    return FetchResult(PERMANENT, status_code=status,
                       error=f"Server returned HTTP {status}")


def fetch_main_content(url):
    """
    Fetch URL and extract main text content with preserved structure.

    Returns a FetchResult whose `kind` says whether (and how) to retry, and
    whose `error` is a human-readable reason admins see per URL.

    - Preserves HTML headers as markdown headers (h1 -> ##, h2 -> ###, etc.)
    - Converts lists to markdown format (- Item)
    - Keeps code blocks intact
    - Maintains document hierarchy for better chunking
    """
    if url.startswith('local://'):
        return FetchResult(PERMANENT, error=(
            "This entry is manually pasted content (local:// URL) and "
            "cannot be crawled. Use 'Paste' to update it."))
    if not url.startswith(('http://', 'https://')):
        return FetchResult(PERMANENT, error=f"Unsupported URL scheme: '{url.split(':', 1)[0]}'")

    host = url_host(url)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.Timeout:
        return FetchResult(TRANSIENT, error=f"{host} did not respond within 10 seconds")
    except requests.exceptions.ConnectionError:
        return FetchResult(TRANSIENT, error=f"Could not connect to {host}")
    except (requests.exceptions.InvalidURL, requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema) as e:
        return FetchResult(PERMANENT, error=f"Invalid URL: {e}")
    except requests.exceptions.TooManyRedirects:
        return FetchResult(PERMANENT, error=f"{host} redirects in a loop — check the URL")
    except requests.exceptions.RequestException as e:
        return FetchResult(TRANSIENT, error=f"Request failed: {e}")
    except ValueError as e:  # e.g. a malformed URL that urllib3 rejects
        return FetchResult(PERMANENT, error=f"Invalid URL: {e}")

    if response.status_code >= 400:
        return _http_error_result(response, host)

    content, error = _extract_text(url, response)
    if error:
        return FetchResult(PERMANENT, error=error, status_code=response.status_code)
    return FetchResult(OK, content=content, status_code=response.status_code)


def extract_main_content_detailed(url):
    """
    Backwards-compatible wrapper: (content, error), exactly one is None.
    """
    result = fetch_main_content(url)
    return result.content, result.error


def _extract_text(url, response):
    """Turn a fetched page into structured text: (content, error)."""
    try:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script, style, nav, footer elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=['content', 'main-content', 'article-body'])
        if not main_content:
            main_content = soup

        # Convert HTML structure to markdown-like text
        # This preserves document structure for better chunking

        # 1. Convert headers to markdown format
        for tag in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            # Use ## for h1, ### for h2, etc. (avoid single # which might be confused with other text)
            markdown_header = '\n\n' + ('#' * (level + 1)) + ' ' + tag.get_text(strip=True) + '\n\n'
            tag.replace_with(markdown_header)

        # 2. Convert unordered lists to markdown
        for ul in main_content.find_all('ul'):
            for li in ul.find_all('li', recursive=False):
                li_text = li.get_text(strip=True)
                li.replace_with(f'\n- {li_text}')
            ul.unwrap()  # Remove <ul> tag but keep content

        # 3. Convert ordered lists to markdown
        for ol in main_content.find_all('ol'):
            for idx, li in enumerate(ol.find_all('li', recursive=False), 1):
                li_text = li.get_text(strip=True)
                li.replace_with(f'\n{idx}. {li_text}')
            ol.unwrap()  # Remove <ol> tag but keep content

        # 4. Preserve code blocks
        for code in main_content.find_all(['code', 'pre']):
            code_text = code.get_text(strip=False)
            # Wrap in markdown code block markers
            code.replace_with(f'\n```\n{code_text}\n```\n')

        # 5. Add double line breaks after paragraphs for clear separation
        for p in main_content.find_all('p'):
            p_text = p.get_text(strip=True)
            p.replace_with(f'{p_text}\n\n')

        # 6. Extract final text
        text = main_content.get_text(separator='', strip=False)

        # Clean up excessive whitespace while preserving structure
        # Remove lines with only whitespace
        lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
            elif lines and lines[-1]:  # Preserve blank lines between content
                lines.append('')

        # Remove excessive consecutive blank lines (max 1)
        cleaned_lines = []
        prev_blank = False
        for line in lines:
            if line:
                cleaned_lines.append(line)
                prev_blank = False
            elif not prev_blank:
                cleaned_lines.append(line)
                prev_blank = True

        cleaned_text = '\n'.join(cleaned_lines)

        if not cleaned_text.strip():
            return None, "Page fetched but no text content could be extracted"

        return cleaned_text, None

    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return None, f"Failed to parse page content: {e}"


def extract_main_content(url):
    """Backwards-compatible wrapper: content on success, None on failure."""
    content, error = extract_main_content_detailed(url)
    if error:
        print(f"Error fetching {url}: {error}")
    return content

def filename_from_url(url):
    """Derive the saved .txt filename for a URL (same rule used everywhere)."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    filename = '_'.join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
    filename = filename.replace('.html', '').replace('.htm', '')
    if not filename:
        filename = 'index'
    return f"{filename}.txt"


def saved_text(url, content):
    """The text a crawl saves for `url`: a provenance header, then the page."""
    return f"Source URL: {url}\n\n{content}"


def crawl_single_url_result(url, esp_name, base_path):
    """
    Crawl a single URL and save it to the ESP folder.

    Returns (filename, FetchResult): filename is None unless result.kind is OK.
    The saved text is saved_text(url, result.content); callers should use
    that rather than re-reading the file, which a crawl of a URL with a
    colliding filename can overwrite.
    """
    print(f"[CRAWLER] Crawling {url}...")
    result = fetch_main_content(url)
    if result.kind != OK:
        print(f"[CRAWLER] Failed to extract content from {url}: {result.error}")
        return None, result

    try:
        filename = save_filename_for(base_path, esp_name, url)
        esp_folder = os.path.join(base_path, 'docs', esp_name)
        os.makedirs(esp_folder, exist_ok=True)

        filepath = os.path.join(esp_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(saved_text(url, result.content))
    except OSError as e:
        print(f"[CRAWLER] Error saving {url}: {e}")
        return None, FetchResult(TRANSIENT, error=f"Could not save the crawled page: {e}")

    print(f"[CRAWLER] Saved to {filepath}")
    return filename, result


def crawl_single_url_detailed(url, esp_name, base_path):
    """
    Backwards-compatible wrapper: (filename, error), exactly one is None.
    """
    filename, result = crawl_single_url_result(url, esp_name, base_path)
    return filename, (None if filename else result.error)


def crawl_single_url(url, esp_name, base_path):
    """Backwards-compatible wrapper: filename on success, None on failure."""
    filename, _error = crawl_single_url_detailed(url, esp_name, base_path)
    return filename

def find_saved_copy(base_path, esp_name, url, doc_filename=None):
    """
    (filename, content) of the file saved on disk for `url`, or (None, None).

    Saved filenames collide (filename_from_url maps every local:// URL and
    every site root to index.txt, and /en/articles/1 and /de/articles/1 to
    the same name), so a file is only accepted if it provably belongs to
    this URL: its first line is "Source URL: <url>" (how every crawl and
    paste writes it), or, for older files written without that header,
    crawl_metadata.json maps this exact URL to it and no other URL to it.
    """
    folder = os.path.join(base_path, 'docs', esp_name)
    entries = []
    try:
        with open(os.path.join(base_path, 'docs', 'crawl_metadata.json'), 'r') as f:
            entries = json.load(f).get(esp_name, []) or []
    except (OSError, ValueError):
        pass
    claimed_by = {}
    for entry in entries:
        if entry.get('filename'):
            claimed_by.setdefault(entry['filename'], set()).add(entry.get('url'))
    metadata_names = [e['filename'] for e in entries if e.get('url') == url and e.get('filename')]

    candidates = (([doc_filename] if doc_filename else []) + metadata_names
                  + [filename_from_url(url), _hashed_filename(url)])
    for name in dict.fromkeys(candidates):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        if not content.strip():
            # Empty: a name reservation whose write never happened (see
            # save_filename_for), never anyone's copy
            continue
        header, _, body = content.partition('\n')
        if header == f"Source URL: {url}":
            if body.strip():
                return name, content
            continue
        # The metadata fallback is only for legacy files written without a
        # header; a file whose header names another URL is that URL's
        if (not content.startswith('Source URL: ')
                and name in metadata_names and claimed_by.get(name) == {url}):
            return name, content
    return None, None


def save_filename_for(base_path, esp_name, url, preferred=None):
    """
    The filename to save `url`'s text under, in docs/<esp_name>/.

    Every writer (crawl, paste, rebuild) goes through this so none of them
    overwrites another URL's saved copy: filenames collide (every local://
    URL and site root maps to index.txt; /en/articles/1 and /de/articles/1
    share a name), and on a doc with no database backup that file is the
    only copy. Order: the file this URL already owns (so a URL keeps one
    stable name and old copies aren't stranded), then `preferred` or the
    usual filename_from_url() name if free, else that name plus a short
    hash of the URL.

    A free name is reserved by creating the (empty) file, under a lock, so
    two threads choosing at once (the crawl worker runs several) can't both
    pick it; the caller then writes it. find_saved_copy ignores empty files,
    so a reservation whose write failed is never taken for anyone's copy,
    and once it is older than a minute it counts as free again.
    """
    own, _content = find_saved_copy(base_path, esp_name, url, preferred)
    if own:
        return own
    folder = os.path.join(base_path, 'docs', esp_name)
    os.makedirs(folder, exist_ok=True)
    with _RESERVE_LOCK:
        for name in (preferred, filename_from_url(url)):
            if not (name and name.endswith('.txt')):
                continue
            path = os.path.join(folder, name)
            if _is_stale_reservation(path):
                try:
                    os.unlink(path)
                except FileNotFoundError:
                    pass
            try:
                with open(path, 'x', encoding='utf-8'):
                    pass
                return name
            except FileExistsError:
                continue
    return _hashed_filename(url)


# Serializes name reservation among this process's threads (the disk is
# per-instance, so no cross-process coordination is needed)
_RESERVE_LOCK = threading.Lock()
STALE_RESERVATION_SECONDS = 60


def _is_stale_reservation(path):
    """An empty file left by a reservation whose write never happened."""
    try:
        st = os.stat(path)
    except OSError:
        return False
    return st.st_size == 0 and time.time() - st.st_mtime > STALE_RESERVATION_SECONDS


def _hashed_filename(url):
    """filename_from_url() plus a short hash of the URL: unique per URL."""
    canonical = filename_from_url(url)
    stem = canonical[:-4] if canonical.endswith('.txt') else canonical
    return f"{stem}-{hashlib.sha1(url.encode()).hexdigest()[:8]}.txt"


def vectorize_single_document(vectorizer, esp_name, url, filepath, filename, content=None,
                              product=None):
    """
    Replace the vectors for one URL without touching the rest of the ESP.

    refresh_esp() deletes the ESP's entire vector namespace and re-adds only
    the files present on the local filesystem — on an ephemeral cloud
    filesystem (Railway) that wipes all previously crawled knowledge every
    time a single URL is crawled. Scoping the update to one URL avoids that.

    `content`, when given, is indexed instead of re-reading `filepath`: a
    concurrent crawl of a URL with a colliding filename may have replaced
    the file in between.

    Every vector carries the document's product label, read from its
    esp_documents row unless `product` is given. A document without one is
    refused before its old vectors are deleted: deleting first would leave
    it with no vectors at all.
    """
    esp_key = esp_name.lower()
    if product is None:
        from esp_manager import get_esp_manager
        product = get_esp_manager().get_document_product(esp_key, url)
    from adapters.vector.base import PRODUCT_LABELS
    if product not in PRODUCT_LABELS:
        raise ValueError(f"{url} has no product label. Pick Loyalty, Reviews or Shared "
                         "beside it, then crawl it again.")

    if content is None:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

    if hasattr(vectorizer, 'delete_by_url'):
        vectorizer.delete_by_url(url, esp_key)

    vectorizer.add_document(content, {
        'esp': esp_key,
        'filename': filename,
        'source_url': url,
        'filepath': filepath,
        'product': product
    })

def crawl_and_save(csv_path, base_docs_path):
    """Read CSV and crawl all URLs, saving to appropriate folders"""

    with open(csv_path, 'r') as f:
        lines = f.readlines()

    current_esp = None
    results = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        line_lower = line.lower()

        # Detect ESP section headers (handle both "Integration URLs" and "Knowledge URLs")
        if 'integration urls' in line_lower or 'knowledge urls' in line_lower:
            # Extract ESP name from pattern "[ESP Name] Integration URLs"
            esp_name = line_lower.replace('integration urls', '').replace('knowledge urls', '').strip()
            # Normalize ESP name (remove spaces, special chars)
            if 'other/webhook' in esp_name or 'other webhook' in esp_name:
                current_esp = 'other_webhook'
            elif 'global' in esp_name:
                current_esp = 'global'
            else:
                current_esp = esp_name.replace(' ', '_').replace('/', '_')
            results[current_esp] = []
            continue

        # Skip if starts with number only (CSV index)
        parts = line.split('\t')
        if len(parts) > 1:
            url = parts[1]
        else:
            # Try to extract URL
            if line.startswith('http'):
                url = line
            else:
                continue

        if current_esp and url.startswith('http'):
            print(f"Crawling {url}...")
            content = extract_main_content(url)

            if content:
                # A name no other URL's saved copy uses (see save_filename_for)
                filename = save_filename_for(os.path.dirname(base_docs_path), current_esp, url)

                # Save to appropriate folder
                esp_folder = os.path.join(base_docs_path, current_esp)
                os.makedirs(esp_folder, exist_ok=True)

                filepath = os.path.join(esp_folder, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Source URL: {url}\n\n")
                    f.write(content)

                results[current_esp].append({
                    'url': url,
                    'filename': filename,
                    'filepath': filepath
                })

                print(f"  Saved to {filepath}")

            # Be polite - don't hammer servers
            time.sleep(1)

    # Merge with existing metadata instead of overwriting it: manually
    # pasted docs and ESPs not in the CSV must survive a "Refresh All",
    # otherwise their vectors get deleted on the next refresh_esp().
    metadata_path = os.path.join(base_docs_path, 'crawl_metadata.json')
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: could not read existing metadata, starting fresh: {e}")

    for esp, docs in results.items():
        existing = metadata.get(esp, [])
        crawled_urls = {doc['url'] for doc in docs}
        # Keep entries for URLs this run didn't touch (e.g. pasted content)
        metadata[esp] = [doc for doc in existing if doc['url'] not in crawled_urls] + docs

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nCrawling complete! Metadata saved to {metadata_path}")
    return results

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_path, "ESP_Support_Links - Sheet1.csv")
    docs_path = os.path.join(base_path, "docs")

    results = crawl_and_save(csv_path, docs_path)

    print("\nSummary:")
    for esp, docs in results.items():
        print(f"  {esp}: {len(docs)} documents crawled")
