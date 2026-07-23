"""
Final verification with n_results=10
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from adapters.vector.vector_manager import get_vector_adapter

load_dotenv()

# Initialize
vectorizer = get_vector_adapter()

# Simulate user query
user_query = "How do I pull in referral link and points till next tier in Klaviyo?"

print("="*80)
print("FINAL VERIFICATION (n_results=10 ESP, 3 global)")
print("="*80)
print(f"\nQuery: {user_query}\n")

# ESP-specific search
print("-"*80)
print("ESP-SPECIFIC SEARCH (Klaviyo, n_results=10)")
print("-"*80)

esp_results = vectorizer.search(user_query, esp_filter='klaviyo', n_results=10)

found_nt_points = False
found_referral_link = False
nt_points_chunk = None
referral_link_chunk = None

if esp_results['documents'] and esp_results['documents'][0]:
    for i, (doc, meta) in enumerate(zip(esp_results['documents'][0], esp_results['metadatas'][0])):
        has_nt_points = 'loyalty_nt_points' in doc
        has_referral_link = 'swell_referral_link' in doc

        if has_nt_points and not found_nt_points:
            found_nt_points = True
            nt_points_chunk = i + 1

        if has_referral_link and not found_referral_link:
            found_referral_link = True
            referral_link_chunk = i + 1

        marker = ""
        if has_nt_points:
            marker += " [✓ loyalty_nt_points]"
        if has_referral_link:
            marker += " [✓ swell_referral_link]"

        print(f"[Result {i+1}]{marker}: {meta.get('filename', 'N/A')[:60]}...")

# Global search
print("\n" + "-"*80)
print("GLOBAL SEARCH (n_results=3)")
print("-"*80)

global_results = vectorizer.search(user_query, esp_filter='global', n_results=3)

if global_results['documents'] and global_results['documents'][0]:
    for i, (doc, meta) in enumerate(zip(global_results['documents'][0], global_results['metadatas'][0])):
        print(f"[Result {i+1}]: {meta.get('filename', 'N/A')[:60]}...")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\n✓ Total chunks: {len(esp_results['documents'][0]) + len(global_results['documents'][0])}")
print(f"✓ ESP-specific: {len(esp_results['documents'][0])}")
print(f"✓ Global: {len(global_results['documents'][0])}")

print(f"\n{'✅' if found_nt_points else '❌'} 'loyalty_nt_points': {found_nt_points}")
if found_nt_points:
    print(f"   → Found at position {nt_points_chunk}")

print(f"{'✅' if found_referral_link else '❌'} 'swell_referral_link': {found_referral_link}")
if found_referral_link:
    print(f"   → Found at position {referral_link_chunk}")

if found_nt_points and found_referral_link:
    print("\n" + "="*80)
    print("✅✅✅ SUCCESS! FIX VERIFIED ✅✅✅")
    print("="*80)
    print("\nBoth critical properties are now in the RAG context.")
    print("OpenAI will have the correct information and won't hallucinate.")
    print("\nBEFORE: Only 3 chunks → missing critical properties → hallucination")
    print("AFTER:  10 chunks → includes all properties → accurate responses")
else:
    print("\n❌ Still missing properties!")

print("\n" + "="*80)
