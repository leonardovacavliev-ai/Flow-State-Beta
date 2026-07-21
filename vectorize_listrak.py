#!/usr/bin/env python3
"""
Manually vectorize Listrak documents that are already crawled but not vectorized.

This script:
1. Checks if Listrak docs exist in the filesystem
2. Updates crawl_metadata.json
3. Triggers vectorization
4. Verifies data appears in Pinecone
"""

import os
import sys
import json

sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv()

def main():
    print("=== Listrak Vectorization Script ===\n")

    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    docs_path = os.path.join(BASE_PATH, 'docs')
    listrak_path = os.path.join(docs_path, 'listrak')

    # Check if files exist
    if not os.path.exists(listrak_path):
        print(f"✗ Listrak folder not found: {listrak_path}")
        return

    files = [f for f in os.listdir(listrak_path) if f.endswith('.txt') and f != '.gitkeep']
    if not files:
        print(f"✗ No .txt files found in {listrak_path}")
        return

    print(f"Found {len(files)} Listrak documents:\n")
    for f in files:
        print(f"  - {f}")

    # Update crawl_metadata.json
    print("\n=== Updating crawl_metadata.json ===")
    metadata_path = os.path.join(docs_path, 'crawl_metadata.json')

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print("✗ crawl_metadata.json not found")
        return

    # Build listrak metadata
    listrak_metadata = []
    for filename in files:
        filepath = os.path.join(listrak_path, filename)

        # Read URL from file
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            url = first_line.replace('Source URL: ', '') if first_line.startswith('Source URL:') else 'unknown'

        listrak_metadata.append({
            'url': url,
            'filename': filename,
            'filepath': filepath
        })

    metadata['listrak'] = listrak_metadata

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Updated crawl_metadata.json with {len(listrak_metadata)} documents")

    # Vectorize
    print("\n=== Vectorizing Listrak documents ===")
    try:
        from adapters.vector.vector_manager import get_vector_adapter

        vectorizer = get_vector_adapter(persist_directory=os.path.join(BASE_PATH, 'backend/chroma_db'))
        vectorizer.refresh_esp('listrak', docs_path)

        print("✓ Vectorization complete!")

    except Exception as e:
        print(f"✗ Vectorization error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verify in Pinecone
    print("\n=== Verifying Pinecone ===")
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index('esp-loyalty-docs1')

        stats = index.describe_index_stats()

        if 'listrak' in stats.namespaces or '' in stats.namespaces:
            # Check default namespace (older code stored everything there)
            default_count = stats.namespaces.get('', {}).vector_count or 0
            listrak_count = stats.namespaces.get('listrak', {}).vector_count or 0

            print(f"Default namespace: {default_count} vectors")
            if listrak_count > 0:
                print(f"✓ Listrak namespace: {listrak_count} vectors")
            else:
                print(f"⚠ No dedicated Listrak namespace (vectors in default namespace)")

            # Sample query
            print("\nSample search test:")
            results = index.query(
                vector=[0.0] * 384,
                top_k=3,
                filter={"esp": {"$eq": "listrak"}},
                include_metadata=True
            )

            if results.matches:
                print(f"✓ Found {len(results.matches)} Listrak vectors via filter")
                for match in results.matches[:3]:
                    print(f"  - {match.metadata.get('filename', 'unknown')}")
            else:
                print("✗ No Listrak vectors found (check filter metadata)")
        else:
            print("✗ No data in Pinecone")

    except Exception as e:
        print(f"✗ Pinecone check error: {e}")

    print("\n=== Next Steps ===")
    print("1. Test in the app:")
    print("   - Select 'Listrak' ESP")
    print("   - Ask: 'How do I integrate Yotpo Loyalty with Listrak?'")
    print("   - Should get specific answer with Listrak details")
    print("\n2. If still not working, check Railway logs for vectorization errors")

if __name__ == "__main__":
    main()
