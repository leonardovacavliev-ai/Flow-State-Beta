"""
Inspect what chunks exist in Pinecone for the Klaviyo document
"""
import os
from dotenv import load_dotenv
from backend.adapters.vector.vector_manager import get_vector_adapter

# Load environment variables
load_dotenv()

# Initialize vector adapter
vectorizer = get_vector_adapter(persist_directory="backend/chroma_db")

print(f"\n{'='*80}")
print(f"INSPECTING KLAVIYO DOCUMENT CHUNKS IN PINECONE")
print(f"{'='*80}\n")

# Search for all chunks from the loyalty setup guide
query = "customer properties list"
results = vectorizer.search(query, esp_filter="klaviyo", n_results=20)

if results['documents'] and results['documents'][0]:
    print(f"Found {len(results['documents'][0])} chunks\n")

    for i, (doc_id, doc, metadata) in enumerate(zip(
        results['ids'][0],
        results['documents'][0],
        results['metadatas'][0]
    )):
        filename = metadata.get('filename', 'Unknown')

        # Only show chunks from the loyalty setup guide
        if 'loyalty-emails-setup-guide' in filename:
            print(f"Chunk {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  Filename: {filename}")
            print(f"  Chunk index: {metadata.get('chunk_index', 'N/A')}")

            # Check if this chunk contains the property definitions
            if 'loyalty_nt_points' in doc:
                print(f"  ✅ Contains 'loyalty_nt_points'")
            else:
                print(f"  ❌ Does not contain 'loyalty_nt_points'")

            # Show preview
            print(f"  Preview: {doc[:150]}...")
            print()
else:
    print("No results found!")

# Now do a specific search for "points to next tier"
print(f"\n{'='*80}")
print(f"SPECIFIC SEARCH: 'points to next tier'")
print(f"{'='*80}\n")

query2 = "points to next tier property klaviyo"
results2 = vectorizer.search(query2, esp_filter="klaviyo", n_results=5)

if results2['documents'] and results2['documents'][0]:
    print(f"Found {len(results2['documents'][0])} results\n")

    for i, (doc, metadata) in enumerate(zip(results2['documents'][0], results2['metadatas'][0])):
        print(f"Result {i+1}:")

        # Check if this chunk contains the property definitions
        if 'loyalty_nt_points' in doc:
            print(f"  ✅ Contains 'loyalty_nt_points'")
        else:
            print(f"  ❌ Does not contain 'loyalty_nt_points'")

        print(f"  Chunk index: {metadata.get('chunk_index', 'N/A')}")
        print(f"  Content: {doc[:300]}...")
        print()
