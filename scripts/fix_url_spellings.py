#!/usr/bin/env python3
"""
Rewrite stored document URLs into their normalised form, row and vectors together.

    python3 scripts/fix_url_spellings.py           # dry run: what would change
    python3 scripts/fix_url_spellings.py --apply   # write (production: Leo)

From C1.1 on, documents are stored and looked up by normalize_url(url)
(backend/urls.py). eval/check_url_normalisation.py lists the rows stored under
another spelling; on 2026-10-13 that was three links ending in a #section.
Leo chose to tidy them rather than keep fragments in the identity.

For each such row, --apply:
  1. sets `source_url` on its vectors to the new URL (Pinecone's update merges
     the metadata and leaves the embedding and text alone);
  2. sets the row's `url` to the new URL.
Vectors go first: if step 2 fails, re-running the script finishes the row
(its vectors have already moved, so it finds none left to re-point).

Refuses a row whose new URL already belongs to another row of the same
integration (that would be a duplicate; decide it by hand). Safe to run twice.

After --apply, the context check differs only where these documents appear,
since each source's URL is shown to the model; `audit_product_labels.py`
must read OK.

Uses DATABASE_URL, PINECONE_API_KEY and PINECONE_INDEX_NAME from the
environment or .env.
"""
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'backend'))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))

from urls import normalize_url  # noqa: E402

DIMENSION = 384  # all-MiniLM-L6-v2


def vector_ids(idx, esp, url):
    """Ids of every chunk of (esp, url), by metadata filter."""
    probe = [1.0] + [0.0] * (DIMENSION - 1)
    res = idx.query(vector=probe, top_k=10000, include_metadata=False,
                    filter={'esp': {'$eq': esp}, 'source_url': {'$eq': url}})
    return [m['id'] for m in res['matches']]


def main(apply):
    import psycopg2
    from pinecone import Pinecone
    idx = Pinecone(api_key=os.environ['PINECONE_API_KEY']).Index(os.environ['PINECONE_INDEX_NAME'])
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    if not apply:
        conn.set_session(readonly=True)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT d.id, e.id, e.name, d.url
            FROM esp_documents d JOIN esps e ON e.id = d.esp_id
            ORDER BY e.name, d.url
        """)
        rows = cur.fetchall()
        taken = {(esp_id, url) for _, esp_id, _, url in rows}
        todo = [(doc_id, esp_id, esp, url, normalize_url(url))
                for doc_id, esp_id, esp, url in rows if normalize_url(url) != url]
        print(f"{len(rows)} document rows; {len(todo)} stored under another spelling\n")

        refused = 0
        for doc_id, esp_id, esp, old, new in todo:
            print(f"[{esp}] {old}\n    -> {new}")
            if (esp_id, new) in taken:
                refused += 1
                print("    REFUSED: another row of this integration already has the new URL")
                continue
            ids = vector_ids(idx, esp, old)
            print(f"    {len(ids)} vector(s) to re-point")
            if not apply:
                continue
            for vid in ids:
                idx.update(id=vid, set_metadata={'source_url': new})
            cur.execute("UPDATE esp_documents SET url = %s WHERE id = %s", (new, doc_id))
            conn.commit()
            print("    done")

        if not apply:
            print(f"\nDry run: nothing written. {len(todo) - refused} row(s) would change.")
            return 1 if refused else 0

        # Pinecone shows updates to reads shortly after, not instantly
        time.sleep(10)
        left = sum(len(vector_ids(idx, esp, old)) for _, _, esp, old, _ in todo)
        print(f"\nVectors still under an old spelling: {left}"
              + ("" if not left else " (re-run in a minute; updates may still be propagating)"))
        print("Next: python3 eval/check_url_normalisation.py and eval/audit_product_labels.py")
        return 1 if refused or left else 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main('--apply' in sys.argv[1:]))
