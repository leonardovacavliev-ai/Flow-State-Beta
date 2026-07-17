#!/usr/bin/env python3
"""
Fix Pinecone data by re-vectorizing all documents with correct ESP metadata
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from adapters.vector.vector_manager import get_vector_adapter

load_dotenv()

def main():
    print("="*80)
    print("FIXING PINECONE DATA")
    print("="*80)

    # Validate
    if not os.getenv('PINECONE_API_KEY'):
        print("\n❌ Error: PINECONE_API_KEY not set in .env")
        sys.exit(1)

    base_path = os.path.dirname(os.path.abspath(__file__))
    docs_path = os.path.join(base_path, "docs")

    print("\n1. Connecting to Pinecone...")
    pinecone = get_vector_adapter()

    # Check current state
    try:
        from pinecone import Pinecone as PC
        pc = PC(api_key=os.getenv('PINECONE_API_KEY'))
        index_name = os.getenv('PINECONE_INDEX_NAME', 'esp-loyalty-docs1')
        index = pc.Index(index_name)
        stats = index.describe_index_stats()

        print(f"\n   Current state:")
        print(f"   - Total vectors: {stats.total_vector_count}")
        print(f"   - Namespaces: {list(stats.namespaces.keys())}")

        if '' in stats.namespaces:
            print(f"   - Default namespace: {stats.namespaces[''].vector_count} vectors")

    except Exception as e:
        print(f"\n   ⚠️ Could not check stats: {e}")

    print("\n2. Clearing existing data...")
    try:
        # Delete all vectors (fresh start)
        index.delete(delete_all=True)
        print("   ✓ Cleared all existing vectors")
    except Exception as e:
        print(f"   ⚠️ Could not clear: {e}")

    print("\n3. Re-vectorizing all documents with correct ESP metadata...")
    print("   (This may take 1-2 minutes)")

    try:
        pinecone.vectorize_all_docs(docs_path)
        print("\n   ✓ Vectorization complete!")
    except Exception as e:
        print(f"\n   ❌ Vectorization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n4. Verifying fix...")
    try:
        stats = index.describe_index_stats()

        print(f"\n   New state:")
        print(f"   - Total vectors: {stats.total_vector_count}")
        print(f"   - Namespaces: {list(stats.namespaces.keys())}")

        # Check for ESP-specific data
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        query_vector = embedding_model.encode("test query").tolist()

        # Test Klaviyo namespace
        klaviyo_results = index.query(
            vector=query_vector,
            filter={"esp": {"$eq": "klaviyo"}},
            top_k=1,
            include_metadata=True
        )

        klaviyo_count = len(klaviyo_results.matches)

        if klaviyo_count > 0:
            print(f"\n   ✅ SUCCESS! Found {klaviyo_count} Klaviyo vectors")
            print(f"   Sample metadata: {klaviyo_results.matches[0].metadata}")
        else:
            print(f"\n   ❌ ERROR: No Klaviyo vectors found")
            print(f"   Pinecone might be storing data incorrectly")

    except Exception as e:
        print(f"\n   ⚠️ Verification failed: {e}")

    print("\n" + "="*80)
    print("DONE")
    print("="*80)

    print("\nNext steps:")
    print("1. Restart your Flask app")
    print("2. Test the admin panel - ESPs should now show 'crawled' status")
    print("3. Test a query about Klaviyo properties")

if __name__ == "__main__":
    main()
