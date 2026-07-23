"""
Fetch and inspect chunk 10 specifically
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# Initialize
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX_NAME', 'esp-loyalty-docs1'))

# Fetch chunk 10 directly by ID
chunk_id = "klaviyo_docs_loyalty-emails-setup-guide-for-klaviyo.txt_10"

print("="*80)
print(f"FETCHING CHUNK: {chunk_id}")
print("="*80)

try:
    result = index.fetch(ids=[chunk_id])

    if chunk_id in result.vectors:
        vector_data = result.vectors[chunk_id]
        metadata = vector_data.metadata
        text = metadata.get('text', '')

        print(f"\nChunk Index: {metadata.get('chunk_index')}")
        print(f"Total Chunks: {metadata.get('total_chunks')}")
        print(f"ESP: {metadata.get('esp')}")
        print(f"Filename: {metadata.get('filename')}")
        print(f"Source URL: {metadata.get('source_url')}")

        # Check for our properties
        has_nt_points = 'loyalty_nt_points' in text
        has_referral_link = 'swell_referral_link' in text

        print(f"\n✓ Contains 'loyalty_nt_points': {has_nt_points}")
        print(f"✓ Contains 'swell_referral_link': {has_referral_link}")

        # Find the exact position
        if has_nt_points:
            idx = text.find('loyalty_nt_points')
            context_start = max(0, idx - 200)
            context_end = min(len(text), idx + 400)
            print(f"\nContext around 'loyalty_nt_points':")
            print("-"*80)
            print(text[context_start:context_end])
            print("-"*80)

    else:
        print(f"\n⚠️  Chunk {chunk_id} not found in index")

except Exception as e:
    print(f"\n⚠️  Error: {e}")

print("\n" + "="*80)
