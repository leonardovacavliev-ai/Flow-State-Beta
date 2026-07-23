"""
Find chunks that contain the correct properties
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

# Query for "referral link" and "points to next tier"
queries = [
    "referral link property klaviyo",
    "points till next tier klaviyo property",
    "loyalty_nt_points",
    "swell_referral_link"
]

print("="*80)
print("SEARCHING FOR CORRECT PROPERTIES")
print("="*80)

for query_text in queries:
    print(f"\nQuery: '{query_text}'")
    print("-"*80)

    query_vector = embedding_model.encode(query_text).tolist()

    results = index.query(
        vector=query_vector,
        filter={"esp": {"$eq": "klaviyo"}},
        top_k=3,
        include_metadata=True
    )

    for i, match in enumerate(results.matches):
        print(f"\n[Result {i+1}] Score: {match.score:.4f}")
        print(f"ID: {match.id}")

        text = match.metadata.get('text', '')

        # Check if it contains the correct properties
        has_nt_points = 'loyalty_nt_points' in text
        has_referral_link = 'swell_referral_link' in text

        print(f"Contains 'loyalty_nt_points': {has_nt_points}")
        print(f"Contains 'swell_referral_link': {has_referral_link}")

        if has_nt_points or has_referral_link:
            print(f"\n✓ FOUND CORRECT PROPERTY!")
            print(f"Text excerpt: {text[:400]}...")
        else:
            print(f"Text excerpt: {text[:200]}...")

print("\n" + "="*80)
print("TESTING WITH ACTUAL USER QUERY")
print("="*80)

user_query = "How do I pull in referral link and points till next tier in Klaviyo?"
print(f"\nUser query: '{user_query}'")

query_vector = embedding_model.encode(user_query).tolist()

results = index.query(
    vector=query_vector,
    filter={"esp": {"$eq": "klaviyo"}},
    top_k=5,  # Try more results
    include_metadata=True
)

print(f"\nTop {len(results.matches)} results:")
print("-"*80)

found_nt_points = False
found_referral_link = False

for i, match in enumerate(results.matches):
    text = match.metadata.get('text', '')

    has_nt_points = 'loyalty_nt_points' in text
    has_referral_link = 'swell_referral_link' in text

    if has_nt_points:
        found_nt_points = True
    if has_referral_link:
        found_referral_link = True

    print(f"\n[{i+1}] Score: {match.score:.4f} | nt_points: {has_nt_points} | referral_link: {has_referral_link}")
    print(f"ID: {match.id}")
    print(f"Text: {text[:150]}...")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"\nWith top_k=5:")
print(f"  ✓ Found 'loyalty_nt_points': {found_nt_points}")
print(f"  ✓ Found 'swell_referral_link': {found_referral_link}")

if not found_nt_points or not found_referral_link:
    print("\n⚠️  PROBLEM: Correct properties NOT in top 5 results")
    print("   SOLUTION: Increase n_results in app.py from 3 to 5-7")
else:
    print("\n✓ Both properties found in top 5 results")

print("\n" + "="*80)
