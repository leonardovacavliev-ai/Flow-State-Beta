"""
Background worker for processing crawl jobs.

Can run as:
1. Thread pool within Flask app (simple, for low volume)
2. Standalone process (for high volume - future)

Features:
- Atomic job claiming (prevents race conditions)
- File locking for crawl_metadata.json
- Retry logic with exponential backoff
- Graceful shutdown
- Stale job detection
"""

import os
import time
import signal
import threading
import traceback
import fcntl
import json
from datetime import datetime
from typing import Optional, Dict

# Import crawler and vectorizer
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler import crawl_single_url
from adapters.database.db_manager import get_database_adapter
from adapters.vector.vector_manager import get_vector_adapter


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

        while self.running:
            try:
                job = self._claim_next_job()

                if job:
                    self._process_job(job)
                else:
                    # No jobs available, sleep before checking again
                    time.sleep(2)

            except Exception as e:
                print(f"[WORKER {thread_name}] ERROR in worker loop: {e}")
                traceback.print_exc()
                time.sleep(5)  # Back off on errors

    def _claim_next_job(self) -> Optional[Dict]:
        """
        Atomically claim the next pending job.

        Uses SELECT FOR UPDATE SKIP LOCKED for atomic claiming without deadlocks.

        Returns:
            Job dict if claimed, None if no jobs available
        """
        try:
            query = """
                UPDATE crawl_jobs
                SET status = 'processing',
                    started_at = NOW(),
                    worker_id = %s,
                    attempts = attempts + 1
                WHERE id = (
                    SELECT id FROM crawl_jobs
                    WHERE status = 'pending'
                    AND attempts < max_attempts
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, esp_id, document_id, attempts, max_attempts
            """

            result = self.db.execute_query(
                query,
                (self.worker_id,),
                fetch=True
            )

            if result and len(result) > 0:
                row = result[0]
                return {
                    'id': row[0],
                    'esp_id': row[1],
                    'document_id': row[2],
                    'attempts': row[3],
                    'max_attempts': row[4]
                }

            return None

        except Exception as e:
            print(f"[WORKER ERROR] Failed to claim job: {e}")
            return None

    def _process_job(self, job: Dict):
        """
        Process a single crawl job.

        Args:
            job: Job dictionary with id, esp_id, document_id
        """
        job_id = job['id']
        document_id = job['document_id']

        try:
            # Get document details
            query = """
                SELECT d.url, d.filename, e.name as esp_name
                FROM esp_documents d
                JOIN esps e ON d.esp_id = e.id
                WHERE d.id = %s
            """
            result = self.db.execute_query(query, (document_id,), fetch=True)

            if not result:
                raise Exception(f"Document {document_id} not found")

            url = result[0][0]
            old_filename = result[0][1]
            esp_name = result[0][2]

            print(f"[WORKER] Processing job {job_id}: {url}")

            # Crawl the URL
            filename = crawl_single_url(url, esp_name, self.base_path)

            if not filename:
                raise Exception("Crawler returned None (empty content or network error)")

            # Update crawl_metadata.json with file lock
            self._update_metadata_atomic(esp_name, url, filename)

            # Vectorize the document
            self._vectorize_document(esp_name)

            # Calculate content hash
            file_path = os.path.join(self.base_path, 'docs', esp_name, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import hashlib
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Update document status
            update_query = """
                UPDATE esp_documents
                SET crawl_status = 'completed',
                    filename = %s,
                    content_hash = %s,
                    last_crawled_at = NOW(),
                    is_crawling = FALSE
                WHERE id = %s
            """
            self.db.execute_query(update_query, (filename, content_hash, document_id))

            # Mark job as completed
            complete_query = """
                UPDATE crawl_jobs
                SET status = 'completed',
                    completed_at = NOW()
                WHERE id = %s
            """
            self.db.execute_query(complete_query, (job_id,))

            print(f"[WORKER] ✓ Job {job_id} completed: {filename}")

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()

            print(f"[WORKER] ✗ Job {job_id} failed: {error_msg}")

            # Determine if should retry
            should_retry = job['attempts'] < job['max_attempts']
            new_status = 'pending' if should_retry else 'failed'

            # Update job status
            fail_query = """
                UPDATE crawl_jobs
                SET status = %s,
                    error_message = %s,
                    error_traceback = %s,
                    completed_at = CASE WHEN %s = 'failed' THEN NOW() ELSE NULL END
                WHERE id = %s
            """
            self.db.execute_query(
                fail_query,
                (new_status, error_msg, error_trace, new_status, job_id)
            )

            # Mark document as failed if no more retries
            if not should_retry:
                doc_fail_query = """
                    UPDATE esp_documents
                    SET crawl_status = 'failed',
                        error_message = %s,
                        is_crawling = FALSE
                    WHERE id = %s
                """
                self.db.execute_query(doc_fail_query, (error_msg, document_id))
            else:
                print(f"[WORKER] Will retry job {job_id} (attempt {job['attempts']}/{job['max_attempts']})")

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

    def _vectorize_document(self, esp_name: str):
        """
        Vectorize documents for an ESP.

        Args:
            esp_name: ESP name
        """
        try:
            docs_path = os.path.join(self.base_path, 'docs')
            self.vectorizer.refresh_esp(esp_name, docs_path)
            print(f"[WORKER] Vectorized {esp_name}")
        except Exception as e:
            print(f"[WORKER] Vectorization error for {esp_name}: {e}")
            # Don't fail the job if vectorization fails - can be re-vectorized later
            # Just log and continue

    @staticmethod
    def cleanup_stale_jobs(db_adapter, timeout_minutes: int = 10):
        """
        Reset jobs stuck in 'processing' for too long.

        Args:
            db_adapter: Database adapter instance
            timeout_minutes: How long before a job is considered stale
        """
        try:
            query = """
                UPDATE crawl_jobs
                SET status = 'pending',
                    worker_id = NULL,
                    started_at = NULL
                WHERE status = 'processing'
                AND started_at < NOW() - INTERVAL '%s minutes'
            """
            # Note: Using string formatting for interval because psycopg2 doesn't support
            # parameterized intervals with %s
            query = query.replace('%s', str(timeout_minutes))

            result = db_adapter.execute_query(query, fetch=False)

            # Get rowcount if available
            if hasattr(db_adapter, 'last_rowcount'):
                reset_count = db_adapter.last_rowcount
                if reset_count > 0:
                    print(f"[CLEANUP] Reset {reset_count} stale jobs")

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
