"""
Crawl queue: retry policy, enqueueing, and how a URL's crawl state is
described to admins.

The policy functions are pure so they can be tested without a database.
Everything that touches the queue assumes Postgres (the worker claims jobs
with FOR UPDATE SKIP LOCKED, so async crawling is Postgres-only anyway).
"""

import random
import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

from crawler import url_host, RATE_LIMITED, TRANSIENT, PERMANENT

# Crawled fine, but the vector-index upsert failed. Retried like TRANSIENT.
INDEX = 'index'
# Couldn't crawl, so the doc was re-indexed from its saved copy instead.
BACKFILLED = 'backfilled'

# Wait before each retry of a transient failure (attempt 1 -> 15s, ...),
# plus up to 25% jitter so a batch of failures doesn't retry in lockstep.
TRANSIENT_BACKOFF_SECONDS = (15, 60, 240)
# 429 without a usable Retry-After: 30s, doubling per consecutive 429 from
# the same host, capped at 15 minutes.
RATE_LIMIT_BASE_SECONDS = 30
RATE_LIMIT_MAX_SECONDS = 15 * 60
# Floor on a server-provided Retry-After ("0", or a reset already passed).
RATE_LIMIT_MIN_SECONDS = 5
# Rate-limit waits don't use up attempts; this is the backstop.
MAX_RATE_LIMIT_WAITS = 10


@dataclass
class RetryDecision:
    retry: bool
    delay: float = 0.0              # seconds until the job may run again
    refund_attempt: bool = False    # rate-limit waits don't count as attempts
    host_backoff: Optional[float] = None  # pause the whole host this long
    give_up_note: Optional[str] = None    # appended to the final error


def rate_limit_delay(retry_after: Optional[float], consecutive_429: int) -> float:
    """Seconds to pause a host after its `consecutive_429`-th 429 in a row."""
    if retry_after is not None:
        return max(float(retry_after), RATE_LIMIT_MIN_SECONDS)
    exponent = max(consecutive_429, 1) - 1
    return float(min(RATE_LIMIT_BASE_SECONDS * (2 ** exponent), RATE_LIMIT_MAX_SECONDS))


def transient_delay(attempt: int, rand=random.random) -> float:
    """Seconds before retrying after failed attempt number `attempt` (1-based)."""
    base = TRANSIENT_BACKOFF_SECONDS[min(max(attempt, 1), len(TRANSIENT_BACKOFF_SECONDS)) - 1]
    return base * (1 + 0.25 * rand())


def plan_retry(kind: str, attempts: int, max_attempts: int, rate_limited_count: int,
               retry_after: Optional[float] = None, consecutive_429: int = 1,
               rand=random.random) -> RetryDecision:
    """
    Decide what happens to a job whose attempt just failed.

    attempts: attempts made so far, including the one that just failed.
    rate_limited_count: rate-limit waits before this one.
    consecutive_429: this host's 429 streak, including this one.
    """
    if kind == RATE_LIMITED:
        if rate_limited_count + 1 > MAX_RATE_LIMIT_WAITS:
            return RetryDecision(False, give_up_note=f"gave up after {MAX_RATE_LIMIT_WAITS} rate-limit waits")
        delay = rate_limit_delay(retry_after, consecutive_429)
        return RetryDecision(True, delay=delay, refund_attempt=True, host_backoff=delay)

    if kind in (TRANSIENT, INDEX):
        if attempts < max_attempts:
            return RetryDecision(True, delay=transient_delay(attempts, rand))
        return RetryDecision(False, give_up_note=f"gave up after {attempts} attempts")

    # PERMANENT, or anything unrecognised: retrying the same request won't help
    return RetryDecision(False)


# ==================== Queue operations ====================

OUT_OF_RETRIES_ERROR = "Stopped: this crawl was out of retries"


def _active_job(db, document_id):
    rows = db.execute_query(
        "SELECT id FROM crawl_jobs WHERE document_id = %s AND status IN ('pending', 'processing')",
        (document_id,), fetch=True)
    return str(rows[0][0]) if rows else None


def enqueue_crawl_job(db, esp_id, document_id, url, priority: int = 10) -> Tuple[str, bool]:
    """
    Queue a crawl for one document.

    Returns (job_id, newly_created). If the document already has a pending or
    processing job, that job's id is returned instead of queueing a duplicate.
    """
    # An active job the worker can never claim (legacy row with no host, or
    # out of attempts) would otherwise hold this document's slot forever and
    # make every later crawl report "already queued"
    repair_queue(db, document_id=document_id)

    existing = _active_job(db, document_id)
    if existing:
        return existing, False

    host = url_host(url)
    job_id = str(uuid.uuid4())
    # The host's pacing gate must exist before the worker can claim the job
    db.execute_query(
        "INSERT INTO crawl_hosts (host) VALUES (%s) ON CONFLICT (host) DO NOTHING",
        (host,))
    try:
        db.execute_query(
            """
            INSERT INTO crawl_jobs (id, esp_id, document_id, priority, host, next_attempt_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (job_id, esp_id, document_id, priority, host))
    except Exception as e:
        # idx_crawl_jobs_one_active: a concurrent request (double click, two
        # admins) queued this document between our check and insert
        if getattr(e, 'pgcode', None) != '23505':
            raise
        existing = _active_job(db, document_id)
        if existing:
            return existing, False
        raise
    db.execute_query(
        "UPDATE esp_documents SET is_crawling = TRUE, crawl_job_id = %s WHERE id = %s",
        (job_id, document_id))
    return job_id, True


def repair_queue(db, document_id=None):
    """
    Make every active job claimable or finished. Idempotent and cheap; runs
    at boot, from the periodic stale-job sweep, and before each enqueue
    (scoped to that document).

    - Jobs with no host (queued by code from before pacing, e.g. an old
      instance during a deploy overlap) get their host from the URL.
    - Every host with jobs gets a pacing gate row.
    - Pending jobs that are out of attempts (which the claim query skips)
      are failed, and their documents released.
    """
    scope = "AND j.document_id = %s" if document_id else ""
    params = (document_id,) if document_id else ()

    rows = db.execute_query(f"""
        SELECT j.id, d.url FROM crawl_jobs j
        JOIN esp_documents d ON d.id = j.document_id
        WHERE j.host IS NULL AND j.status IN ('pending', 'processing') {scope}
    """, params, fetch=True) or []
    for job_id, url in rows:
        db.execute_query("UPDATE crawl_jobs SET host = %s WHERE id = %s AND host IS NULL",
                         (url_host(url), job_id))

    db.execute_query(f"""
        INSERT INTO crawl_hosts (host)
        SELECT DISTINCT j.host FROM crawl_jobs j
        WHERE j.host IS NOT NULL AND j.status IN ('pending', 'processing') {scope}
        ON CONFLICT (host) DO NOTHING
    """, params)

    failed = db.execute_query(f"""
        UPDATE crawl_jobs j
        SET status = 'failed', completed_at = NOW(),
            error_kind = COALESCE(error_kind, 'transient'),
            error_message = COALESCE(error_message, %s)
        WHERE j.status = 'pending' AND j.attempts >= j.max_attempts {scope}
        RETURNING j.id, j.document_id, j.error_message
    """, (OUT_OF_RETRIES_ERROR,) + params, fetch=True) or []
    for job_id, doc_id, error in failed:
        db.execute_query("""
            UPDATE esp_documents
            SET crawl_status = 'failed', error_message = %s, is_crawling = FALSE
            WHERE id = %s AND (crawl_job_id = %s OR crawl_job_id IS NULL)
        """, (error, doc_id, job_id))
    return len(rows), len(failed)


def enqueue_urls(db, esp_mgr, esp, esp_name, urls):
    """
    Queue a crawl for each URL under an ESP, creating document rows as needed.

    Returns (job_ids, skipped_urls); skipped URLs already had an active job,
    whose id is included in job_ids so the caller can track it.
    """
    job_ids, skipped = [], []
    for url in urls:
        doc = esp_mgr.get_document_by_url(esp['id'], url)
        if not doc:
            doc = esp_mgr.add_document(esp_name, url)
        job_id, created = enqueue_crawl_job(db, esp['id'], doc['id'], url)
        job_ids.append(job_id)
        if not created:
            skipped.append(url)
    return job_ids, skipped


def queued_response(job_ids, skipped):
    """JSON body for a crawl-selected request that queued jobs."""
    message = f'Queued {len(job_ids)} URLs for crawling'
    if skipped:
        message += f' ({len(skipped)} already queued/processing)'
    return {
        'success': True,
        'job_ids': job_ids,
        'total': len(job_ids),
        'message': message,
        'skipped_count': len(skipped),
    }


# ==================== Describing state to admins ====================

def format_wait(seconds: Optional[float]) -> str:
    """'in ~40s' / 'in ~3 min' / 'shortly' for a retry that's that far away."""
    if seconds is None or seconds < 5:
        return 'shortly'
    if seconds < 90:
        return f"in ~{int(round(seconds))}s"
    return f"in ~{int(round(seconds / 60))} min"


def describe_link(crawl_status, has_content, doc_error, job_status=None,
                  job_error_kind=None, job_error=None, wait_seconds=None, url=None):
    """
    (state, detail) for one URL, as shown in the admin link lists.

    state is one of: crawled, saved_copy (couldn't crawl; indexed from the
    copy we already had), pending (never crawled), failed, queued, crawling,
    retrying, waiting (rate-limited). detail is a short human-readable
    reason, or None.
    """
    if job_status == 'processing':
        return 'crawling', 'Crawling now'
    if job_status == 'pending':
        if job_error_kind == RATE_LIMITED:
            return 'waiting', f"{job_error} — retrying {format_wait(wait_seconds)}"
        if job_error_kind:
            return 'retrying', f"{job_error} — retrying {format_wait(wait_seconds)}"
        if wait_seconds and wait_seconds >= 5:
            return 'queued', f"Queued — the site is paused after a rate limit, starts {format_wait(wait_seconds)}"
        return 'queued', 'Queued'

    if crawl_status == 'completed':
        if job_error_kind == BACKFILLED and job_error:
            # A pasted doc can only ever be re-indexed, so that's a success;
            # a web page we couldn't fetch is a problem even if it's indexed
            if url and url.startswith('local://'):
                return 'crawled', job_error
            return 'saved_copy', job_error
        return 'crawled', None
    if crawl_status == 'failed':
        detail = doc_error or 'The last crawl failed'
        if job_error_kind == INDEX:
            # Re-indexing replaces a URL's vectors (delete, then add), so a
            # failed add means the old copy has left search results too
            if url and url.startswith('local://'):
                detail += ' · not in search results until it is re-indexed (run Crawl Selected again)'
            else:
                detail += ' · not in search results until a crawl succeeds'
        elif has_content:
            detail += ' · the previously saved copy is still in use'
        return 'failed', detail
    return 'pending', None


# Everything describe_link needs for every document of one ESP, joined to
# the document's latest job and that job's host gate.
DOCUMENT_STATE_QUERY = """
    SELECT d.url, d.filename, d.crawl_status, d.last_crawled_at, d.error_message,
           d.content IS NOT NULL AS has_content, d.is_crawling,
           j.status, j.error_kind, j.error_message,
           EXTRACT(EPOCH FROM (
               GREATEST(COALESCE(j.next_attempt_at, NOW()),
                        COALESCE(h.backoff_until, NOW())) - NOW()
           )) AS wait_seconds
    FROM esp_documents d
    LEFT JOIN crawl_jobs j ON j.id = d.crawl_job_id
    LEFT JOIN crawl_hosts h ON h.host = j.host
    WHERE d.esp_id = %s
    ORDER BY d.created_at DESC
"""


def list_document_states(db, esp_id):
    """Rows of DOCUMENT_STATE_QUERY as dicts, with state/detail added."""
    rows = db.execute_query(DOCUMENT_STATE_QUERY, (esp_id,), fetch=True) or []
    docs = []
    for (url, filename, crawl_status, last_crawled_at, doc_error, has_content,
         is_crawling, job_status, job_error_kind, job_error, wait_seconds) in rows:
        wait = float(wait_seconds) if wait_seconds is not None else None
        state, detail = describe_link(crawl_status, bool(has_content), doc_error,
                                      job_status, job_error_kind, job_error, wait, url)
        docs.append({
            'url': url,
            'filename': filename,
            'crawl_status': crawl_status,
            'last_crawled_at': last_crawled_at.isoformat() if last_crawled_at else None,
            'error_message': doc_error,
            'has_content': bool(has_content),
            'is_crawling': bool(is_crawling),
            'state': state,
            'detail': detail,
        })
    return docs
