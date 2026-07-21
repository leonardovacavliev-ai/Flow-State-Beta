#!/usr/bin/env python3
"""Check if Listrak data exists in Pinecone"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('esp-loyalty-docs1')

# Get index stats
stats = index.describe_index_stats()
print("=== Pinecone Index Stats ===")
print(f"Total vectors: {stats.total_vector_count}")
print(f"\nNamespaces:")
for namespace, info in stats.namespaces.items():
    print(f"  {namespace}: {info.vector_count} vectors")

# Check for Listrak specifically
print("\n=== Checking for Listrak data ===")
if 'listrak' in stats.namespaces:
    count = stats.namespaces['listrak'].vector_count
    print(f"✓ Found Listrak namespace with {count} vectors")

    # Query a few vectors to see what's there
    print("\nSample Listrak vectors:")
    results = index.query(
        namespace='listrak',
        vector=[0.0] * 384,  # Dummy vector
        top_k=5,
        include_metadata=True
    )
    for match in results.matches:
        print(f"  ID: {match.id}")
        print(f"  Metadata: {match.metadata}")
        print()
else:
    print("✗ No Listrak namespace found in Pinecone")
    print("\nAvailable namespaces:", list(stats.namespaces.keys()))
