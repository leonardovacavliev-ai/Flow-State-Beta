"""
Verify analytics.py works through the database adapter with both providers.

Usage:
    python test_analytics_providers.py sqlite     # temp SQLite file
    python test_analytics_providers.py postgres   # DATABASE_URL from .env,
                                                  # isolated in schema
                                                  # analytics_ci_test

The postgres run never touches production tables: it creates (and drops)
a dedicated schema and points search_path at it via the connection URL.
"""

import os
import sys
import json
import uuid
import tempfile
from datetime import datetime, timedelta

TEST_SCHEMA = 'analytics_ci_test'


def _find_env_file():
    """Walk upward from this file to find the project .env."""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        candidate = os.path.join(d, '.env')
        if os.path.exists(candidate):
            return candidate
        d = os.path.dirname(d)
    return None


def setup_provider(provider):
    if provider == 'sqlite':
        db_file = os.path.join(tempfile.mkdtemp(prefix='analytics_test_'), 'analytics.db')
        os.environ['DATABASE_PROVIDER'] = 'sqlite'
        os.environ['SQLITE_DB_PATH'] = db_file
        print(f"Using temp SQLite db: {db_file}")
        return None

    # postgres
    from dotenv import dotenv_values
    env_file = _find_env_file()
    if not env_file:
        print("FAIL: no .env found for DATABASE_URL")
        sys.exit(1)
    url = dotenv_values(env_file).get('DATABASE_URL')
    if not url:
        print("FAIL: DATABASE_URL not set in .env")
        sys.exit(1)

    import psycopg2
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
    cur.execute(f"CREATE SCHEMA {TEST_SCHEMA}")
    conn.close()

    sep = '&' if '?' in url else '?'
    os.environ['DATABASE_URL'] = f"{url}{sep}options=-csearch_path%3D{TEST_SCHEMA}"
    os.environ['DATABASE_PROVIDER'] = 'postgres'
    print(f"Using isolated Postgres schema: {TEST_SCHEMA}")
    return url


def teardown_postgres(base_url):
    import psycopg2
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
    conn.close()
    print(f"Dropped schema {TEST_SCHEMA}")


def run_checks():
    import analytics

    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))
        print(f"  {'✓' if cond else '✗ FAIL'} {name}")

    now = datetime.utcnow()
    sess_a = f"test-{uuid.uuid4()}"
    sess_b = f"test-{uuid.uuid4()}"

    # --- write path: ordered batch queue ---
    analytics.create_session(sess_a, '203.0.113.10')
    analytics.create_session(sess_b, '203.0.113.11')
    analytics.create_session(sess_a, '203.0.113.10')  # dup -> ON CONFLICT DO NOTHING
    analytics.end_session(sess_a)
    analytics.track_message(sess_a, 'user', 'How do I set up a welcome flow?', 'klaviyo')
    analytics.track_message(sess_a, 'assistant', 'Here is how you set it up...', 'klaviyo')
    analytics.track_message(sess_b, 'user', 'Points expiry campaign?', 'attentive')
    analytics.track_message(sess_b, 'assistant', 'Use a segment trigger...', 'attentive')
    analytics.track_esp_selection(sess_a, 'klaviyo')
    analytics.track_feedback(sess_a, 'test@example.com', 'klaviyo', 5, 'great')

    # A deliberately broken statement must not poison the rest of the batch
    analytics.batch_queue.add("INSERT INTO nonexistent_table (x) VALUES (?)", ('boom',))
    analytics.track_esp_selection(sess_b, 'attentive')

    # Give session A a known 120s duration
    start = (now - timedelta(seconds=300)).isoformat()
    end = (now - timedelta(seconds=180)).isoformat()
    analytics.batch_queue.add(
        "UPDATE sessions SET start_time = ?, end_time = ? WHERE session_id = ?",
        (start, end, sess_a)
    )

    analytics.batch_queue.force_flush()

    with analytics.get_db_connection() as conn:
        cur = analytics._dict_cursor(conn)
        cur.execute(analytics._sql(
            "SELECT COUNT(*) AS c FROM sessions WHERE session_id IN (?, ?)"), (sess_a, sess_b))
        check("both sessions persisted (dup ignored)", cur.fetchone()['c'] == 2)
        cur.execute(analytics._sql(
            "SELECT COUNT(*) AS c FROM esp_selections WHERE session_id IN (?, ?)"), (sess_a, sess_b))
        check("write after failed statement still applied", cur.fetchone()['c'] == 2)
        cur.execute(analytics._sql(
            "SELECT end_time FROM sessions WHERE session_id = ?"), (sess_a,))
        check("end_session recorded", cur.fetchone()['end_time'] is not None)

    # --- read path: full dashboard shape for every time range ---
    kpi_keys = ['sessions', 'unique_users', 'avg_messages',
                'feedback_count', 'avg_session_time', 'avg_message_length']

    for time_range in ['last_7_days', 'last_90_days', 'all_time']:
        data = analytics.get_analytics(time_range)
        ok_shape = all(
            k in data and 'value' in data[k] and 'change' in data[k]
            for k in kpi_keys
        ) and all(k in data for k in ['esp_breakdown', 'country_breakdown', 'sparkline', 'time_range'])
        check(f"{time_range}: KPI + breakdown shape", ok_shape)
        try:
            json.dumps(data)
            check(f"{time_range}: JSON-serializable (no Decimal/date leaks)", True)
        except TypeError as e:
            check(f"{time_range}: JSON-serializable ({e})", False)

    data = analytics.get_analytics('last_7_days')
    check("7d sessions >= 2", data['sessions']['value'] >= 2)
    check("7d unique users >= 2", data['unique_users']['value'] >= 2)
    check("7d feedback >= 1", data['feedback_count']['value'] >= 1)
    check("7d avg session time > 0 (duration SQL works)", data['avg_session_time']['value'] > 0)
    esps = {e['esp'] for e in data['esp_breakdown']}
    check("esp breakdown has klaviyo + attentive", {'klaviyo', 'attentive'} <= esps)
    spark = data['sparkline']
    check("sparkline has all 7 series", all(
        k in spark for k in ['dates', 'sessions', 'unique_users', 'avg_messages',
                             'feedback', 'session_time', 'msg_length']))
    check("sparkline covers today", spark['dates'] and spark['dates'][-1] == now.date().isoformat())
    check("sparkline series lengths match", len({len(v) for v in spark.values()}) == 1)
    check("today's sparkline sessions >= 2", spark['sessions'] and spark['sessions'][-1] >= 2)

    failed = [n for n, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    provider = sys.argv[1] if len(sys.argv) > 1 else 'sqlite'
    if provider not in ('sqlite', 'postgres'):
        print("Usage: python test_analytics_providers.py [sqlite|postgres]")
        sys.exit(1)

    base_url = setup_provider(provider)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        run_checks()
        print(f"\n✅ Analytics verified with provider: {provider}")
    finally:
        if provider == 'postgres' and base_url:
            teardown_postgres(base_url)
