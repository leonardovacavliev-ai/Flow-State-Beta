#!/usr/bin/env python3
"""
Check, and once fill in, the product label on every vector in the live index.

    python3 eval/audit_product_labels.py                   # audit (read-only), exit 1 on problems
    python3 eval/audit_product_labels.py backfill          # dry run: what would change
    python3 eval/audit_product_labels.py backfill --write  # write the labels

The label's source of truth is esp_documents.product, looked up by
(esp, source_url) -- the key the table enforces and every vector carries.

audit checks that:
  - every vector has `product` in loyalty | reviews | shared,
  - it matches its document's row,
  - every vector belongs to a row (none left behind by a deleted link),
  - no orphans: per (esp, source_url) one filename and one chunk 0, and no
    chunk_index at or past chunk 0's total_chunks (chunk 0 is rewritten on
    every write, so a leftover tail from a longer old version shows up here).

backfill sets `product` on vectors whose label is missing or differs, using
Pinecone's update (merges set_metadata, leaves the embedding alone). With
--write it first proves that on one vector: fetch, update, re-fetch until the
change is visible, and compare everything else -- text, esp, source_url, the
embedding. Vectors without a row are reported and left alone.

Reads Postgres read-only. backfill --write is the only thing that writes, and
only the `product` metadata key.
"""
import os
import sys
import time
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'backend'))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))

LABELS = ('loyalty', 'reviews', 'shared')


def index():
    from pinecone import Pinecone
    return Pinecone(api_key=os.environ['PINECONE_API_KEY']).Index(os.environ['PINECONE_INDEX_NAME'])


def all_vectors(idx):
    """{id: metadata without text} for every vector in the default namespace."""
    # pinecone 7.x pages hold id strings; 10.x pages hold items with an .id
    ids = [getattr(i, 'id', i) for page in idx.list() for i in page]
    out = {}
    for i in range(0, len(ids), 100):
        for vid, v in idx.fetch(ids=ids[i:i + 100]).vectors.items():
            md = dict(v.metadata or {})
            md.pop('text', None)
            out[vid] = md
    return out


def db_labels():
    """{(esp, url): product} for every esp_documents row."""
    import psycopg2
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.set_session(readonly=True)
    cur = conn.cursor()
    cur.execute("SELECT e.name, d.url, d.product FROM esp_documents d JOIN esps e ON e.id = d.esp_id")
    rows = {(esp, url): product for esp, url, product in cur.fetchall()}
    conn.close()
    return rows


def find_problems(vectors, labels):
    """Lists of problems, by kind. Pure, so it can be tested."""
    problems = defaultdict(list)
    by_doc = defaultdict(list)
    for vid, md in vectors.items():
        key = (md.get('esp'), md.get('source_url'))
        by_doc[key].append((vid, md))
        if key not in labels:
            problems['no database row'].append(f"{vid}  {key[0]} {key[1]}")
            continue
        want = labels[key]
        got = md.get('product')
        if want not in LABELS:
            problems['row has no label'].append(f"{vid}  {key[0]} {key[1]}")
        elif got not in LABELS:
            problems['vector has no label'].append(f"{vid}  (row says {want})")
        elif got != want:
            problems['label differs from row'].append(f"{vid}  vector {got}, row {want}")
    for (esp, url), chunks in by_doc.items():
        filenames = {md.get('filename') for _, md in chunks}
        firsts = [md for _, md in chunks if md.get('chunk_index') == 0]
        if len(filenames) > 1:
            problems['several filenames for one document'].append(f"{esp} {url}: {sorted(map(str, filenames))}")
        if len(firsts) != 1:
            problems['not exactly one chunk 0'].append(f"{esp} {url}: {len(firsts)}")
            continue
        total = firsts[0].get('total_chunks')
        for vid, md in chunks:
            if isinstance(total, (int, float)) and md.get('chunk_index', 0) >= total:
                problems['orphan chunk'].append(f"{vid}  chunk {md.get('chunk_index')} of {int(total)}")
    return problems


def plan_backfill(vectors, labels):
    """[(id, product)] for vectors whose label is missing or differs from a labelled row."""
    plan = []
    for vid, md in sorted(vectors.items()):
        want = labels.get((md.get('esp'), md.get('source_url')))
        if want in LABELS and md.get('product') != want:
            plan.append((vid, want))
    return plan


def audit():
    idx = index()
    vectors, labels = all_vectors(idx), db_labels()
    problems = find_problems(vectors, labels)
    counts = defaultdict(int)
    for md in vectors.values():
        counts[md.get('product') or '(none)'] += 1
    print(f"{len(vectors)} vectors, {len(labels)} document rows")
    print("vectors by label: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if not problems:
        print("OK: every vector is labelled, matches its row, and has no orphans")
        return 0
    for kind, items in problems.items():
        print(f"\n{kind}: {len(items)}")
        for line in items[:15]:
            print(f"  {line}")
        if len(items) > 15:
            print(f"  ... {len(items) - 15} more")
    return 1


def _fetch_one(idx, vid):
    v = idx.fetch(ids=[vid]).vectors[vid]
    return dict(v.metadata or {}), list(v.values)


def verify_on_one(idx, vid, product, wait_seconds=60):
    """Update one vector and prove only `product` changed. Raises otherwise."""
    before_md, before_values = _fetch_one(idx, vid)
    idx.update(id=vid, set_metadata={'product': product})
    deadline = time.time() + wait_seconds
    while True:
        after_md, after_values = _fetch_one(idx, vid)
        if after_md.get('product') == product or time.time() > deadline:
            break
        time.sleep(2)   # updates become visible shortly after, not instantly
    if after_md.get('product') != product:
        raise RuntimeError(f"{vid}: the label did not appear within {wait_seconds}s")
    expected = {**before_md, 'product': product}
    if after_md != expected:
        changed = sorted(k for k in set(expected) | set(after_md) if expected.get(k) != after_md.get(k))
        raise RuntimeError(f"{vid}: update changed more than the label: {changed}")
    if after_values != before_values:
        raise RuntimeError(f"{vid}: update changed the embedding")
    print(f"verified on {vid}: only `product` changed (text, esp, source_url, embedding identical)")


def backfill(write):
    idx = index()
    vectors, labels = all_vectors(idx), db_labels()
    plan = plan_backfill(vectors, labels)
    unowned = [vid for vid, md in vectors.items() if (md.get('esp'), md.get('source_url')) not in labels]
    print(f"{len(vectors)} vectors; {len(plan)} to label; {len(unowned)} without a database row (left alone)")
    by_label = defaultdict(int)
    for _, product in plan:
        by_label[product] += 1
    if plan:
        print("to write: " + ", ".join(f"{k} {v}" for k, v in sorted(by_label.items())))
    if not write or not plan:
        if plan:
            print("dry run; add --write to write them")
        return 0
    first_id, first_product = plan[0]
    verify_on_one(idx, first_id, first_product)
    failed = []
    for n, (vid, product) in enumerate(plan[1:], start=2):
        try:
            idx.update(id=vid, set_metadata={'product': product})
        except Exception as e:
            failed.append(vid)
            print(f"  failed {vid}: {e}")
        if n % 100 == 0:
            print(f"  {n}/{len(plan)}")
    print(f"wrote {len(plan) - len(failed)} of {len(plan)} labels"
          + (f"; {len(failed)} failed, run again to retry" if failed else ""))
    print("updates become visible within seconds; then run the audit")
    return 1 if failed else 0


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(audit())
    if args[0] == 'backfill' and args[1:] in ([], ['--write']):
        sys.exit(backfill(write=args[1:] == ['--write']))
    print(__doc__)
    sys.exit(2)


if __name__ == '__main__':
    main()
