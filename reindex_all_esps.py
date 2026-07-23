"""
Re-index all ESP documentation with improved chunking

This script will:
1. Get list of all ESPs from PostgreSQL
2. For each ESP, re-crawl all URLs with new crawler
3. Re-vectorize with new chunking to Pinecone
4. Update database with new status

IMPORTANT: This replaces chunks in Pinecone (upsert = update or insert)
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from esp_manager import get_esp_manager
from adapters.vector.vector_manager import get_vector_adapter
from crawler import extract_main_content
import time

# Initialize managers
esp_mgr = get_esp_manager()
vectorizer = get_vector_adapter(persist_directory="backend/chroma_db")

print("="*80)
print("RE-INDEXING ALL ESP DOCUMENTATION")
print("="*80)
print(f"\nVector DB: {vectorizer.__class__.__name__}")
print(f"Total vectors before: {vectorizer.get_collection_count()}")

# Get all ESPs
esps = esp_mgr.list_esps()
print(f"\nFound {len(esps)} ESPs to process")

# Statistics
total_docs = 0
total_success = 0
total_failed = 0
total_chunks = 0

# Process each ESP
for esp_data in esps:
    esp_name = esp_data['name']
    print(f"\n{'='*80}")
    print(f"Processing: {esp_name.upper()}")
    print(f"{'='*80}")

    # Get documents for this ESP
    docs = esp_mgr.list_documents(esp_name)
    print(f"  Documents: {len(docs)}")

    if not docs:
        print(f"  ⚠️  No documents to process")
        continue

    esp_success = 0
    esp_failed = 0

    for doc in docs:
        doc_id = doc['id']
        url = doc['url']
        total_docs += 1

        print(f"\n  [{total_docs}] Crawling: {url[:60]}...")

        # Step 1: Crawl with new crawler
        try:
            content = extract_main_content(url)

            if not content:
                print(f"       ❌ Failed to crawl")
                esp_mgr.update_document_crawl_status(doc_id, 'failed', error_message='Crawl returned no content')
                esp_failed += 1
                total_failed += 1
                continue

            print(f"       ✓ Crawled ({len(content)} chars)")

            # Step 2: Save to filesystem (maintain compatibility)
            filename = doc.get('filename')
            if not filename:
                # Generate filename from URL
                from urllib.parse import urlparse
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                filename = '_'.join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
                filename = filename.replace('.html', '').replace('.htm', '')
                if not filename:
                    filename = 'index'
                filename = f"{filename}.txt"

            # Save to docs folder
            esp_folder = os.path.join('docs', esp_name)
            os.makedirs(esp_folder, exist_ok=True)
            filepath = os.path.join(esp_folder, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Source URL: {url}\n\n")
                f.write(content)

            print(f"       ✓ Saved to {filepath}")

            # Step 3: Vectorize with new chunking
            metadata = {
                'esp': esp_name,
                'filename': filename,
                'source_url': url,
                'filepath': filepath
            }

            vectorizer.add_document(content, metadata)
            num_chunks = len(vectorizer.chunk_text(content))  # Count chunks
            total_chunks += num_chunks

            print(f"       ✓ Vectorized ({num_chunks} chunks)")

            # Step 4: Update database status
            esp_mgr.update_document_crawl_status(doc_id, 'completed')

            esp_success += 1
            total_success += 1

            # Be polite to servers
            time.sleep(1)

        except Exception as e:
            print(f"       ❌ Error: {e}")
            esp_mgr.update_document_crawl_status(doc_id, 'failed', error_message=str(e))
            esp_failed += 1
            total_failed += 1
            continue

    # ESP summary
    print(f"\n  {esp_name} Summary:")
    print(f"    Success: {esp_success}")
    print(f"    Failed: {esp_failed}")

# Final summary
print(f"\n{'='*80}")
print("FINAL SUMMARY")
print(f"{'='*80}")
print(f"\n📊 Statistics:")
print(f"   Total ESPs: {len(esps)}")
print(f"   Total documents: {total_docs}")
print(f"   ✅ Success: {total_success}")
print(f"   ❌ Failed: {total_failed}")
print(f"   📦 Total chunks created: {total_chunks}")
print(f"\n🗄️  Pinecone:")
print(f"   Vectors before: (see above)")
print(f"   Vectors after: {vectorizer.get_collection_count()}")

if total_failed > 0:
    print(f"\n⚠️  {total_failed} document(s) failed - check error messages above")

if total_success > 0:
    print(f"\n✅ Successfully re-indexed {total_success} documents!")
    print(f"   Production is ready to test")
else:
    print(f"\n❌ No documents were successfully indexed")

print(f"\n{'='*80}")
print("Next steps:")
print("1. Commit and push code changes to GitHub")
print("2. Railway will auto-deploy (~3 minutes)")
print("3. Test production with query: 'How do I pull in points till next tier?'")
print("4. Verify response mentions 'loyalty_nt_points'")
print(f"{'='*80}")
