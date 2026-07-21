#!/usr/bin/env python3
"""Check if Listrak ESP exists in database and check documents"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("=== All ESPs in database ===")
cur.execute("SELECT id, name, display_name, status FROM esps ORDER BY name")
esps = cur.fetchall()
for esp_id, name, display_name, status in esps:
    print(f"{name}: {display_name} ({status}) - ID: {esp_id}")

print("\n=== Listrak ESP details ===")
cur.execute("SELECT id, name, display_name, status, created_at FROM esps WHERE name = 'listrak'")
listrak = cur.fetchone()

if listrak:
    esp_id, name, display_name, status, created_at = listrak
    print(f"Found Listrak ESP:")
    print(f"  ID: {esp_id}")
    print(f"  Name: {name}")
    print(f"  Display: {display_name}")
    print(f"  Status: {status}")
    print(f"  Created: {created_at}")

    print(f"\n=== Listrak Documents ===")
    cur.execute("""
        SELECT id, url, filename, crawl_status, last_crawled_at, vector_ids
        FROM esp_documents
        WHERE esp_id = %s
        ORDER BY created_at
    """, (esp_id,))
    docs = cur.fetchall()

    if docs:
        for doc_id, url, filename, crawl_status, last_crawled, vector_ids in docs:
            print(f"\nDocument ID: {doc_id}")
            print(f"  URL: {url}")
            print(f"  Filename: {filename}")
            print(f"  Status: {crawl_status}")
            print(f"  Last crawled: {last_crawled}")
            print(f"  Vector IDs: {vector_ids}")
    else:
        print("No documents found for Listrak")
else:
    print("Listrak ESP not found in database")

cur.close()
conn.close()
