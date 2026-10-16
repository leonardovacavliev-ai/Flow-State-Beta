"""
Keeping documents current (roadmap C1.3): the rules every crawl path
follows, the async worker (workers/crawl_worker.py) and the synchronous
Crawl Selected (app_admin_esp_routes.py) alike.

- Unchanged text is not re-indexed: same hash as the stored copy, and the
  document has vectors, so re-embedding it would write the same chunks.
- A page that answers 404 or 410 is a miss; MISS_LIMIT misses in a row, and
  the admin offers to retire or replace it. A good crawl resets the count.
- A Yotpo guide's header (title, plans, platforms) is stored on its row when
  it is crawled. It is never a label: labels stay a person's choice (I1).
- Retiring a document deletes its vectors and keeps the row (crawl_status
  'retired', retired_at), so it is not crawled, counted, rebuilt or audited
  again, and a later import or sitemap run doesn't bring it back. Crawling
  it again by hand un-retires it.

Pure functions first; the database operations take the adapter.
"""

import hashlib
import json
from typing import Dict, List, Optional

from urls import normalize_url

MISS_LIMIT = 3
MISS_STATUSES = (404, 410)
YOTPO_GUIDE_HOST = 'support.yotpo.com'
# What the job (and the admin) say about a crawl that changed nothing
UNCHANGED = 'unchanged'
UNCHANGED_NOTE = 'Unchanged since the last crawl; not re-indexed'


# ---------- pure ----------

def content_hash(text: str) -> str:
    """The esp_documents.content_hash of a stored text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def unchanged(stored_hash: Optional[str], vector_count: Optional[int], text: str) -> bool:
    """True when re-indexing `text` would write what the index already has:
    its hash is the stored one and the document has chunks. A count of NULL
    (indexed before counts were kept) or 0 is re-indexed once, which records
    the count."""
    return bool(stored_hash) and isinstance(vector_count, int) and vector_count > 0 \
        and content_hash(text) == stored_hash


def is_miss(kind: Optional[str], status_code: Optional[int]) -> bool:
    """A crawl that found the page gone (404 or 410, not retried)."""
    from crawler import PERMANENT
    return kind == PERMANENT and status_code in MISS_STATUSES


def is_yotpo_guide(url: str) -> bool:
    from urllib.parse import urlsplit
    return (urlsplit(url or '').hostname or '').lower() == YOTPO_GUIDE_HOST


def header_fields(url: str, text: str, title: Optional[str] = None) -> Dict:
    """{title, supported_plans, supported_platforms} for a Yotpo guide's
    crawl, as JSON-ready values; {} for any other page."""
    if not is_yotpo_guide(url):
        return {}
    import doc_header
    header = doc_header.parse_header(text)
    return {'title': (title or '').strip()[:300] or None,
            'supported_plans': header['plans'],
            'supported_platforms': header['platforms']}


# ---------- database ----------

def record_success(db, doc_id: str, fields: Dict, job_id: Optional[str] = None,
                   reset_misses: bool = True) -> None:
    """After a crawl that indexed the document: the header fields, the miss
    count back to 0, and the row un-retired.

    Un-retiring follows the indexing, whatever its source: a re-index from
    the saved copy (a pasted document) is in the chat just the same. Only
    the document's own crawl un-retires it (crawl_job_id = job_id; the
    synchronous path passes None: an admin asked for that crawl). A saved
    copy keeps its misses (reset_misses False): the page itself is still
    gone."""
    sets, params = [], []
    if fields:
        sets += ['title = COALESCE(%s, title)', 'supported_plans = %s', 'supported_platforms = %s']
        params += [fields.get('title'), json.dumps(fields.get('supported_plans') or []),
                   json.dumps(fields.get('supported_platforms') or [])]
    if reset_misses:
        sets.append('consecutive_misses = 0')
    if job_id is None:
        sets.append('retired_at = NULL')
    else:
        sets.append('retired_at = CASE WHEN crawl_job_id = %s THEN NULL ELSE retired_at END')
        params.append(job_id)
    db.execute_query(f"UPDATE esp_documents SET {', '.join(sets)} WHERE id = %s",
                     tuple(params) + (doc_id,))


def record_miss(db, doc_id: str) -> None:
    db.execute_query("UPDATE esp_documents SET consecutive_misses = COALESCE(consecutive_misses, 0) + 1 "
                     "WHERE id = %s", (doc_id,))


def retire(db, vectorizer, esp_name: str, urls: List[str]) -> Dict[str, List]:
    """Retire some of one integration's documents: their rows stay, marked
    retired, and their vectors go. Returns {retired: [url], skipped:
    [{url, error}]}.

    The database comes first, so no crawl can index the page again in
    between: waiting crawls are cancelled, then the row is marked retired
    unless a crawl is running right now (that one would index it again, so
    it is left alone), then the vectors are deleted and checked gone. An
    already retired document is retired again: its delete is re-run, which
    is how a delete that failed is repaired."""
    out = {'retired': [], 'skipped': []}
    esp_name = (esp_name or '').lower()
    for url in urls:
        url = normalize_url(url) if isinstance(url, str) else url
        rows = db.execute_query("""
            SELECT d.id FROM esp_documents d JOIN esps e ON e.id = d.esp_id
            WHERE e.name = %s AND d.url = %s
        """, (esp_name, url), fetch=True)
        if not rows:
            out['skipped'].append({'url': url, 'error': 'Not a document of this integration'})
            continue
        doc_id = rows[0][0]
        # crawl_jobs exists on both databases; only the async queue fills it
        db.execute_query("UPDATE crawl_jobs SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP "
                         "WHERE document_id = %s AND status = 'pending'", (doc_id,))
        marked = db.execute_query("""
            UPDATE esp_documents
            SET retired_at = COALESCE(retired_at, CURRENT_TIMESTAMP), crawl_status = 'retired',
                vector_count = 0, is_crawling = FALSE, crawl_job_id = NULL
            WHERE id = %s AND NOT EXISTS (
                SELECT 1 FROM crawl_jobs j WHERE j.document_id = %s AND j.status = 'processing')
            RETURNING id
        """, (doc_id, doc_id), fetch=True)
        if not marked:
            out['skipped'].append({'url': url, 'error': 'Being crawled right now: retire it when that finishes'})
            continue
        problem = _delete_vectors(vectorizer, esp_name, url)
        if problem:
            out['skipped'].append({'url': url, 'error': f'Marked retired, but {problem}. Retire it again.'})
            continue
        out['retired'].append(url)
    return out


def _delete_vectors(vectorizer, esp_name: str, url: str) -> Optional[str]:
    """Delete one document's vectors and check they are gone (the Pinecone
    adapter reports a failed delete as "0 deleted"). Why not, or None."""
    try:
        if hasattr(vectorizer, 'delete_by_url'):
            vectorizer.delete_by_url(url, esp_name)
        if hasattr(vectorizer, 'url_exists') and vectorizer.url_exists(url, esp_name):
            return 'its search entries are still there'
    except Exception as e:
        return f'its search entries could not be removed ({e})'
    return None


def retire_replaced(db, vectorizer, new_doc_id: str) -> List[str]:
    """Retire the documents waiting for `new_doc_id` to be indexed (Replace):
    called after a crawl of it indexed it."""
    rows = db.execute_query("""
        SELECT e.name, d.url FROM esp_documents d JOIN esps e ON e.id = d.esp_id
        WHERE d.replaced_by = %s AND d.retired_at IS NULL
    """, (new_doc_id,), fetch=True) or []
    done = []
    for esp_name, url in rows:
        done += retire(db, vectorizer, esp_name, [url])['retired']
    return done


def still_retired(db, doc_id: str, job_id: str) -> bool:
    """True when the document was retired since this crawl was queued (its
    crawl_job_id cleared): the worker must not index it again."""
    rows = db.execute_query("SELECT retired_at, crawl_job_id FROM esp_documents WHERE id = %s",
                            (doc_id,), fetch=True)
    return bool(rows and rows[0][0] and str(rows[0][1] or '') != str(job_id))

