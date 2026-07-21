#!/usr/bin/env python3
"""Check test_mailchimp status in database"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, 'backend')
load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("=== test_mailchimp Status ===\n")

# Check ESP
cur.execute("SELECT id, name, display_name, status FROM esps WHERE name = 'test_mailchimp'")
esp = cur.fetchone()

if esp:
    esp_id, name, display_name, status = esp
    print(f"ESP Found:")
    print(f"  ID: {esp_id}")
    print(f"  Name: {name}")
    print(f"  Display: {display_name}")
    print(f"  Status: {status}")

    # Check documents
    print(f"\n=== Documents ===")
    cur.execute("""
        SELECT id, url, filename, crawl_status, last_crawled_at, created_at
        FROM esp_documents
        WHERE esp_id = %s
        ORDER BY created_at
    """, (esp_id,))

    docs = cur.fetchall()
    if docs:
        for doc_id, url, filename, crawl_status, last_crawled, created_at in docs:
            print(f"\nDocument: {doc_id}")
            print(f"  URL: {url}")
            print(f"  Filename: {filename}")
            print(f"  Status: {crawl_status}")
            print(f"  Last crawled: {last_crawled}")
            print(f"  Created: {created_at}")
    else:
        print("No documents found")
else:
    print("test_mailchimp ESP not found in database")

cur.close()
conn.close()
