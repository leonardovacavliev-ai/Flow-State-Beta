import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse

def extract_main_content(url):
    """Fetch URL and extract main text content"""
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

        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)

        return cleaned_text

    except Exception as e:
        print(f"Error fetching {url}: {e}")
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

        # Detect ESP section headers
        if 'integration urls' in line.lower():
            # Extract ESP name from pattern "[ESP Name] Integration URLs"
            esp_name = line.lower().replace('integration urls', '').strip()
            # Normalize ESP name (remove spaces, special chars)
            if 'other/webhook' in esp_name or 'other webhook' in esp_name:
                current_esp = 'other_webhook'
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
