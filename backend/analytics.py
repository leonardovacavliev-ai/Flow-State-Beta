"""
Analytics layer.

All reads and writes go through the database adapter selected by
DATABASE_PROVIDER (sqlite locally, postgres on Railway), so analytics
survive redeploys on ephemeral filesystems. SQL is written once with `?`
placeholders and translated per dialect; the few constructs that genuinely
differ between SQLite and PostgreSQL (duration math, day truncation) are
isolated in the fragments below.
"""

import os
import json
import atexit
import queue
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import time
import requests
from contextlib import contextmanager

from adapters.database.db_manager import get_database_adapter

_adapter = None
_adapter_lock = threading.Lock()


def _get_adapter():
    global _adapter
    if _adapter is None:
        with _adapter_lock:
            if _adapter is None:
                _adapter = get_database_adapter()
    return _adapter


def _is_postgres() -> bool:
    return _get_adapter().dialect == 'postgres'


@contextmanager
def get_db_connection():
    with _get_adapter().connection() as conn:
        yield conn


def _dict_cursor(conn):
    """Cursor whose rows support row['column'] access in both dialects."""
    if _is_postgres():
        from psycopg2.extras import RealDictCursor
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()  # sqlite3.Row is set on the connection


def _sql(query: str) -> str:
    """Translate canonical `?` placeholders to the dialect's style."""
    if _is_postgres():
        return query.replace('?', '%s')
    return query


def _duration_seconds() -> str:
    """SQL expression: session duration in seconds."""
    if _is_postgres():
        return "EXTRACT(EPOCH FROM (end_time - start_time))"
    return "(julianday(end_time) - julianday(start_time)) * 86400"


def _day(col: str) -> str:
    """SQL expression: truncate a timestamp column to its calendar day."""
    if _is_postgres():
        return f"({col})::date"
    return f"DATE({col})"


# Every reported session metric counts *engaged* sessions: ones where the
# visitor actually sent a message. A session row is created on script load,
# before any interaction, and the id is never persisted client-side -- so a
# bounce, a refresh and a second tab each add a row. Counting rows would
# report page loads, not usage.
#
# Written against the alias `s`, so every query that uses it must say
# `FROM sessions s`.
_ENGAGED_SESSION = """
    EXISTS (
        SELECT 1 FROM messages m
        WHERE m.session_id = s.session_id AND m.role = 'user'
    )
"""

# Users are counted in two disjoint populations, because IP is a poor identity
# (one office NAT collapses a team into one "user"; one person on wifi then
# mobile counts twice) and we have a real one for anybody signed in:
#   - signed in: distinct Google account, via sessions.user_id -> users.email
#   - guests:    distinct IP among sessions with no account attached
_GUEST_USER = "s.user_id IS NULL AND s.ip_address IS NOT NULL AND s.ip_address != ''"

# Bumped whenever a metric's definition changes. Daily rows already stored
# under the old definition feed the sparklines, so they are recomputed on the
# next dashboard load rather than left to mix old and new math in one chart.
_AGGREGATE_DEFINITION_VERSION = '2'


def _num(value, default=0.0) -> float:
    """Coerce SQL numerics (incl. psycopg2 Decimal) to float for JSON."""
    return float(value) if value is not None else default


def _int(value, default=0) -> int:
    return int(value) if value is not None else default


# Thread-safe batch write queue: a single background worker executes writes
# strictly in enqueue order (an UPDATE can never run before its INSERT).
class BatchWriteQueue:
    def __init__(self, max_batch=100, poll_interval=5):
        self.queue = queue.Queue()
        self.max_batch = max_batch
        self.poll_interval = poll_interval
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def add(self, operation, params):
        """Enqueue canonical (`?`-placeholder) SQL; translated at execute time."""
        self.queue.put((operation, params))

    def _run(self):
        while True:
            items = []
            try:
                items.append(self.queue.get(timeout=self.poll_interval))
            except queue.Empty:
                continue
            while len(items) < self.max_batch:
                try:
                    items.append(self.queue.get_nowait())
                except queue.Empty:
                    break
            self._execute_batch(items)
            for _ in items:
                self.queue.task_done()

    def _execute_batch(self, items):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # In Postgres a failed statement aborts the whole transaction;
                # savepoints let one bad write skip without losing the batch.
                use_savepoints = _is_postgres()
                for operation, params in items:
                    try:
                        if use_savepoints:
                            cursor.execute("SAVEPOINT analytics_batch")
                        cursor.execute(_sql(operation), params)
                        if use_savepoints:
                            cursor.execute("RELEASE SAVEPOINT analytics_batch")
                    except Exception as e:
                        print(f"Error executing analytics write: {e}")
                        if use_savepoints:
                            cursor.execute("ROLLBACK TO SAVEPOINT analytics_batch")
                conn.commit()
        except Exception as e:
            print(f"Error flushing analytics batch: {e}")

    def force_flush(self, timeout=10):
        """Block until all queued writes have been executed (or timeout)."""
        deadline = time.time() + timeout
        while self.queue.unfinished_tasks and time.time() < deadline:
            time.sleep(0.05)


# Global batch queue
batch_queue = BatchWriteQueue()

# Flush pending analytics writes on shutdown/redeploy so they aren't lost
atexit.register(batch_queue.force_flush)


def init_db():
    """Ensure the analytics schema exists in the configured database."""
    # The adapter factory runs CREATE TABLE IF NOT EXISTS for the full
    # analytics schema on first creation (both dialects).
    _get_adapter()

    if not _is_postgres():
        # Legacy SQLite files created before these columns existed
        with get_db_connection() as conn:
            cursor = conn.cursor()
            import sqlite3
            try:
                cursor.execute("ALTER TABLE daily_aggregates ADD COLUMN unique_users INTEGER DEFAULT 0")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE daily_aggregates RENAME COLUMN avg_messages_per_session TO avg_messages_per_conversation")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already renamed or doesn't exist

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


def _resolve_country_async(session_id: str, ip_address: str):
    """Resolve country in the background and update the session row."""
    country = get_country_from_ip(ip_address)
    if country and country != 'Unknown':
        batch_queue.add(
            "UPDATE sessions SET country = ? WHERE session_id = ?",
            (country, session_id)
        )


def create_session(session_id: str, ip_address: Optional[str] = None,
                   user_id: Optional[str] = None):
    """Create a new session (geolocation happens off the request path)"""
    operation = """
        INSERT INTO sessions (session_id, start_time, country, ip_address, user_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (session_id) DO NOTHING
    """
    params = (session_id, datetime.utcnow().isoformat(), 'Unknown', ip_address, user_id)
    batch_queue.add(operation, params)

    if ip_address:
        threading.Thread(
            target=_resolve_country_async,
            args=(session_id, ip_address),
            daemon=True
        ).start()


def attach_user_to_session(session_id: str, user_id: str):
    """Attribute an existing session to a signed-in account.

    The session row is created at page load, which is usually *before* anyone
    signs in -- so the stamp has to happen again on the first authenticated
    request of that session, or every sign-in would still be counted as a
    guest. Last account to act in the session wins, which is the right answer
    when two people share a browser.
    """
    operation = """
        UPDATE sessions SET user_id = ? WHERE session_id = ?
    """
    batch_queue.add(operation, (user_id, session_id))


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

    # Force flush pending writes first (blocks until drained)
    batch_queue.force_flush()

    with get_db_connection() as conn:
        cursor = _dict_cursor(conn)

        # Total sessions (engaged only, matching the dashboard KPI)
        cursor.execute(_sql(f"""
            SELECT COUNT(*) as count
            FROM sessions s
            WHERE {_day('s.start_time')} = ? AND {_ENGAGED_SESSION}
        """), (date_str,))
        total_sessions = _int(cursor.fetchone()['count'])

        # Total messages
        cursor.execute(_sql(f"""
            SELECT COUNT(*) as count
            FROM messages
            WHERE {_day('timestamp')} = ?
        """), (date_str,))
        total_messages = _int(cursor.fetchone()['count'])

        # Total user messages
        cursor.execute(_sql(f"""
            SELECT COUNT(*) as count
            FROM messages
            WHERE {_day('timestamp')} = ? AND role = 'user'
        """), (date_str,))
        total_user_messages = _int(cursor.fetchone()['count'])

        # Total feedback
        cursor.execute(_sql(f"""
            SELECT COUNT(*) as count
            FROM feedback
            WHERE {_day('submitted_at')} = ?
        """), (date_str,))
        total_feedback = _int(cursor.fetchone()['count'])

        # ESP selections count
        cursor.execute(_sql(f"""
            SELECT esp, COUNT(*) as count
            FROM esp_selections
            WHERE {_day('selected_at')} = ?
            GROUP BY esp
        """), (date_str,))
        esp_selections = {row['esp']: _int(row['count']) for row in cursor.fetchall()}

        # Country breakdown
        cursor.execute(_sql(f"""
            SELECT s.country, COUNT(*) as count
            FROM sessions s
            WHERE {_day('s.start_time')} = ? AND {_ENGAGED_SESSION}
            GROUP BY s.country
        """), (date_str,))
        country_breakdown = {row['country']: _int(row['count']) for row in cursor.fetchall()}

        # Average session duration (in seconds)
        cursor.execute(_sql(f"""
            SELECT AVG(
                CASE
                    WHEN end_time IS NOT NULL
                    THEN {_duration_seconds()}
                    ELSE NULL
                END
            ) as avg_duration
            FROM sessions s
            WHERE {_day('s.start_time')} = ? AND {_ENGAGED_SESSION}
        """), (date_str,))
        avg_session_duration = _num(cursor.fetchone()['avg_duration'])

        # Average messages per conversation (count unique session+ESP combinations)
        cursor.execute(_sql(f"""
            SELECT COUNT(DISTINCT session_id || '-' || esp) as conversation_count
            FROM messages
            WHERE {_day('timestamp')} = ? AND role = 'user'
        """), (date_str,))
        total_conversations = _int(cursor.fetchone()['conversation_count'])
        avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0

        # Average conversation length (AI responses per conversation)
        cursor.execute(_sql(f"""
            SELECT AVG(assistant_count) as avg_conv_length
            FROM (
                SELECT COUNT(*) as assistant_count
                FROM messages
                WHERE {_day('timestamp')} = ? AND role = 'assistant'
                GROUP BY session_id, esp
            ) AS conv
        """), (date_str,))
        avg_message_length = _num(cursor.fetchone()['avg_conv_length'])

        # Unique users: guest IPs + signed-in accounts, same split as the KPI.
        # Only the total is stored -- the daily rows exist to draw sparklines,
        # and the pill's breakdown comes from the raw tables.
        cursor.execute(_sql(f"""
            SELECT COUNT(DISTINCT s.ip_address) as count
            FROM sessions s
            WHERE {_day('s.start_time')} = ? AND {_ENGAGED_SESSION} AND {_GUEST_USER}
        """), (date_str,))
        unique_users = _int(cursor.fetchone()['count'])

        cursor.execute(_sql(f"""
            SELECT COUNT(DISTINCT LOWER(u.email)) as count
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE {_day('s.start_time')} = ? AND {_ENGAGED_SESSION}
            AND u.email IS NOT NULL AND u.email != ''
        """), (date_str,))
        unique_users += _int(cursor.fetchone()['count'])

        # Insert or update aggregate
        cursor.execute(_sql("""
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
        """), (
            date_str, total_sessions, total_messages, total_user_messages, total_feedback,
            json.dumps(esp_selections), json.dumps(country_breakdown), avg_session_duration,
            avg_messages_per_conversation, avg_message_length, unique_users, datetime.utcnow().isoformat()
        ))

        conn.commit()
        print(f"✓ Calculated aggregates for {date_str}")


def should_refresh_aggregates() -> bool:
    """Check if aggregates should be refreshed (once per day)"""
    with get_db_connection() as conn:
        cursor = _dict_cursor(conn)
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


def _stored_definition_version() -> Optional[str]:
    """Which metric definitions the stored daily rows were computed under."""
    with get_db_connection() as conn:
        cursor = _dict_cursor(conn)
        cursor.execute("""
            SELECT value FROM aggregation_metadata WHERE key = 'definition_version'
        """)
        row = cursor.fetchone()
        return row['value'] if row else None


def _set_metadata(key: str, value: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_sql("""
            INSERT INTO aggregation_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """), (key, value, datetime.utcnow().isoformat()))
        conn.commit()


def refresh_aggregates_if_needed():
    """Refresh aggregates if 24+ hours have passed, or definitions changed"""
    definitions_changed = _stored_definition_version() != _AGGREGATE_DEFINITION_VERSION

    if not definitions_changed and not should_refresh_aggregates():
        return

    today = datetime.utcnow()

    with get_db_connection() as conn:
        cursor = _dict_cursor(conn)
        # A definition change invalidates every stored row, so recompute from
        # the earliest one; otherwise resume from the latest, which backfills
        # quiet periods rather than leaving permanent gaps. Either way the
        # window is capped at 60 days.
        cursor.execute(
            "SELECT MIN(date) as first_date, MAX(date) as last_date FROM daily_aggregates"
        )
        row = cursor.fetchone()
        anchor_date = (row['first_date'] if definitions_changed else row['last_date']) if row else None

    if anchor_date:
        # SQLite returns TEXT, Postgres a datetime.date — str() normalizes both
        start_day = datetime.fromisoformat(str(anchor_date))
    else:
        start_day = today - timedelta(days=1)

    earliest = today - timedelta(days=60)
    if start_day < earliest:
        start_day = earliest

    day = start_day
    while day.date() <= today.date():
        calculate_daily_aggregates(day)
        day += timedelta(days=1)

    _set_metadata('last_refresh', datetime.utcnow().isoformat())
    _set_metadata('definition_version', _AGGREGATE_DEFINITION_VERSION)


def get_analytics(time_range: str = 'all_time') -> Dict:
    """
    Get analytics for dashboard with percentage changes
    time_range: 'all_time', 'last_90_days', 'last_7_days', 'last_24_hours'
    """
    # Refresh aggregates if needed
    refresh_aggregates_if_needed()

    # Force flush any pending writes (blocks until drained)
    batch_queue.force_flush()

    now = datetime.utcnow()

    # Calculate date ranges
    if time_range == 'last_24_hours':
        current_start = now - timedelta(hours=24)
        previous_start = now - timedelta(hours=48)
        previous_end = current_start
    elif time_range == 'last_7_days':
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
        cursor = _dict_cursor(conn)

        def get_metrics(start_date, end_date=None):
            """Get metrics for a date range (start_date=None means all time).

            All ranges query the raw tables so every view uses identical
            math; daily_aggregates is only used for sparklines.
            """
            if start_date is None:
                date_filter = session_filter = feedback_filter = "1=1"
                params = ()
            elif end_date is None:
                date_filter = "timestamp >= ?"
                session_filter = "start_time >= ?"
                feedback_filter = "submitted_at >= ?"
                params = (start_date.isoformat(),)
            else:
                date_filter = "timestamp >= ? AND timestamp < ?"
                session_filter = "start_time >= ? AND start_time < ?"
                feedback_filter = "submitted_at >= ? AND submitted_at < ?"
                params = (start_date.isoformat(), end_date.isoformat())

            # Sessions (engaged only -- see _ENGAGED_SESSION)
            cursor.execute(_sql(f"""
                SELECT COUNT(*) as count
                FROM sessions s
                WHERE {session_filter} AND {_ENGAGED_SESSION}
            """), params)
            total_sessions = _int(cursor.fetchone()['count'])

            # Messages
            cursor.execute(_sql(f"""
                SELECT COUNT(*) as count
                FROM messages
                WHERE {date_filter}
            """), params)
            total_messages = _int(cursor.fetchone()['count'])

            # User messages
            cursor.execute(_sql(f"""
                SELECT COUNT(*) as count
                FROM messages
                WHERE role = 'user' AND {date_filter}
            """), params)
            total_user_messages = _int(cursor.fetchone()['count'])

            # Feedback
            cursor.execute(_sql(f"""
                SELECT COUNT(*) as count
                FROM feedback
                WHERE {feedback_filter}
            """), params)
            total_feedback = _int(cursor.fetchone()['count'])

            # Avg session duration (engaged sessions, so it measures time spent
            # using the tool rather than being averaged down by bounces)
            cursor.execute(_sql(f"""
                SELECT AVG(
                    CASE
                        WHEN end_time IS NOT NULL
                        THEN {_duration_seconds()}
                        ELSE NULL
                    END
                ) as avg_duration
                FROM sessions s
                WHERE {session_filter} AND {_ENGAGED_SESSION}
            """), params)
            avg_duration = _num(cursor.fetchone()['avg_duration'])

            # Avg conversation length (AI responses per conversation)
            cursor.execute(_sql(f"""
                SELECT AVG(assistant_count) as avg_conv_length
                FROM (
                    SELECT COUNT(*) as assistant_count
                    FROM messages
                    WHERE {date_filter} AND role = 'assistant'
                    GROUP BY session_id, esp
                ) AS conv
            """), params)
            avg_length = _num(cursor.fetchone()['avg_conv_length'])

            # Guest users: distinct IP among engaged sessions with no account
            cursor.execute(_sql(f"""
                SELECT COUNT(DISTINCT s.ip_address) as count
                FROM sessions s
                WHERE {session_filter} AND {_ENGAGED_SESSION} AND {_GUEST_USER}
            """), params)
            guest_users = _int(cursor.fetchone()['count'])

            # Signed-in users: distinct Google account. Counted by email rather
            # than by session or IP, so the same person on a laptop and a phone
            # is one user. LOWER matches the unique index on users(email).
            cursor.execute(_sql(f"""
                SELECT COUNT(DISTINCT LOWER(u.email)) as count
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE {session_filter} AND {_ENGAGED_SESSION}
                AND u.email IS NOT NULL AND u.email != ''
            """), params)
            signed_in_users = _int(cursor.fetchone()['count'])

            # The two populations are disjoint by construction (a session
            # either has an account attached or it doesn't), so the headline
            # number is simply their sum.
            unique_users = guest_users + signed_in_users

            # Average messages per conversation (count unique session+ESP combinations)
            cursor.execute(_sql(f"""
                SELECT COUNT(DISTINCT session_id || '-' || esp) as conversation_count
                FROM messages
                WHERE {date_filter} AND role = 'user'
            """), params)
            total_conversations = _int(cursor.fetchone()['conversation_count'])
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0

            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'total_user_messages': total_user_messages,
                'total_feedback': total_feedback,
                'avg_duration': avg_duration,
                'avg_length': avg_length,
                'unique_users': unique_users,
                'guest_users': guest_users,
                'signed_in_users': signed_in_users,
                'avg_messages': avg_messages
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
            cursor.execute(_sql("""
                SELECT esp, COUNT(DISTINCT session_id) as count
                FROM messages
                WHERE timestamp >= ? AND role = 'user'
                GROUP BY esp
                ORDER BY count DESC
            """), (current_start.isoformat(),))
        else:
            cursor.execute("""
                SELECT esp, COUNT(DISTINCT session_id) as count
                FROM messages
                WHERE role = 'user'
                GROUP BY esp
                ORDER BY count DESC
            """)

        esp_breakdown = [
            {'esp': row['esp'], 'conversations': _int(row['count'])}
            for row in cursor.fetchall()
        ]

        # Get country breakdown (current period). Engaged sessions only, so
        # this table adds up to the Sessions KPI above it.
        if current_start:
            cursor.execute(_sql(f"""
                SELECT s.country, COUNT(*) as count
                FROM sessions s
                WHERE s.start_time >= ? AND {_ENGAGED_SESSION}
                GROUP BY s.country
                ORDER BY count DESC
            """), (current_start.isoformat(),))
        else:
            cursor.execute(f"""
                SELECT s.country, COUNT(*) as count
                FROM sessions s
                WHERE {_ENGAGED_SESSION}
                GROUP BY s.country
                ORDER BY count DESC
            """)

        country_breakdown = [
            {'country': row['country'], 'sessions': _int(row['count'])}
            for row in cursor.fetchall()
        ]

        # Calculate percentage changes
        def calc_change(current_val, previous_val):
            if previous_val == 0:
                return None if current_val == 0 else 100
            return ((current_val - previous_val) / previous_val) * 100

        # Sparklines always show a fixed trailing 6-week, week-over-week trend,
        # independent of the `time_range` filter above (which only scopes the
        # KPI cards/tables). Bucketing is done in Python rather than SQL so the
        # 7-day-aligned-on-today buckets are identical across SQLite/Postgres.
        sparkline_weeks = 6
        sparkline_window_start = now - timedelta(days=sparkline_weeks * 7)

        cursor.execute(_sql("""
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
        """), (sparkline_window_start.date().isoformat(), now.date().isoformat()))

        # Postgres returns datetime.date objects for `date`; str() normalizes
        # both dialects to ISO date strings for use as a dict key.
        by_date = {str(row['date']): row for row in cursor.fetchall()}

        def _mean(values):
            return sum(values) / len(values) if values else 0.0

        today = now.date()
        dates, sessions_wk, unique_users_wk = [], [], []
        avg_messages_wk, feedback_wk, session_time_wk, msg_length_wk = [], [], [], []

        for week_index in range(sparkline_weeks):
            week_end = today - timedelta(days=7 * (sparkline_weeks - 1 - week_index))
            week_start = week_end - timedelta(days=6)
            week_rows = [
                by_date[d] for d in (
                    (week_start + timedelta(days=offset)).isoformat() for offset in range(7)
                ) if d in by_date
            ]

            dates.append(week_start.isoformat())
            sessions_wk.append(sum(_int(row['total_sessions']) for row in week_rows))
            unique_users_wk.append(sum(_int(row['unique_users']) for row in week_rows))
            feedback_wk.append(sum(_int(row['total_feedback']) for row in week_rows))
            avg_messages_wk.append(round(_mean([_num(row['avg_messages_per_conversation']) for row in week_rows]), 1))
            session_time_wk.append(round(_mean([_num(row['avg_session_duration']) for row in week_rows]), 1))
            msg_length_wk.append(round(_mean([_num(row['avg_message_length']) for row in week_rows]), 1))

        sparkline_data = {
            'dates': dates,
            'sessions': sessions_wk,
            'unique_users': unique_users_wk,
            'avg_messages': avg_messages_wk,
            'feedback': feedback_wk,
            'session_time': session_time_wk,
            'msg_length': msg_length_wk
        }

        result = {
            'sessions': {
                'value': current['total_sessions'],
                'change': calc_change(current['total_sessions'], previous['total_sessions']) if previous else None
            },
            'unique_users': {
                'value': current['unique_users'],
                'change': calc_change(current['unique_users'], previous['unique_users']) if previous else None,
                'guest': current['guest_users'],
                'signed_in': current['signed_in_users']
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
