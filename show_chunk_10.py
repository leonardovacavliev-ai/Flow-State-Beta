"""
Show the full content of chunk 10 which contains loyalty_nt_points
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX', 'esp-loyalty-docs1'))

# Fetch chunk 10 directly by ID
chunk_id = "klaviyo_docs_loyalty-emails-setup-guide-for-klaviyo.txt_10"

print(f"\n{'='*80}")
print(f"FETCHING CHUNK 10 DIRECTLY")
print(f"{'='*80}\n")

try:
    result = index.fetch(ids=[chunk_id])

    if hasattr(result, 'vectors') and chunk_id in result.vectors:
        vector_data = result.vectors[chunk_id]
        metadata = vector_data['metadata']
        text = metadata.get('text', '')

        print(f"Chunk ID: {chunk_id}")
        print(f"Chunk index: {metadata.get('chunk_index', 'N/A')}")
        print(f"Total chunks: {metadata.get('total_chunks', 'N/A')}")
        print(f"ESP: {metadata.get('esp', 'N/A')}")
        print(f"Filename: {metadata.get('filename', 'N/A')}")
        print(f"\n{'-'*80}")
        print("FULL CONTENT:")
        print(f"{'-'*80}\n")
        print(text)

        # Highlight the property
        if 'loyalty_nt_points' in text:
            print(f"\n{'-'*80}")
            print("✅ This chunk DOES contain 'loyalty_nt_points'")
            print(f"{'-'*80}\n")

            # Find and show the relevant section
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'loyalty_nt' in line.lower() or 'loyalty_mt' in line.lower():
                    start = max(0, i - 3)
                    end = min(len(lines), i + 5)
                    print(f"Context around property (lines {start}-{end}):")
                    for j in range(start, end):
                        prefix = ">>> " if j == i else "    "
                        print(f"{prefix}{lines[j]}")
                    print()
    else:
        print(f"❌ Chunk {chunk_id} not found in index")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
