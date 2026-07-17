"""
PostgreSQL database adapter for analytics.

Uses cloud PostgreSQL - suitable for production deployments.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import requests

from .base import DatabaseAdapter


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL implementation of DatabaseAdapter."""

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
            self._connection_pool = pool.SimpleConnectionPool(
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

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_esp_selections_session ON esp_selections(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_submitted ON feedback(submitted_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")

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
        finally:
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
