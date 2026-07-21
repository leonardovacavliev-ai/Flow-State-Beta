#!/usr/bin/env python3
"""Test crawling the stuck Omnisend URLs"""

import sys
sys.path.insert(0, 'backend')

from crawler import crawl_single_url
import os

# The two stuck URLs
test_urls = [
    "https://support.yotpo.com/docs/omnisend-integration-guide-for-yotpo-loyalty-referrals",
    "https://support.omnisend.com/en/articles/2851596-integrate-yotpo-product-reviews-with-omnisend"
]

base_path = os.path.dirname(os.path.abspath(__file__))

print("Testing stuck Omnisend URLs...")
print(f"Base path: {base_path}\n")

for url in test_urls:
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    print('='*80)

    filename = crawl_single_url(url, 'omnisend', base_path)

    if filename:
        print(f"✓ Success: {filename}")

        # Check file content
        file_path = os.path.join(base_path, 'docs', 'omnisend', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"  File size: {len(content)} bytes")
            print(f"  First 200 chars: {content[:200]}...")
        else:
            print(f"  ✗ File not found: {file_path}")
    else:
        print(f"✗ Failed to crawl")
