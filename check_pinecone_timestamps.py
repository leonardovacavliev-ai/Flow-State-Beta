"""
Check when Klaviyo docs were vectorized to Pinecone
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX', 'esp-loyalty-docs1'))

# Get stats
stats = index.describe_index_stats()
print("\n" + "="*80)
print("PINECONE INDEX STATS")
print("="*80)
print(f"\nTotal vectors: {stats.total_vector_count}")
print(f"\nNamespace breakdown:")

if hasattr(stats, 'namespaces'):
    for namespace, data in stats.namespaces.items():
        count = data.vector_count if hasattr(data, 'vector_count') else data
        print(f"  {namespace}: {count} vectors")

# Fetch a sample Klaviyo vector to see metadata
print("\n" + "="*80)
print("SAMPLE KLAVIYO VECTOR METADATA")
print("="*80)

try:
    # Query to get any Klaviyo vector
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode("test").tolist()

    results = index.query(
        vector=query_vector,
        filter={"esp": {"$eq": "klaviyo"}},
        top_k=1,
        include_metadata=True
    )

    if results.matches:
        match = results.matches[0]
        print(f"\nVector ID: {match.id}")
        print(f"Metadata:")
        for key, value in match.metadata.items():
            if key != 'text':  # Skip the full text content
                print(f"  {key}: {value}")
except Exception as e:
    print(f"\nError fetching sample: {e}")
