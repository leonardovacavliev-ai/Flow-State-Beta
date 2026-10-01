#!/usr/bin/env python3
"""
Copy the knowledge-base rows (esps, esp_documents) from production Postgres
into a local SQLite file, so the admin screens can be run and tested without
touching production.

    python3 eval/seed_local_db.py [backend/local_dev.db]

Reads production only (DATABASE_URL from .env, read-only session). Overwrites
the esps / esp_documents rows in the local file; analytics tables stay empty.
Pair it with the "backend-local" launch configuration.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'backend'))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))

import psycopg2  # noqa: E402
from adapters.database.sqlite_adapter import SQLiteAdapter  # noqa: E402

COLUMNS = ['id', 'esp_id', 'url', 'filename', 'content_hash', 'crawl_status',
           'last_crawled_at', 'error_message', 'content', 'created_at', 'updated_at',
           'product']


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'backend', 'local_dev.db')
    local = SQLiteAdapter(db_path=target)
    local.initialize()

    prod = psycopg2.connect(os.environ['DATABASE_URL'])
    prod.set_session(readonly=True)
    cur = prod.cursor()
    cur.execute("SELECT id, name, display_name, description, status, created_at, updated_at FROM esps")
    esps = cur.fetchall()
    cur.execute(f"SELECT {', '.join(COLUMNS)} FROM esp_documents")
    docs = cur.fetchall()
    prod.close()

    with local.connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM esp_documents")
        c.execute("DELETE FROM esps")
        c.executemany(
            "INSERT INTO esps (id, name, display_name, description, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [tuple(str(v) if v is not None else None for v in row) for row in esps])
        c.executemany(
            f"INSERT INTO esp_documents ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
            [tuple(str(v) if v is not None else None for v in row) for row in docs])
        conn.commit()
    print(f"seeded {len(esps)} ESPs and {len(docs)} documents into {target}")


if __name__ == '__main__':
    main()
