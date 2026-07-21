# Async Crawl Implementation Plan

## Executive Summary

Convert the synchronous ESP crawl system to an **asynchronous background job system** to eliminate timeouts, enable progress tracking, and support concurrent operations.

**Goal**: Users can queue 100 URLs, close their browser, and come back later to see results.

**Key Requirement**: Zero downtime migration, no breaking changes, clean rollback path.

---

## Table of Contents

1. [Current Architecture](#current-architecture)
2. [Proposed Architecture](#proposed-architecture)
3. [Database Schema Changes](#database-schema-changes)
4. [Background Job System](#background-job-system)
5. [API Changes](#api-changes)
6. [Frontend Changes](#frontend-changes)
7. [Edge Cases & Conflicts](#edge-cases--conflicts)
8. [Migration Strategy](#migration-strategy)
9. [Testing Plan](#testing-plan)
10. [Rollback Plan](#rollback-plan)
11. [Deployment Checklist](#deployment-checklist)

---

## Current Architecture

### Synchronous Flow (Current)
```
User clicks "Crawl" → API /crawl-selected
  ↓ (blocking HTTP request)
For each URL:
  1. Crawl HTML (5-10 sec)
  2. Save to filesystem
  3. Update crawl_metadata.json (file lock)
  4. Vectorize (10-20 sec per doc)
  5. Update PostgreSQL
  ↓ (30-90 seconds later)
Return response → Frontend shows result
```

**Problems**:
- ⏱️ Times out after 30-60 seconds (Railway limit)
- 🚫 Blocks API server thread
- 😞 No progress updates
- 🐛 Silent failures if timeout occurs
- ❌ Can't handle multiple users crawling

---

## Proposed Architecture

### Asynchronous Flow (New)
```
User clicks "Crawl" → API /crawl-selected
  ↓ (returns immediately)
Creates job entries in PostgreSQL → Returns job IDs
  ↓
Frontend polls /crawl-status → Shows progress
  ↓ (in parallel)
Background Worker(s) process jobs:
  1. Pick next pending job
  2. Mark as "processing"
  3. Crawl → Save → Vectorize
  4. Mark as "completed" or "failed"
  ↓
Frontend shows final results
```

**Benefits**:
- ✅ No timeouts (unlimited processing time)
- ✅ Progress tracking (2/10 URLs complete)
- ✅ Can handle 100s of concurrent users
- ✅ Retry logic built-in
- ✅ Users can close browser and come back

---

## Database Schema Changes

### New Table: `crawl_jobs`

```sql
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    esp_id UUID NOT NULL REFERENCES esps(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES esp_documents(id) ON DELETE CASCADE,
    
    -- Job metadata
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- Values: 'pending', 'processing', 'completed', 'failed', 'cancelled'
    priority INTEGER NOT NULL DEFAULT 0,
        -- Higher = process first. User-initiated = 10, scheduled = 0
    
    -- Retry logic
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Error tracking
    error_message TEXT,
    error_traceback TEXT,
    
    -- Worker tracking
    worker_id VARCHAR(100),
        -- Which worker is processing this job
    
    -- Deduplication
    UNIQUE(document_id, status)
        -- Prevents duplicate pending jobs for same document
);

CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_esp ON crawl_jobs(esp_id);
CREATE INDEX idx_crawl_jobs_created ON crawl_jobs(created_at);
CREATE INDEX idx_crawl_jobs_priority ON crawl_jobs(priority DESC, created_at ASC);
```

### Modified Table: `esp_documents`

**Add columns** (no schema migration needed - all nullable):
```sql
ALTER TABLE esp_documents ADD COLUMN IF NOT EXISTS crawl_job_id UUID;
ALTER TABLE esp_documents ADD COLUMN IF NOT EXISTS is_crawling BOOLEAN DEFAULT FALSE;
```

**Why**: Track which job is currently processing a document, prevent concurrent crawls.

### New Table: `crawl_batches` (Optional, for UX)

```sql
CREATE TABLE crawl_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    esp_id UUID NOT NULL REFERENCES esps(id) ON DELETE CASCADE,
    user_identifier VARCHAR(255),
        -- IP address or session ID (for analytics)
    
    total_jobs INTEGER NOT NULL,
    completed_jobs INTEGER NOT NULL DEFAULT 0,
    failed_jobs INTEGER NOT NULL DEFAULT 0,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

**Purpose**: Group related jobs so frontend can show "Batch 3/10 complete" instead of individual job status.

---

## Background Job System

### Architecture Choice: **Python Threading + PostgreSQL Queue**

**Why NOT Celery/RQ**:
- ✅ No new dependencies (Redis already available)
- ✅ Simpler deployment (no separate worker process initially)
- ✅ PostgreSQL as queue is reliable and we already have it
- ⚠️ Can upgrade to Celery later if needed (same job table structure)

### Worker Implementation

**Location**: `backend/workers/crawl_worker.py`

```python
"""
Background worker for processing crawl jobs.

Can run as:
1. Thread pool within Flask app (simple, for low volume)
2. Standalone process (for high volume)
3. Multiple processes on different machines (for scale)
"""

import os
import time
import signal
import threading
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

class CrawlWorker:
    def __init__(self, worker_id: str, max_workers: int = 3):
        self.worker_id = worker_id
        self.max_workers = max_workers
        self.running = True
        self.threads = []
        
    def start(self):
        """Start worker threads"""
        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._worker_loop,
                name=f"CrawlWorker-{self.worker_id}-{i}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            
    def stop(self):
        """Graceful shutdown"""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=30)
            
    def _worker_loop(self):
        """Main worker loop - continuously process jobs"""
        while self.running:
            job = self._claim_next_job()
            
            if job:
                self._process_job(job)
            else:
                # No jobs available, sleep
                time.sleep(2)
                
    def _claim_next_job(self):
        """Atomically claim the next pending job"""
        conn = self._get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Use SELECT FOR UPDATE SKIP LOCKED for atomic claim
            cur.execute("""
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
                RETURNING *
            """, (self.worker_id,))
            
            job = cur.fetchone()
            conn.commit()
            return job
            
        except Exception as e:
            conn.rollback()
            print(f"[WORKER ERROR] Failed to claim job: {e}")
            return None
        finally:
            cur.close()
            conn.close()
            
    def _process_job(self, job):
        """Process a single crawl job"""
        job_id = job['id']
        document_id = job['document_id']
        
        conn = self._get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get document details
            cur.execute("""
                SELECT d.*, e.name as esp_name
                FROM esp_documents d
                JOIN esps e ON d.esp_id = e.id
                WHERE d.id = %s
            """, (document_id,))
            doc = cur.fetchone()
            
            if not doc:
                raise Exception(f"Document {document_id} not found")
                
            # Crawl the URL
            from crawler import crawl_single_url
            filename = crawl_single_url(
                doc['url'],
                doc['esp_name'],
                os.path.dirname(os.path.dirname(__file__))
            )
            
            if not filename:
                raise Exception("Crawler returned None")
                
            # Update crawl_metadata.json (with file lock)
            self._update_metadata(doc['esp_name'], doc['url'], filename)
            
            # Vectorize
            self._vectorize_document(doc['esp_name'], filename)
            
            # Update document status
            cur.execute("""
                UPDATE esp_documents
                SET crawl_status = 'completed',
                    filename = %s,
                    last_crawled_at = NOW(),
                    is_crawling = FALSE
                WHERE id = %s
            """, (filename, document_id))
            
            # Mark job as completed
            cur.execute("""
                UPDATE crawl_jobs
                SET status = 'completed',
                    completed_at = NOW()
                WHERE id = %s
            """, (job_id,))
            
            conn.commit()
            print(f"[WORKER] ✓ Job {job_id} completed: {filename}")
            
        except Exception as e:
            conn.rollback()
            
            # Check if should retry
            should_retry = job['attempts'] < job['max_attempts']
            new_status = 'pending' if should_retry else 'failed'
            
            cur.execute("""
                UPDATE crawl_jobs
                SET status = %s,
                    error_message = %s,
                    error_traceback = %s,
                    completed_at = CASE WHEN %s = 'failed' THEN NOW() ELSE NULL END
                WHERE id = %s
            """, (new_status, str(e), traceback.format_exc(), new_status, job_id))
            
            # Mark document as failed if no more retries
            if not should_retry:
                cur.execute("""
                    UPDATE esp_documents
                    SET crawl_status = 'failed',
                        is_crawling = FALSE
                    WHERE id = %s
                """, (document_id,))
                
            conn.commit()
            print(f"[WORKER] ✗ Job {job_id} failed: {e}")
            
        finally:
            cur.close()
            conn.close()
```

### Worker Startup

**Option 1: Run inside Flask app** (Simpler)
```python
# backend/app.py
from workers.crawl_worker import CrawlWorker

# Start worker threads when app starts
if os.environ.get('ENABLE_CRAWL_WORKER', 'true').lower() == 'true':
    worker = CrawlWorker(
        worker_id=f"flask-{os.getpid()}",
        max_workers=int(os.environ.get('CRAWL_WORKER_THREADS', '3'))
    )
    worker.start()
    
    # Graceful shutdown
    import atexit
    atexit.register(worker.stop)
```

**Option 2: Standalone worker process** (Scalable)
```bash
# Run separately
python backend/workers/crawl_worker.py --workers 5
```

---

## API Changes

### New Endpoint: `POST /api/admin/esp/<esp_name>/crawl-selected`

**Replace synchronous version with async version**:

```python
@app.route('/api/admin/esp/<esp_name>/crawl-selected', methods=['POST'])
def crawl_esp_selected(esp_name):
    """Queue URLs for async crawling"""
    try:
        esp_mgr = get_mgr()
        data = request.json
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
            
        # Get or create ESP
        esp = esp_mgr.get_esp_by_name(esp_name)
        if not esp:
            return jsonify({'error': f"ESP '{esp_name}' not found"}), 404
            
        job_ids = []
        document_ids = []
        
        # Create/get documents
        for url in urls:
            doc = esp_mgr.get_document_by_url(esp['id'], url)
            if not doc:
                doc = esp_mgr.add_document(esp_name, url)
            document_ids.append(doc['id'])
            
        # Create crawl jobs
        conn = get_db_connection()
        cur = conn.cursor()
        
        for doc_id in document_ids:
            # Check if job already exists
            cur.execute("""
                SELECT id FROM crawl_jobs
                WHERE document_id = %s AND status IN ('pending', 'processing')
            """, (doc_id,))
            
            existing_job = cur.fetchone()
            if existing_job:
                job_ids.append(existing_job[0])
            else:
                # Create new job
                cur.execute("""
                    INSERT INTO crawl_jobs (esp_id, document_id, priority)
                    VALUES (%s, %s, 10)
                    RETURNING id
                """, (esp['id'], doc_id))
                job_ids.append(cur.fetchone()[0])
                
                # Mark document as crawling
                cur.execute("""
                    UPDATE esp_documents
                    SET is_crawling = TRUE
                    WHERE id = %s
                """, (doc_id,))
                
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'job_ids': job_ids,
            'total': len(job_ids),
            'message': f'Queued {len(job_ids)} URLs for crawling'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### New Endpoint: `GET /api/admin/crawl-status`

**Poll for job progress**:

```python
@app.route('/api/admin/crawl-status', methods=['GET'])
def get_crawl_status():
    """Get status of crawl jobs"""
    try:
        job_ids = request.args.get('job_ids', '').split(',')
        job_ids = [j for j in job_ids if j]  # Filter empty
        
        if not job_ids:
            return jsonify({'error': 'No job_ids provided'}), 400
            
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get job status
        placeholders = ','.join(['%s'] * len(job_ids))
        cur.execute(f"""
            SELECT 
                j.id,
                j.status,
                j.attempts,
                j.error_message,
                j.created_at,
                j.completed_at,
                d.url,
                d.filename,
                d.crawl_status as doc_status
            FROM crawl_jobs j
            JOIN esp_documents d ON j.document_id = d.id
            WHERE j.id IN ({placeholders})
        """, job_ids)
        
        jobs = cur.fetchall()
        
        # Calculate summary
        total = len(jobs)
        completed = sum(1 for j in jobs if j['status'] == 'completed')
        failed = sum(1 for j in jobs if j['status'] == 'failed')
        processing = sum(1 for j in jobs if j['status'] == 'processing')
        pending = sum(1 for j in jobs if j['status'] == 'pending')
        
        cur.close()
        conn.close()
        
        return jsonify({
            'jobs': jobs,
            'summary': {
                'total': total,
                'completed': completed,
                'failed': failed,
                'processing': processing,
                'pending': pending,
                'is_complete': (completed + failed) == total
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### New Endpoint: `POST /api/admin/crawl-cancel`

**Cancel in-progress jobs**:

```python
@app.route('/api/admin/crawl-cancel', methods=['POST'])
def cancel_crawl_jobs():
    """Cancel pending/processing jobs"""
    try:
        data = request.json
        job_ids = data.get('job_ids', [])
        
        if not job_ids:
            return jsonify({'error': 'No job_ids provided'}), 400
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        placeholders = ','.join(['%s'] * len(job_ids))
        cur.execute(f"""
            UPDATE crawl_jobs
            SET status = 'cancelled',
                completed_at = NOW()
            WHERE id IN ({placeholders})
            AND status IN ('pending', 'processing')
        """, job_ids)
        
        cancelled_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'cancelled': cancelled_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Frontend Changes

### New UI Component: Progress Tracker

**Location**: `frontend/app.js`

**Replace**:
```javascript
// OLD: Blocking alert
alert(`Successfully crawled ${totalCrawled} links!`);
```

**With**:
```javascript
// NEW: Progress tracker
class CrawlProgressTracker {
    constructor(jobIds, container) {
        this.jobIds = jobIds;
        this.container = container;
        this.pollInterval = null;
    }
    
    start() {
        // Show progress UI
        this.container.innerHTML = `
            <div class="crawl-progress">
                <div class="progress-header">
                    <span class="progress-text">Crawling: <span id="progress-count">0/${this.jobIds.length}</span></span>
                    <button id="cancel-crawl" class="btn-danger-sm">Cancel</button>
                </div>
                <div class="progress-bar-container">
                    <div id="progress-bar" class="progress-bar" style="width: 0%"></div>
                </div>
                <ul id="progress-items"></ul>
            </div>
        `;
        
        // Poll for updates
        this.pollInterval = setInterval(() => this.updateProgress(), 2000);
        
        // Cancel button
        document.getElementById('cancel-crawl').onclick = () => this.cancel();
    }
    
    async updateProgress() {
        try {
            const response = await fetch(
                `${API_URL}/admin/crawl-status?job_ids=${this.jobIds.join(',')}`,
                { method: 'GET' }
            );
            
            const data = await response.json();
            
            if (!data.jobs) return;
            
            // Update progress bar
            const progress = (data.summary.completed + data.summary.failed) / data.summary.total * 100;
            document.getElementById('progress-bar').style.width = `${progress}%`;
            document.getElementById('progress-count').textContent = 
                `${data.summary.completed + data.summary.failed}/${data.summary.total}`;
            
            // Update item list
            const itemsList = document.getElementById('progress-items');
            itemsList.innerHTML = data.jobs.map(job => {
                const icon = {
                    'completed': '✓',
                    'failed': '✗',
                    'processing': '⏳',
                    'pending': '⌛'
                }[job.status] || '?';
                
                return `
                    <li class="progress-item status-${job.status}">
                        <span class="item-icon">${icon}</span>
                        <span class="item-url">${job.url}</span>
                        ${job.error_message ? `<span class="item-error">${job.error_message}</span>` : ''}
                    </li>
                `;
            }).join('');
            
            // Check if complete
            if (data.summary.is_complete) {
                clearInterval(this.pollInterval);
                this.onComplete(data.summary);
            }
            
        } catch (error) {
            console.error('Failed to update progress:', error);
        }
    }
    
    async cancel() {
        if (!confirm('Cancel crawling?')) return;
        
        try {
            await fetch(`${API_URL}/admin/crawl-cancel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_ids: this.jobIds })
            });
            
            clearInterval(this.pollInterval);
            alert('Crawl cancelled');
            await loadESPManagement(); // Refresh
            
        } catch (error) {
            alert('Failed to cancel: ' + error.message);
        }
    }
    
    onComplete(summary) {
        // Show completion message
        const message = `Crawling complete!\n✓ Success: ${summary.completed}\n✗ Failed: ${summary.failed}`;
        alert(message);
        
        // Reload ESP management to show updated checkmarks
        loadESPManagement();
    }
}

// Usage in crawlAllSelected function:
async function crawlAllSelected() {
    // ... get selected URLs ...
    
    const response = await fetch(`${API_URL}/admin/esp/${espName}/crawl-selected`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Start progress tracker
        const progressContainer = document.getElementById('crawl-progress-container');
        const tracker = new CrawlProgressTracker(data.job_ids, progressContainer);
        tracker.start();
    }
}
```

### CSS Styles

```css
/* frontend/styles.css */

.crawl-progress {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
}

.progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.progress-text {
    font-weight: 600;
    color: #374151;
}

.progress-bar-container {
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 16px;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #2563eb);
    transition: width 0.3s ease;
}

#progress-items {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 300px;
    overflow-y: auto;
}

.progress-item {
    display: flex;
    align-items: center;
    padding: 8px;
    margin: 4px 0;
    border-radius: 4px;
    font-size: 14px;
}

.progress-item.status-completed {
    background: #d1fae5;
    color: #065f46;
}

.progress-item.status-failed {
    background: #fee2e2;
    color: #991b1b;
}

.progress-item.status-processing {
    background: #fef3c7;
    color: #92400e;
    animation: pulse 2s infinite;
}

.progress-item.status-pending {
    background: #e0e7ff;
    color: #3730a3;
}

.item-icon {
    margin-right: 8px;
    font-weight: bold;
}

.item-url {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.item-error {
    margin-left: 8px;
    font-size: 12px;
    color: #dc2626;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

---

## Edge Cases & Conflicts

### 1. Concurrent Crawls of Same URL

**Problem**: Two users try to crawl the same URL simultaneously.

**Solution**:
```sql
-- UNIQUE constraint prevents duplicate pending jobs
UNIQUE(document_id, status) WHERE status IN ('pending', 'processing')

-- When creating job:
INSERT INTO crawl_jobs (document_id, ...)
ON CONFLICT (document_id) WHERE status IN ('pending', 'processing')
DO NOTHING
RETURNING id
```

**Result**: Second user gets the existing job ID, both see same progress.

---

### 2. crawl_metadata.json File Lock

**Problem**: Multiple workers writing to `crawl_metadata.json` simultaneously = corrupted JSON.

**Solution**: Use file locking
```python
import fcntl
import json

def update_metadata_atomic(esp_name, url, filename):
    """Atomically update crawl_metadata.json"""
    metadata_path = 'docs/crawl_metadata.json'
    
    # Open with read+write, create if missing
    with open(metadata_path, 'r+' if os.path.exists(metadata_path) else 'w+') as f:
        # Acquire exclusive lock (blocks other workers)
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        
        try:
            f.seek(0)
            try:
                metadata = json.load(f)
            except json.JSONDecodeError:
                metadata = {}
            
            # Update metadata
            if esp_name not in metadata:
                metadata[esp_name] = []
            
            metadata[esp_name] = [d for d in metadata[esp_name] if d.get('url') != url]
            metadata[esp_name].append({
                'url': url,
                'filename': filename,
                'filepath': f'docs/{esp_name}/{filename}'
            })
            
            # Write back
            f.seek(0)
            f.truncate()
            json.dump(metadata, f, indent=2)
            
        finally:
            # Release lock
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

---

### 3. Worker Crash Mid-Job

**Problem**: Worker dies while processing job, leaving it stuck in "processing" forever.

**Solution**: Stale job detector
```python
# Run every 5 minutes
def cleanup_stale_jobs():
    """Reset jobs stuck in 'processing' for >10 minutes"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE crawl_jobs
        SET status = 'pending',
            worker_id = NULL,
            started_at = NULL
        WHERE status = 'processing'
        AND started_at < NOW() - INTERVAL '10 minutes'
    """)
    
    reset_count = cur.rowcount
    if reset_count > 0:
        print(f"[CLEANUP] Reset {reset_count} stale jobs")
    
    conn.commit()
    cur.close()
    conn.close()
```

**Run in Flask app**:
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_stale_jobs, 'interval', minutes=5)
scheduler.start()
```

---

### 4. Database Connection Pool Exhaustion

**Problem**: Each worker thread holds a connection, pool runs out.

**Solution**: Use connection pooling
```python
from psycopg2 import pool

# Create connection pool at app startup
db_pool = pool.ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    dsn=os.environ['DATABASE_URL']
)

def get_db_connection():
    """Get connection from pool"""
    return db_pool.getconn()

def return_db_connection(conn):
    """Return connection to pool"""
    db_pool.putconn(conn)
```

**Worker pattern**:
```python
def _process_job(self, job):
    conn = get_db_connection()
    try:
        # ... process job ...
    finally:
        return_db_connection(conn)
```

---

### 5. Vectorization Timeout

**Problem**: Pinecone API timeout during vectorization (happens occasionally).

**Solution**: Retry with exponential backoff
```python
import time

def vectorize_with_retry(esp_name, docs_path, max_retries=3):
    """Vectorize with retry logic"""
    for attempt in range(max_retries):
        try:
            vectorizer.refresh_esp(esp_name, docs_path)
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Last attempt, re-raise
            
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"[VECTORIZE] Retry {attempt+1}/{max_retries} after {wait_time}s: {e}")
            time.sleep(wait_time)
    
    return False
```

---

### 6. Redis Session Conflicts

**Problem**: Worker uses Redis, sessions use Redis, keys might conflict.

**Solution**: Use key prefixes
```python
# Session keys
REDIS_KEY_SESSION = "session:{session_id}"

# Job keys (if using Redis for queue in future)
REDIS_KEY_JOB = "job:{job_id}"
REDIS_KEY_JOB_QUEUE = "queue:crawl_jobs"
```

**Current implementation**: Uses PostgreSQL, no Redis conflict.

---

### 7. Memory Usage with Large Batches

**Problem**: Vectorizing 100 docs simultaneously = high memory usage.

**Solution**: Process in smaller batches
```python
def refresh_esp_batched(esp_name, docs_path, batch_size=10):
    """Vectorize documents in batches"""
    from vectorize import get_all_docs
    
    docs = get_all_docs(esp_name, docs_path)
    
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        vectorizer.add_documents_batch(esp_name, batch)
        
        # Allow garbage collection
        import gc
        gc.collect()
```

---

### 8. Orphaned Documents

**Problem**: Document exists in database but no file on disk.

**Solution**: Add validation check
```python
def validate_document_consistency():
    """Check database vs filesystem consistency"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT d.id, d.filename, e.name as esp_name
        FROM esp_documents d
        JOIN esps e ON d.esp_id = e.id
        WHERE d.crawl_status = 'completed'
        AND d.filename IS NOT NULL
    """)
    
    docs = cur.fetchall()
    orphaned = []
    
    for doc in docs:
        filepath = f"docs/{doc['esp_name']}/{doc['filename']}"
        if not os.path.exists(filepath):
            orphaned.append(doc)
            
            # Mark for re-crawl
            cur.execute("""
                UPDATE esp_documents
                SET crawl_status = 'pending'
                WHERE id = %s
            """, (doc['id'],))
    
    conn.commit()
    cur.close()
    conn.close()
    
    if orphaned:
        print(f"[VALIDATION] Found {len(orphaned)} orphaned documents, marked for re-crawl")
```

---

### 9. Analytics System Interference

**Problem**: Analytics tracks ESP selections, now needs to track job submissions.

**Solution**: Extend analytics
```python
# backend/analytics.py

def track_crawl_job_submitted(session_id, esp_name, url_count):
    """Track when user submits crawl job"""
    query = """
        INSERT INTO analytics_events (session_id, event_type, metadata)
        VALUES (%s, 'crawl_job_submitted', %s)
    """
    db_adapter.execute(query, (session_id, json.dumps({
        'esp': esp_name,
        'url_count': url_count
    })))
```

**No breaking changes**: Analytics continues to work unchanged.

---

### 10. Admin Panel State Refresh

**Problem**: Admin sees stale checkboxes after crawl completes in background.

**Solution**: Auto-refresh when jobs complete
```javascript
class CrawlProgressTracker {
    onComplete(summary) {
        // ... show message ...
        
        // Auto-refresh ESP management
        loadESPManagement();
    }
}
```

---

## Migration Strategy

### Phase 1: Add Database Schema (Zero Downtime)

```sql
-- Run these migrations first
CREATE TABLE crawl_jobs (...);
ALTER TABLE esp_documents ADD COLUMN crawl_job_id UUID;
ALTER TABLE esp_documents ADD COLUMN is_crawling BOOLEAN DEFAULT FALSE;
```

**Deploy**: Backend code unchanged, new tables exist but unused.

---

### Phase 2: Deploy Async Code (Backwards Compatible)

**Feature flag**:
```python
# backend/app.py

USE_ASYNC_CRAWL = os.environ.get('USE_ASYNC_CRAWL', 'false').lower() == 'true'

if USE_ASYNC_CRAWL:
    from app_admin_esp_routes_async import register_esp_admin_routes_async
    register_esp_admin_routes_async(app, BASE_PATH, vectorizer)
else:
    from app_admin_esp_routes import register_esp_admin_routes
    register_esp_admin_routes(app, BASE_PATH, vectorizer)
```

**Deploy**: Set `USE_ASYNC_CRAWL=false` initially, test in staging.

---

### Phase 3: Test in Staging

```bash
# Enable async crawl in staging
railway variables set USE_ASYNC_CRAWL=true --environment staging

# Test:
1. Add new ESP with 10 URLs
2. Crawl all simultaneously
3. Check progress updates
4. Verify all complete successfully
5. Check Pinecone has vectors
6. Test chat interface
```

---

### Phase 4: Enable in Production

```bash
# Enable in production
railway variables set USE_ASYNC_CRAWL=true --environment production

# Monitor for 24 hours
- Check worker threads are running
- Check for stale jobs
- Check database connection count
- Check memory usage
```

---

### Phase 5: Remove Old Code

After 1 week of successful operation:
```bash
# Remove old synchronous code
rm backend/app_admin_esp_routes_old.py

# Remove feature flag
# backend/app.py - always use async version
```

---

## Testing Plan

### Unit Tests

```python
# tests/test_crawl_worker.py

def test_claim_next_job():
    """Test atomic job claiming"""
    # Create pending job
    job_id = create_test_job()
    
    # Worker claims it
    worker = CrawlWorker("test-worker")
    job = worker._claim_next_job()
    
    assert job['id'] == job_id
    assert job['status'] == 'processing'
    assert job['worker_id'] == 'test-worker'

def test_concurrent_claim():
    """Test two workers don't claim same job"""
    job_id = create_test_job()
    
    worker1 = CrawlWorker("worker-1")
    worker2 = CrawlWorker("worker-2")
    
    # Both try to claim simultaneously
    job1 = worker1._claim_next_job()
    job2 = worker2._claim_next_job()
    
    # Only one succeeds
    assert (job1 is not None) != (job2 is not None)

def test_metadata_file_lock():
    """Test concurrent metadata updates don't corrupt file"""
    import threading
    
    def update(i):
        update_metadata_atomic(f'test_esp_{i}', f'url_{i}', f'file_{i}.txt')
    
    # 10 threads updating simultaneously
    threads = [threading.Thread(target=update, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Verify JSON is still valid
    with open('docs/crawl_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    assert len(metadata) == 10
```

---

### Integration Tests

```python
# tests/test_crawl_api.py

def test_async_crawl_flow():
    """Test full async crawl workflow"""
    # 1. Create test ESP
    create_test_esp('test_async')
    
    # 2. Queue 3 URLs
    response = client.post('/api/admin/esp/test_async/crawl-selected', json={
        'urls': [
            'https://example.com/doc1',
            'https://example.com/doc2',
            'https://example.com/doc3'
        ]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert len(data['job_ids']) == 3
    
    # 3. Wait for completion (poll status)
    job_ids = data['job_ids']
    max_wait = 60  # seconds
    elapsed = 0
    
    while elapsed < max_wait:
        response = client.get(f'/api/admin/crawl-status?job_ids={",".join(job_ids)}')
        data = response.json()
        
        if data['summary']['is_complete']:
            break
        
        time.sleep(2)
        elapsed += 2
    
    # 4. Verify all completed
    assert data['summary']['completed'] == 3
    assert data['summary']['failed'] == 0
    
    # 5. Verify files exist
    for job in data['jobs']:
        filepath = f"docs/test_async/{job['filename']}"
        assert os.path.exists(filepath)
    
    # 6. Verify vectors in Pinecone
    results = index.query(
        vector=[0.0] * 384,
        filter={"esp": "test_async"},
        top_k=10
    )
    assert len(results.matches) > 0
```

---

### Load Tests

```python
# tests/load_test.py

def test_concurrent_users():
    """Test 10 users crawling simultaneously"""
    import concurrent.futures
    
    def user_crawl(user_id):
        response = client.post(f'/api/admin/esp/test_esp/crawl-selected', json={
            'urls': [f'https://example.com/doc_{user_id}']
        })
        return response.json()
    
    # 10 concurrent users
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(user_crawl, i) for i in range(10)]
        results = [f.result() for f in futures]
    
    # All should succeed
    assert all(r['success'] for r in results)
```

---

## Rollback Plan

### Immediate Rollback (< 1 hour)

If critical issue discovered:

```bash
# 1. Disable async crawl
railway variables set USE_ASYNC_CRAWL=false

# 2. Restart app
railway restart

# 3. Stop any stuck workers
railway run python -c "
import psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute(\"UPDATE crawl_jobs SET status='cancelled' WHERE status='processing'\")
conn.commit()
"
```

**Impact**: Old synchronous crawl resumes, no data loss.

---

### Full Rollback (> 1 hour)

If need to revert schema changes:

```sql
-- 1. Mark all pending jobs as cancelled
UPDATE crawl_jobs SET status = 'cancelled' WHERE status IN ('pending', 'processing');

-- 2. Drop new tables (data preserved via backups)
DROP TABLE IF EXISTS crawl_jobs;
DROP TABLE IF EXISTS crawl_batches;

-- 3. Remove new columns
ALTER TABLE esp_documents DROP COLUMN IF EXISTS crawl_job_id;
ALTER TABLE esp_documents DROP COLUMN IF EXISTS is_crawling;
```

**Restore from backup**:
```bash
# Railway auto-backups database every 24 hours
railway db:restore <backup-id>
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Run all unit tests: `pytest tests/`
- [ ] Run integration tests: `pytest tests/integration/`
- [ ] Load test with 10 concurrent users
- [ ] Review code changes with another developer
- [ ] Update `requirements.txt` if new dependencies added
- [ ] Create database backup: `railway db:backup`
- [ ] Deploy to staging first

### Deployment Steps

1. **Apply database migrations** (idempotent)
   ```bash
   railway run python scripts/migrate_crawl_jobs.py
   ```

2. **Deploy code** (feature flag OFF)
   ```bash
   git push origin main
   # Railway auto-deploys
   ```

3. **Verify deployment**
   - Check `/api/debug/esps` returns 200
   - Check logs for errors
   - Test old crawl still works

4. **Enable feature flag in staging**
   ```bash
   railway variables set USE_ASYNC_CRAWL=true --environment staging
   ```

5. **Test in staging** (30 min)
   - Add test ESP with 5 URLs
   - Crawl all simultaneously
   - Verify progress updates work
   - Verify all complete successfully
   - Check worker logs for errors

6. **Enable in production** (if staging passed)
   ```bash
   railway variables set USE_ASYNC_CRAWL=true --environment production
   ```

7. **Monitor production** (24 hours)
   - Watch error logs
   - Check crawl_jobs table for stale jobs
   - Monitor database connections
   - Check memory usage
   - Test a few ESPs manually

8. **Remove feature flag** (after 1 week)
   - Delete old synchronous code
   - Remove `USE_ASYNC_CRAWL` checks
   - Deploy final cleanup

### Post-Deployment

- [ ] Update documentation
- [ ] Notify team of new feature
- [ ] Create runbook for troubleshooting
- [ ] Schedule cleanup of old jobs after 30 days
- [ ] Set up monitoring alerts

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Job completion rate**: % of jobs that complete vs fail
2. **Average crawl time**: Time from job creation to completion
3. **Queue depth**: Number of pending jobs
4. **Stale jobs**: Jobs stuck in "processing" > 10 min
5. **Worker health**: Are worker threads running?

### Grafana Dashboard (Example)

```sql
-- Job status breakdown
SELECT status, COUNT(*) 
FROM crawl_jobs 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;

-- Average completion time
SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_seconds
FROM crawl_jobs
WHERE status = 'completed'
AND created_at > NOW() - INTERVAL '24 hours';

-- Failure rate by ESP
SELECT e.name, 
       COUNT(*) as total,
       SUM(CASE WHEN j.status = 'failed' THEN 1 ELSE 0 END) as failed
FROM crawl_jobs j
JOIN esps e ON j.esp_id = e.id
WHERE j.created_at > NOW() - INTERVAL '7 days'
GROUP BY e.name;
```

### Alerts

**PagerDuty/Email alerts**:
- Queue depth > 100 for > 10 minutes
- Failure rate > 20% in last hour
- No jobs completed in last 30 minutes (worker dead?)
- Stale jobs > 5

---

## Future Enhancements

### After V1 is Stable

1. **Priority queues**
   - User-initiated crawls = priority 10
   - Scheduled refreshes = priority 0
   - Admin re-indexing = priority 5

2. **Scheduled re-crawls**
   - Cron job: nightly refresh of all docs
   - Detect changes (content hash comparison)
   - Only re-vectorize if content changed

3. **Batch operations**
   - "Import 100 URLs from CSV"
   - Progress bar for entire batch
   - Email notification when complete

4. **Webhook notifications**
   - Call webhook when crawl completes
   - Integrate with Slack ("Omnisend docs updated")

5. **Distributed workers**
   - Run workers on separate machines
   - Auto-scale based on queue depth
   - Use Redis Pub/Sub for coordination

6. **Smart retry logic**
   - Detect temporary errors (network timeout) vs permanent (404)
   - Exponential backoff for temp errors
   - Give up immediately for permanent errors

7. **Rate limiting**
   - Respect robots.txt
   - Delay between requests to same domain
   - Avoid hammering external APIs

---

## Summary

This plan provides a **complete, production-ready async crawl system** that:

✅ **Eliminates timeouts** (unlimited processing time)  
✅ **Provides progress tracking** (real-time updates)  
✅ **Handles concurrent users** (atomic job claiming)  
✅ **Prevents conflicts** (file locks, deduplication)  
✅ **Enables retry logic** (automatic failure recovery)  
✅ **Backwards compatible** (feature flag, graceful migration)  
✅ **Zero downtime deployment** (incremental rollout)  
✅ **Clean rollback path** (revert in < 5 minutes)  

**Implementation Time Estimate**: 2-3 days for experienced developer

**Deployment Risk**: Low (incremental, tested, reversible)

**User Impact**: Positive (no more timeouts, better UX)

---

## Questions?

Before starting implementation, review:
1. Database schema - does it capture all necessary state?
2. Worker architecture - thread pool vs separate process?
3. Frontend UX - is progress UI clear enough?
4. Error handling - are all edge cases covered?
5. Testing strategy - do we have sufficient coverage?

**Ready to implement**: All potential issues identified and solutions provided. 🚀
