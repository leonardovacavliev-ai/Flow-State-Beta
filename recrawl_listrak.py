#!/usr/bin/env python3
"""
Re-crawl failed Listrak URLs in production after fix deployment.

Usage:
  python3 recrawl_listrak.py

This will:
1. Check which Listrak URLs are marked as 'failed'
2. Reset them to 'pending'
3. Trigger a re-crawl via the API
4. Verify they succeed and data appears in Pinecone
"""

import os
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'RICHCSM')

# API endpoint (change to production URL)
API_BASE = "https://flow-state-beta-production.up.railway.app"  # Update this

def main():
    print("=== Listrak Re-Crawl Script ===\n")

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get failed Listrak documents
    cur.execute("""
        SELECT d.id, d.url, d.crawl_status
        FROM esp_documents d
        JOIN esps e ON d.esp_id = e.id
        WHERE e.name = 'listrak'
        AND d.crawl_status = 'failed'
        ORDER BY d.url
    """)

    failed_docs = cur.fetchall()

    if not failed_docs:
        print("✓ No failed Listrak documents found!")
        cur.close()
        conn.close()
        return

    print(f"Found {len(failed_docs)} failed Listrak documents:\n")
    urls_to_recrawl = []
    for doc_id, url, status in failed_docs:
        print(f"  - {url}")
        urls_to_recrawl.append(url)

    print(f"\nResetting status to 'pending'...")
    for doc_id, url, status in failed_docs:
        cur.execute("""
            UPDATE esp_documents
            SET crawl_status = 'pending', last_crawled_at = NULL
            WHERE id = %s
        """, (doc_id,))

    conn.commit()
    print("✓ Reset complete\n")

    # Trigger re-crawl via API
    print(f"Triggering re-crawl via API: {API_BASE}/api/admin/esp/listrak/crawl-selected")

    response = requests.post(
        f"{API_BASE}/api/admin/esp/listrak/crawl-selected",
        json={'urls': urls_to_recrawl},
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ API response: {result.get('message', 'Success')}")
        print(f"  Success: {len(result.get('results', {}).get('success', []))}")
        print(f"  Failed: {len(result.get('results', {}).get('failed', []))}")

        if result.get('results', {}).get('failed'):
            print("\nFailed URLs:")
            for fail in result['results']['failed']:
                print(f"  - {fail['url']}: {fail['error']}")
    else:
        print(f"✗ API error: {response.status_code}")
        print(f"  Response: {response.text}")

    # Check final status
    print("\n=== Final Status Check ===")
    cur.execute("""
        SELECT d.url, d.crawl_status, d.last_crawled_at
        FROM esp_documents d
        JOIN esps e ON d.esp_id = e.id
        WHERE e.name = 'listrak'
        ORDER BY d.url
    """)

    docs = cur.fetchall()
    for url, status, last_crawled in docs:
        status_icon = "✓" if status == "completed" else "✗" if status == "failed" else "⏳"
        print(f"{status_icon} {url}: {status}")
        if last_crawled:
            print(f"   Last crawled: {last_crawled}")

    cur.close()
    conn.close()

    print("\n=== Next Steps ===")
    print("1. Check Pinecone for 'listrak' namespace:")
    print("   python3 check_listrak_pinecone.py")
    print("\n2. Test in the app:")
    print("   - Select Listrak ESP")
    print("   - Ask: 'How do I integrate Yotpo Loyalty with Listrak?'")
    print("   - Verify AI gives a real answer")

if __name__ == "__main__":
    main()
