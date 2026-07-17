"""
SQLite database adapter for analytics.

Uses local SQLite file - suitable for development and small deployments.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import requests

from .base import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite implementation of DatabaseAdapter."""

    def __init__(self, db_path: str = None):
        """
        Initialize SQLite adapter.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_path, "analytics.db")

        self.db_path = db_path
        self._connection = None

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    country TEXT,
                    ip_address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message_length INTEGER NOT NULL,
                    esp TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)

            # ESP selections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS esp_selections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    esp TEXT NOT NULL,
                    selected_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)

            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    email TEXT,
                    esp TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comments TEXT,
                    submitted_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
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
                    esp_selections JSON,
                    country_breakdown JSON,
                    avg_session_duration REAL DEFAULT 0,
                    avg_messages_per_conversation REAL DEFAULT 0,
                    avg_message_length REAL DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Aggregation metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregation_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_esp_selections_session ON esp_selections(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_submitted ON feedback(submitted_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")

            conn.commit()
            print("✓ SQLite analytics database initialized")

    def close(self):
        """Close database connection (no persistent connection for SQLite)."""
        pass

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
        # Convert PostgreSQL placeholders (%s) to SQLite placeholders (?)
        query = query.replace('%s', '?')

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                # Convert Row objects to tuples for consistency with PostgreSQL
                return [tuple(row) for row in result]
            else:
                conn.commit()
                return None

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

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO sessions (session_id, start_time, country, ip_address)
                VALUES (?, ?, ?, ?)
            """, (session_id, datetime.utcnow().isoformat(), country, ip_address))
            conn.commit()
            return cursor.lastrowid

    def end_session(self, session_id: str, duration_seconds: int = None):
        """Mark session as ended."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET end_time = ? WHERE session_id = ?
            """, (datetime.utcnow().isoformat(), session_id))
            conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def log_message(self, session_id: str, role: str, message: str,
                   esp_name: Optional[str] = None, response_time: Optional[float] = None):
        """Log a chat message."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (session_id, role, message_length, esp, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, len(message), esp_name or 'unknown', datetime.utcnow().isoformat()))
            conn.commit()

    def log_esp_selection(self, session_id: str, esp_name: str):
        """Log ESP selection."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO esp_selections (session_id, esp, selected_at)
                VALUES (?, ?, ?)
            """, (session_id, esp_name, datetime.utcnow().isoformat()))
            conn.commit()

    def log_feedback(self, session_id: str, rating: int, comment: Optional[str] = None):
        """Log user feedback."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (session_id, esp, rating, comments, submitted_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, 'unknown', rating, comment, datetime.utcnow().isoformat()))
            conn.commit()

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

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_clause = ""
            params = []
            if start_date:
                where_clause = "WHERE s.start_time >= ?"
                params = [start_date.isoformat()]

            # Total sessions
            cursor.execute(f"SELECT COUNT(*) as count FROM sessions s {where_clause}", params)
            total_sessions = cursor.fetchone()['count']

            # Total messages
            cursor.execute(f"SELECT COUNT(*) as count FROM messages m JOIN sessions s ON m.session_id = s.session_id {where_clause}", params)
            total_messages = cursor.fetchone()['count']

            # Unique users (by IP)
            cursor.execute(f"""
                SELECT COUNT(DISTINCT ip_address) as count
                FROM sessions s
                {where_clause} AND ip_address IS NOT NULL AND ip_address != ''
            """, params)
            unique_users = cursor.fetchone()['count']

            # Average session duration
            cursor.execute(f"""
                SELECT AVG(
                    CASE
                        WHEN end_time IS NOT NULL
                        THEN (julianday(end_time) - julianday(start_time)) * 86400
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
                WHERE start_time >= ?
                GROUP BY DATE(start_time)
                ORDER BY date
            """, [(now - timedelta(days=30)).isoformat()])
            daily_sessions = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]

            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'unique_users': unique_users,
                'avg_session_duration': round(avg_session_duration, 2),
                'avg_messages_per_session': round(total_messages / total_sessions, 2) if total_sessions > 0 else 0,
                'esp_breakdown': esp_breakdown,
                'country_breakdown': country_breakdown,
                'feedback_stats': {
                    'avg_rating': round(avg_rating, 2),
                    'total_feedback': feedback_count
                },
                'daily_sparklines': {
                    'sessions': daily_sessions
                }
            }

    def get_sessions_list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of recent sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY timestamp
            """, (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_old_data(self, days: int):
        """Delete data older than specified days."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete old messages
            cursor.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff_date,))

            # Delete old ESP selections
            cursor.execute("DELETE FROM esp_selections WHERE selected_at < ?", (cutoff_date,))

            # Delete old feedback
            cursor.execute("DELETE FROM feedback WHERE submitted_at < ?", (cutoff_date,))

            # Delete old sessions
            cursor.execute("DELETE FROM sessions WHERE start_time < ?", (cutoff_date,))

            conn.commit()
            print(f"✓ Deleted data older than {days} days")

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get table row counts
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            session_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM messages")
            message_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM feedback")
            feedback_count = cursor.fetchone()['count']

            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

            return {
                'provider': 'sqlite',
                'database_path': self.db_path,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'table_counts': {
                    'sessions': session_count,
                    'messages': message_count,
                    'feedback': feedback_count
                }
            }
