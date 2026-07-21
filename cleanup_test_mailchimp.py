#!/usr/bin/env python3
"""
Complete cleanup of test_mailchimp from all systems:
1. PostgreSQL database (ESP + documents)
2. Pinecone (vectors)
3. Filesystem (docs folder)
4. Metadata (crawl_metadata.json)
"""

import os
import sys
import json
import shutil
import psycopg2
from pinecone import Pinecone
from dotenv import load_dotenv

sys.path.insert(0, 'backend')
load_dotenv()

TEST_ESP = "test_mailchimp"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

print("=== test_mailchimp Cleanup ===\n")

# 1. PostgreSQL Cleanup
print("=== Step 1: PostgreSQL ===")
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    # Get ESP ID
    cur.execute("SELECT id FROM esps WHERE name = %s", (TEST_ESP,))
    result = cur.fetchone()

    if result:
        esp_id = result[0]
        print(f"Found ESP: {esp_id}")

        # Count documents
        cur.execute("SELECT COUNT(*) FROM esp_documents WHERE esp_id = %s", (esp_id,))
        doc_count = cur.fetchone()[0]
        print(f"Found {doc_count} documents")

        # Delete documents
        cur.execute("DELETE FROM esp_documents WHERE esp_id = %s", (esp_id,))
        deleted_docs = cur.rowcount
        print(f"✓ Deleted {deleted_docs} documents")

        # Delete ESP
        cur.execute("DELETE FROM esps WHERE id = %s", (esp_id,))
        print(f"✓ Deleted ESP")

        conn.commit()
    else:
        print("ESP not found in database")

    cur.close()
    conn.close()
except Exception as e:
    print(f"✗ Database error: {e}")

# 2. Pinecone Cleanup
print("\n=== Step 2: Pinecone ===")
try:
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index('esp-loyalty-docs1')

    # Query for test_mailchimp vectors
    dummy_vector = [0.0] * 384
    results = index.query(
        vector=dummy_vector,
        top_k=10000,
        filter={"esp": {"$eq": TEST_ESP}},
        include_metadata=False
    )

    vector_ids = [match['id'] for match in results['matches']]

    if vector_ids:
        print(f"Found {len(vector_ids)} vectors")
        # Delete in batches
        batch_size = 1000
        for i in range(0, len(vector_ids), batch_size):
            batch = vector_ids[i:i + batch_size]
            index.delete(ids=batch)
        print(f"✓ Deleted {len(vector_ids)} vectors from Pinecone")
    else:
        print("No vectors found in Pinecone")

except Exception as e:
    print(f"✗ Pinecone error: {e}")

# 3. Filesystem Cleanup
print("\n=== Step 3: Filesystem ===")
try:
    docs_path = os.path.join(BASE_PATH, 'docs', TEST_ESP)

    if os.path.exists(docs_path):
        files = [f for f in os.listdir(docs_path) if f.endswith('.txt')]
        print(f"Found folder with {len(files)} files")

        shutil.rmtree(docs_path)
        print(f"✓ Deleted folder: {docs_path}")
    else:
        print("Folder does not exist")

except Exception as e:
    print(f"✗ Filesystem error: {e}")

# 4. Metadata Cleanup
print("\n=== Step 4: crawl_metadata.json ===")
try:
    metadata_path = os.path.join(BASE_PATH, 'docs', 'crawl_metadata.json')

    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        if TEST_ESP in metadata:
            doc_count = len(metadata[TEST_ESP])
            print(f"Found {doc_count} documents in metadata")

            del metadata[TEST_ESP]

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"✓ Removed test_mailchimp from crawl_metadata.json")
        else:
            print("Not found in metadata")
    else:
        print("Metadata file does not exist")

except Exception as e:
    print(f"✗ Metadata error: {e}")

# 5. Verification
print("\n=== Verification ===")
try:
    # Check Pinecone
    results = index.query(
        vector=dummy_vector,
        top_k=10,
        filter={"esp": {"$eq": TEST_ESP}},
        include_metadata=False
    )

    if results['matches']:
        print(f"⚠ Still found {len(results['matches'])} vectors in Pinecone!")
    else:
        print("✓ Pinecone: clean")

    # Check filesystem
    if os.path.exists(docs_path):
        print(f"⚠ Folder still exists: {docs_path}")
    else:
        print("✓ Filesystem: clean")

    # Check database
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM esps WHERE name = %s", (TEST_ESP,))
    count = cur.fetchone()[0]
    if count > 0:
        print(f"⚠ ESP still in database!")
    else:
        print("✓ Database: clean")
    cur.close()
    conn.close()

except Exception as e:
    print(f"✗ Verification error: {e}")

print("\n" + "="*60)
print("✅ CLEANUP COMPLETE")
print("="*60)
print("\ntest_mailchimp removed from:")
print("  ✓ PostgreSQL (ESP + documents)")
print("  ✓ Pinecone (vectors)")
print("  ✓ Filesystem (docs folder)")
print("  ✓ Metadata (crawl_metadata.json)")
