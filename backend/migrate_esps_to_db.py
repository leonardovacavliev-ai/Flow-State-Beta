"""
Migrate ESPs from Filesystem to PostgreSQL

This script migrates existing ESP data from the filesystem (docs/ folders + CSV)
to the PostgreSQL database.

Run once after deploying Phase 4 schema.
"""

import os
import sys
import csv
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from esp_manager import get_esp_manager
from adapters.database.db_manager import get_database_adapter

# Paths
BASE_PATH = Path(__file__).parent.parent
DOCS_PATH = BASE_PATH / 'docs'
CSV_PATH = BASE_PATH / 'ESP_Support_Links - Sheet1.csv'
METADATA_PATH = DOCS_PATH / 'crawl_metadata.json'


def run_schema():
    """Run the database schema to create tables."""
    print("\n=== Running Database Schema ===")
    schema_path = Path(__file__).parent / 'schema_esp.sql'

    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False

    db = get_database_adapter()

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    try:
        # Execute schema (create tables, indexes, triggers)
        db.execute_query(schema_sql, fetch=False)
        print("✓ Database schema applied successfully")
        return True
    except Exception as e:
        print(f"❌ Schema error: {e}")
        return False


def migrate_esps():
    """Migrate ESPs from filesystem to database."""
    print("\n=== Migrating ESPs ===")

    if not DOCS_PATH.exists():
        print(f"❌ Docs path not found: {DOCS_PATH}")
        return

    esp_mgr = get_esp_manager()

    # Hardcoded display names (from app.py)
    display_names = {
        'other_webhook': 'Other/Webhook',
        'klaviyo': 'Klaviyo',
        'dotdigital': 'DotDigital',
        'attentive': 'Attentive',
        'ometria': 'Ometria',
        'global': 'Global Knowledge'
    }

    # Scan docs/ folder for ESP directories
    esps_found = []
    for item in DOCS_PATH.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            esp_name = item.name
            display_name = display_names.get(esp_name, esp_name.title())

            # Count .txt files
            doc_count = len(list(item.glob('*.txt')))

            esps_found.append({
                'name': esp_name,
                'display_name': display_name,
                'doc_count': doc_count,
                'path': item
            })

    print(f"Found {len(esps_found)} ESP directories:")
    for esp in esps_found:
        print(f"  - {esp['name']}: {esp['doc_count']} documents")

    # Migrate each ESP
    migrated = 0
    skipped = 0

    for esp_data in esps_found:
        esp_name = esp_data['name']
        display_name = esp_data['display_name']

        # Check if already exists
        existing = esp_mgr.get_esp_by_name(esp_name)
        if existing:
            print(f"⏭  Skipping '{esp_name}' (already exists)")
            skipped += 1
            continue

        # Create ESP
        try:
            esp = esp_mgr.create_esp(
                name=esp_name,
                display_name=display_name,
                description=f"Migrated from filesystem on {os.environ.get('USER', 'unknown')}"
            )
            print(f"✓ Created ESP: {display_name} ({esp_name})")
            migrated += 1
        except Exception as e:
            print(f"❌ Failed to create ESP '{esp_name}': {e}")
            continue

    print(f"\n✓ Migrated {migrated} ESPs, skipped {skipped}")


def migrate_links():
    """Migrate document URLs from CSV to database."""
    print("\n=== Migrating Document Links ===")

    if not CSV_PATH.exists():
        print(f"⚠️  CSV not found: {CSV_PATH}")
        print("   Skipping link migration (no CSV file)")
        return

    esp_mgr = get_esp_manager()

    # Load crawl metadata to get filenames
    crawl_metadata = {}
    if METADATA_PATH.exists():
        with open(METADATA_PATH, 'r') as f:
            crawl_metadata = json.load(f)

    # Parse CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_esp = None
    links_by_esp = {}

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Detect section headers
        if 'integration urls' in line_lower or 'knowledge urls' in line_lower:
            # Extract ESP name from header
            for part in line_lower.split():
                if part.replace('_', '').isalpha() and part not in ['integration', 'knowledge', 'urls']:
                    current_esp = part.lower().replace('/', '_')
                    break

            if current_esp:
                links_by_esp[current_esp] = []
                print(f"\nFound section: {current_esp}")

        # Collect URLs
        elif current_esp and line_stripped.startswith('http'):
            url = line_stripped
            links_by_esp[current_esp].append(url)

    # Migrate links to database
    total_added = 0
    total_skipped = 0

    for esp_name, urls in links_by_esp.items():
        print(f"\nMigrating links for '{esp_name}': {len(urls)} URLs")

        # Check ESP exists
        esp = esp_mgr.get_esp_by_name(esp_name)
        if not esp:
            print(f"  ⚠️  ESP '{esp_name}' not found in database, skipping")
            continue

        for url in urls:
            # Check if already exists
            existing = esp_mgr.get_document_by_url(esp['id'], url)
            if existing:
                total_skipped += 1
                continue

            # Get filename from metadata
            filename = crawl_metadata.get(url, {}).get('filename')
            if not filename:
                filename = url.split('/')[-1] or 'document.txt'

            # Determine crawl status
            crawl_status = 'pending'
            if url in crawl_metadata:
                # Check if file exists
                file_path = DOCS_PATH / esp_name / filename
                if file_path.exists():
                    crawl_status = 'completed'

            try:
                # Add document
                doc = esp_mgr.add_document(esp_name, url, filename)

                # Update status if completed
                if crawl_status == 'completed':
                    # Read file to calculate hash
                    file_path = DOCS_PATH / esp_name / filename
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    content_hash = esp_mgr.calculate_content_hash(content)

                    esp_mgr.update_document_crawl_status(
                        doc['id'],
                        status='completed',
                        content_hash=content_hash
                    )

                total_added += 1

            except Exception as e:
                print(f"  ❌ Failed to add '{url}': {e}")

    print(f"\n✓ Added {total_added} links, skipped {total_skipped}")


def verify_migration():
    """Verify the migration was successful."""
    print("\n=== Verifying Migration ===")

    esp_mgr = get_esp_manager()

    # Count ESPs
    esps = esp_mgr.list_esps()
    print(f"✓ Total ESPs in database: {len(esps)}")

    for esp in esps:
        docs = esp_mgr.list_documents(esp['name'])
        completed = len([d for d in docs if d['crawl_status'] == 'completed'])
        pending = len([d for d in docs if d['crawl_status'] == 'pending'])
        failed = len([d for d in docs if d['crawl_status'] == 'failed'])

        print(f"  - {esp['display_name']} ({esp['name']}): {len(docs)} docs "
              f"(✓ {completed}, ⏳ {pending}, ❌ {failed})")


def main():
    """Run the full migration."""
    print("=" * 60)
    print("ESP Migration: Filesystem → PostgreSQL")
    print("=" * 60)

    # Check database provider
    db_provider = os.getenv('DATABASE_PROVIDER', 'sqlite')
    print(f"\nDatabase Provider: {db_provider}")

    if db_provider != 'postgres':
        print("\n⚠️  WARNING: DATABASE_PROVIDER is not 'postgres'")
        print("   This migration requires PostgreSQL.")
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    # Step 1: Run schema
    if not run_schema():
        print("\n❌ Migration aborted (schema failed)")
        return

    # Step 2: Migrate ESPs
    migrate_esps()

    # Step 3: Migrate links
    migrate_links()

    # Step 4: Verify
    verify_migration()

    print("\n" + "=" * 60)
    print("✓ Migration Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update app.py to use database-backed ESP routes")
    print("2. Test admin panel (add/remove ESPs, crawl URLs)")
    print("3. Deploy to production")


if __name__ == '__main__':
    main()
