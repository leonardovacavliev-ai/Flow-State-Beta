#!/usr/bin/env python3
"""
Sync PostgreSQL crawl_status with Pinecone reality

This is a one-time data migration to fix Phase 4 migration issues.
Documents were crawled pre-Phase 4, but database wasn't updated.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from esp_manager import get_esp_manager
from adapters.vector.vector_manager import get_vector_adapter

load_dotenv()

def main():
    print("="*80)
    print("SYNCING DATABASE STATUS WITH PINECONE")
    print("="*80)

    mgr = get_esp_manager()
    vectorizer = get_vector_adapter()

    # Get all ESPs
    esps = mgr.list_esps()

    total_docs = 0
    updated_docs = 0
    already_correct = 0
    failed_docs = 0

    for esp in esps:
        esp_name = esp['name']
        print(f"\n{'='*80}")
        print(f"Processing: {esp_name}")
        print(f"{'='*80}")

        docs = mgr.list_documents(esp_name)

        if not docs:
            print(f"  No documents in database")
            continue

        for doc in docs:
            total_docs += 1
            url = doc['url']
            current_status = doc['crawl_status']

            print(f"\n  Checking: {url[:70]}...")
            print(f"    Current status: {current_status}")

            # Check if vectorized in Pinecone
            try:
                exists_in_pinecone = vectorizer.url_exists(url, esp_name)
                print(f"    In Pinecone: {exists_in_pinecone}")

                if exists_in_pinecone and current_status != 'completed':
                    # Update to completed
                    print(f"    → Updating status to 'completed'")

                    # Update database
                    from adapters.database.db_manager import get_database_adapter
                    db = get_database_adapter()

                    update_query = """
                        UPDATE esp_documents
                        SET crawl_status = 'completed',
                            last_crawled_at = %s
                        WHERE id = %s
                    """
                    db.execute_query(update_query, (datetime.utcnow(), doc['id']))

                    updated_docs += 1
                    print(f"    ✅ Updated!")

                elif exists_in_pinecone and current_status == 'completed':
                    print(f"    ✅ Already correct")
                    already_correct += 1

                elif not exists_in_pinecone and current_status == 'pending':
                    print(f"    ℹ️  Correctly marked as pending")
                    already_correct += 1

                elif not exists_in_pinecone:
                    print(f"    ⚠️  Not in Pinecone, status: {current_status}")
                    failed_docs += 1

            except Exception as e:
                print(f"    ❌ Error checking: {e}")
                failed_docs += 1

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nTotal documents checked: {total_docs}")
    print(f"  ✅ Updated to 'completed': {updated_docs}")
    print(f"  ✅ Already correct: {already_correct}")
    print(f"  ⚠️  Issues/Not in Pinecone: {failed_docs}")

    if updated_docs > 0:
        print(f"\n{'='*80}")
        print("✅ SUCCESS! Database synced with Pinecone")
        print("{'='*80}")
        print("\nNext steps:")
        print("1. Restart Flask app (Railway auto-deploys)")
        print("2. Check admin panel - links should show 'crawled' (green)")
        print("3. Test AI with ESP-specific questions")
    else:
        print(f"\n{'='*80}")
        print("ℹ️  No updates needed - database already in sync")
        print("{'='*80}")

if __name__ == "__main__":
    main()
