#!/usr/bin/env python3
"""
Apply database migration for async crawl jobs.

Usage:
    python backend/migrations/apply_migration.py

This script is IDEMPOTENT - safe to run multiple times.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from adapters.database.db_manager import get_database_adapter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def apply_migration():
    """Apply the crawl jobs migration."""
    print("=" * 60)
    print("ASYNC CRAWL MIGRATION - Database Schema Update")
    print("=" * 60)
    print()

    # Get database adapter
    db_adapter = get_database_adapter()
    print(f"✓ Connected to database: {os.environ.get('DATABASE_PROVIDER', 'unknown')}")
    print()

    # Read migration file
    migration_file = os.path.join(os.path.dirname(__file__), '001_create_crawl_jobs.sql')
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print("Applying migration...")
    print("-" * 60)

    try:
        # Execute migration
        db_adapter.execute_query(migration_sql)
        print("✓ Migration applied successfully")
        print()

        # Verify tables exist
        print("Verifying migration...")
        print("-" * 60)

        # Check crawl_jobs table
        result = db_adapter.execute_query("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'crawl_jobs'
        """, fetch=True)

        if result and result[0][0] > 0:
            print("✓ Table 'crawl_jobs' exists")
        else:
            print("✗ ERROR: Table 'crawl_jobs' not found")
            sys.exit(1)

        # Check new columns on esp_documents
        result = db_adapter.execute_query("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'esp_documents'
            AND column_name IN ('crawl_job_id', 'is_crawling')
            ORDER BY column_name
        """, fetch=True)

        columns_found = [row[0] for row in result]

        if 'crawl_job_id' in columns_found:
            print("✓ Column 'esp_documents.crawl_job_id' exists")
        else:
            print("✗ ERROR: Column 'crawl_job_id' not found")
            sys.exit(1)

        if 'is_crawling' in columns_found:
            print("✓ Column 'esp_documents.is_crawling' exists")
        else:
            print("✗ ERROR: Column 'is_crawling' not found")
            sys.exit(1)

        # Check indexes
        result = db_adapter.execute_query("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE tablename = 'crawl_jobs'
        """, fetch=True)

        index_count = result[0][0] if result else 0
        print(f"✓ Created {index_count} indexes on 'crawl_jobs' table")

        print()
        print("=" * 60)
        print("MIGRATION COMPLETE ✓")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Deploy updated backend code with async crawl worker")
        print("2. Set environment variable: USE_ASYNC_CRAWL=true")
        print("3. Monitor worker logs for any issues")
        print()

    except Exception as e:
        print()
        print("=" * 60)
        print("MIGRATION FAILED ✗")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    apply_migration()
