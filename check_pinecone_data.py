"""
Check if Klaviyo docs are properly indexed in Pinecone
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX_NAME', 'esp-loyalty-docs1'))

# Get index stats
stats = index.describe_index_stats()

print("="*80)
print("PINECONE INDEX STATS")
print("="*80)
print(f"\nTotal vectors: {stats.total_vector_count}")
print(f"\nNamespaces:")
for namespace, info in stats.namespaces.items():
    print(f"  - {namespace}: {info.vector_count} vectors")

# Try a simple query for Klaviyo namespace
print("\n" + "="*80)
print("TESTING KLAVIYO NAMESPACE QUERY")
print("="*80)

from sentence_transformers import SentenceTransformer

# Use same embedding model as the app
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

query = "referral link klaviyo property"
query_embedding = embedding_model.encode(query).tolist()

# Query Klaviyo namespace
try:
    results = index.query(
        vector=query_embedding,
        namespace='klaviyo',
        top_k=5,
        include_metadata=True
    )

    print(f"\nFound {len(results.matches)} results in 'klaviyo' namespace")

    for i, match in enumerate(results.matches):
        print(f"\n[Result {i+1}] Score: {match.score:.4f}")
        print(f"ID: {match.id}")
        if match.metadata:
            print(f"Source: {match.metadata.get('source_url', 'N/A')}")
            print(f"Text: {match.metadata.get('text', 'N/A')[:200]}...")
except Exception as e:
    print(f"\n⚠️  ERROR querying Klaviyo namespace: {e}")

print("\n" + "="*80)
