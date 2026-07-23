"""
Test script to debug Klaviyo search accuracy issues
"""
import os
from dotenv import load_dotenv
from backend.adapters.vector.vector_manager import get_vector_adapter

# Load environment variables
load_dotenv()

# Initialize vector adapter (should use Pinecone based on .env)
vectorizer = get_vector_adapter(persist_directory="backend/chroma_db")

print(f"\n🔍 Using vector provider: {vectorizer.__class__.__name__}")
print(f"Index stats: {vectorizer.get_collection_count()} total vectors")

# Test the exact query from the user
query = "How do I pull in how many points till the next tier?"
esp_filter = "klaviyo"

print(f"\n📝 Query: {query}")
print(f"📍 ESP Filter: {esp_filter}")
print("-" * 80)

# Perform search
results = vectorizer.search(query, esp_filter=esp_filter, n_results=5)

# Display results
if results['documents'] and results['documents'][0]:
    print(f"\n✅ Found {len(results['documents'][0])} results\n")

    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"Result {i+1}:")
        print(f"  Source: {metadata.get('source_url', 'N/A')}")
        print(f"  Filename: {metadata.get('filename', 'N/A')}")
        print(f"  ESP: {metadata.get('esp', 'N/A')}")
        print(f"  Content preview: {doc[:200]}...")
        print()
else:
    print("\n❌ No results found!")

# Also test with global search (no ESP filter)
print("\n" + "="*80)
print("Testing global search (no ESP filter):")
print("="*80)

global_results = vectorizer.search(query, esp_filter=None, n_results=5)

if global_results['documents'] and global_results['documents'][0]:
    print(f"\n✅ Found {len(global_results['documents'][0])} results\n")

    for i, (doc, metadata) in enumerate(zip(global_results['documents'][0], global_results['metadatas'][0])):
        print(f"Result {i+1}:")
        print(f"  Source: {metadata.get('source_url', 'N/A')}")
        print(f"  ESP: {metadata.get('esp', 'N/A')}")
        print(f"  Content preview: {doc[:200]}...")
        print()
else:
    print("\n❌ No results found!")
