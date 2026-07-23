"""
Test new RAG configuration with increased n_results
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

# Simulate user query
user_query = "How do I pull in referral link and points till next tier in Klaviyo?"

print("="*80)
print("TESTING NEW CONFIGURATION (n_results=7 for ESP, 3 for global)")
print("="*80)
print(f"\nQuery: {user_query}\n")

# ESP-specific search with n_results=7
query_vector = embedding_model.encode(user_query).tolist()

print("-"*80)
print("ESP-SPECIFIC SEARCH (Klaviyo, n_results=7)")
print("-"*80)

esp_results = index.query(
    vector=query_vector,
    filter={"esp": {"$eq": "klaviyo"}},
    top_k=7,
    include_metadata=True
)

found_nt_points = False
found_referral_link = False
nt_points_position = -1
referral_link_position = -1

for i, match in enumerate(esp_results.matches):
    text = match.metadata.get('text', '')

    has_nt_points = 'loyalty_nt_points' in text
    has_referral_link = 'swell_referral_link' in text

    if has_nt_points and not found_nt_points:
        found_nt_points = True
        nt_points_position = i + 1

    if has_referral_link and not found_referral_link:
        found_referral_link = True
        referral_link_position = i + 1

    marker = ""
    if has_nt_points:
        marker += " [✓ loyalty_nt_points]"
    if has_referral_link:
        marker += " [✓ swell_referral_link]"

    print(f"\n[Result {i+1}]{marker}")
    print(f"ID: {match.id}")
    print(f"Score: {match.score:.4f}")
    print(f"Text: {text[:150]}...")

# Global search
print("\n" + "-"*80)
print("GLOBAL SEARCH (n_results=3)")
print("-"*80)

global_results = index.query(
    vector=query_vector,
    filter={"esp": {"$eq": "global"}},
    top_k=3,
    include_metadata=True
)

for i, match in enumerate(global_results.matches):
    text = match.metadata.get('text', '')
    print(f"\n[Result {i+1}]")
    print(f"ID: {match.id}")
    print(f"Score: {match.score:.4f}")
    print(f"Text: {text[:150]}...")

# Summary
print("\n" + "="*80)
print("SUMMARY - NEW CONFIGURATION")
print("="*80)

print(f"\n✓ Total chunks retrieved: {len(esp_results.matches) + len(global_results.matches)}")
print(f"✓ ESP-specific: {len(esp_results.matches)}")
print(f"✓ Global: {len(global_results.matches)}")

print(f"\n{'✓' if found_nt_points else '✗'} Contains 'loyalty_nt_points': {found_nt_points}")
if found_nt_points:
    print(f"   → Found at position {nt_points_position}")

print(f"{'✓' if found_referral_link else '✗'} Contains 'swell_referral_link': {found_referral_link}")
if found_referral_link:
    print(f"   → Found at position {referral_link_position}")

if found_nt_points and found_referral_link:
    print("\n✅ SUCCESS! Both properties now included in context")
    print("   OpenAI will no longer hallucinate property names")
else:
    print("\n⚠️  Still missing properties. May need to increase further.")

print("\n" + "="*80)
