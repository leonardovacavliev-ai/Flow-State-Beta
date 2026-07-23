"""Show full content of chunk 27 to see if loyalty_nt_points is really there"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from crawler import extract_main_content
from adapters.vector.base import VectorAdapter

class DummyAdapter(VectorAdapter):
    def add_document(self, text, metadata): pass
    def search(self, query, esp_filter=None, n_results=5): pass
    def refresh_esp(self, esp_name, docs_path): pass
    def vectorize_all_docs(self, docs_path): pass
    def delete_documents(self, ids): pass
    def get_collection_count(self): pass
    def url_exists(self, url, esp_name): pass

test_url = "https://support.yotpo.com/docs/loyalty-emails-setup-guide-for-klaviyo"
content = extract_main_content(test_url)
adapter = DummyAdapter()
chunks = adapter.chunk_text(content, chunk_size=300, overlap=100)

print("="*80)
print("CHUNK #27 FULL CONTENT")
print("="*80)
print(chunks[27])
print("\n" + "="*80)

# Check position of key terms
chunk = chunks[27]
if 'loyalty_nt_points' in chunk:
    pos = chunk.index('loyalty_nt_points')
    print(f"\n'loyalty_nt_points' appears at character position: {pos}/{len(chunk)}")
    print(f"That's {pos/len(chunk)*100:.1f}% through the chunk")

    # Show context around it
    start = max(0, pos - 100)
    end = min(len(chunk), pos + 200)
    print(f"\nContext around 'loyalty_nt_points':")
    print("-"*80)
    print(chunk[start:end])
    print("-"*80)
