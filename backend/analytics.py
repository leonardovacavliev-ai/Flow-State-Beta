import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import time
import requests
from contextlib import contextmanager

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_PATH, "backend/analytics.db")

# Thread-safe batch write queue
class BatchWriteQueue:
    def __init__(self, max_size=100, flush_interval=5):
        self.queue = []
        self.lock = threading.Lock()
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.last_flush = time.time()

    def add(self, operation, params):
        with self.lock:
            self.queue.append((operation, params))
            if len(self.queue) >= self.max_size or (time.time() - self.last_flush) > self.flush_interval:
                self._flush()

    def _flush(self):
        if not self.queue:
            return

        items = self.queue[:]
        self.queue.clear()
        self.last_flush = time.time()

        # Execute batch in separate thread to avoid blocking
        threading.Thread(target=self._execute_batch, args=(items,)).start()

    def _execute_batch(self, items):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for operation, params in items:
                    cursor.execute(operation, params)
                conn.commit()
        except Exception as e:
            print(f"Error flushing analytics batch: {e}")

    def force_flush(self):
        with self.lock:
            self._flush()

# Global batch queue
batch_queue = BatchWriteQueue()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize analytics database with schema"""
    with get_db_connection() as conn:
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

        # Feedback submissions (enhanced from CSV)
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

        # Daily aggregates table for performance
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

        # Add unique_users column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE daily_aggregates ADD COLUMN unique_users INTEGER DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Rename avg_messages_per_session to avg_messages_per_conversation (migration)
        try:
            cursor.execute("ALTER TABLE daily_aggregates RENAME COLUMN avg_messages_per_session TO avg_messages_per_conversation")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already renamed or doesn't exist

        # Last aggregation timestamp
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregation_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_esp_selections_session ON esp_selections(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_submitted ON feedback(submitted_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")

        conn.commit()
        print("✓ Analytics database initialized")

def get_country_from_ip(ip_address: str) -> str:
    """Get country from IP address using ipapi.co (free tier)"""
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        return 'Unknown'

    try:
        # Use ipapi.co free API (no key required, 1000 requests/day)
        response = requests.get(f"https://ipapi.co/{ip_address}/country_name/", timeout=2)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass

    return 'Unknown'

def create_session(session_id: str, ip_address: Optional[str] = None):
    """Create a new session"""
    country = get_country_from_ip(ip_address) if ip_address else 'Unknown'

    operation = """
        INSERT OR IGNORE INTO sessions (session_id, start_time, country, ip_address)
        VALUES (?, ?, ?, ?)
    """
    params = (session_id, datetime.utcnow().isoformat(), country, ip_address)
    batch_queue.add(operation, params)

def end_session(session_id: str):
    """Mark session as ended"""
    operation = """
        UPDATE sessions SET end_time = ? WHERE session_id = ?
    """
    params = (datetime.utcnow().isoformat(), session_id)
    batch_queue.add(operation, params)

def track_message(session_id: str, role: str, message: str, esp: str):
    """Track a message in a session"""
    operation = """
        INSERT INTO messages (session_id, role, message_length, esp, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (session_id, role, len(message), esp, datetime.utcnow().isoformat())
    batch_queue.add(operation, params)

def track_esp_selection(session_id: str, esp: str):
    """Track ESP selection"""
    operation = """
        INSERT INTO esp_selections (session_id, esp, selected_at)
        VALUES (?, ?, ?)
    """
    params = (session_id, esp, datetime.utcnow().isoformat())
    batch_queue.add(operation, params)

def track_feedback(session_id: Optional[str], email: str, esp: str, rating: int, comments: str):
    """Track feedback submission"""
    operation = """
        INSERT INTO feedback (session_id, email, esp, rating, comments, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (session_id, email, esp, rating, comments, datetime.utcnow().isoformat())
    batch_queue.add(operation, params)

def calculate_daily_aggregates(target_date: datetime):
    """Calculate aggregates for a specific day"""
    date_str = target_date.date().isoformat()
    start_of_day = datetime.combine(target_date.date(), datetime.min.time())
    end_of_day = datetime.combine(target_date.date(), datetime.max.time())

    # Force flush pending writes first
    batch_queue.force_flush()
    time.sleep(1)  # Give time for async flush

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total sessions
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) as count
            FROM sessions
            WHERE DATE(start_time) = ?
        """, (date_str,))
        total_sessions = cursor.fetchone()['count']

        # Total messages
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE DATE(timestamp) = ?
        """, (date_str,))
        total_messages = cursor.fetchone()['count']

        # Total user messages
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE DATE(timestamp) = ? AND role = 'user'
        """, (date_str,))
        total_user_messages = cursor.fetchone()['count']

        # Total feedback
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM feedback
            WHERE DATE(submitted_at) = ?
        """, (date_str,))
        total_feedback = cursor.fetchone()['count']

        # ESP selections count
        cursor.execute("""
            SELECT esp, COUNT(*) as count
            FROM esp_selections
            WHERE DATE(selected_at) = ?
            GROUP BY esp
        """, (date_str,))
        esp_selections = {row['esp']: row['count'] for row in cursor.fetchall()}

        # Country breakdown
        cursor.execute("""
            SELECT s.country, COUNT(DISTINCT s.session_id) as count
            FROM sessions s
            WHERE DATE(s.start_time) = ?
            GROUP BY s.country
        """, (date_str,))
        country_breakdown = {row['country']: row['count'] for row in cursor.fetchall()}

        # Average session duration (in seconds)
        cursor.execute("""
            SELECT AVG(
                CASE
                    WHEN end_time IS NOT NULL
                    THEN (julianday(end_time) - julianday(start_time)) * 86400
                    ELSE NULL
                END
            ) as avg_duration
            FROM sessions
            WHERE DATE(start_time) = ?
        """, (date_str,))
        result = cursor.fetchone()
        avg_session_duration = result['avg_duration'] or 0

        # Average messages per conversation (count unique session+ESP combinations)
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id || '-' || esp) as conversation_count
            FROM messages
            WHERE DATE(timestamp) = ? AND role = 'user'
        """, (date_str,))
        total_conversations = cursor.fetchone()['conversation_count']
        avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0

        # Average conversation length (AI responses per conversation)
        cursor.execute("""
            SELECT AVG(assistant_count) as avg_conv_length
            FROM (
                SELECT COUNT(*) as assistant_count
                FROM messages
                WHERE DATE(timestamp) = ? AND role = 'assistant'
                GROUP BY session_id, esp
            )
        """, (date_str,))
        result = cursor.fetchone()
        avg_message_length = result['avg_conv_length'] or 0

        # Unique users (by IP)
        cursor.execute("""
            SELECT COUNT(DISTINCT ip_address) as count
            FROM sessions
            WHERE DATE(start_time) = ? AND ip_address IS NOT NULL AND ip_address != ''
        """, (date_str,))
        unique_users = cursor.fetchone()['count']

        # Insert or update aggregate
        cursor.execute("""
            INSERT INTO daily_aggregates (
                date, total_sessions, total_messages, total_user_messages, total_feedback,
                esp_selections, country_breakdown, avg_session_duration,
                avg_messages_per_conversation, avg_message_length, unique_users, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                total_sessions = excluded.total_sessions,
                total_messages = excluded.total_messages,
                total_user_messages = excluded.total_user_messages,
                total_feedback = excluded.total_feedback,
                esp_selections = excluded.esp_selections,
                country_breakdown = excluded.country_breakdown,
                avg_session_duration = excluded.avg_session_duration,
                avg_messages_per_conversation = excluded.avg_messages_per_conversation,
                avg_message_length = excluded.avg_message_length,
                unique_users = excluded.unique_users,
                updated_at = excluded.updated_at
        """, (
            date_str, total_sessions, total_messages, total_user_messages, total_feedback,
            json.dumps(esp_selections), json.dumps(country_breakdown), avg_session_duration,
            avg_messages_per_conversation, avg_message_length, unique_users, datetime.utcnow().isoformat()
        ))

        conn.commit()
        print(f"✓ Calculated aggregates for {date_str}")

def should_refresh_aggregates() -> bool:
    """Check if aggregates should be refreshed (once per day)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT value FROM aggregation_metadata WHERE key = 'last_refresh'
        """)
        result = cursor.fetchone()

        if not result:
            return True

        last_refresh = datetime.fromisoformat(result['value'])
        now = datetime.utcnow()

        # Refresh if last refresh was more than 24 hours ago
        return (now - last_refresh).total_seconds() > 86400

def refresh_aggregates_if_needed():
    """Refresh aggregates if 24+ hours have passed"""
    if not should_refresh_aggregates():
        return

    # Calculate aggregates for yesterday and today
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)

    calculate_daily_aggregates(yesterday)
    calculate_daily_aggregates(today)

    # Update last refresh timestamp
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO aggregation_metadata (key, value, updated_at)
            VALUES ('last_refresh', ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        conn.commit()

def get_analytics(time_range: str = 'all_time') -> Dict:
    """
    Get analytics for dashboard with percentage changes
    time_range: 'all_time', 'last_90_days', 'last_7_days'
    """
    # Refresh aggregates if needed
    refresh_aggregates_if_needed()

    # Force flush any pending writes
    batch_queue.force_flush()
    time.sleep(0.5)

    now = datetime.utcnow()

    # Calculate date ranges
    if time_range == 'last_7_days':
        current_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)
        previous_end = current_start
    elif time_range == 'last_90_days':
        current_start = now - timedelta(days=90)
        previous_start = now - timedelta(days=180)
        previous_end = current_start
    else:  # all_time
        current_start = None
        previous_start = None
        previous_end = None

    with get_db_connection() as conn:
        cursor = conn.cursor()

        def get_metrics(start_date, end_date=None):
            """Get metrics for a date range"""
            if start_date is None:
                # All time - use aggregates + today's live data
                cursor.execute("""
                    SELECT
                        COALESCE(SUM(total_sessions), 0) as total_sessions,
                        COALESCE(SUM(total_messages), 0) as total_messages,
                        COALESCE(SUM(total_user_messages), 0) as total_user_messages,
                        COALESCE(SUM(total_feedback), 0) as total_feedback,
                        COALESCE(AVG(avg_session_duration), 0) as avg_duration,
                        COALESCE(AVG(avg_message_length), 0) as avg_length,
                        COALESCE(SUM(unique_users), 0) as unique_users,
                        COALESCE(AVG(avg_messages_per_conversation), 0) as avg_messages
                    FROM daily_aggregates
                """)
            else:
                # Specific range - query raw data
                date_filter = "timestamp >= ?" if end_date is None else "timestamp >= ? AND timestamp < ?"
                params = (start_date.isoformat(),) if end_date is None else (start_date.isoformat(), end_date.isoformat())

                # Sessions
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT session_id) as count
                    FROM sessions
                    WHERE start_time >= ?{' AND start_time < ?' if end_date else ''}
                """, params)
                total_sessions = cursor.fetchone()['count']

                # Messages
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM messages
                    WHERE {date_filter}
                """, params)
                total_messages = cursor.fetchone()['count']

                # User messages
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM messages
                    WHERE role = 'user' AND {date_filter}
                """, params)
                total_user_messages = cursor.fetchone()['count']

                # Feedback
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM feedback
                    WHERE submitted_at >= ?{' AND submitted_at < ?' if end_date else ''}
                """, params)
                total_feedback = cursor.fetchone()['count']

                # Avg session duration
                cursor.execute(f"""
                    SELECT AVG(
                        CASE
                            WHEN end_time IS NOT NULL
                            THEN (julianday(end_time) - julianday(start_time)) * 86400
                            ELSE NULL
                        END
                    ) as avg_duration
                    FROM sessions
                    WHERE start_time >= ?{' AND start_time < ?' if end_date else ''}
                """, params)
                result = cursor.fetchone()
                avg_duration = result['avg_duration'] or 0

                # Avg conversation length (AI responses per conversation)
                cursor.execute(f"""
                    SELECT AVG(assistant_count) as avg_conv_length
                    FROM (
                        SELECT COUNT(*) as assistant_count
                        FROM messages
                        WHERE {date_filter} AND role = 'assistant'
                        GROUP BY session_id, esp
                    )
                """, params)
                result = cursor.fetchone()
                avg_length = result['avg_conv_length'] or 0

                # Unique users (by IP)
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT ip_address) as count
                    FROM sessions
                    WHERE start_time >= ?{' AND start_time < ?' if end_date else ''}
                    AND ip_address IS NOT NULL AND ip_address != ''
                """, params)
                unique_users = cursor.fetchone()['count']

                # Average messages per conversation (count unique session+ESP combinations)
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT session_id || '-' || esp) as conversation_count
                    FROM messages
                    WHERE {date_filter.replace('timestamp', 'timestamp')} AND role = 'user'
                """, params)
                total_conversations = cursor.fetchone()['conversation_count']
                avg_messages = total_messages / total_conversations if total_conversations > 0 else 0

                return {
                    'total_sessions': total_sessions,
                    'total_messages': total_messages,
                    'total_user_messages': total_user_messages,
                    'total_feedback': total_feedback,
                    'avg_duration': avg_duration,
                    'avg_length': avg_length,
                    'unique_users': unique_users,
                    'avg_messages': avg_messages
                }

            # For all_time aggregate query
            row = cursor.fetchone()
            return {
                'total_sessions': row['total_sessions'],
                'total_messages': row['total_messages'],
                'total_user_messages': row['total_user_messages'],
                'total_feedback': row['total_feedback'],
                'avg_duration': row['avg_duration'],
                'avg_length': row['avg_length'],
                'unique_users': row['unique_users'],
                'avg_messages': row['avg_messages']
            }

        # Get current period metrics
        current = get_metrics(current_start)

        # Get previous period metrics for comparison (if not all_time)
        previous = None
        if time_range != 'all_time':
            previous = get_metrics(previous_start, previous_end)

        # Calculate average messages per session
        current['avg_messages'] = current['total_messages'] / current['total_sessions'] if current['total_sessions'] > 0 else 0
        if previous:
            previous['avg_messages'] = previous['total_messages'] / previous['total_sessions'] if previous['total_sessions'] > 0 else 0

        # Get ESP breakdown (current period) - count unique conversations (session+ESP with messages)
        if current_start:
            cursor.execute("""
                SELECT esp, COUNT(DISTINCT session_id) as count
                FROM messages
                WHERE timestamp >= ? AND role = 'user'
                GROUP BY esp
                ORDER BY count DESC
            """, (current_start.isoformat(),))
        else:
            cursor.execute("""
                SELECT esp, COUNT(DISTINCT session_id) as count
                FROM messages
                WHERE role = 'user'
                GROUP BY esp
                ORDER BY count DESC
            """)

        esp_breakdown = [
            {'esp': row['esp'], 'conversations': row['count']}
            for row in cursor.fetchall()
        ]

        # Get country breakdown (current period)
        if current_start:
            cursor.execute("""
                SELECT s.country, COUNT(DISTINCT s.session_id) as count
                FROM sessions s
                WHERE s.start_time >= ?
                GROUP BY s.country
                ORDER BY count DESC
            """, (current_start.isoformat(),))
        else:
            cursor.execute("""
                SELECT s.country, COUNT(DISTINCT s.session_id) as count
                FROM sessions s
                GROUP BY s.country
                ORDER BY count DESC
            """)

        country_breakdown = [
            {'country': row['country'], 'sessions': row['count']}
            for row in cursor.fetchall()
        ]

        # Calculate percentage changes
        def calc_change(current_val, previous_val):
            if previous_val == 0:
                return None if current_val == 0 else 100
            return ((current_val - previous_val) / previous_val) * 100

        # Get daily sparkline data for the current period
        sparkline_data = {}
        if current_start:
            # For time-based ranges, get daily data
            if time_range == 'last_7_days':
                days = 7
            elif time_range == 'last_90_days':
                days = 30  # Show last 30 days for 90-day view (for readability)
            else:
                days = 7

            sparkline_start = now - timedelta(days=days)

            # Get daily aggregates for sparkline
            cursor.execute("""
                SELECT
                    date,
                    total_sessions,
                    unique_users,
                    avg_messages_per_conversation,
                    total_feedback,
                    avg_session_duration,
                    avg_message_length
                FROM daily_aggregates
                WHERE date >= ? AND date <= ?
                ORDER BY date ASC
            """, (sparkline_start.date().isoformat(), now.date().isoformat()))

            daily_data = cursor.fetchall()

            sparkline_data = {
                'dates': [row['date'] for row in daily_data],
                'sessions': [row['total_sessions'] for row in daily_data],
                'unique_users': [row['unique_users'] for row in daily_data],
                'avg_messages': [round(row['avg_messages_per_conversation'], 1) for row in daily_data],
                'feedback': [row['total_feedback'] for row in daily_data],
                'session_time': [round(row['avg_session_duration'], 1) for row in daily_data],
                'msg_length': [round(row['avg_message_length'], 1) for row in daily_data]
            }

        result = {
            'sessions': {
                'value': current['total_sessions'],
                'change': calc_change(current['total_sessions'], previous['total_sessions']) if previous else None
            },
            'unique_users': {
                'value': current['unique_users'],
                'change': calc_change(current['unique_users'], previous['unique_users']) if previous else None
            },
            'avg_messages': {
                'value': round(current['avg_messages'], 1),
                'change': calc_change(current['avg_messages'], previous['avg_messages']) if previous else None
            },
            'feedback_count': {
                'value': current['total_feedback'],
                'change': calc_change(current['total_feedback'], previous['total_feedback']) if previous else None
            },
            'avg_session_time': {
                'value': round(current['avg_duration'], 1),
                'change': calc_change(current['avg_duration'], previous['avg_duration']) if previous else None
            },
            'avg_message_length': {
                'value': round(current['avg_length'], 1),
                'change': calc_change(current['avg_length'], previous['avg_length']) if previous else None
            },
            'esp_breakdown': esp_breakdown,
            'country_breakdown': country_breakdown,
            'time_range': time_range,
            'sparkline': sparkline_data
        }

        return result

# Initialize database on module import
init_db()
