#!/usr/bin/env python3
"""Test crawling Listrak URLs locally"""

import sys
sys.path.insert(0, 'backend')

from crawler import crawl_single_url
import os

# Test URLs
test_urls = [
    "https://help.listrak.com/en/articles/2283752-integration-guide-yotpo",
    "https://help.listrak.com/en/articles/6909272-loyalty-automations-in-listrak-conductor",
    "https://help.listrak.com/en/articles/2465793-listrak-conductor-steps",
    "https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-listrak"
]

base_path = os.path.dirname(os.path.abspath(__file__))

print("Testing Listrak URL crawling...")
print(f"Base path: {base_path}\n")

for url in test_urls:
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    print('='*80)

    filename = crawl_single_url(url, 'listrak', base_path)

    if filename:
        print(f"✓ Success: {filename}")

        # Check file content
        file_path = os.path.join(base_path, 'docs', 'listrak', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"  File size: {len(content)} bytes")
            print(f"  First 200 chars: {content[:200]}...")
        else:
            print(f"  ✗ File not found: {file_path}")
    else:
        print(f"✗ Failed to crawl")
