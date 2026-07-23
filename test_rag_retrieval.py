"""
Test RAG retrieval to diagnose hallucination issue
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from adapters.vector.vector_manager import get_vector_adapter

# Initialize vector database
vectorizer = get_vector_adapter()

# Simulate the user's question
query = "How do I pull in referral link and points till next tier in Klaviyo?"

print("="*80)
print("TESTING RAG RETRIEVAL")
print("="*80)
print(f"\nQuery: {query}\n")

# Test ESP-specific search (Klaviyo)
print("-"*80)
print("ESP-SPECIFIC SEARCH (Klaviyo, n_results=3)")
print("-"*80)
esp_results = vectorizer.search(query, esp_filter='klaviyo', n_results=3)

for i, (doc, metadata) in enumerate(zip(esp_results['documents'][0], esp_results['metadatas'][0])):
    print(f"\n[Result {i+1}]")
    print(f"Source: {metadata.get('source_url', 'N/A')}")
    print(f"Filename: {metadata.get('filename', 'N/A')}")
    print(f"Content preview: {doc[:300]}...")
    print()

# Test global search
print("-"*80)
print("GLOBAL SEARCH (n_results=2)")
print("-"*80)
global_results = vectorizer.search(query, esp_filter='global', n_results=2)

for i, (doc, metadata) in enumerate(zip(global_results['documents'][0], global_results['metadatas'][0])):
    print(f"\n[Result {i+1}]")
    print(f"Source: {metadata.get('source_url', 'N/A')}")
    print(f"Filename: {metadata.get('filename', 'N/A')}")
    print(f"Content preview: {doc[:300]}...")
    print()

# Check if the correct information is in the results
print("-"*80)
print("CHECKING FOR CORRECT PROPERTIES")
print("-"*80)

all_docs = esp_results['documents'][0] + global_results['documents'][0]
combined_text = ' '.join(all_docs)

has_loyalty_nt_points = 'loyalty_nt_points' in combined_text
has_swell_referral_link = 'swell_referral_link' in combined_text

print(f"\n✓ Contains 'loyalty_nt_points': {has_loyalty_nt_points}")
print(f"✓ Contains 'swell_referral_link': {has_swell_referral_link}")

if not has_loyalty_nt_points or not has_swell_referral_link:
    print("\n⚠️  WARNING: Correct properties NOT found in retrieved chunks!")
    print("   This explains why the AI hallucinated the response.")
    print("\n   SOLUTION: Increase n_results to retrieve more chunks")
else:
    print("\n✓ All correct properties found in retrieved chunks")

print("\n" + "="*80)
