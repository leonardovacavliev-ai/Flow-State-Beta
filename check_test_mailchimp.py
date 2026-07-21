#!/usr/bin/env python3
import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('esp-loyalty-docs1')

stats = index.describe_index_stats()
print(f"Total vectors: {stats.total_vector_count}")
print(f"Namespaces: {list(stats.namespaces.keys())}")

# Query for test_mailchimp
dummy = [0.0] * 384
results = index.query(vector=dummy, top_k=10, filter={"esp": {"$eq": "test_mailchimp"}}, include_metadata=True)
print(f"\ntest_mailchimp filter results: {len(results.matches)}")
for m in results.matches:
    print(f"  {m.id}: {m.metadata.get('esp')}")

# Query without filter to see all recent additions
results_all = index.query(vector=dummy, top_k=20, include_metadata=True)
print(f"\nRecent vectors (top 20):")
for m in results_all.matches:
    if 'test_mailchimp' in m.id or 'test_mailchimp' in str(m.metadata):
        print(f"  ✓ FOUND: {m.id} - esp={m.metadata.get('esp')}")
