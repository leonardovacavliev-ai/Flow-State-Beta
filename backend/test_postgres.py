#!/usr/bin/env python3
"""
Test PostgreSQL connection and database adapter.

Usage:
    python test_postgres.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.database import get_database_adapter


def test_postgres_connection():
    """Test PostgreSQL database adapter."""
    print("=" * 60)
    print("PostgreSQL Database Adapter Test")
    print("=" * 60)

    # Force PostgreSQL provider
    os.environ['DATABASE_PROVIDER'] = 'postgres'

    try:
        # Initialize adapter
        print("\n1. Initializing PostgreSQL adapter...")
        db = get_database_adapter()
        print("✓ Database connected successfully!")

        # Test session creation
        print("\n2. Testing session creation...")
        session_id = f"test_session_{datetime.now().timestamp()}"
        db.create_session(session_id, '8.8.8.8', 'United States')
        print(f"✓ Session created: {session_id}")

        # Test message logging
        print("\n3. Testing message logging...")
        db.log_message(session_id, 'user', 'Hello, this is a test message', 'klaviyo')
        db.log_message(session_id, 'assistant', 'This is a test response', 'klaviyo')
        print("✓ Messages logged")

        # Test ESP selection
        print("\n4. Testing ESP selection...")
        db.log_esp_selection(session_id, 'klaviyo')
        print("✓ ESP selection logged")

        # Test feedback
        print("\n5. Testing feedback logging...")
        db.log_feedback(session_id, 5, 'Great tool!')
        print("✓ Feedback logged")

        # Test analytics query
        print("\n6. Testing analytics query...")
        analytics = db.get_analytics_summary('all')
        print(f"✓ Analytics retrieved:")
        print(f"  - Total sessions: {analytics['total_sessions']}")
        print(f"  - Total messages: {analytics['total_messages']}")
        print(f"  - Unique users: {analytics['unique_users']}")

        # Test session end
        print("\n7. Testing session end...")
        db.end_session(session_id)
        print("✓ Session ended")

        # Test database stats
        print("\n8. Testing database stats...")
        stats = db.get_database_stats()
        print(f"✓ Database stats:")
        print(f"  - Provider: {stats['provider']}")
        print(f"  - Database size: {stats['database_size_mb']} MB")
        print(f"  - Sessions: {stats['table_counts']['sessions']}")
        print(f"  - Messages: {stats['table_counts']['messages']}")
        print(f"  - Feedback: {stats['table_counts']['feedback']}")

        print("\n" + "=" * 60)
        print("✅ All tests passed! PostgreSQL adapter is working.")
        print("=" * 60)

        # Close connection
        db.close()

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_postgres_connection()
    sys.exit(0 if success else 1)
