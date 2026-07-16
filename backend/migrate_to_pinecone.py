#!/usr/bin/env python3
"""
Migration script to copy data from ChromaDB to Pinecone

Usage:
    python migrate_to_pinecone.py

Environment variables required:
    PINECONE_API_KEY
    PINECONE_INDEX_NAME (default: esp-loyalty-docs1)
"""

import os
import sys
from adapters.vector.vector_manager import get_vector_adapter

def migrate_chromadb_to_pinecone():
    """Copy all documents from ChromaDB to Pinecone"""

    # Paths
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_path = os.path.join(base_path, "docs")
    chroma_path = os.path.join(base_path, "backend/chroma_db")

    print("=" * 60)
    print("ChromaDB → Pinecone Migration")
    print("=" * 60)

    # Validate environment
    if not os.getenv('PINECONE_API_KEY'):
        print("❌ Error: PINECONE_API_KEY not set")
        sys.exit(1)

    pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'esp-loyalty-docs1')
    print(f"\nTarget Pinecone index: {pinecone_index}")

    # Initialize adapters
    print("\n1. Connecting to ChromaDB...")
    try:
        chroma_adapter = get_vector_adapter(
            provider='chromadb',
            persist_directory=chroma_path
        )
        doc_count = chroma_adapter.get_collection_count()
        print(f"   ✓ ChromaDB connected ({doc_count} chunks)")
    except Exception as e:
        print(f"   ❌ ChromaDB connection failed: {e}")
        sys.exit(1)

    print("\n2. Connecting to Pinecone...")
    try:
        pinecone_adapter = get_vector_adapter(
            provider='pinecone',
            api_key=os.getenv('PINECONE_API_KEY'),
            index_name=pinecone_index
        )
        print(f"   ✓ Pinecone connected")
    except Exception as e:
        print(f"   ❌ Pinecone connection failed: {e}")
        sys.exit(1)

    # Migrate data
    print("\n3. Migrating documents...")
    print("   (This will re-vectorize all docs from source files)")

    try:
        pinecone_adapter.vectorize_all_docs(docs_path)
        print("\n   ✓ Migration complete!")
    except Exception as e:
        print(f"\n   ❌ Migration failed: {e}")
        sys.exit(1)

    # Verify
    print("\n4. Verifying migration...")
    pinecone_count = pinecone_adapter.get_collection_count()
    print(f"   ChromaDB: {doc_count} chunks")
    print(f"   Pinecone: {pinecone_count} vectors")

    if pinecone_count > 0:
        print("\n✅ Migration successful!")
        print("\nTo switch to Pinecone, update .env:")
        print("   VECTOR_DB_PROVIDER=pinecone")
        print(f"   PINECONE_INDEX_NAME={pinecone_index}")
    else:
        print("\n⚠️  Warning: Pinecone index is empty")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    migrate_chromadb_to_pinecone()
