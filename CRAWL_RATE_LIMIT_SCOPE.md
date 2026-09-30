# Crawl Rate Limiting & Status Honesty — Scope

**Date:** 2026-09-29
**Trigger:** 50-URL crawl of `develop.yotpo.com` (other_webhook ESP) — 5 succeeded, 45 failed (44× HTTP 429, 1× 404). Re-run at 12:08 failed the same way. The admin UI never said why.

---

## 1. What actually happened

Measured from production `crawl_jobs` (read-only):

| Fact | Evidence |
|------|----------|
| All 50 URLs are on one host | `develop.yotpo.com` (ReadMe behind Cloudflare, `x-ratelimit-limit: 100`) |
| 3 worker threads drained the queue with no pacing | `CRAWL_WORKER_THREADS=3`, single worker `flask-3`, 50 jobs finished in ~7s |
| **Retries fired instantly** | Each 429'd job used all 3 attempts in **24–37 ms** total |
| Retries tripled the load | ~145 requests in ~7s against a 100-request budget, and never let the bucket refill |
| 404 was retried 3× too | Permanent errors are treated the same as transient ones |

Three bugs working together:

1. **No backoff on retry.** `_process_job` sets a failed job back to `status='pending'` and `_claim_next_job` re-claims it on the next loop iteration ([crawl_worker.py:258-274](backend/workers/crawl_worker.py:258)). The module docstring claims "retry logic with exponential backoff". That isn't true.
2. **No per-host pacing.** The claim query only orders by priority and creation time ([crawl_worker.py:138-153](backend/workers/crawl_worker.py:138)). Fifty URLs on one host run as fast as three threads can go.
3. **429 is an opaque string.** `extract_main_content_detailed` turns every `HTTPError` into `"Server returned HTTP {status}"` ([crawler.py:35-37](backend/crawler.py:35)). The worker can't tell "slow down" from "gone", and it throws away `Retry-After` / `x-ratelimit-reset`.

---

## 2. Long-term fix: host-aware, rate-limit-aware queue

**Principle:** Postgres is already the queue and the source of truth, so it also owns pacing. There's no Redis token bucket and no in-process limiter, because both break once Railway runs more than one replica.

### 2.1 Schema (`backend/migrations/002_crawl_pacing.sql`, additive)

```sql
ALTER TABLE crawl_jobs
  ADD COLUMN host            TEXT,                                -- filled at enqueue
  ADD COLUMN next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- backoff lives here
  ADD COLUMN error_kind      VARCHAR(20),                         -- see 2.2
  ADD COLUMN rate_limited_count INTEGER NOT NULL DEFAULT 0;

CREATE TABLE crawl_hosts (
  host             TEXT PRIMARY KEY,
  min_interval_ms  INTEGER     NOT NULL DEFAULT 2000,  -- 1 req / 2s per host
  next_allowed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- the pacing gate
  backoff_until    TIMESTAMPTZ,                        -- set from Retry-After on 429
  last_429_at      TIMESTAMPTZ
);

CREATE INDEX idx_crawl_jobs_ready ON crawl_jobs (status, next_attempt_at);
```

Backfill `host` for existing rows from `esp_documents.url`.

### 2.2 Classify every outcome

Change `extract_main_content_detailed` to return a small result object (status code, `Retry-After`, `x-ratelimit-reset`, message) instead of a string. The worker maps it to:

| `error_kind` | Triggers | Behaviour |
|---|---|---|
| `rate_limited` | 429, 503 with `Retry-After` | Set `crawl_hosts.backoff_until` from the header, or fall back to 30s → 60s → 120s … capped at 15 min. Re-queue with `next_attempt_at = backoff_until`. **Does not consume `attempts`.** A separate cap (`rate_limited_count` ≤ 10) is the backstop. |
| `transient` | 5xx, timeout, connection error | Exponential backoff with jitter (15s, 60s, 240s). Consumes `attempts`. |
| `permanent` | 404, 410, 401/403, bad scheme, `local://`, parse produced no content | Fail immediately, no retries. |
| `index` | Crawl OK, Pinecone upsert failed | Job **fails** (today it's silently marked completed, see [crawl_worker.py:355-358](backend/workers/crawl_worker.py:355)). |

### 2.3 Claim only what's ready *and* whose host is free

One transaction:

```sql
-- 1. pick a ready job whose host gate is open
SELECT j.id, j.host
FROM crawl_jobs j JOIN crawl_hosts h ON h.host = j.host
WHERE j.status = 'pending'
  AND j.next_attempt_at <= NOW()
  AND h.next_allowed_at <= NOW()
  AND (h.backoff_until IS NULL OR h.backoff_until <= NOW())
ORDER BY j.priority DESC, j.created_at
LIMIT 1
FOR UPDATE OF j, h SKIP LOCKED;

-- 2. close the host gate for min_interval, claim the job
UPDATE crawl_hosts SET next_allowed_at = NOW() + make_interval(secs => min_interval_ms / 1000.0) WHERE host = $host;
UPDATE crawl_jobs  SET status = 'processing', started_at = NOW(), worker_id = $w, attempts = attempts + 1 WHERE id = $id;
```

`FOR UPDATE OF h` means two threads (or two replicas) can never both take the same host inside one interval. Different hosts still run in parallel, so a mixed Klaviyo + Listrak + Yotpo batch isn't serialised.

**For this incident:** 50 URLs at 1 req/2s takes about 100 seconds and stays well under the 100-request budget.

### 2.4 Small hygiene items bundled in

- Default `min_interval_ms` is configurable per host from the admin panel later. It stays as a DB value for now, with no UI yet.
- Replace the spoofed Chrome UA with an honest one (`YotpoESPHelper/1.0 (+contact)`). `develop.yotpo.com` is Yotpo's own docs, so it could be allowlisted internally.
- Optional, separate: `develop.yotpo.com/llms.txt` returns 200. ReadMe serves clean markdown, which would be a better source than scraping HTML for that host. Out of scope here. It's a note for later.

### 2.5 Tests (`backend/tests/test_crawl_pacing.py`)

- 429 with `Retry-After: 30` sets `next_attempt_at` about 30s out and doesn't increment `attempts`.
- 404 goes straight to `failed` after exactly one request.
- Two threads racing on one host: only one claim per interval (against real Postgres or a test DB, not mocks).
- Vectorization failure marks the job failed, not completed.

---

## 3. Status & progress audit

What the admin sees today, in order of how much it misled:

| # | Problem | Where | Effect |
|---|---|---|---|
| 1 | **Failed docs are shown as `PENDING`.** The links endpoint collapses everything that isn't `completed` into `'pending'`. `error_message` is returned but never rendered. | [app_admin_esp_routes_async.py:73](backend/app_admin_esp_routes_async.py:73), [app.js:1352-1370](frontend/app.js:1352) | After the run, 45 URLs looked like they'd never been tried: yellow badge, pre-checked, "Paste Content" button. No failure, no reason. |
| 2 | **The progress panel deletes itself.** The tracker is inserted *inside* `#espManagement`. On completion, `loadESPManagement()` runs after 1.5s and does `container.innerHTML = ''` on that same element. | [app.js:1634-1638](frontend/app.js:1634), [crawl-progress-tracker.js:214-218](frontend/crawl-progress-tracker.js:214), [app.js:1328](frontend/app.js:1328) | The per-URL error list and the "45 failed" summary are visible for 1.5 seconds and then wiped. |
| 3 | Retrying looks identical to waiting. A job that's been re-queued shows `⌛ pending`, and `attempts` is returned but unused. | [crawl-progress-tracker.js:113-146](frontend/crawl-progress-tracker.js:113) | There's no way to tell "not started" from "failed twice, trying again". |
| 4 | Raw error strings, one per row, ungrouped. | same | 44 identical `Crawl failed: Server returned HTTP 429` lines. No explanation that it means rate limiting or what happens next. |
| 5 | Summary says **"Crawling complete!"** even when 90% failed. | [crawl-progress-tracker.js:205](frontend/crawl-progress-tracker.js:205) | The framing reads as success. |
| 6 | Progress is lost on reload. The tracker only knows job IDs held in memory, and there's no "what's running now" endpoint. | — | Close the tab and the in-flight crawl disappears from the UI. |
| 7 | Poll failures are console-only. A 403 (expired session) or a 500 freezes the panel at its last state with no message. | [crawl-progress-tracker.js:103-106](frontend/crawl-progress-tracker.js:103) | The panel looks stuck rather than broken. |
| 8 | Vectorization failures are swallowed. The job shows ✓ even if the doc never reached Pinecone. | [crawl_worker.py:355-358](backend/workers/crawl_worker.py:355) | "Completed" doesn't mean searchable. |
| 9 | `is_crawling` is returned per link and never shown. | [app_admin_esp_routes_async.py:78](backend/app_admin_esp_routes_async.py:78) | There's no in-progress state on the ESP list itself. |

### 3.1 Target status model

One vocabulary for both backend and UI:

| State | Badge | Shown text (example) |
|---|---|---|
| `queued` | grey | Queued |
| `crawling` | blue, spinner | Crawling… |
| `waiting` | amber | Rate-limited by develop.yotpo.com — retrying at 12:10 |
| `retrying` | amber | Server error (HTTP 500) — attempt 2 of 3 at 12:04 |
| `completed` | green | Crawled 12:03 · indexed |
| `failed` | red | Not found (HTTP 404) — check the URL · or · Gave up after 10 rate-limit waits |
| `never_crawled` | outline | Not crawled yet |

`waiting` and `retrying` are derived from `status='pending'` + `error_kind` + `next_attempt_at`. They don't need new DB states.

### 3.2 UI changes

- **Links endpoint:** return the real state + human reason + `next_attempt_at`. Render a red `FAILED` badge with the reason inline. Pre-check `never_crawled` / `failed` (and `saved_copy`) so the next "Crawl Selected" retries them. *(Decided: no separate "Retry failed" button — see §5.)*
- **Progress panel:** move it outside `#espManagement` so the list refresh can't destroy it. Keep it until it's dismissed.
- **Grouped summary:** "5 crawled · 44 waiting on develop.yotpo.com rate limit (next try 12:10) · 1 not found". It should say "finished with problems" instead of "complete!" when anything failed.
- **Pace/ETA line:** "45 left · about 1 every 2s on develop.yotpo.com · ~1.5 min". This comes from `crawl_hosts`, not from guessing.
- **Resume on load:** add a `GET /api/admin/crawl-active` endpoint (jobs not terminal, or finished in the last hour). The admin panel reattaches the tracker on page load.
- **Poll failure:** after 3 consecutive poll errors, show "Lost connection to progress updates (HTTP 403 — sign in again)". The jobs keep running server-side.

---

## 4. Phasing

| Phase | Contents | Size |
|---|---|---|
| **P1: stop hitting the wall** | Migration 002, result classification, backoff via `next_attempt_at`, per-host claim gate, honor `Retry-After`, no retries on permanent errors, vectorization failure = job failure, tests | ~1 day |
| **P2: tell the truth in the UI** | Audit items 1, 2, 5 (the misleading ones), real states in the links endpoint, grouped summary (failed links stay pre-selected, in red) | ~0.5 day |
| **P3: progress you can trust** | `waiting`/`retrying` display with times, ETA from host pacing, `crawl-active` resume, poll-failure banner, `is_crawling` on the list | ~0.5–1 day |
| Later / optional | Per-host interval in admin UI, adaptive rate (back off on 429, creep up on sustained success), `llms.txt` source for ReadMe-hosted docs | — |

P1 and P2 should ship together. Pacing without honest status would just hide slower failures.

## 5. Decisions

1. **Pace:** 1 request / 2s per host, as proposed. `Retry-After` / `X-RateLimit-Reset` are honoured on top of it.
2. **Failed URLs:** stay pre-selected for the next "Crawl Selected", with a **red** badge and the reason — no separate "Retry failed" button.
3. **Global knowledge:** moved onto the queue. "Refresh All" goes through the queue too, since it was the other path that could burst a site.

## 6. What shipped beyond this scope

Found during implementation and review, and fixed in the same change:

- A new `saved_copy` state (amber, pre-selected): a page that couldn't be crawled but was re-indexed from the copy already on file is a problem, not a green success.
- Saved copies are only used when they provably belong to the URL (`Source URL:` header, or an unambiguous legacy metadata entry); saved filenames collide (every `local://` URL and site root maps to `index.txt`), and every writer now picks a name no other URL's copy uses.
- Queue repair (`repair_queue`): legacy jobs with no host, and pending jobs out of attempts, no longer hold a URL in QUEUED forever. A unique index allows one active job per document.
- The chat's retrieval cache is cleared when a crawl actually re-indexes a doc, not when it is queued.
- Status polling uses POST (a Refresh All of every doc overflowed the request line as a query string).
- Queueing endpoints refuse with 503 when the crawl worker isn't running, instead of queueing jobs nothing will process.
