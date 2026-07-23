"""
Test the new chunking and crawling improvements

This script will:
1. Re-crawl ONE Klaviyo URL with the new crawler
2. Chunk it with the new chunking algorithm
3. Compare old vs new chunk quality
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from crawler import extract_main_content
from adapters.vector.base import VectorAdapter

# Test URL - the one with property definitions
test_url = "https://support.yotpo.com/docs/loyalty-emails-setup-guide-for-klaviyo"

print("="*80)
print("TESTING NEW CHUNKING & CRAWLING")
print("="*80)

# Step 1: Crawl with new crawler
print("\n1. Crawling URL with improved crawler...")
print(f"   URL: {test_url}")

new_content = extract_main_content(test_url)

if not new_content:
    print("   ❌ Failed to crawl URL")
    sys.exit(1)

print(f"   ✓ Crawled successfully ({len(new_content)} characters)")

# Save new content for inspection
with open('test_new_crawl.txt', 'w', encoding='utf-8') as f:
    f.write(new_content)
print(f"   ✓ Saved to test_new_crawl.txt")

# Step 2: Chunk with new algorithm
print("\n2. Chunking with improved algorithm...")

# Create a dummy adapter just to use the chunk_text method
class DummyAdapter(VectorAdapter):
    def add_document(self, text, metadata): pass
    def search(self, query, esp_filter=None, n_results=5): pass
    def refresh_esp(self, esp_name, docs_path): pass
    def vectorize_all_docs(self, docs_path): pass
    def delete_documents(self, ids): pass
    def get_collection_count(self): pass
    def url_exists(self, url, esp_name): pass

adapter = DummyAdapter()
new_chunks = adapter.chunk_text(new_content, chunk_size=300, overlap=100)

print(f"   ✓ Created {len(new_chunks)} chunks")

# Step 3: Analyze chunks
print("\n3. Analyzing chunk quality...")

# Find chunks containing property definitions
property_chunks = []
for i, chunk in enumerate(new_chunks):
    if 'loyalty_nt_points' in chunk or 'List of customer properties' in chunk:
        property_chunks.append((i, chunk))

if property_chunks:
    print(f"   ✓ Found {len(property_chunks)} chunk(s) with property definitions")

    for idx, (chunk_num, chunk) in enumerate(property_chunks):
        print(f"\n   Chunk #{chunk_num}:")
        print(f"   - Size: {len(chunk.split())} words")
        print(f"   - First 150 chars: {chunk[:150]}...")

        # Check what's at the start
        if chunk.strip().startswith('List of') or chunk.strip().startswith('##'):
            print(f"   - ✅ Starts with header/section marker (GOOD)")
        else:
            print(f"   - ⚠️  Doesn't start with clear section marker")

        # Check if property is near the start
        if 'loyalty_nt_points' in chunk[:500]:
            print(f"   - ✅ Property definition in first 500 chars (GOOD)")
        else:
            print(f"   - ❌ Property definition buried (BAD)")
else:
    print("   ❌ No chunks found with property definitions!")

# Step 4: Compare with old file
print("\n4. Comparing with old crawled file...")

old_file_path = 'docs/klaviyo/docs_loyalty-emails-setup-guide-for-klaviyo.txt'
if os.path.exists(old_file_path):
    with open(old_file_path, 'r', encoding='utf-8') as f:
        old_content = f.read()

    # Skip "Source URL:" line
    old_content = '\n'.join(old_content.split('\n')[2:])

    print(f"   Old content: {len(old_content)} chars")
    print(f"   New content: {len(new_content)} chars")

    # Check for headers in new content
    new_has_headers = '##' in new_content
    old_has_headers = '##' in old_content

    print(f"   Old has markdown headers: {old_has_headers}")
    print(f"   New has markdown headers: {new_has_headers}")

    if new_has_headers and not old_has_headers:
        print(f"   ✅ NEW CONTENT HAS BETTER STRUCTURE")
    else:
        print(f"   ⚠️  Structure may not have improved")
else:
    print(f"   ⚠️  Old file not found at {old_file_path}")

# Step 5: Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\n📊 Statistics:")
print(f"   - Total chunks: {len(new_chunks)}")
print(f"   - Chunks with properties: {len(property_chunks)}")
print(f"   - Avg chunk size: {sum(len(c.split()) for c in new_chunks) // len(new_chunks)} words")

# Check if improvement is significant
if property_chunks:
    first_prop_chunk = property_chunks[0]
    chunk_starts_clean = first_prop_chunk[1].strip().startswith(('List of', '##'))
    prop_near_start = 'loyalty_nt_points' in first_prop_chunk[1][:500]

    if chunk_starts_clean and prop_near_start:
        print(f"\n✅ SUCCESS: Property definitions are now well-positioned for retrieval!")
    else:
        print(f"\n⚠️  PARTIAL: Some improvements but may need tuning")
else:
    print(f"\n❌ FAILURE: Property definitions not found in chunks")

print(f"\n📄 Review files:")
print(f"   - test_new_crawl.txt (new crawled content)")
print(f"   - {old_file_path} (old crawled content)")
