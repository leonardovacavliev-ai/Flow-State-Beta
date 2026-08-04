import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse

def extract_main_content_detailed(url):
    """
    Fetch URL and extract main text content with preserved structure.

    Returns (content, error): exactly one of the two is None. The error is a
    human-readable reason (HTTP status, timeout, unsupported scheme, ...) so
    admin endpoints can report per-URL failures instead of silently skipping.

    - Preserves HTML headers as markdown headers (h1 -> ##, h2 -> ###, etc.)
    - Converts lists to markdown format (- Item)
    - Keeps code blocks intact
    - Maintains document hierarchy for better chunking
    """
    if url.startswith('local://'):
        return None, ("This entry is manually pasted content (local:// URL) and "
                      "cannot be crawled. Use 'Paste' to update it.")
    if not url.startswith(('http://', 'https://')):
        return None, f"Unsupported URL scheme: '{url.split(':', 1)[0]}'"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return None, "Request timed out after 10 seconds"
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else '?'
        return None, f"Server returned HTTP {status}"
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to the server"
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"

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


def crawl_single_url_detailed(url, esp_name, base_path):
    """
    Crawl a single URL and save to ESP folder.

    Args:
        url: URL to crawl
        esp_name: ESP name (e.g., 'klaviyo', 'listrak')
        base_path: Base path of the application

    Returns:
        (filename, error): filename on success, error message on failure
        (exactly one is None)
    """
    try:
        print(f"[CRAWLER] Crawling {url}...")
        content, error = extract_main_content_detailed(url)

        if error:
            print(f"[CRAWLER] Failed to extract content from {url}: {error}")
            return None, error

        filename = filename_from_url(url)

        # Save to ESP folder
        docs_path = os.path.join(base_path, 'docs')
        esp_folder = os.path.join(docs_path, esp_name)
        os.makedirs(esp_folder, exist_ok=True)

        filepath = os.path.join(esp_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n\n")
            f.write(content)

        print(f"[CRAWLER] Saved to {filepath}")
        return filename, None

    except Exception as e:
        print(f"[CRAWLER] Error crawling {url}: {e}")
        return None, str(e)


def crawl_single_url(url, esp_name, base_path):
    """Backwards-compatible wrapper: filename on success, None on failure."""
    filename, _error = crawl_single_url_detailed(url, esp_name, base_path)
    return filename

def vectorize_single_document(vectorizer, esp_name, url, filepath, filename):
    """
    Replace the vectors for one URL without touching the rest of the ESP.

    refresh_esp() deletes the ESP's entire vector namespace and re-adds only
    the files present on the local filesystem — on an ephemeral cloud
    filesystem (Railway) that wipes all previously crawled knowledge every
    time a single URL is crawled. Scoping the update to one URL avoids that.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    esp_key = esp_name.lower()
    if hasattr(vectorizer, 'delete_by_url'):
        vectorizer.delete_by_url(url, esp_key)

    vectorizer.add_document(content, {
        'esp': esp_key,
        'filename': filename,
        'source_url': url,
        'filepath': filepath
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
                # Generate filename from URL
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                filename = '_'.join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
                filename = filename.replace('.html', '').replace('.htm', '')
                if not filename:
                    filename = 'index'
                filename = f"{filename}.txt"

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
