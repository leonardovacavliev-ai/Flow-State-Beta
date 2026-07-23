"""
Inspect what's actually in Pinecone
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX_NAME', 'esp-loyalty-docs1'))
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Query with a generic vector to fetch some samples
query_vector = embedding_model.encode("sample query").tolist()

print("="*80)
print("INSPECTING PINECONE INDEX")
print("="*80)

# Fetch from default namespace
results = index.query(
    vector=query_vector,
    top_k=5,
    include_metadata=True
)

print(f"\nFound {len(results.matches)} vectors in DEFAULT namespace")
print("\nSample vectors:")
print("-"*80)

for i, match in enumerate(results.matches):
    print(f"\n[Vector {i+1}]")
    print(f"ID: {match.id}")
    print(f"Score: {match.score:.4f}")
    if match.metadata:
        print(f"Metadata keys: {list(match.metadata.keys())}")
        print(f"ESP: {match.metadata.get('esp', 'N/A')}")
        print(f"Filename: {match.metadata.get('filename', 'N/A')}")
        print(f"Source URL: {match.metadata.get('source_url', 'N/A')[:80]}...")
        if 'text' in match.metadata:
            print(f"Text: {match.metadata['text'][:150]}...")
    else:
        print("No metadata!")

# Now try querying WITH filter
print("\n" + "="*80)
print("TESTING FILTER QUERY (esp=klaviyo)")
print("="*80)

filtered_results = index.query(
    vector=query_vector,
    filter={"esp": {"$eq": "klaviyo"}},
    top_k=5,
    include_metadata=True
)

print(f"\nFound {len(filtered_results.matches)} vectors with esp=klaviyo")

if filtered_results.matches:
    for i, match in enumerate(filtered_results.matches):
        print(f"\n[Match {i+1}]")
        print(f"ID: {match.id}")
        print(f"ESP: {match.metadata.get('esp', 'N/A')}")
        print(f"Text: {match.metadata.get('text', 'N/A')[:100]}...")
else:
    print("\n⚠️  No results with filter! This confirms the issue.")
    print("\nPossible causes:")
    print("1. ESP metadata field doesn't exist")
    print("2. ESP values don't match (e.g., 'Klaviyo' vs 'klaviyo')")
    print("3. Vectors were upserted without namespace/metadata")

print("\n" + "="*80)
