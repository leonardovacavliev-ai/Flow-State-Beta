#!/usr/bin/env python3
"""
Fix stuck Omnisend URLs by crawling and vectorizing them manually.
"""

import os
import sys
import json
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from crawler import crawl_single_url
from adapters.vector.vector_manager import get_vector_adapter

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=== Fixing Stuck Omnisend URLs ===\n")

    # Connect to database
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    # Get pending Omnisend docs
    cur.execute("""
        SELECT d.id, d.url, e.name
        FROM esp_documents d
        JOIN esps e ON d.esp_id = e.id
        WHERE e.name = 'omnisend' AND d.crawl_status = 'pending'
        ORDER BY d.created_at
    """)

    pending_docs = cur.fetchall()

    if not pending_docs:
        print("✓ No pending Omnisend documents found!")
        cur.close()
        conn.close()
        return

    print(f"Found {len(pending_docs)} pending documents:\n")
    for doc_id, url, esp_name in pending_docs:
        print(f"  - {url}")

    print("\n=== Crawling ===")
    docs_path = os.path.join(BASE_PATH, 'docs')

    for doc_id, url, esp_name in pending_docs:
        print(f"\nProcessing: {url}")

        # Crawl
        filename = crawl_single_url(url, esp_name, BASE_PATH)

        if not filename:
            print(f"  ✗ Crawl failed")
            cur.execute("""
                UPDATE esp_documents
                SET crawl_status = 'failed', error_message = 'Manual crawl failed'
                WHERE id = %s
            """, (doc_id,))
            continue

        print(f"  ✓ Crawled: {filename}")

        # Read content for hash
        file_path = os.path.join(docs_path, esp_name, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Calculate hash
        import hashlib
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Update crawl_metadata.json
        metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except FileNotFoundError:
            metadata = {}

        if esp_name not in metadata:
            metadata[esp_name] = []

        # Remove old entry if exists
        metadata[esp_name] = [d for d in metadata[esp_name] if d.get('url') != url]
        metadata[esp_name].append({
            'url': url,
            'filename': filename,
            'filepath': file_path
        })

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"  ✓ Updated metadata")

        # Update database
        cur.execute("""
            UPDATE esp_documents
            SET crawl_status = 'completed',
                filename = %s,
                content_hash = %s,
                last_crawled_at = NOW()
            WHERE id = %s
        """, (filename, content_hash, doc_id))

        print(f"  ✓ Updated database")

    conn.commit()

    # Vectorize all omnisend docs
    print("\n=== Vectorizing ===")
    try:
        vectorizer = get_vector_adapter(persist_directory=os.path.join(BASE_PATH, 'backend/chroma_db'))
        vectorizer.refresh_esp('omnisend', docs_path)
        print("✓ Vectorization complete!")
    except Exception as e:
        print(f"✗ Vectorization error: {e}")
        import traceback
        traceback.print_exc()

    cur.close()
    conn.close()

    print("\n=== Done! ===")
    print("Check Pinecone: python3 check_omnisend.py")

if __name__ == "__main__":
    main()
