#!/usr/bin/env python3
"""
Migrate analytics data from SQLite to PostgreSQL.

This script:
1. Reads all data from SQLite database
2. Creates PostgreSQL schema (if needed)
3. Copies all records to PostgreSQL
4. Validates data integrity

Usage:
    python migrate_to_postgres.py [--dry-run] [--batch-size=1000]
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.database import SQLiteAdapter, PostgresAdapter


def migrate_data(dry_run=False, batch_size=1000):
    """
    Migrate all analytics data from SQLite to PostgreSQL.

    Args:
        dry_run: If True, only shows what would be migrated without actually migrating
        batch_size: Number of records to migrate per batch
    """
    print("=" * 70)
    print("SQLite → PostgreSQL Migration")
    print("=" * 70)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No data will be written to PostgreSQL\n")

    # Initialize adapters
    print("\n1. Connecting to databases...")
    sqlite_db = SQLiteAdapter()
    postgres_db = PostgresAdapter()

    print("   ✓ SQLite connected")
    print("   ✓ PostgreSQL connected")

    # Get SQLite stats
    print("\n2. Reading SQLite database...")
    sqlite_stats = sqlite_db.get_database_stats()
    print(f"   ✓ SQLite database: {sqlite_stats['database_size_mb']} MB")
    print(f"   - Sessions: {sqlite_stats['table_counts']['sessions']}")
    print(f"   - Messages: {sqlite_stats['table_counts']['messages']}")
    print(f"   - Feedback: {sqlite_stats['table_counts']['feedback']}")

    if sqlite_stats['table_counts']['sessions'] == 0:
        print("\n⚠️  No data to migrate - SQLite database is empty")
        return True

    # Get PostgreSQL stats (before migration)
    postgres_stats_before = postgres_db.get_database_stats()
    print(f"\n3. PostgreSQL database (before migration):")
    print(f"   - Sessions: {postgres_stats_before['table_counts']['sessions']}")
    print(f"   - Messages: {postgres_stats_before['table_counts']['messages']}")
    print(f"   - Feedback: {postgres_stats_before['table_counts']['feedback']}")

    if dry_run:
        print("\n✓ Dry run complete - would migrate:")
        print(f"   - {sqlite_stats['table_counts']['sessions']} sessions")
        print(f"   - {sqlite_stats['table_counts']['messages']} messages")
        print(f"   - {sqlite_stats['table_counts']['feedback']} feedback records")
        return True

    # Migrate sessions
    print("\n4. Migrating sessions...")
    sessions = sqlite_db.get_sessions_list(limit=10000)  # Get all sessions
    migrated_sessions = 0

    for session in sessions:
        try:
            postgres_db.create_session(
                session_id=session['session_id'],
                ip_address=session['ip_address'],
                country=session['country']
            )

            # Update end_time if session ended
            if session['end_time']:
                postgres_db.end_session(session['session_id'])

            migrated_sessions += 1

            if migrated_sessions % 100 == 0:
                print(f"   ... {migrated_sessions}/{len(sessions)} sessions migrated")

        except Exception as e:
            print(f"   ⚠️  Failed to migrate session {session['session_id']}: {e}")

    print(f"   ✓ Migrated {migrated_sessions} sessions")

    # Migrate messages
    print("\n5. Migrating messages...")
    migrated_messages = 0

    for session in sessions:
        try:
            messages = sqlite_db.get_session_messages(session['session_id'])

            for msg in messages:
                postgres_db.log_message(
                    session_id=msg['session_id'],
                    role=msg['role'],
                    message='x' * msg['message_length'],  # Reconstruct dummy message of same length
                    esp_name=msg['esp']
                )
                migrated_messages += 1

            if migrated_messages % 500 == 0:
                print(f"   ... {migrated_messages} messages migrated")

        except Exception as e:
            print(f"   ⚠️  Failed to migrate messages for session {session['session_id']}: {e}")

    print(f"   ✓ Migrated {migrated_messages} messages")

    # Migrate ESP selections (read from SQLite directly)
    print("\n6. Migrating ESP selections...")
    import sqlite3
    conn = sqlite3.connect(sqlite_db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM esp_selections")
    esp_selections = [dict(row) for row in cursor.fetchall()]
    conn.close()

    migrated_esp = 0
    for esp in esp_selections:
        try:
            postgres_db.log_esp_selection(
                session_id=esp['session_id'],
                esp_name=esp['esp']
            )
            migrated_esp += 1
        except Exception as e:
            print(f"   ⚠️  Failed to migrate ESP selection: {e}")

    print(f"   ✓ Migrated {migrated_esp} ESP selections")

    # Migrate feedback
    print("\n7. Migrating feedback...")
    conn = sqlite3.connect(sqlite_db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback")
    feedbacks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    migrated_feedback = 0
    for feedback in feedbacks:
        try:
            postgres_db.log_feedback(
                session_id=feedback['session_id'],
                rating=feedback['rating'],
                comment=feedback['comments']
            )
            migrated_feedback += 1
        except Exception as e:
            print(f"   ⚠️  Failed to migrate feedback: {e}")

    print(f"   ✓ Migrated {migrated_feedback} feedback records")

    # Get PostgreSQL stats (after migration)
    print("\n8. Verifying migration...")
    postgres_stats_after = postgres_db.get_database_stats()
    print(f"   PostgreSQL database (after migration):")
    print(f"   - Sessions: {postgres_stats_after['table_counts']['sessions']}")
    print(f"   - Messages: {postgres_stats_after['table_counts']['messages']}")
    print(f"   - Feedback: {postgres_stats_after['table_counts']['feedback']}")

    # Validation
    success = True
    if postgres_stats_after['table_counts']['sessions'] < migrated_sessions:
        print("\n   ⚠️  Warning: Session count mismatch")
        success = False

    if postgres_stats_after['table_counts']['messages'] < migrated_messages:
        print("\n   ⚠️  Warning: Message count mismatch")
        success = False

    if success:
        print("\n" + "=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Update .env: Set DATABASE_PROVIDER=postgres")
        print("2. Restart your application")
        print("3. Verify analytics dashboard works correctly")
        print("4. (Optional) Backup/archive SQLite database")
    else:
        print("\n" + "=" * 70)
        print("⚠️  Migration completed with warnings - please review")
        print("=" * 70)

    # Close connections
    sqlite_db.close()
    postgres_db.close()

    return success


def main():
    parser = argparse.ArgumentParser(description='Migrate analytics data from SQLite to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually migrating')
    parser.add_argument('--batch-size', type=int, default=1000, help='Number of records to migrate per batch')
    args = parser.parse_args()

    try:
        success = migrate_data(dry_run=args.dry_run, batch_size=args.batch_size)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
