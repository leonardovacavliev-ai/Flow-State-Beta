"""
PostgreSQL database adapter for analytics.

Uses cloud PostgreSQL - suitable for production deployments.
"""

import os
import json
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import requests

from .base import DatabaseAdapter


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL implementation of DatabaseAdapter."""

    dialect = 'postgres'

    def __init__(self, connection_url: str = None):
        """
        Initialize PostgreSQL adapter.

        Args:
            connection_url: PostgreSQL connection string (postgresql://user:pass@host:port/db)
        """
        if connection_url is None:
            connection_url = os.environ.get('DATABASE_URL')

        if not connection_url:
            raise ValueError("DATABASE_URL environment variable is required for PostgreSQL")

        self.connection_url = connection_url
        self._connection_pool = None

    def _get_pool(self):
        """Get or create connection pool."""
        if self._connection_pool is None:
            # ThreadedConnectionPool: this adapter is shared across Flask
            # request threads and the crawl worker threads; SimpleConnectionPool
            # is not thread-safe and can hand one connection to two threads.
            self._connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.connection_url
            )
        return self._connection_pool

    def _get_connection(self):
        """Get a connection from the pool."""
        return self._get_pool().getconn()

    def _put_connection(self, conn):
        """Return a connection to the pool."""
        self._get_pool().putconn(conn)

    @contextmanager
    def connection(self):
        """Public context manager yielding a pooled psycopg2 connection.

        Rolls back on error so an aborted transaction is never returned to
        the pool. Callers commit themselves.
        """
        conn = self._get_connection()
        try:
            yield conn
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            self._put_connection(conn)

    def initialize(self):
        """Initialize database schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    country TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message_length INTEGER NOT NULL,
                    esp TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # ESP selections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS esp_selections (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    esp TEXT NOT NULL,
                    selected_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    email TEXT,
                    esp TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comments TEXT,
                    submitted_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
                )
            """)

            # Daily aggregates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_aggregates (
                    date DATE PRIMARY KEY,
                    total_sessions INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    total_user_messages INTEGER DEFAULT 0,
                    total_feedback INTEGER DEFAULT 0,
                    esp_selections JSONB,
                    country_breakdown JSONB,
                    avg_session_duration REAL DEFAULT 0,
                    avg_messages_per_conversation REAL DEFAULT 0,
                    avg_message_length REAL DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Aggregation metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregation_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # App settings (config + audit log) — persisted here so admin
            # model/prompt changes survive container redeploys
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ESP management tables (mirrors schema_esp.sql + migration 001,
            # made idempotent so fresh databases need no manual migration)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS esps (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS esp_documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    esp_id UUID NOT NULL REFERENCES esps(id) ON DELETE CASCADE,
                    url TEXT NOT NULL,
                    filename VARCHAR(500),
                    content_hash VARCHAR(64),
                    crawl_status VARCHAR(20) DEFAULT 'pending',
                    last_crawled_at TIMESTAMP,
                    error_message TEXT,
                    vector_ids JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(esp_id, url)
                )
            """)

            # Account system: Google-authenticated users and their saved
            # conversations. `google_sub` is the identity key, not email --
            # Google's subject id is permanent, email addresses are not.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    google_sub    TEXT UNIQUE NOT NULL,
                    email         TEXT NOT NULL,
                    name          TEXT,
                    picture_url   TEXT,
                    hd            TEXT,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP
                )
            """)

            # A conversation spans from the first message after the gradient
            # intro until the user picks an ESP again or closes the window.
            # Reopening one resumes it, so `ended_at` is "last time it ended",
            # not an immutable close, and a conversation may have many spans.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    esp             TEXT NOT NULL,
                    title           TEXT,
                    status          TEXT DEFAULT 'active',
                    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at        TIMESTAMP,
                    last_message_at TIMESTAMP,
                    message_count   INTEGER DEFAULT 0,
                    session_id      TEXT
                )
            """)

            # `seq` gives explicit ordering. The old client-side history relied
            # on strict user/assistant alternation, which desynchronized
            # whenever a request failed.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id              BIGSERIAL PRIMARY KEY,
                    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    seq             INTEGER NOT NULL,
                    role            TEXT NOT NULL,
                    content         TEXT NOT NULL,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (conversation_id, seq)
                )
            """)

            # Account attribution on the existing analytics tables. Nullable
            # and deliberately un-keyed: anonymous visitors still produce
            # sessions, and a FK would force a join on the hot path.
            cursor.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS user_id UUID")
            cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id UUID")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_jobs (
                    id UUID PRIMARY KEY,
                    esp_id UUID,
                    document_id UUID,
                    priority INTEGER DEFAULT 10,
                    status VARCHAR(20) DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    worker_id TEXT,
                    error_message TEXT,
                    error_traceback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # Columns added after the original schema (idempotent):
            # - is_crawling / crawl_job_id from migration 001
            # - content: the crawled text itself, so the knowledge base can be
            #   rebuilt/re-vectorized after the ephemeral filesystem is wiped
            cursor.execute("ALTER TABLE esp_documents ADD COLUMN IF NOT EXISTS crawl_job_id UUID")
            cursor.execute("ALTER TABLE esp_documents ADD COLUMN IF NOT EXISTS is_crawling BOOLEAN DEFAULT FALSE")
            cursor.execute("ALTER TABLE esp_documents ADD COLUMN IF NOT EXISTS content TEXT")

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_esp_selections_session ON esp_selections(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_submitted ON feedback(submitted_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_esps_name ON esps(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_esp_docs_esp_id ON esp_documents(esp_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_esp_docs_status ON esp_documents(crawl_status)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (LOWER(email))")
            # Serves the per-ESP history modal: this user's conversations for
            # one ESP, newest first.
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_user_esp ON conversations(user_id, esp, last_message_at DESC)")
            # Serves the 90-day retention purge.
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_last_message ON conversations(last_message_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_convmsg_conv ON conversation_messages(conversation_id, seq)")

            conn.commit()
            print("✓ PostgreSQL analytics database initialized")

        finally:
            cursor.close()
            self._put_connection(conn)

    def close(self):
        """Close database connection pool."""
        if self._connection_pool:
            self._connection_pool.closeall()
            self._connection_pool = None

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """
        Execute a raw SQL query (for ESP manager).

        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch: If True, return results; if False, commit and return None

        Returns:
            List of tuples if fetch=True, None otherwise
        """
        conn = self._get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                # Commit even when fetching (for INSERT...RETURNING, UPDATE...RETURNING)
                conn.commit()
                return result
            else:
                conn.commit()
                return None
        except Exception:
            # Roll back so the connection isn't returned to the pool with an
            # aborted transaction, which would poison every later request
            # that draws it ("current transaction is aborted").
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            if cursor is not None:
                cursor.close()
            self._put_connection(conn)

    def _get_country_from_ip(self, ip_address: str) -> str:
        """Get country from IP address using ipapi.co."""
        if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
            return 'Unknown'

        try:
            response = requests.get(f"https://ipapi.co/{ip_address}/country_name/", timeout=2)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass

        return 'Unknown'

    def create_session(self, session_id: str, ip_address: str, country: str = None) -> int:
        """Create a new session record."""
        if country is None:
            country = self._get_country_from_ip(ip_address)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, start_time, country, ip_address)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (session_id) DO NOTHING
                RETURNING session_id
            """, (session_id, datetime.utcnow(), country, ip_address))
            conn.commit()
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()
            self._put_connection(conn)

    def end_session(self, session_id: str, duration_seconds: int = None):
        """Mark session as ended."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET end_time = %s WHERE session_id = %s
            """, (datetime.utcnow(), session_id))
            conn.commit()
        finally:
            cursor.close()
            self._put_connection(conn)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()
            self._put_connection(conn)

    def log_message(self, session_id: str, role: str, message: str,
                   esp_name: Optional[str] = None, response_time: Optional[float] = None):
        """Log a chat message."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (session_id, role, message_length, esp, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, role, len(message), esp_name or 'unknown', datetime.utcnow()))
            conn.commit()
        finally:
            cursor.close()
            self._put_connection(conn)

    def log_esp_selection(self, session_id: str, esp_name: str):
        """Log ESP selection."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO esp_selections (session_id, esp, selected_at)
                VALUES (%s, %s, %s)
            """, (session_id, esp_name, datetime.utcnow()))
            conn.commit()
        finally:
            cursor.close()
            self._put_connection(conn)

    def log_feedback(self, session_id: str, rating: int, comment: Optional[str] = None):
        """Log user feedback."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (session_id, esp, rating, comments, submitted_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, 'unknown', rating, comment, datetime.utcnow()))
            conn.commit()
        finally:
            cursor.close()
            self._put_connection(conn)

    def get_analytics_summary(self, time_range: str = 'all') -> Dict[str, Any]:
        """Get analytics summary for dashboard."""
        now = datetime.utcnow()

        # Calculate date ranges
        if time_range == '24h':
            start_date = now - timedelta(hours=24)
        elif time_range == '7d':
            start_date = now - timedelta(days=7)
        elif time_range == '30d':
            start_date = now - timedelta(days=30)
        else:  # 'all'
            start_date = None

        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Build WHERE clause
            where_clause = ""
            params = []
            if start_date:
                where_clause = "WHERE s.start_time >= %s"
                params = [start_date]

            # Total sessions
            cursor.execute(f"SELECT COUNT(*) as count FROM sessions s {where_clause}", params)
            total_sessions = cursor.fetchone()['count']

            # Total messages
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM messages m
                JOIN sessions s ON m.session_id = s.session_id
                {where_clause}
            """, params)
            total_messages = cursor.fetchone()['count']

            # Unique users (by IP)
            cursor.execute(f"""
                SELECT COUNT(DISTINCT ip_address) as count
                FROM sessions s
                {where_clause + ' AND' if where_clause else 'WHERE'} ip_address IS NOT NULL AND ip_address != ''
            """, params)
            unique_users = cursor.fetchone()['count']

            # Average session duration
            cursor.execute(f"""
                SELECT AVG(
                    CASE
                        WHEN end_time IS NOT NULL
                        THEN EXTRACT(EPOCH FROM (end_time - start_time))
                        ELSE NULL
                    END
                ) as avg_duration
                FROM sessions s {where_clause}
            """, params)
            result = cursor.fetchone()
            avg_session_duration = result['avg_duration'] or 0

            # ESP breakdown
            cursor.execute(f"""
                SELECT esp, COUNT(*) as count
                FROM esp_selections e
                JOIN sessions s ON e.session_id = s.session_id
                {where_clause}
                GROUP BY esp
            """, params)
            esp_breakdown = {row['esp']: row['count'] for row in cursor.fetchall()}

            # Country breakdown
            cursor.execute(f"""
                SELECT country, COUNT(*) as count
                FROM sessions s
                {where_clause}
                GROUP BY country
            """, params)
            country_breakdown = {row['country']: row['count'] for row in cursor.fetchall()}

            # Feedback stats
            cursor.execute(f"""
                SELECT AVG(rating) as avg_rating, COUNT(*) as count
                FROM feedback f
                JOIN sessions s ON f.session_id = s.session_id
                {where_clause}
            """, params)
            feedback = cursor.fetchone()
            avg_rating = feedback['avg_rating'] or 0
            feedback_count = feedback['count']

            # Daily sparklines (last 30 days)
            cursor.execute("""
                SELECT DATE(start_time) as date, COUNT(*) as count
                FROM sessions
                WHERE start_time >= %s
                GROUP BY DATE(start_time)
                ORDER BY date
            """, [now - timedelta(days=30)])
            daily_sessions = [{'date': str(row['date']), 'count': row['count']} for row in cursor.fetchall()]

            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'unique_users': unique_users,
                'avg_session_duration': round(float(avg_session_duration), 2),
                'avg_messages_per_session': round(total_messages / total_sessions, 2) if total_sessions > 0 else 0,
                'esp_breakdown': esp_breakdown,
                'country_breakdown': country_breakdown,
                'feedback_stats': {
                    'avg_rating': round(float(avg_rating), 2),
                    'total_feedback': feedback_count
                },
                'daily_sparklines': {
                    'sessions': daily_sessions
                }
            }

        finally:
            cursor.close()
            self._put_connection(conn)

    def get_sessions_list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of recent sessions."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            self._put_connection(conn)

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM messages
                WHERE session_id = %s
                ORDER BY timestamp
            """, (session_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            self._put_connection(conn)

    def delete_old_data(self, days: int):
        """Delete data older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Delete old messages
            cursor.execute("DELETE FROM messages WHERE timestamp < %s", (cutoff_date,))

            # Delete old ESP selections
            cursor.execute("DELETE FROM esp_selections WHERE selected_at < %s", (cutoff_date,))

            # Delete old feedback
            cursor.execute("DELETE FROM feedback WHERE submitted_at < %s", (cutoff_date,))

            # Delete old sessions (cascades to related records)
            cursor.execute("DELETE FROM sessions WHERE start_time < %s", (cutoff_date,))

            conn.commit()
            print(f"✓ Deleted data older than {days} days")

        finally:
            cursor.close()
            self._put_connection(conn)

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get table row counts
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            session_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM messages")
            message_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM feedback")
            feedback_count = cursor.fetchone()['count']

            # Get database size
            cursor.execute("""
                SELECT pg_database_size(current_database()) as size
            """)
            db_size = cursor.fetchone()['size']

            return {
                'provider': 'postgresql',
                'database_url': self.connection_url.split('@')[1] if '@' in self.connection_url else 'masked',
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'table_counts': {
                    'sessions': session_count,
                    'messages': message_count,
                    'feedback': feedback_count
                }
            }

        finally:
            cursor.close()
            self._put_connection(conn)
