#!/usr/bin/env python3
"""
Test the complete flow of adding a brand new ESP with links.

This simulates:
1. Creating a new ESP in database
2. Adding URLs to the ESP
3. Crawling the URLs
4. Verifying vectorization
5. Testing RAG search

Run this LOCALLY before deploying to catch any issues.
"""

import os
import sys
import json
import requests

sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv()

def main():
    print("=== New ESP Flow Test ===\n")

    # Test configuration
    TEST_ESP = "test_mailchimp"
    TEST_URLS = [
        "https://help.listrak.com/en/articles/2283752-integration-guide-yotpo",  # Known working URL
    ]

    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

    print(f"Testing with ESP: {TEST_ESP}")
    print(f"Test URLs: {len(TEST_URLS)}")
    print()

    # Step 1: Create ESP in database
    print("=== Step 1: Create ESP in Database ===")
    try:
        from esp_manager import get_esp_manager
        esp_mgr = get_esp_manager()

        # Check if exists
        existing = esp_mgr.get_esp_by_name(TEST_ESP)
        if existing:
            print(f"⚠ ESP '{TEST_ESP}' already exists, deleting...")
            # Clean up previous test
            esp_mgr.delete_documents_by_urls(TEST_ESP, TEST_URLS)
        else:
            # Create new ESP
            print(f"Creating new ESP: {TEST_ESP}")
            esp = esp_mgr.create_esp(
                name=TEST_ESP,
                display_name="Test Mailchimp",
                description="Test ESP for flow verification"
            )
            print(f"✓ Created ESP with ID: {esp['id']}")
    except Exception as e:
        print(f"✗ Database error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Add URLs
    print("\n=== Step 2: Add URLs ===")
    try:
        esp = esp_mgr.get_esp_by_name(TEST_ESP)
        for url in TEST_URLS:
            doc = esp_mgr.add_document(TEST_ESP, url)
            print(f"✓ Added URL: {url}")
            print(f"  Document ID: {doc['id']}")
    except Exception as e:
        print(f"✗ Failed to add URLs: {e}")
        return

    # Step 3: Crawl URLs (simulate API endpoint)
    print("\n=== Step 3: Crawl URLs ===")
    try:
        from crawler import crawl_single_url

        base_docs_path = os.path.join(BASE_PATH, 'docs')
        esp_docs_path = os.path.join(base_docs_path, TEST_ESP)
        os.makedirs(esp_docs_path, exist_ok=True)

        for url in TEST_URLS:
            print(f"Crawling {url}...")
            filename = crawl_single_url(url, TEST_ESP, BASE_PATH)

            if filename:
                print(f"  ✓ Saved as: {filename}")

                # Check file exists and has content
                file_path = os.path.join(esp_docs_path, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"  ✓ File size: {len(content)} bytes")
                else:
                    print(f"  ✗ File not found: {file_path}")
            else:
                print(f"  ✗ Crawl failed")
                return
    except Exception as e:
        print(f"✗ Crawl error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Update metadata (what the API does)
    print("\n=== Step 4: Update Metadata ===")
    try:
        metadata_path = os.path.join(base_docs_path, 'crawl_metadata.json')

        # Load existing
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except FileNotFoundError:
            metadata = {}

        if TEST_ESP not in metadata:
            metadata[TEST_ESP] = []

        # Add document metadata
        for url in TEST_URLS:
            filename = crawl_single_url(url, TEST_ESP, BASE_PATH)
            if filename:
                file_path = os.path.join(esp_docs_path, filename)
                doc_metadata = {
                    'url': url,
                    'filename': filename,
                    'filepath': file_path
                }

                # Remove old entry if exists
                metadata[TEST_ESP] = [d for d in metadata[TEST_ESP] if d.get('url') != url]
                metadata[TEST_ESP].append(doc_metadata)

        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ Updated crawl_metadata.json with {len(metadata[TEST_ESP])} documents")
    except Exception as e:
        print(f"✗ Metadata update error: {e}")
        return

    # Step 5: Vectorize
    print("\n=== Step 5: Vectorize ===")
    try:
        from adapters.vector.vector_manager import get_vector_adapter

        vectorizer = get_vector_adapter(persist_directory=os.path.join(BASE_PATH, 'backend/chroma_db'))

        print(f"Calling vectorizer.refresh_esp('{TEST_ESP}', '{base_docs_path}')")
        vectorizer.refresh_esp(TEST_ESP, base_docs_path)

        print(f"✓ Vectorization complete!")
    except Exception as e:
        print(f"✗ Vectorization error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 6: Verify in Pinecone
    print("\n=== Step 6: Verify Pinecone ===")
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index('esp-loyalty-docs1')

        # Query with filter
        dummy_vector = [0.0] * 384
        results = index.query(
            vector=dummy_vector,
            top_k=5,
            filter={"esp": {"$eq": TEST_ESP}},
            include_metadata=True
        )

        if results.matches:
            print(f"✓ Found {len(results.matches)} vectors in Pinecone")
            for match in results.matches:
                print(f"  - {match.metadata.get('filename', 'unknown')}")
        else:
            print(f"✗ No vectors found for ESP '{TEST_ESP}'")
            return
    except Exception as e:
        print(f"✗ Pinecone check error: {e}")
        return

    # Step 7: Test RAG search
    print("\n=== Step 7: Test RAG Search ===")
    try:
        query = "What is Mailchimp?"
        results = vectorizer.search(query, esp_filter=TEST_ESP, n_results=3)

        if results['documents'][0]:
            print(f"✓ RAG search returned {len(results['documents'][0])} results")
            for i, doc in enumerate(results['documents'][0], 1):
                snippet = doc[:100] + "..." if len(doc) > 100 else doc
                print(f"  {i}. {snippet}")
        else:
            print(f"✗ No search results for query: '{query}'")
            return
    except Exception as e:
        print(f"✗ RAG search error: {e}")
        return

    # Step 8: Cleanup (optional)
    print("\n=== Step 8: Cleanup ===")
    cleanup = input("Delete test ESP? (y/n): ").strip().lower()
    if cleanup == 'y':
        try:
            # Delete from database
            esp_mgr.delete_documents_by_urls(TEST_ESP, TEST_URLS)

            # Delete from Pinecone
            existing = index.query(
                vector=dummy_vector,
                top_k=10000,
                filter={"esp": {"$eq": TEST_ESP}},
                include_metadata=False
            )
            existing_ids = [match['id'] for match in existing['matches']]
            if existing_ids:
                index.delete(ids=existing_ids)
                print(f"✓ Deleted {len(existing_ids)} vectors from Pinecone")

            # Delete files
            import shutil
            if os.path.exists(esp_docs_path):
                shutil.rmtree(esp_docs_path)
                print(f"✓ Deleted folder: {esp_docs_path}")

            # Update metadata
            if TEST_ESP in metadata:
                del metadata[TEST_ESP]
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"✓ Removed from crawl_metadata.json")

            print("✓ Cleanup complete")
        except Exception as e:
            print(f"⚠ Cleanup error: {e}")
    else:
        print("⚠ Test ESP left in system (clean up manually later)")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nThe complete flow works:")
    print("  1. ✓ Create ESP in database")
    print("  2. ✓ Add URLs")
    print("  3. ✓ Crawl content")
    print("  4. ✓ Update metadata")
    print("  5. ✓ Vectorize documents")
    print("  6. ✓ Data in Pinecone")
    print("  7. ✓ RAG search works")
    print("\n🎉 You can safely add new ESPs in production!")

if __name__ == "__main__":
    main()
