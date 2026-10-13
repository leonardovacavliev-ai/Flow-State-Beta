#!/usr/bin/env python3
"""
List knowledge-base rows whose URL is not already in normalised form.

    python3 eval/check_url_normalisation.py    # exit 1 when anything is listed

From C1.1 on, documents are stored and looked up by normalize_url(url)
(backend/urls.py). Vectors are keyed on (esp, source_url), so a row stored
under a different spelling would stop being found by lookups. Before that
change ships, this must list nothing -- or Leo decides each row.

Also lists rows that would collide: two spellings of one page, which would
become duplicates.

Read-only: the connection is opened as a read-only session, so nothing can be
written even by mistake. Uses DATABASE_URL from the environment or .env.
"""
import os
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'backend'))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))

from urls import normalize_url  # noqa: E402


def rows_from_postgres(url):
    import psycopg2
    conn = psycopg2.connect(url)
    conn.set_session(readonly=True)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT e.name, e.status, d.url
            FROM esp_documents d
            JOIN esps e ON e.id = d.esp_id
            ORDER BY e.name, d.url
        """)
        return cur.fetchall()
    finally:
        conn.close()


def report(rows):
    """Print the rows that need a decision; return how many there are."""
    changed = [(esp, status, url, normalize_url(url)) for esp, status, url in rows
               if normalize_url(url) != url]
    by_key = defaultdict(list)
    for esp, status, url in rows:
        by_key[normalize_url(url)].append((esp, status, url))
    collisions = {k: v for k, v in by_key.items() if len(v) > 1}

    print(f"{len(rows)} document rows checked")
    print(f"\n{len(changed)} stored in a different spelling:")
    for esp, status, url, normal in changed:
        print(f"  [{esp}{'' if status == 'active' else ', ' + status}] {url}\n      -> {normal}")
    print(f"\n{len(collisions)} pages stored more than once:")
    for normal, owners in collisions.items():
        print(f"  {normal}")
        for esp, status, url in owners:
            print(f"      [{esp}] {url}")
    return len(changed) + len(collisions)


def main():
    url = os.environ.get('DATABASE_URL')
    if not url:
        print("DATABASE_URL is not set")
        return 2
    problems = report(rows_from_postgres(url))
    print("\nOK" if not problems else f"\n{problems} to decide before C1.1's URL change ships")
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
