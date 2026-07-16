#!/usr/bin/env python3
"""
Test Pinecone connection and basic operations

Usage:
    export PINECONE_API_KEY=your-key
    export PINECONE_INDEX_NAME=esp-loyalty-docs1
    python test_pinecone.py
"""

import os
from adapters.vector.vector_manager import get_vector_adapter

def test_pinecone():
    """Test Pinecone adapter functionality"""

    print("=" * 60)
    print("Pinecone Connection Test")
    print("=" * 60)

    # Check environment
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'esp-loyalty-docs1')

    if not api_key:
        print("❌ PINECONE_API_KEY not set")
        return False

    print(f"\nIndex: {index_name}")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")

    # Test 1: Connection
    print("\n1. Testing connection...")
    try:
        adapter = get_vector_adapter(
            provider='pinecone',
            api_key=api_key,
            index_name=index_name
        )
        print("   ✓ Connected successfully")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

    # Test 2: Get count
    print("\n2. Checking index stats...")
    try:
        count = adapter.get_collection_count()
        print(f"   ✓ Total vectors: {count}")
    except Exception as e:
        print(f"   ❌ Stats check failed: {e}")
        return False

    # Test 3: Add test document
    print("\n3. Adding test document...")
    try:
        test_metadata = {
            'esp': 'test',
            'filename': 'test_doc.txt',
            'source_url': 'http://test.com',
            'filepath': '/tmp/test.txt'
        }
        adapter.add_document("This is a test document for Pinecone.", test_metadata)
        print("   ✓ Document added")
    except Exception as e:
        print(f"   ❌ Add document failed: {e}")
        return False

    # Test 4: Search
    print("\n4. Testing search...")
    try:
        results = adapter.search("test document", n_results=1)
        if results['documents'] and len(results['documents'][0]) > 0:
            print(f"   ✓ Search returned {len(results['documents'][0])} results")
            print(f"   First result: {results['documents'][0][0][:50]}...")
        else:
            print("   ⚠️  Search returned no results")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return False

    # Test 5: ESP-filtered search
    print("\n5. Testing ESP-filtered search...")
    try:
        results = adapter.search("test document", esp_filter='test', n_results=1)
        if results['documents'] and len(results['documents'][0]) > 0:
            print(f"   ✓ Filtered search returned {len(results['documents'][0])} results")
        else:
            print("   ⚠️  Filtered search returned no results")
    except Exception as e:
        print(f"   ❌ Filtered search failed: {e}")
        return False

    # Test 6: Delete test document
    print("\n6. Cleaning up test document...")
    try:
        adapter.delete_documents(['test_test_doc.txt_0'])
        print("   ✓ Test document deleted")
    except Exception as e:
        print(f"   ⚠️  Cleanup failed (not critical): {e}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nYour Pinecone index is ready to use.")
    print("Update .env to switch:")
    print("   VECTOR_DB_PROVIDER=pinecone")

    return True

if __name__ == "__main__":
    success = test_pinecone()
    exit(0 if success else 1)
