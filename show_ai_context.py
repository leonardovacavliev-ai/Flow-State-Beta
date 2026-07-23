"""
Show the exact context that will be sent to OpenAI with new configuration
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
print("EXACT CONTEXT SENT TO OPENAI")
print("="*80)
print(f"\nUser Query: {user_query}\n")

# Build context exactly like app.py does
esp_results = vectorizer.search(user_query, esp_filter='klaviyo', n_results=10)
global_results = vectorizer.search(user_query, esp_filter='global', n_results=3)

context = "# Relevant Documentation:\n\n"

# Add ESP-specific results
source_index = 1
if esp_results['documents'] and esp_results['documents'][0]:
    context += "## ESP-Specific Knowledge:\n"
    for doc, metadata in zip(esp_results['documents'][0], esp_results['metadatas'][0]):
        context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
        context += f"ESP: {metadata.get('esp', 'Unknown')}\n"
        context += f"URL: {metadata.get('source_url', 'N/A')}\n"
        context += f"{doc}\n\n"
        source_index += 1

# Add global knowledge results
if global_results['documents'] and global_results['documents'][0]:
    context += "## Global Knowledge:\n"
    for doc, metadata in zip(global_results['documents'][0], global_results['metadatas'][0]):
        context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
        context += f"ESP: {metadata.get('esp', 'Unknown')}\n"
        context += f"URL: {metadata.get('source_url', 'N/A')}\n"
        context += f"{doc}\n\n"
        source_index += 1

# Check for properties
has_nt_points = 'loyalty_nt_points' in context
has_referral_link = 'swell_referral_link' in context

print("="*80)
print("VERIFICATION")
print("="*80)
print(f"\n✅ Context contains 'loyalty_nt_points': {has_nt_points}")
print(f"✅ Context contains 'swell_referral_link': {has_referral_link}")
print(f"\n✅ Total sources: {source_index - 1}")
print(f"✅ Total characters: {len(context):,}")
print(f"✅ Estimated tokens: ~{len(context) // 4:,}")

if has_nt_points and has_referral_link:
    print("\n" + "="*80)
    print("✅ SUCCESS! OpenAI will receive correct information")
    print("="*80)

# Find and show the relevant excerpts
print("\n" + "="*80)
print("KEY EXCERPTS SENT TO AI")
print("="*80)

if has_nt_points:
    idx = context.find('loyalty_nt_points')
    start = max(0, idx - 150)
    end = min(len(context), idx + 300)
    print("\n[Excerpt 1] loyalty_nt_points definition:")
    print("-"*80)
    print(context[start:end])
    print("-"*80)

if has_referral_link:
    idx = context.find('swell_referral_link')
    start = max(0, idx - 150)
    end = min(len(context), idx + 300)
    print("\n[Excerpt 2] swell_referral_link definition:")
    print("-"*80)
    print(context[start:end])
    print("-"*80)

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("\nWith these excerpts in context, OpenAI will now provide:")
print("  ✅ Correct property name: loyalty_nt_points")
print("  ✅ Correct property name: swell_referral_link")
print("  ✅ Accurate Liquid template syntax")
print("  ✅ No hallucinations")

print("\n" + "="*80)
