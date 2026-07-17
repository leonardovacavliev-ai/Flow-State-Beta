#!/usr/bin/env python3
"""
Restore ESPs from crawl_metadata.json to PostgreSQL database (Phase 4 architecture)
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from esp_manager import get_esp_manager

# Load environment variables
load_dotenv()

def restore_esps():
    """Restore all ESPs and their documents from crawl_metadata.json"""

    # Load crawl metadata
    metadata_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'crawl_metadata.json')
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    esp_manager = get_esp_manager()

    # ESP display names mapping
    esp_display_names = {
        'klaviyo': 'Klaviyo',
        'dotdigital': 'DotDigital',
        'attentive': 'Attentive',
        'ometria': 'Ometria',
        'other_webhook': 'Other/Webhook',
        'listrak': 'Listrak',
        'postscript': 'Postscript',
        'global': 'Global Knowledge'  # Special case
    }

    print("🔄 Starting ESP restoration from crawl_metadata.json\n")

    for esp_name, documents in metadata.items():
        display_name = esp_display_names.get(esp_name, esp_name.title())

        print(f"📦 Processing: {display_name} ({esp_name})")
        print(f"   Found {len(documents)} documents")

        # Check if ESP already exists
        existing_esps = esp_manager.list_esps()
        esp_exists = any(esp['name'] == esp_name for esp in existing_esps)

        if esp_exists:
            print(f"   ⚠️  ESP already exists in database, skipping creation")
            # Get the existing ESP
            esp = next(esp for esp in existing_esps if esp['name'] == esp_name)
        else:
            # Create ESP
            print(f"   ✅ Creating ESP in database")
            esp = esp_manager.create_esp(esp_name, display_name)

        # Verify ESP exists (fetch from DB to ensure it was committed)
        esp = esp_manager.get_esp_by_name(esp_name)
        if not esp:
            print(f"   ❌ Failed to create ESP - database error")
            continue

        # Add documents
        if documents:
            print(f"   📄 Adding {len(documents)} documents:")
            for doc in documents:
                url = doc['url']
                filename = doc['filename']

                # Check if document already exists
                existing_docs = esp_manager.list_documents(esp_name)
                doc_exists = any(d['url'] == url for d in existing_docs)

                if doc_exists:
                    print(f"      ⚠️  {filename} (already exists)")
                else:
                    try:
                        # Add document
                        doc = esp_manager.add_document(
                            esp_name=esp_name,
                            url=url,
                            filename=filename
                        )
                        # Mark as completed since it was already crawled
                        esp_manager.update_document_crawl_status(
                            doc_id=doc['id'],
                            status='completed'
                        )
                        print(f"      ✅ {filename}")
                    except Exception as e:
                        print(f"      ❌ {filename} - Error: {str(e)}")
        else:
            print(f"   📭 No documents to add")

        print()

    print("✨ ESP restoration complete!")
    print("\n📊 Final ESP summary:")

    all_esps = esp_manager.list_esps()
    for esp in all_esps:
        docs = esp_manager.list_documents(esp['name'])
        print(f"   {esp['display_name']}: {len(docs)} documents")

if __name__ == '__main__':
    try:
        restore_esps()
    except Exception as e:
        print(f"❌ Error during restoration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
