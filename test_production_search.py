"""
Test what Pinecone is actually returning for the production query
"""
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX_NAME', 'esp-loyalty-docs1'))

# Use same embedding model as production
model = SentenceTransformer('all-MiniLM-L6-v2')

# The exact query from the user
query = "How do I pull in how many points till the next tier?"
query_vector = model.encode(query).tolist()

print("="*80)
print("TESTING PRODUCTION PINECONE SEARCH")
print("="*80)
print(f"\nQuery: {query}")
print(f"ESP Filter: klaviyo")

# Search with ESP filter (like production does)
results = index.query(
    vector=query_vector,
    filter={"esp": {"$eq": "klaviyo"}},
    top_k=5,
    include_metadata=True
)

print(f"\nFound {len(results.matches)} results:")

for i, match in enumerate(results.matches):
    print(f"\n{'='*80}")
    print(f"Result #{i+1} (Score: {match.score:.4f})")
    print(f"{'='*80}")
    print(f"ID: {match.id}")
    print(f"Filename: {match.metadata.get('filename', 'N/A')}")

    text = match.metadata.get('text', '')
    print(f"Text length: {len(text)} chars")
    print(f"First 200 chars: {text[:200]}...")

    # Check for the correct property
    if 'loyalty_nt_points' in text:
        print(f"✅ Contains 'loyalty_nt_points'")
        # Find position
        pos = text.index('loyalty_nt_points')
        print(f"   Position: {pos}/{len(text)} ({pos/len(text)*100:.1f}%)")
    else:
        print(f"❌ Does NOT contain 'loyalty_nt_points'")

    # Check for common tier-related terms
    tier_terms = ['next tier', 'tier', 'loyalty_nt', 'points']
    found_terms = [term for term in tier_terms if term in text.lower()]
    print(f"Contains terms: {', '.join(found_terms)}")

print(f"\n{'='*80}")
print("DIAGNOSIS")
print(f"{'='*80}")

# Check if result #1 has the property
if results.matches:
    top_result = results.matches[0]
    if 'loyalty_nt_points' in top_result.metadata.get('text', ''):
        print("\n✅ TOP RESULT contains correct property")
        print("   Issue: AI might be ignoring it or context isn't clear enough")
    else:
        print("\n❌ TOP RESULT does NOT contain correct property")
        print("   Issue: Chunking/ranking problem - correct chunk not ranking #1")
