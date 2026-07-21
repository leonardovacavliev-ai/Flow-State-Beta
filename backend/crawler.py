import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse

def extract_main_content(url):
    """
    Fetch URL and extract main text content with preserved structure

    Improvements over old version:
    - Preserves HTML headers as markdown headers (h1 -> ##, h2 -> ###, etc.)
    - Converts lists to markdown format (- Item)
    - Keeps code blocks intact
    - Maintains document hierarchy for better chunking
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

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

        return cleaned_text

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def crawl_single_url(url, esp_name, base_path):
    """
    Crawl a single URL and save to ESP folder.

    Args:
        url: URL to crawl
        esp_name: ESP name (e.g., 'klaviyo', 'listrak')
        base_path: Base path of the application

    Returns:
        filename if successful, None if failed
    """
    try:
        print(f"[CRAWLER] Crawling {url}...")
        content = extract_main_content(url)

        if not content:
            print(f"[CRAWLER] Failed to extract content from {url}")
            return None

        # Generate filename from URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        filename = '_'.join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
        filename = filename.replace('.html', '').replace('.htm', '')
        if not filename:
            filename = 'index'
        filename = f"{filename}.txt"

        # Save to ESP folder
        docs_path = os.path.join(base_path, 'docs')
        esp_folder = os.path.join(docs_path, esp_name)
        os.makedirs(esp_folder, exist_ok=True)

        filepath = os.path.join(esp_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n\n")
            f.write(content)

        print(f"[CRAWLER] Saved to {filepath}")
        return filename

    except Exception as e:
        print(f"[CRAWLER] Error crawling {url}: {e}")
        return None

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

    # Save metadata
    metadata_path = os.path.join(base_docs_path, 'crawl_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(results, f, indent=2)

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
