#!/usr/bin/env python3
"""Check Omnisend ESP status in database and Pinecone"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("=== Omnisend ESP Status ===\n")

# Check if ESP exists
cur.execute("SELECT id, name, display_name, status, created_at FROM esps WHERE name = 'omnisend'")
omnisend = cur.fetchone()

if omnisend:
    esp_id, name, display_name, status, created_at = omnisend
    print(f"✓ Found Omnisend ESP:")
    print(f"  ID: {esp_id}")
    print(f"  Name: {name}")
    print(f"  Display: {display_name}")
    print(f"  Status: {status}")
    print(f"  Created: {created_at}")

    print(f"\n=== Omnisend Documents ===")
    cur.execute("""
        SELECT id, url, filename, crawl_status, last_crawled_at, vector_ids, created_at
        FROM esp_documents
        WHERE esp_id = %s
        ORDER BY created_at
    """, (esp_id,))
    docs = cur.fetchall()

    if docs:
        for doc_id, url, filename, crawl_status, last_crawled, vector_ids, created_at in docs:
            print(f"\nDocument: {filename or 'N/A'}")
            print(f"  URL: {url}")
            print(f"  Status: {crawl_status}")
            print(f"  Created: {created_at}")
            print(f"  Last crawled: {last_crawled}")
            print(f"  Vector IDs: {vector_ids}")
    else:
        print("No documents found for Omnisend")
else:
    print("✗ Omnisend ESP not found in database")

cur.close()
conn.close()

# Check Pinecone
print("\n=== Pinecone Check ===")
try:
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index('esp-loyalty-docs1')

    stats = index.describe_index_stats()
    print(f"Total vectors: {stats.total_vector_count}")

    # Check for omnisend
    dummy_vector = [0.0] * 384
    results = index.query(
        vector=dummy_vector,
        top_k=10,
        filter={"esp": {"$eq": "omnisend"}},
        include_metadata=True
    )

    if results.matches:
        print(f"✓ Found {len(results.matches)} Omnisend vectors")
        for match in results.matches[:3]:
            print(f"  - {match.metadata.get('filename', 'unknown')}")
    else:
        print("✗ No Omnisend vectors found")

except Exception as e:
    print(f"Error checking Pinecone: {e}")
