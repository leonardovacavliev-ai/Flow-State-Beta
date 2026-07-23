"""
Test what RAG context is being sent to the AI
"""
import os
from dotenv import load_dotenv
from backend.adapters.vector.vector_manager import get_vector_adapter

# Load environment variables
load_dotenv()

# Initialize vector adapter
vectorizer = get_vector_adapter(persist_directory="backend/chroma_db")

# Test the exact query from the user
query = "How do I pull in how many points till the next tier?"
esp = "klaviyo"

print(f"\n{'='*80}")
print(f"SIMULATING RAG CONTEXT BUILDING")
print(f"{'='*80}\n")
print(f"Query: {query}")
print(f"ESP: {esp}\n")

# Perform searches (same as app.py)
esp_results = vectorizer.search(query, esp_filter=esp, n_results=3)
global_results = vectorizer.search(query, esp_filter=None, n_results=2)

# Build context (same as app.py does)
context = ""
source_index = 1

# Add ESP-specific results
if esp_results['documents'] and esp_results['documents'][0]:
    context += f"## {esp.title()} Documentation:\n"
    for doc, metadata in zip(esp_results['documents'][0], esp_results['metadatas'][0]):
        context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
        context += f"Type: {esp.title()}-specific documentation\n"
        context += f"URL: {metadata.get('source_url', 'N/A')}\n"
        context += f"{doc}\n\n"
        source_index += 1

# Add global knowledge results
if global_results['documents'] and global_results['documents'][0]:
    context += "## Global Knowledge:\n"
    for doc, metadata in zip(global_results['documents'][0], global_results['metadatas'][0]):
        context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
        context += f"Type: Global Knowledge Base\n"
        context += f"URL: {metadata.get('source_url', 'N/A')}\n"
        context += f"{doc}\n\n"
        source_index += 1

print(f"{'='*80}")
print(f"GENERATED CONTEXT (sent to AI)")
print(f"{'='*80}\n")
print(context)

print(f"\n{'='*80}")
print(f"ANALYSIS")
print(f"{'='*80}\n")

# Check if correct property is mentioned
if 'loyalty_nt_points' in context:
    print("✅ CORRECT property 'loyalty_nt_points' found in context")
else:
    print("❌ CORRECT property 'loyalty_nt_points' NOT found in context")

if 'swell_points_to_next_tier' in context:
    print("❌ INCORRECT property 'swell_points_to_next_tier' found in context")
else:
    print("✅ INCORRECT property 'swell_points_to_next_tier' not in context")

print(f"\nContext length: {len(context)} characters")
print(f"Number of sources: {source_index - 1}")
