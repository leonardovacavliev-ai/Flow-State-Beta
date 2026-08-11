#!/usr/bin/env python3
"""
Audit drift between the vector index and the docs/ filesystem.

Why this exists
---------------
The two are separate sources of truth and they have already diverged: the
Klaviyo namespace serves chunks from `docs_klaviyo-integration-guide.txt`,
which is in the index but has no file in `docs/klaviyo/`. Anything authored by
reading local files -- curated invariants, line-number citations, corpus
coverage claims -- is therefore describing a corpus the model may never see.

Run this before trusting any filesystem-derived statement about the corpus.

Usage
-----
    python3 backend/audit_index_drift.py
    python3 backend/audit_index_drift.py --esp klaviyo

Exit code is 1 when drift is found, so this can gate a deploy.
"""
import argparse
import os
import sys
from collections import defaultdict

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_PATH, 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_PATH, '.env'))

DOCS_PATH = os.path.join(BASE_PATH, 'docs')


def collect_indexed(index, batch_size=100):
    """Return {esp: {filename: chunk_count}} for everything in the index."""
    indexed = defaultdict(lambda: defaultdict(int))

    all_ids = []
    for page in index.list():
        all_ids.extend(page)

    for i in range(0, len(all_ids), batch_size):
        batch = all_ids[i:i + batch_size]
        fetched = index.fetch(ids=batch)
        vectors = getattr(fetched, 'vectors', None) or {}
        for vec in vectors.values():
            meta = getattr(vec, 'metadata', None) or {}
            esp = (meta.get('esp') or 'UNKNOWN').lower()
            filename = meta.get('filename') or 'UNKNOWN'
            indexed[esp][filename] += 1

    return indexed, len(all_ids)


def collect_on_disk():
    """Return {esp: {filename}} for everything under docs/."""
    on_disk = defaultdict(set)
    if not os.path.isdir(DOCS_PATH):
        return on_disk
    for esp in sorted(os.listdir(DOCS_PATH)):
        esp_dir = os.path.join(DOCS_PATH, esp)
        if not os.path.isdir(esp_dir):
            continue
        for fn in sorted(os.listdir(esp_dir)):
            if fn.endswith('.txt'):
                on_disk[esp.lower()].add(fn)
    return on_disk


def export_orphans(index, esp, filenames, out_dir):
    """
    Write the text of index-only files to `out_dir` so it can be read.

    This is a review aid, not a restored document. Chunks are stored with a
    100-word overlap, so they are emitted individually with their chunk index
    rather than stitched together -- concatenating them would invent a
    document that never existed and any line numbers taken from it would be
    fiction. Cite chunk indexes from here, not line numbers.
    """
    os.makedirs(out_dir, exist_ok=True)
    query_vector = None
    written = []

    for filename in filenames:
        # Pull every chunk for this file via metadata filter.
        if query_vector is None:
            from adapters.vector.vector_manager import get_vector_adapter
            query_vector = get_vector_adapter().embedding_model.encode(
                "document content").tolist()

        res = index.query(
            vector=query_vector,
            top_k=10000,
            filter={"esp": {"$eq": esp}, "filename": {"$eq": filename}},
            include_metadata=True,
        )
        chunks = []
        for m in res['matches']:
            meta = m.get('metadata') or {}
            chunks.append((meta.get('chunk_index'), meta.get('text', ''),
                           meta.get('source_url', 'N/A')))
        chunks.sort(key=lambda c: (c[0] is None, c[0]))

        out_path = os.path.join(out_dir, f"{esp}__{filename}")
        with open(out_path, 'w') as f:
            f.write(f"# RECOVERED FROM VECTOR INDEX -- NOT A CRAWLED FILE\n")
            f.write(f"# esp={esp} filename={filename}\n")
            f.write(f"# source_url={chunks[0][2] if chunks else 'N/A'}\n")
            f.write(f"# {len(chunks)} chunks, stored with ~100-word overlap.\n")
            f.write(f"# Chunks are emitted separately on purpose: they overlap,\n")
            f.write(f"# so line numbers in this file are NOT source line numbers.\n\n")
            for ci, text, _ in chunks:
                f.write(f"\n===== chunk_index={ci} =====\n{text}\n")
        written.append((out_path, len(chunks)))

    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--esp', help='Audit a single ESP only')
    parser.add_argument('--export-orphans', metavar='DIR',
                        help='Write the text of INDEXED-NOT-ON-DISK files to DIR '
                             'so the invisible corpus can be reviewed. '
                             'Non-destructive: reads only.')
    args = parser.parse_args()

    provider = os.environ.get('VECTOR_DB_PROVIDER', 'chromadb').lower()
    if provider != 'pinecone':
        print(f"This audit targets Pinecone; VECTOR_DB_PROVIDER={provider}.")
        return 2

    from adapters.vector.vector_manager import get_vector_adapter
    adapter = get_vector_adapter()

    print("Enumerating index (this reads every vector's metadata)...")
    indexed, total_vectors = collect_indexed(adapter.index)
    on_disk = collect_on_disk()

    esps = sorted(set(indexed) | set(on_disk))
    if args.esp:
        esps = [e for e in esps if e == args.esp.lower()]

    drift_found = False
    print(f"\nIndex holds {total_vectors} vectors across {len(indexed)} ESPs.")
    print("=" * 72)

    for esp in esps:
        idx_files = indexed.get(esp, {})
        disk_files = on_disk.get(esp, set())

        only_index = sorted(set(idx_files) - disk_files)
        only_disk = sorted(disk_files - set(idx_files))

        status = "OK" if not (only_index or only_disk) else "DRIFT"
        if status == "DRIFT":
            drift_found = True

        print(f"\n[{status}] {esp}  "
              f"({len(idx_files)} indexed files / {len(disk_files)} on disk, "
              f"{sum(idx_files.values())} chunks)")

        for fn in only_index:
            print(f"    INDEXED, NOT ON DISK  {fn}  ({idx_files[fn]} chunks)")
        for fn in only_disk:
            print(f"    ON DISK, NOT INDEXED  {fn}")

        if only_index and args.export_orphans:
            for path, n in export_orphans(adapter.index, esp, only_index,
                                          args.export_orphans):
                print(f"      -> recovered {n} chunks to {path}")

    print("\n" + "=" * 72)
    if drift_found:
        print("DRIFT FOUND. Do not author invariants or cite line numbers from")
        print("local files for the ESPs flagged above until this is reconciled:")
        print("  - INDEXED, NOT ON DISK -> the model sees text you cannot read;")
        print("    re-crawl to restore the file, or delete the stale vectors.")
        print("  - ON DISK, NOT INDEXED -> the file is dead weight; vectorize it")
        print("    or remove it so it stops implying coverage that isn't there.")
        return 1

    print("No drift: index and filesystem agree.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
