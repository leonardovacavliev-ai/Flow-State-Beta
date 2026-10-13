#!/usr/bin/env python3
"""
Rename the old integration key 'other/webhook' to 'other_webhook' in analytics.

    python3 scripts/normalize_esp_keys.py           # dry run: counts per table
    python3 scripts/normalize_esp_keys.py --apply   # write (production: Leo)

One integration key everywhere is esps.name (I6). The page used to send
'other/webhook' to some endpoints, so analytics and saved conversations hold
both spellings and the dashboard counts one integration twice. Since C1.1 the
server normalises new rows; this fixes the old ones.

--apply runs every UPDATE in one transaction, then clears the stored
aggregate definition version so the dashboard recomputes its daily rows on
the next load, under the corrected keys. Safe to run twice: the second run
finds nothing.

Uses DATABASE_URL from the environment or .env (Postgres).
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))

OLD, NEW = 'other/webhook', 'other_webhook'
TABLES = ('esp_selections', 'feedback', 'messages', 'conversations')


def main(apply):
    url = os.environ.get('DATABASE_URL')
    if not url:
        print("DATABASE_URL is not set")
        return 2
    import psycopg2
    conn = psycopg2.connect(url)
    if not apply:
        conn.set_session(readonly=True)
    try:
        cur = conn.cursor()
        total = 0
        for table in TABLES:
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE esp = %s", (OLD,))
            count = cur.fetchone()[0]
            total += count
            print(f"  {table}: {count} row(s) with esp = '{OLD}'")
        if not apply:
            print(f"\nDry run: {total} row(s) would be renamed to '{NEW}'. Nothing written.")
            return 0
        if total:
            for table in TABLES:
                cur.execute(f"UPDATE {table} SET esp = %s WHERE esp = %s", (NEW, OLD))
            # Daily aggregates were computed under the old keys
            cur.execute("DELETE FROM aggregation_metadata WHERE key = 'definition_version'")
        conn.commit()
        print(f"\nRenamed {total} row(s) to '{NEW}'." if total else "\nNothing to rename.")
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main('--apply' in sys.argv[1:]))
