"""
Background worker for processing crawl jobs.

Can run as:
1. Thread pool within Flask app (simple, for low volume)
2. Standalone process (for high volume - future)

Features:
- Atomic job claiming (prevents race conditions)
- Per-host pacing: at most one request per host every min_interval_ms,
  enforced in Postgres so it holds across threads and replicas
- Retries scheduled by outcome: rate limits wait as long as the site asks
  (without using up attempts), transient errors back off exponentially,
  permanent errors (404, bad URL) fail at once
- File locking for crawl_metadata.json
- Graceful shutdown
- Stale job detection
"""

import os
import time
import signal
import hashlib
import threading
import traceback
import fcntl
import json
from typing import Optional, Dict

# Import crawler and vectorizer
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import (crawl_single_url_result, filename_from_url, vectorize_single_document,
                     find_saved_copy, save_filename_for, saved_text, FetchResult, OK, RATE_LIMITED, TRANSIENT, PERMANENT)
from adapters.database.db_manager import get_database_adapter
from adapters.vector.vector_manager import get_vector_adapter
from mechanics_cache import clear_mechanics_cache
from workers.crawl_queue import plan_retry, repair_queue, INDEX, BACKFILLED

# How long an idle thread waits before looking for a claimable job again:
# 1s right after work (the next job is usually just waiting out its host's
# 2s gate), doubling while the queue stays empty, up to 5s.
IDLE_POLL_SECONDS = 1
IDLE_POLL_MAX_SECONDS = 5

# Claim the highest-priority job that is due and whose host gate is open.
# FOR UPDATE OF j, h SKIP LOCKED: two threads can't take the same job, and
# can't both take a job on the same host in the same instant. Once the
# claiming transaction commits the new next_allowed_at, the row's WHERE
# clause is re-checked for anyone else, so the gate holds.
CLAIM_QUERY = """
    SELECT j.id, j.host
    FROM crawl_jobs j
    JOIN crawl_hosts h ON h.host = j.host
    WHERE j.status = 'pending'
      AND j.attempts < j.max_attempts
      AND (j.next_attempt_at IS NULL OR j.next_attempt_at <= NOW())
      AND h.next_allowed_at <= NOW()
      AND (h.backoff_until IS NULL OR h.backoff_until <= NOW())
    ORDER BY j.priority DESC, j.created_at ASC
    LIMIT 1
    FOR UPDATE OF j, h SKIP LOCKED
"""


class CrawlWorker:
    """Background worker for processing crawl jobs."""

    def __init__(self, worker_id: str, max_workers: int = 3, base_path: str = None):
        """
        Initialize worker.

        Args:
            worker_id: Unique identifier for this worker instance
            max_workers: Number of concurrent worker threads
            base_path: Base path of the application
        """
        self.worker_id = worker_id
        self.max_workers = max_workers
        self.running = False
        self.threads = []

        # Get base path
        if base_path:
            self.base_path = base_path
        else:
            # Default: two levels up from this file
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Initialize database adapter
        self.db = get_database_adapter()

        # Initialize vectorizer
        db_path = os.path.join(self.base_path, "backend/chroma_db")
        self.vectorizer = get_vector_adapter(persist_directory=db_path)

        print(f"[WORKER {self.worker_id}] Initialized with {max_workers} threads")

    def start(self):
        """Start worker threads."""
        if self.running:
            print(f"[WORKER {self.worker_id}] Already running")
            return

        self.running = True
        try:
            # Jobs queued before pacing existed (or by an old instance during
            # a deploy) need a host and a gate before anything can claim them
            fixed, failed = repair_queue(self.db)
            if fixed or failed:
                print(f"[WORKER {self.worker_id}] Queue repair: {fixed} jobs given a host, {failed} out-of-retries jobs failed")
        except Exception as e:
            print(f"[WORKER {self.worker_id}] Queue repair failed: {e}")
        print(f"[WORKER {self.worker_id}] Starting {self.max_workers} worker threads...")

        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._worker_loop,
                name=f"CrawlWorker-{self.worker_id}-{i}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)

        print(f"[WORKER {self.worker_id}] All threads started ✓")

    def stop(self, timeout: int = 30):
        """
        Graceful shutdown.

        Args:
            timeout: Max seconds to wait for threads to finish
        """
        if not self.running:
            return

        print(f"[WORKER {self.worker_id}] Shutting down gracefully...")
        self.running = False

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=timeout)
            if thread.is_alive():
                print(f"[WORKER {self.worker_id}] WARNING: Thread {thread.name} did not finish in time")

        print(f"[WORKER {self.worker_id}] Shutdown complete")

    def _worker_loop(self):
        """Main worker loop - continuously process jobs."""
        thread_name = threading.current_thread().name
        idle = IDLE_POLL_SECONDS

        while self.running:
            try:
                job = self._claim_next_job()

                if job:
                    self._process_job(job)
                    idle = IDLE_POLL_SECONDS
                else:
                    # Nothing due, or every due job's host is still gated
                    time.sleep(idle)
                    idle = min(idle * 2, IDLE_POLL_MAX_SECONDS)

            except Exception as e:
                print(f"[WORKER {thread_name}] ERROR in worker loop: {e}")
                traceback.print_exc()
                time.sleep(5)  # Back off on errors

    def _claim_next_job(self) -> Optional[Dict]:
        """
        Atomically claim the next due job whose host is free, and close that
        host's gate for its min_interval_ms.

        Returns:
            Job dict if claimed, None if no jobs available
        """
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(CLAIM_QUERY)
                    row = cursor.fetchone()
                    if not row:
                        conn.rollback()
                        return None
                    job_id, host = row

                    # clock_timestamp(), not NOW(): NOW() is when this
                    # transaction began, which on a slow database link can be
                    # a second before the request actually goes out, and the
                    # gap between two requests would shrink by that much
                    cursor.execute("""
                        UPDATE crawl_hosts
                        SET next_allowed_at = clock_timestamp()::timestamp
                                              + make_interval(secs => min_interval_ms / 1000.0)
                        WHERE host = %s
                    """, (host,))
                    cursor.execute("""
                        UPDATE crawl_jobs
                        SET status = 'processing',
                            started_at = NOW(),
                            worker_id = %s,
                            attempts = attempts + 1
                        WHERE id = %s
                        RETURNING id, esp_id, document_id, attempts, max_attempts,
                                  host, rate_limited_count
                    """, (self.worker_id, job_id))
                    claimed = cursor.fetchone()
                    conn.commit()
                finally:
                    cursor.close()

            return {
                'id': claimed[0],
                'esp_id': claimed[1],
                'document_id': claimed[2],
                'attempts': claimed[3],
                'max_attempts': claimed[4],
                'host': claimed[5],
                'rate_limited_count': claimed[6],
            }

        except Exception as e:
            print(f"[WORKER ERROR] Failed to claim job: {e}")
            return None

    def _process_job(self, job: Dict):
        """
        Process a single crawl job and record its outcome.

        Args:
            job: Job dictionary from _claim_next_job
        """
        job_id = job['id']
        document_id = job['document_id']

        try:
            result = self.db.execute_query("""
                SELECT d.url, d.filename, e.name, d.content IS NOT NULL
                FROM esp_documents d
                JOIN esps e ON d.esp_id = e.id
                WHERE d.id = %s
            """, (document_id,), fetch=True)
            if not result:
                self._finish_failed(job, None, FetchResult(PERMANENT, error="The document was deleted"), None)
                return
            url, old_filename, esp_name, has_content = result[0]
        except Exception as e:
            # Database hiccup before we even know the URL: retry the job
            self._handle_failure(job, None, None, FetchResult(TRANSIENT, error=f"Internal error: {e}"))
            return

        doc = {'id': document_id, 'url': url, 'filename': old_filename,
               'esp_name': esp_name, 'has_content': bool(has_content)}

        try:
            print(f"[WORKER] Processing job {job_id}: {url}")
            filename, fetch = crawl_single_url_result(url, esp_name, self.base_path)
        except Exception as e:
            traceback.print_exc()
            filename, fetch = None, FetchResult(TRANSIENT, error=f"Internal error while crawling: {e}")

        if fetch.kind != OK:
            self._handle_failure(job, doc, filename, fetch)
            return

        # The text as crawled, not re-read from disk: another URL whose
        # filename collides with this one may have overwritten the file
        content = saved_text(url, fetch.content)
        filepath = os.path.join(self.base_path, 'docs', esp_name, filename)
        try:
            self._update_metadata_atomic(esp_name, url, filename)
        except Exception as e:
            # Local bookkeeping, before any vectors are touched: retry it
            traceback.print_exc()
            self._handle_failure(job, doc, filename, FetchResult(
                TRANSIENT, error=f"Crawled, but saving it locally failed: {e}"))
            return
        try:
            vectorize_single_document(self.vectorizer, esp_name, url, filepath, filename, content=content)
        except Exception as e:
            traceback.print_exc()
            self._handle_failure(job, doc, filename, FetchResult(
                INDEX, error=f"Crawled, but adding it to the search index failed: {e}"))
            return

        self._finish_completed(job, doc, filename, content)
        self._notify_indexed(esp_name)
        print(f"[WORKER] ✓ Job {job_id} completed: {filename}")

    def _notify_indexed(self, esp_name):
        """
        This ESP's chunks changed, so memoized Query B results are stale.
        Only reaches the chat workers when the worker runs in the Flask
        process (start_worker_in_background); a standalone worker is a
        separate process and they expire on the TTL.
        """
        try:
            clear_mechanics_cache()
        except Exception as e:
            print(f"[WORKER] Could not clear the mechanics cache: {e}")

    # ==================== Outcomes ====================

    def _handle_failure(self, job: Dict, doc: Optional[Dict], filename, fetch: FetchResult):
        """Schedule a retry, fall back to the saved copy, or fail the job."""
        try:
            consecutive_429 = 1
            if fetch.kind == RATE_LIMITED and job.get('host'):
                rows = self.db.execute_query("""
                    UPDATE crawl_hosts
                    SET consecutive_429 = consecutive_429 + 1, last_429_at = NOW()
                    WHERE host = %s
                    RETURNING consecutive_429
                """, (job['host'],), fetch=True)
                if rows:
                    consecutive_429 = rows[0][0]

            decision = plan_retry(fetch.kind, job['attempts'], job['max_attempts'],
                                  job['rate_limited_count'], fetch.retry_after, consecutive_429)

            if decision.retry:
                self._schedule_retry(job, fetch, decision)
                return

            # Not after an index failure of a fresh crawl: the "saved copy"
            # would be the file this crawl just wrote, and the result would be
            # reported as "couldn't crawl, served an old copy" when the page
            # crawled fine and only indexing failed
            if doc and fetch.kind != INDEX:
                outcome = self._try_saved_copy(job, doc, fetch)
                if outcome is True:
                    return
                if isinstance(outcome, FetchResult):
                    # There is a saved copy, but indexing it failed: that's a
                    # (usually transient) index failure, not the crawl error,
                    # so retry it as one and report it as one
                    fetch = outcome
                    decision = plan_retry(outcome.kind, job['attempts'], job['max_attempts'],
                                          job['rate_limited_count'])
                    if decision.retry:
                        self._schedule_retry(job, fetch, decision)
                        return

            error = fetch.error or 'Crawl failed'
            if decision.give_up_note:
                error = f"{error} — {decision.give_up_note}"
            self._finish_failed(job, doc, fetch, error)

        except Exception as e:
            # Never leave a job stuck in 'processing' because recording its
            # outcome failed; the stale-job sweeper will pick it up otherwise
            print(f"[WORKER] ✗ Could not record outcome of job {job['id']}: {e}")
            traceback.print_exc()

    def _schedule_retry(self, job: Dict, fetch: FetchResult, decision):
        rows = self.db.execute_query("""
            UPDATE crawl_jobs
            SET status = 'pending',
                worker_id = NULL,
                error_kind = %s,
                error_message = %s,
                next_attempt_at = NOW() + make_interval(secs => %s),
                attempts = attempts - %s,
                rate_limited_count = rate_limited_count + %s
            WHERE id = %s AND status = 'processing'
            RETURNING id
        """, (fetch.kind, fetch.error, float(decision.delay),
              1 if decision.refund_attempt else 0,
              1 if fetch.kind == RATE_LIMITED else 0,
              job['id']), fetch=True)

        if decision.host_backoff and job.get('host'):
            # Pause the whole host: every other job queued for it waits too
            self.db.execute_query("""
                UPDATE crawl_hosts
                SET backoff_until = GREATEST(COALESCE(backoff_until, NOW()),
                                             NOW() + make_interval(secs => %s))
                WHERE host = %s
            """, (float(decision.host_backoff), job['host']))

        if rows:
            print(f"[WORKER] ↻ Job {job['id']} ({fetch.kind}): {fetch.error} — retry in {decision.delay:.0f}s")
        else:
            print(f"[WORKER] Job {job['id']} was cancelled while running; not retrying")

    def _finish_completed(self, job: Dict, doc: Dict, filename, content, note=None):
        """Record a successful crawl (or a re-index from the saved copy)."""
        # The document is updated even if the job was cancelled mid-flight:
        # its vectors were already replaced, so the stored content must match
        self.db.execute_query("""
            UPDATE esp_documents
            SET crawl_status = 'completed',
                filename = %s,
                content_hash = %s,
                content = %s,
                error_message = NULL,
                last_crawled_at = NOW(),
                is_crawling = CASE WHEN crawl_job_id = %s THEN FALSE ELSE is_crawling END
            WHERE id = %s
        """, (filename, hashlib.sha256(content.encode()).hexdigest(), content,
              job['id'], doc['id']))

        if job.get('host') and not note:
            self.db.execute_query(
                "UPDATE crawl_hosts SET consecutive_429 = 0 WHERE host = %s", (job['host'],))

        self.db.execute_query("""
            UPDATE crawl_jobs
            SET status = 'completed',
                completed_at = NOW(),
                error_kind = %s,
                error_message = %s
            WHERE id = %s AND status = 'processing'
        """, (BACKFILLED if note else None, note, job['id']))

    def _finish_failed(self, job: Dict, doc: Optional[Dict], fetch: FetchResult, error):
        error = error or fetch.error or 'Crawl failed'
        rows = self.db.execute_query("""
            UPDATE crawl_jobs
            SET status = 'failed',
                completed_at = NOW(),
                error_kind = %s,
                error_message = %s
            WHERE id = %s AND status = 'processing'
            RETURNING id
        """, (fetch.kind, error, job['id']), fetch=True)

        if not rows:
            print(f"[WORKER] Job {job['id']} was cancelled while running")
            return

        if doc:
            # Only if this is still the document's latest job; a newer crawl
            # of the same URL owns its status otherwise
            self.db.execute_query("""
                UPDATE esp_documents
                SET crawl_status = 'failed',
                    error_message = %s,
                    is_crawling = FALSE
                WHERE id = %s AND (crawl_job_id = %s OR crawl_job_id IS NULL)
            """, (error, doc['id'], job['id']))

        print(f"[WORKER] ✗ Job {job['id']} failed: {error}")

    def _try_saved_copy(self, job: Dict, doc: Dict, fetch: FetchResult) -> bool:
        """
        When a URL can't be crawled, re-index it from the copy we already have.

        Applies to pasted (local://) docs, which can never be crawled, and to
        docs with no database backup yet (crawled before content was stored
        in the database) whose saved file is still on disk. A doc that is
        already backed up is left alone and the failure is reported:
        silently serving an old copy of a page that now 404s would hide it.

        Only a copy that provably belongs to this URL is used: the database
        row's own content, or a file whose "Source URL:" header names it.
        Saved filenames collide (every local:// URL maps to index.txt), so a
        file found by name alone could be another document's text.

        Returns True if the job was completed from the saved copy, False if
        there is no usable copy, or a FetchResult (INDEX, or TRANSIENT for a
        local file error) if there is one but re-indexing it failed.
        """
        url = doc['url']
        is_pasted = url.startswith('local://')
        if not is_pasted and doc['has_content']:
            return False

        esp_name = doc['esp_name']
        filename, content = None, None
        if is_pasted and doc['has_content']:
            rows = self.db.execute_query(
                "SELECT filename, content FROM esp_documents WHERE id = %s",
                (doc['id'],), fetch=True)
            if rows and rows[0][1]:
                filename = rows[0][0] or filename_from_url(url)
                content = rows[0][1]
        if content is None:
            filename, content = find_saved_copy(self.base_path, esp_name, url, doc['filename'])
        if content is None:
            return False

        try:
            esp_folder = os.path.join(self.base_path, 'docs', esp_name)
            os.makedirs(esp_folder, exist_ok=True)
            own, _ = find_saved_copy(self.base_path, esp_name, url, filename)
            if own:
                filename = own  # already on disk under this URL's name
            else:
                # Restore it (usual on Railway's ephemeral disk) under a name
                # that no other URL's saved copy uses
                filename = save_filename_for(self.base_path, esp_name, url, preferred=filename)
                with open(os.path.join(esp_folder, filename), 'w', encoding='utf-8') as f:
                    f.write(content)
            filepath = os.path.join(esp_folder, filename)
            self._update_metadata_atomic(esp_name, url, filename)
        except Exception as e:
            print(f"[WORKER] Could not restore the saved copy of {url}: {e}")
            return FetchResult(TRANSIENT, error=f"Couldn't restore the saved copy locally: {e}")
        try:
            vectorize_single_document(self.vectorizer, esp_name, url, filepath, filename, content=content)
        except Exception as e:
            print(f"[WORKER] Could not re-index {url} from its saved copy: {e}")
            return FetchResult(INDEX, error=f"Couldn't add the saved copy to the search index: {e}")

        if is_pasted:
            note = "Pasted content — re-indexed from the saved copy"
        else:
            note = f"Couldn't crawl ({fetch.error}); re-indexed from the saved copy instead"
        self._finish_completed(job, doc, filename, content, note=note)
        self._notify_indexed(esp_name)
        print(f"[WORKER] ✓ Job {job['id']}: {note}")
        return True

    def _update_metadata_atomic(self, esp_name: str, url: str, filename: str):
        """
        Atomically update crawl_metadata.json with file locking.

        Args:
            esp_name: ESP name
            url: Document URL
            filename: Saved filename
        """
        metadata_path = os.path.join(self.base_path, 'docs', 'crawl_metadata.json')

        # Ensure docs directory exists
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

        # Open with read+write, create if missing
        mode = 'r+' if os.path.exists(metadata_path) else 'w+'

        with open(metadata_path, mode) as f:
            # Acquire exclusive lock (blocks other workers)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)

            try:
                f.seek(0)
                try:
                    metadata = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    metadata = {}

                # Update metadata
                if esp_name not in metadata:
                    metadata[esp_name] = []

                # Remove old entry if exists (by URL)
                metadata[esp_name] = [d for d in metadata[esp_name] if d.get('url') != url]

                # Add new entry
                filepath = os.path.join(self.base_path, 'docs', esp_name, filename)
                metadata[esp_name].append({
                    'url': url,
                    'filename': filename,
                    'filepath': filepath
                })

                # Write back
                f.seek(0)
                f.truncate()
                json.dump(metadata, f, indent=2)
                f.flush()

            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def cleanup_stale_jobs(db_adapter, timeout_minutes: int = 10):
        """
        Recover jobs stuck in 'processing' (the worker died mid-job, e.g. a
        redeploy): re-queue them, or fail them if they're out of attempts —
        re-queueing an exhausted job would leave it pending forever, since
        the claim query skips jobs with attempts >= max_attempts.
        """
        minutes = int(timeout_minutes)
        try:
            repair_queue(db_adapter)
            db_adapter.execute_query(f"""
                UPDATE crawl_jobs
                SET status = 'pending',
                    worker_id = NULL,
                    started_at = NULL,
                    next_attempt_at = NOW()
                WHERE status = 'processing'
                AND started_at < NOW() - INTERVAL '{minutes} minutes'
                AND attempts < max_attempts
            """)

            error = ("The crawl worker stopped while processing this URL "
                     "(for example during a redeploy), and it is out of retries")
            failed = db_adapter.execute_query(f"""
                UPDATE crawl_jobs
                SET status = 'failed',
                    completed_at = NOW(),
                    error_kind = 'transient',
                    error_message = %s
                WHERE status = 'processing'
                AND started_at < NOW() - INTERVAL '{minutes} minutes'
                AND attempts >= max_attempts
                RETURNING id, document_id
            """, (error,), fetch=True) or []

            for job_id, document_id in failed:
                db_adapter.execute_query("""
                    UPDATE esp_documents
                    SET crawl_status = 'failed', error_message = %s, is_crawling = FALSE
                    WHERE id = %s AND (crawl_job_id = %s OR crawl_job_id IS NULL)
                """, (error, document_id, job_id))
            if failed:
                print(f"[CLEANUP] Failed {len(failed)} stale jobs that were out of retries")

        except Exception as e:
            print(f"[CLEANUP ERROR] Failed to cleanup stale jobs: {e}")


def start_worker_in_background(worker_id: str = None, max_workers: int = 3, base_path: str = None):
    """
    Start a crawl worker in the background (for use in Flask app).

    Args:
        worker_id: Unique identifier for this worker (default: flask-{pid})
        max_workers: Number of concurrent worker threads
        base_path: Base path of the application

    Returns:
        CrawlWorker instance (call .stop() to shutdown)
    """
    if worker_id is None:
        worker_id = f"flask-{os.getpid()}"

    worker = CrawlWorker(worker_id, max_workers, base_path)
    worker.start()

    return worker


if __name__ == '__main__':
    """Standalone worker mode (for testing or separate process)."""
    import argparse

    parser = argparse.ArgumentParser(description='Crawl worker')
    parser.add_argument('--workers', type=int, default=3, help='Number of worker threads')
    parser.add_argument('--worker-id', type=str, default=None, help='Worker ID')
    args = parser.parse_args()

    worker_id = args.worker_id or f"standalone-{os.getpid()}"

    print("=" * 60)
    print("ESP LOYALTY HELPER - ASYNC CRAWL WORKER")
    print("=" * 60)
    print(f"Worker ID: {worker_id}")
    print(f"Threads: {args.workers}")
    print(f"Press Ctrl+C to stop")
    print("=" * 60)
    print()

    worker = CrawlWorker(worker_id, args.workers)
    worker.start()

    # Handle shutdown signals
    def signal_handler(sig, frame):
        print()
        print("Received shutdown signal...")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        worker.stop()
