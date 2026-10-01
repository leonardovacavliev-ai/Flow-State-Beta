"""
Verify crawl pacing, retry classification and crawl-state reporting.

Usage:
    python test_crawl_pacing.py            # pure checks only (no database)
    python test_crawl_pacing.py postgres   # + queue/worker checks against
                                           #   DATABASE_URL from .env, isolated
                                           #   in schema crawl_ci_test

The postgres run never touches production tables: it creates (and drops) a
dedicated schema and points search_path at it via the connection URL. No
network requests are made: the crawler and vectorizer are replaced by fakes.
"""

import os
import sys
import time
import uuid
import tempfile
import shutil
import threading
from email.utils import formatdate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_SCHEMA = 'crawl_ci_test'

checks = []


def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"  {'✓' if cond else '✗ FAIL'} {name}")


# ==================== Pure checks ====================

class FakeResponse:
    def __init__(self, status_code, headers=None, content=b''):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content


def run_pure_checks():
    import crawler
    from crawler import parse_retry_after, fetch_main_content, url_host, OK, RATE_LIMITED, TRANSIENT, PERMANENT
    from workers.crawl_queue import (plan_retry, describe_link, rate_limit_delay, transient_delay,
                                     format_wait, MAX_RATE_LIMIT_WAITS, INDEX, BACKFILLED)

    print("\nRetry-After parsing")
    now = 1_790_000_000.0
    check("Retry-After seconds", parse_retry_after({'Retry-After': '30'}, now) == 30)
    check("Retry-After HTTP-date", abs(parse_retry_after({'Retry-After': formatdate(now + 60, usegmt=True)}, now) - 60) < 1.5)
    check("X-RateLimit-Reset as epoch", parse_retry_after({'X-RateLimit-Reset': str(int(now + 12))}, now) == 12)
    check("X-RateLimit-Reset as delta", parse_retry_after({'X-RateLimit-Reset': '7'}, now) == 7)
    check("reset in the past clamps to 0", parse_retry_after({'X-RateLimit-Reset': str(int(now - 50))}, now) == 0)
    check("huge wait clamps to 15 min", parse_retry_after({'Retry-After': '999999'}, now) == 900)
    check("garbage header -> None", parse_retry_after({'Retry-After': 'soon'}, now) is None)
    check("no header -> None", parse_retry_after({}, now) is None)
    check("Retry-After 0 defers to a later X-RateLimit-Reset",
          parse_retry_after({'Retry-After': '0', 'X-RateLimit-Reset': str(int(now + 40))}, now) == 40)
    check("'-0000' HTTP-date is read as UTC",
          abs(parse_retry_after({'Retry-After': formatdate(now + 60).replace('+0000', '-0000')}, now) - 60) < 1.5)

    print("\nFetch classification")
    real_get = crawler.requests.get
    html = b"<html><body><main><h1>Title</h1><p>Some real content here.</p></main></body></html>"

    def fake_get(response=None, exc=None):
        def _get(url, headers=None, timeout=None):
            if exc:
                raise exc
            return response
        return _get

    try:
        crawler.requests.get = fake_get(FakeResponse(429, {'Retry-After': '20'}))
        r = fetch_main_content('https://develop.yotpo.com/docs/x')
        check("429 -> rate_limited with retry_after", r.kind == RATE_LIMITED and r.retry_after == 20)
        check("429 message names the host", 'develop.yotpo.com' in r.error and '429' in r.error)

        crawler.requests.get = fake_get(FakeResponse(503, {'Retry-After': '5'}))
        check("503 + Retry-After -> rate_limited", fetch_main_content('https://a.com/').kind == RATE_LIMITED)
        crawler.requests.get = fake_get(FakeResponse(503))
        check("503 without Retry-After -> transient", fetch_main_content('https://a.com/').kind == TRANSIENT)
        crawler.requests.get = fake_get(FakeResponse(500))
        check("500 -> transient", fetch_main_content('https://a.com/').kind == TRANSIENT)
        crawler.requests.get = fake_get(FakeResponse(404))
        r = fetch_main_content('https://a.com/gone')
        check("404 -> permanent, says not found", r.kind == PERMANENT and 'not found' in r.error.lower())
        crawler.requests.get = fake_get(FakeResponse(403))
        check("403 -> permanent", fetch_main_content('https://a.com/').kind == PERMANENT)
        crawler.requests.get = fake_get(exc=crawler.requests.exceptions.Timeout())
        check("timeout -> transient", fetch_main_content('https://a.com/').kind == TRANSIENT)
        crawler.requests.get = fake_get(exc=crawler.requests.exceptions.ConnectionError())
        check("connection error -> transient", fetch_main_content('https://a.com/').kind == TRANSIENT)
        crawler.requests.get = fake_get(exc=crawler.requests.exceptions.TooManyRedirects())
        check("redirect loop -> permanent", fetch_main_content('https://a.com/').kind == PERMANENT)
        crawler.requests.get = fake_get(exc=ValueError("bad label"))
        check("URL the HTTP stack rejects -> permanent", fetch_main_content('https://a..com/').kind == PERMANENT)
        crawler.requests.get = fake_get(FakeResponse(200, content=html))
        r = fetch_main_content('https://a.com/ok')
        check("200 -> ok with content", r.kind == OK and 'Some real content' in r.content)
        crawler.requests.get = fake_get(FakeResponse(200, content=b"<html><body></body></html>"))
        check("empty page -> permanent", fetch_main_content('https://a.com/').kind == PERMANENT)
        check("local:// -> permanent without a request", fetch_main_content('local://pasted').kind == PERMANENT)
        check("ftp:// -> permanent", fetch_main_content('ftp://a.com/x').kind == PERMANENT)

        crawler.requests.get = fake_get(FakeResponse(404))
        content, error = crawler.extract_main_content_detailed('https://a.com/gone')
        check("legacy (content, error) wrapper still works", content is None and '404' in error)
    finally:
        crawler.requests.get = real_get

    check("url_host lowercases and drops port", url_host('https://Develop.Yotpo.com:443/docs') == 'develop.yotpo.com')
    check("url_host of junk -> 'unknown'", url_host('not a url') == 'unknown')

    print("\nRetry policy")
    d = plan_retry(RATE_LIMITED, attempts=1, max_attempts=3, rate_limited_count=0, retry_after=20)
    check("429: retry, refund the attempt, pause the host for Retry-After",
          d.retry and d.refund_attempt and d.delay == 20 and d.host_backoff == 20)
    d = plan_retry(RATE_LIMITED, attempts=1, max_attempts=3, rate_limited_count=0, retry_after=0)
    check("429 with Retry-After 0 still waits the 5s floor", d.delay == 5)
    check("429 without header backs off exponentially per host streak",
          [rate_limit_delay(None, n) for n in (1, 2, 3, 6, 20)] == [30, 60, 120, 900, 900])
    d = plan_retry(RATE_LIMITED, attempts=1, max_attempts=3, rate_limited_count=MAX_RATE_LIMIT_WAITS)
    check("429 gives up after MAX_RATE_LIMIT_WAITS", not d.retry and 'rate-limit waits' in d.give_up_note)
    d = plan_retry(RATE_LIMITED, attempts=3, max_attempts=3, rate_limited_count=0, retry_after=10)
    check("429 on the last attempt still retries (waits don't use attempts)", d.retry)
    d = plan_retry(TRANSIENT, attempts=1, max_attempts=3, rate_limited_count=0, rand=lambda: 0)
    check("transient attempt 1 -> retry in 15s, attempt used", d.retry and d.delay == 15 and not d.refund_attempt)
    check("transient backoff grows 15/60/240 with <=25% jitter",
          [transient_delay(n, lambda: 0) for n in (1, 2, 3, 9)] == [15, 60, 240, 240]
          and transient_delay(1, lambda: 1) == 18.75)
    d = plan_retry(TRANSIENT, attempts=3, max_attempts=3, rate_limited_count=0)
    check("transient out of attempts -> fail with note", not d.retry and '3 attempts' in d.give_up_note)
    check("index failure retries like transient", plan_retry(INDEX, 1, 3, 0).retry)
    d = plan_retry(PERMANENT, attempts=1, max_attempts=3, rate_limited_count=0)
    check("permanent -> fail at once", not d.retry and d.give_up_note is None)

    print("\nState descriptions")
    check("never crawled -> pending", describe_link(None, False, None) == ('pending', None))
    check("pending row -> pending", describe_link('pending', False, None)[0] == 'pending')
    state, detail = describe_link('failed', False, 'Page not found (HTTP 404) — check the URL')
    check("failed -> failed with reason (not 'pending')", state == 'failed' and '404' in detail)
    state, detail = describe_link('failed', True, 'Server error')
    check("failed with a backup says the saved copy is still used", state == 'failed' and 'saved copy' in detail)
    check("completed -> crawled", describe_link('completed', True, None) == ('crawled', None))
    state, detail = describe_link('completed', True, None, 'completed', BACKFILLED,
                                  'Pasted content — re-indexed from the saved copy', url='local://x')
    check("pasted doc re-indexed from its copy -> crawled with a note", state == 'crawled' and 'saved copy' in detail)
    state, detail = describe_link('completed', True, None, 'completed', BACKFILLED,
                                  "Couldn't crawl (HTTP 403); re-indexed from the saved copy instead", url='https://a.com/x')
    check("web page served from an old copy -> saved_copy, not a green 'crawled'", state == 'saved_copy' and '403' in detail)
    check("processing job -> crawling", describe_link('failed', False, 'x', 'processing')[0] == 'crawling')
    state, detail = describe_link('failed', False, 'x', 'pending', RATE_LIMITED, 'Rate-limited by a.com (HTTP 429)', 120)
    check("rate-limited pending job -> waiting with retry time",
          state == 'waiting' and '429' in detail and '~2 min' in detail)
    state, detail = describe_link(None, False, None, 'pending', TRANSIENT, 'Server error at a.com (HTTP 500)', 40)
    check("transient pending job -> retrying", state == 'retrying' and '~40s' in detail)
    check("fresh queued job -> queued", describe_link(None, False, None, 'pending', None, None, 0) == ('queued', 'Queued'))
    check("queued behind a host pause says so", 'paused' in describe_link(None, False, None, 'pending', None, None, 300)[1])
    check("format_wait", (format_wait(2), format_wait(30), format_wait(600)) == ('shortly', 'in ~30s', 'in ~10 min'))
    state, detail = describe_link('failed', True, 'Crawled, but adding it to the search index failed: x', job_error_kind=INDEX)
    check("index failure doesn't claim the old copy is still in use",
          'not in search results' in detail and 'still in use' not in detail)

    print("\nSaved-copy attribution")
    import json as _json
    from crawler import find_saved_copy
    base = tempfile.mkdtemp(prefix='saved_copy_')
    g = os.path.join(base, 'docs', 'global')
    os.makedirs(g)
    def write(name, text):
        with open(os.path.join(g, name), 'w') as f:
            f.write(text)
    write('index.txt', 'Source URL: local://someone-else\n\nother text')
    write('legacy.txt', 'Source: Some.pdf\nno header here')
    write('shared.txt', 'Source: shared\nclaimed twice')
    with open(os.path.join(base, 'docs', 'crawl_metadata.json'), 'w') as f:
        _json.dump({'global': [
            {'url': 'local://Some.pdf', 'filename': 'legacy.txt'},
            {'url': 'local://a', 'filename': 'shared.txt'},
            {'url': 'local://b', 'filename': 'shared.txt'},
        ]}, f)
    check("a colliding file with another URL's header is rejected", find_saved_copy(base, 'global', 'local://mine') == (None, None))
    check("a file whose header names the URL is accepted",
          find_saved_copy(base, 'global', 'local://someone-else')[0] == 'index.txt')
    check("a legacy header-less file is accepted when metadata maps only this URL to it",
          find_saved_copy(base, 'global', 'local://Some.pdf')[0] == 'legacy.txt')
    check("a header-less file that metadata maps to two URLs is rejected",
          find_saved_copy(base, 'global', 'local://a') == (None, None))
    write('articles_1.txt', 'Source URL: https://h.test/de/articles/1\n\nGerman page')
    with open(os.path.join(base, 'docs', 'crawl_metadata.json'), 'w') as f:
        _json.dump({'global': [{'url': 'https://h.test/en/articles/1', 'filename': 'articles_1.txt'}]}, f)
    check("metadata can't vouch for a file whose header names another URL",
          find_saved_copy(base, 'global', 'https://h.test/en/articles/1') == (None, None))

    print("\nCrawling never overwrites another URL's saved file")
    import crawler as _crawler
    real_fetch = _crawler.fetch_main_content
    try:
        _crawler.fetch_main_content = lambda url: _crawler.FetchResult(_crawler.OK, content='English page')
        name, result = _crawler.crawl_single_url_result('https://h.test/en/articles/1', 'global', base)
    finally:
        _crawler.fetch_main_content = real_fetch
    with open(os.path.join(g, 'articles_1.txt')) as f:
        check("the other URL's file is intact", 'German page' in f.read())
    with open(os.path.join(g, name)) as f:
        check(f"this URL's copy went to its own name ({name})",
              name != 'articles_1.txt' and f.readline().strip() == 'Source URL: https://h.test/en/articles/1')
    try:
        _crawler.fetch_main_content = lambda url: _crawler.FetchResult(_crawler.OK, content='English page v2')
        again, _ = _crawler.crawl_single_url_result('https://h.test/en/articles/1', 'global', base)
        os.remove(os.path.join(g, 'articles_1.txt'))  # the other URL's copy goes away
        third, _ = _crawler.crawl_single_url_result('https://h.test/en/articles/1', 'global', base)
    finally:
        _crawler.fetch_main_content = real_fetch
    check("a re-crawl reuses the name the URL already owns", again == name)
    with open(os.path.join(g, name)) as f:
        latest = f.read()
    check("…even once the usual name frees up, so the URL keeps one up-to-date copy",
          third == name and 'English page v2' in latest
          and not os.path.exists(os.path.join(g, 'articles_1.txt')))

    from crawler import save_filename_for
    check("save_filename_for: free usual name is used", save_filename_for(base, 'global', 'https://new.test/x/y') == 'x_y.txt')
    check("save_filename_for: a preferred free name wins",
          save_filename_for(base, 'global', 'https://new.test/x/y', preferred='keep.txt') == 'keep.txt')
    # Several threads choosing a name for different URLs that map to the
    # same usual filename must end up with different names
    race_dir = os.path.join(base, 'docs', 'race')
    barrier = threading.Barrier(8)
    picked = []
    def pick(i):
        barrier.wait()
        picked.append(save_filename_for(base, 'race', f'https://host{i}.test/docs/same'))
    threads = [threading.Thread(target=pick, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    check(f"8 concurrent writers with colliding names get 8 distinct names ({len(set(picked))})",
          len(set(picked)) == 8 and picked.count('docs_same.txt') == 1)
    # A reservation whose write never happened is nobody's copy, and is
    # reclaimed once stale
    import crawler as _cr
    empty_url = 'https://empty.test/a/b'
    with open(os.path.join(base, 'docs', 'crawl_metadata.json'), 'w') as f:
        _json.dump({'global': [{'url': empty_url, 'filename': 'a_b.txt'}]}, f)
    reserved = save_filename_for(base, 'global', empty_url)  # reserves a_b.txt, never written
    check("an empty reserved file is not accepted as a saved copy (even when metadata maps it)",
          reserved == 'a_b.txt' and find_saved_copy(base, 'global', empty_url) == (None, None))
    check("a fresh empty reservation is still taken (another writer may be about to fill it)",
          save_filename_for(base, 'global', 'https://other.test/a/b') != 'a_b.txt')
    old = time.time() - _cr.STALE_RESERVATION_SECONDS - 5
    os.utime(os.path.join(g, 'a_b.txt'), (old, old))
    check("a stale empty reservation is reclaimed instead of stranding the URL on a hashed name",
          save_filename_for(base, 'global', empty_url) == 'a_b.txt')
    write('hdr_only.txt', 'Source URL: https://hdr.test/\n\n   ')
    check("a file with a header but no text is not a saved copy",
          find_saved_copy(base, 'global', 'https://hdr.test/', 'hdr_only.txt') == (None, None))
    shutil.rmtree(base, ignore_errors=True)


# ==================== Postgres checks ====================

class FakeVectorizer:
    def __init__(self):
        self.fail = False
        self.indexed = []

    def delete_by_url(self, url, esp):
        pass

    def add_document(self, content, metadata):
        if self.fail:
            raise RuntimeError("pinecone unavailable")
        self.indexed.append(metadata['source_url'])


def setup_postgres():
    from dotenv import dotenv_values
    d = os.path.dirname(os.path.abspath(__file__))
    env_file = None
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.env')):
            env_file = os.path.join(d, '.env')
            break
        d = os.path.dirname(d)
    url = dotenv_values(env_file).get('DATABASE_URL') if env_file else None
    if not url:
        print("FAIL: DATABASE_URL not set in .env")
        sys.exit(1)

    import psycopg2
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", (TEST_SCHEMA,))
    if cur.fetchone():
        # Only ever drop a schema this script created; a leftover one from an
        # aborted run is ours, but say so rather than silently replacing it
        print(f"Found leftover schema {TEST_SCHEMA} from an earlier run; dropping it")
        cur.execute(f"DROP SCHEMA {TEST_SCHEMA} CASCADE")
    cur.execute(f"CREATE SCHEMA {TEST_SCHEMA}")
    conn.close()

    sep = '&' if '?' in url else '?'
    schema_url = f"{url}{sep}options=-csearch_path%3D{TEST_SCHEMA}"

    # Refuse to run unless the connection really lands in the test schema:
    # the checks below delete and update crawl rows wholesale
    conn = psycopg2.connect(schema_url)
    cur = conn.cursor()
    cur.execute("SELECT current_schema()")
    landed = cur.fetchone()[0]
    conn.close()
    if landed != TEST_SCHEMA:
        print(f"FAIL: search_path did not take effect (current_schema() = {landed!r}); refusing to run")
        teardown_postgres(url)
        sys.exit(1)
    return url, schema_url


def teardown_postgres(base_url):
    import psycopg2
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    conn.cursor().execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
    conn.close()
    print(f"\nDropped schema {TEST_SCHEMA}")


def run_postgres_checks(schema_url):
    from adapters.database.postgres_adapter import PostgresAdapter
    from crawler import FetchResult, OK, RATE_LIMITED, TRANSIENT, PERMANENT
    import workers.crawl_worker as cw
    from workers.crawl_queue import enqueue_crawl_job, list_document_states, BACKFILLED

    db = PostgresAdapter(schema_url)
    q = lambda sql, params=(): db.execute_query(sql, params, fetch=True)
    if q("SELECT current_schema()")[0][0] != TEST_SCHEMA:
        raise SystemExit("refusing to run: not connected to the test schema")
    db.initialize()
    db.initialize()  # schema setup must be idempotent (runs on every boot)

    # Singletons (esp manager, routes) must use this adapter, not build one
    # from DATABASE_URL, which points at production
    import adapters.database.db_manager as db_manager
    db_manager._adapter_instance = db

    base_path = tempfile.mkdtemp(prefix='crawl_test_')
    vectorizer = FakeVectorizer()

    # Scripted crawler: url -> list of FetchResults, consumed per call
    script, calls = {}, []

    call_times = {}
    fixed_names = {}
    indexed_esps = []

    def fake_crawl(url, esp_name, base):
        calls.append(url)
        call_times.setdefault(url, time.time())
        outcomes = script.get(url) or [FetchResult(OK, content='fresh content')]
        result = outcomes.pop(0) if len(outcomes) > 1 else outcomes[0]
        if result.kind != OK:
            return None, result
        folder = os.path.join(base, 'docs', esp_name)
        os.makedirs(folder, exist_ok=True)
        name = fixed_names.get(url) or f"{uuid.uuid4().hex}.txt"
        with open(os.path.join(folder, name), 'w') as f:
            f.write(f"Source URL: {url}\n\n{result.content}")
        return name, result

    cw.crawl_single_url_result = fake_crawl
    # Same signature as crawler.vectorize_single_document; records what was
    # indexed so checks can tell the right text from a colliding file's
    indexed_text = {}

    def fake_vectorize(vec, esp, url, path, name, content=None):
        if content is None:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        vec.add_document(content, {'source_url': url})
        indexed_text[url] = content

    cw.vectorize_single_document = fake_vectorize

    worker = object.__new__(cw.CrawlWorker)
    worker.worker_id, worker.max_workers, worker.running, worker.threads = 'test', 3, False, []
    worker.base_path, worker.db, worker.vectorizer = base_path, db, vectorizer
    # Record cache invalidations instead of touching the real cache
    cw.clear_mechanics_cache = lambda: indexed_esps.append('cleared')

    esp_id = q("INSERT INTO esps (name, display_name) VALUES ('testesp', 'Test') RETURNING id")[0][0]
    global_id = q("INSERT INTO esps (name, display_name) VALUES ('global', 'Global') RETURNING id")[0][0]

    def add_doc(url, esp=None, content=None):
        return q("INSERT INTO esp_documents (esp_id, url, content, product) "
                 "VALUES (%s, %s, %s, 'shared') RETURNING id",
                 (esp or esp_id, url, content))[0][0]

    def reset_queue():
        q("DELETE FROM crawl_jobs RETURNING id")
        q("DELETE FROM crawl_hosts RETURNING host")
        calls.clear()
        script.clear()

    def job(job_id):
        return q("""SELECT status, attempts, rate_limited_count, error_kind, error_message,
                           EXTRACT(EPOCH FROM (next_attempt_at - NOW()))
                    FROM crawl_jobs WHERE id = %s""", (job_id,))[0]

    def doc(doc_id):
        return q("SELECT crawl_status, error_message, is_crawling, content FROM esp_documents WHERE id = %s", (doc_id,))[0]

    def run_one():
        claimed = worker._claim_next_job()
        if claimed:
            worker._process_job(claimed)
        return claimed

    print("\nEnqueue")
    d1 = add_doc('https://one.test/a')
    j1, created = enqueue_crawl_job(db, esp_id, d1, 'https://one.test/a')
    j1b, created_again = enqueue_crawl_job(db, esp_id, d1, 'https://one.test/a')
    check("enqueue creates a job with its host and gate", created and
          q("SELECT host FROM crawl_jobs WHERE id = %s", (j1,))[0][0] == 'one.test' and
          q("SELECT count(*) FROM crawl_hosts WHERE host = 'one.test'")[0][0] == 1)
    check("re-enqueueing an active doc returns the same job", not created_again and j1b == j1)
    check("doc is marked crawling", doc(d1)[2] is True)

    print("\nPer-host pacing")
    reset_queue()
    same = [add_doc(f'https://paced.test/{i}') for i in range(3)]
    other = add_doc('https://other.test/x')
    for i, d in enumerate(same):
        enqueue_crawl_job(db, esp_id, d, f'https://paced.test/{i}')
    enqueue_crawl_job(db, esp_id, other, 'https://other.test/x')
    # Wide interval: each round trip to the test DB can take ~0.3s from a laptop
    q("UPDATE crawl_hosts SET min_interval_ms = 8000 RETURNING host")

    first = worker._claim_next_job()
    second = worker._claim_next_job()
    third = worker._claim_next_job()
    check("first claim gets the oldest paced.test job", first and first['host'] == 'paced.test')
    check("second claim skips gated paced.test and takes other.test", second and second['host'] == 'other.test')
    check("third claim finds nothing: paced.test is gated", third is None)
    time.sleep(8.5)
    fourth = worker._claim_next_job()
    check("after min_interval the next paced.test job is claimable", fourth and fourth['host'] == 'paced.test')

    # Race: many threads claiming at once may take at most one job per host
    reset_queue()
    racers = [add_doc(f'https://race.test/{i}') for i in range(6)]
    for i, d in enumerate(racers):
        enqueue_crawl_job(db, esp_id, d, f'https://race.test/{i}')
    # A gate far longer than the race: each racer may need a fresh pooled
    # connection (a TLS handshake over a slow link), which can spread the
    # claims past a 2s gate — where a second claim is correct behaviour
    q("UPDATE crawl_hosts SET min_interval_ms = 60000 WHERE host = 'race.test' RETURNING host")
    [db._put_connection(c) for c in [db._get_connection() for _ in range(6)]]  # warm the pool
    barrier = threading.Barrier(6)
    won = []

    def racer():
        barrier.wait()
        c = worker._claim_next_job()
        if c:
            won.append(c['id'])

    threads = [threading.Thread(target=racer, daemon=True) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    check(f"6 concurrent claimers on one host -> exactly 1 claim (got {len(won)})", len(won) == 1)

    print("\nOutcomes")
    reset_queue()
    d404 = add_doc('https://outcome.test/gone')
    script['https://outcome.test/gone'] = [FetchResult(PERMANENT, error='Page not found (HTTP 404) — check the URL', status_code=404)]
    j404, _ = enqueue_crawl_job(db, esp_id, d404, 'https://outcome.test/gone')
    run_one()
    s = job(j404)
    check("404 fails after exactly one request", s[0] == 'failed' and s[1] == 1 and calls.count('https://outcome.test/gone') == 1)
    check("404 reason reaches the document", doc(d404)[0] == 'failed' and '404' in doc(d404)[1] and doc(d404)[2] is False)

    reset_queue()
    d429 = add_doc('https://limited.test/a')
    d429b = add_doc('https://limited.test/b')
    script['https://limited.test/a'] = [FetchResult(RATE_LIMITED, error='Rate-limited by limited.test (HTTP 429)', status_code=429, retry_after=60)]
    j429, _ = enqueue_crawl_job(db, esp_id, d429, 'https://limited.test/a')
    j429b, _ = enqueue_crawl_job(db, esp_id, d429b, 'https://limited.test/b')
    run_one()
    s = job(j429)
    check("429 re-queues the job", s[0] == 'pending' and s[3] == RATE_LIMITED)
    check("429 does not use up an attempt", s[1] == 0 and s[2] == 1)
    check("429 waits as long as Retry-After asked (~60s)", 45 < float(s[5]) <= 60.5)
    backoff = q("SELECT EXTRACT(EPOCH FROM (backoff_until - NOW())), consecutive_429 FROM crawl_hosts WHERE host = 'limited.test'")[0]
    check("429 pauses the whole host", 45 < float(backoff[0]) <= 60.5 and backoff[1] == 1)
    q("UPDATE crawl_hosts SET next_allowed_at = NOW() - INTERVAL '1 second' RETURNING host")
    check("other jobs on the paused host are not claimed", worker._claim_next_job() is None)
    check("the document still reads as crawling, not failed", doc(d429)[0] != 'failed' and doc(d429)[2] is True)
    states = {x['url']: x for x in list_document_states(db, esp_id)}
    check("links state for the 429'd doc is 'waiting' with the reason",
          states['https://limited.test/a']['state'] == 'waiting' and '429' in states['https://limited.test/a']['detail'])
    check("links state for its queued neighbour explains the pause",
          states['https://limited.test/b']['state'] == 'queued' and 'paused' in states['https://limited.test/b']['detail'])

    # Backoff over: the retry succeeds, clears the error, resets the streak
    q("UPDATE crawl_hosts SET backoff_until = NULL, next_allowed_at = NOW() - INTERVAL '1 second' RETURNING host")
    q("UPDATE crawl_jobs SET next_attempt_at = NOW() - INTERVAL '1 second' WHERE id = %s RETURNING id", (j429,))
    script['https://limited.test/a'] = [FetchResult(OK, content='finally')]
    run_one()
    s = job(j429)
    check("retry after the wait completes and clears the old error", s[0] == 'completed' and s[4] is None and s[3] is None)
    check("success resets the host's 429 streak",
          q("SELECT consecutive_429 FROM crawl_hosts WHERE host = 'limited.test'")[0][0] == 0)
    check("document completed with content, error cleared",
          doc(d429)[0] == 'completed' and doc(d429)[3].endswith('finally') and doc(d429)[1] is None)

    reset_queue()
    dt = add_doc('https://flaky.test/a')
    script['https://flaky.test/a'] = [FetchResult(TRANSIENT, error='Server error at flaky.test (HTTP 500)', status_code=500)]
    jt, _ = enqueue_crawl_job(db, esp_id, dt, 'https://flaky.test/a')
    for attempt in range(3):
        q("UPDATE crawl_hosts SET next_allowed_at = NOW() - INTERVAL '1 second' RETURNING host")
        q("UPDATE crawl_jobs SET next_attempt_at = NOW() - INTERVAL '1 second' WHERE id = %s RETURNING id", (jt,))
        run_one()
        if attempt == 0:
            s = job(jt)
            check("transient failure retries with backoff (~15-19s)", s[0] == 'pending' and 8 < float(s[5]) < 19.5)
    s = job(jt)
    check("transient gives up after max_attempts with a note", s[0] == 'failed' and s[1] == 3 and 'gave up after 3 attempts' in s[4])

    reset_queue()
    dv = add_doc('https://index.test/a')
    jv, _ = enqueue_crawl_job(db, esp_id, dv, 'https://index.test/a')
    vectorizer.fail = True
    run_one()
    vectorizer.fail = False
    s = job(jv)
    check("vector index failure is not reported as completed", s[0] == 'pending' and s[3] == 'index' and 'search index' in s[4])
    vectorizer.fail = True
    for _ in range(2):
        q("UPDATE crawl_hosts SET next_allowed_at = NOW() - INTERVAL '1 second' RETURNING host")
        q("UPDATE crawl_jobs SET next_attempt_at = NOW() - INTERVAL '1 second' WHERE id = %s RETURNING id", (jv,))
        run_one()
    vectorizer.fail = False
    s = job(jv)
    check("index failure that persists ends failed, never completed",
          s[0] == 'failed' and 'pinecone unavailable' in s[4] and doc(dv)[0] == 'failed')
    states = {x['url']: x for x in list_document_states(db, esp_id)}
    check("…reported as an index failure, not as 'couldn't crawl, served a saved copy'",
          s[3] == 'index' and states['https://index.test/a']['state'] == 'failed'
          and 'not in search results' in states['https://index.test/a']['detail'])

    reset_queue()
    dm = add_doc('https://meta.test/a')
    jm, _ = enqueue_crawl_job(db, esp_id, dm, 'https://meta.test/a')
    real_meta = worker._update_metadata_atomic
    worker._update_metadata_atomic = lambda *a: (_ for _ in ()).throw(OSError("disk full"))
    run_one()
    worker._update_metadata_atomic = real_meta
    s = job(jm)
    check("a local file/metadata error is retried as transient, not called an index failure",
          s[0] == 'pending' and s[3] == 'transient' and 'disk full' in s[4])

    reset_queue()
    dc = add_doc('https://cancel.test/a')
    script['https://cancel.test/a'] = [FetchResult(TRANSIENT, error='Server error', status_code=500)]
    jc, _ = enqueue_crawl_job(db, esp_id, dc, 'https://cancel.test/a')
    claimed = worker._claim_next_job()
    q("UPDATE crawl_jobs SET status = 'cancelled' WHERE id = %s RETURNING id", (jc,))
    worker._process_job(claimed)
    check("a job cancelled mid-crawl stays cancelled", job(jc)[0] == 'cancelled')

    print("\nSaved-copy fallback")
    reset_queue()
    dp = add_doc('local://pasted-guide', esp=global_id, content='pasted text')
    jp, _ = enqueue_crawl_job(db, global_id, dp, 'local://pasted-guide')
    script['local://pasted-guide'] = [FetchResult(PERMANENT, error="manually pasted content")]
    vectorizer.indexed.clear()
    run_one()
    s = job(jp)
    check("pasted local:// doc is re-indexed from its saved copy",
          s[0] == 'completed' and s[3] == BACKFILLED and 'local://pasted-guide' in vectorizer.indexed)
    gstates = {x['url']: x for x in list_document_states(db, global_id)}
    check("its state is crawled, with a note", gstates['local://pasted-guide']['state'] == 'crawled'
          and 'saved copy' in gstates['local://pasted-guide']['detail'])

    reset_queue()
    db_backed = add_doc('https://backed.test/a', content='old good copy')
    script['https://backed.test/a'] = [FetchResult(PERMANENT, error='Page not found (HTTP 404) — check the URL', status_code=404)]
    jb, _ = enqueue_crawl_job(db, esp_id, db_backed, 'https://backed.test/a')
    run_one()
    states = {x['url']: x for x in list_document_states(db, esp_id)}
    check("a backed-up page that now 404s is reported failed, not silently served",
          job(jb)[0] == 'failed' and states['https://backed.test/a']['state'] == 'failed'
          and 'still in use' in states['https://backed.test/a']['detail'])

    print("\nSaved copies are only used when they provably belong to the URL")
    reset_queue()
    folder = os.path.join(base_path, 'docs', 'testesp')
    os.makedirs(folder, exist_ok=True)
    # Another document's file sitting at the name this URL maps to
    with open(os.path.join(folder, 'index.txt'), 'w') as f:
        f.write("Source URL: https://someone-else.test/\n\nsomeone else's text")
    dn = add_doc('https://collide.test/')
    script['https://collide.test/'] = [FetchResult(PERMANENT, error='Page not found (HTTP 404) — check the URL', status_code=404)]
    jn, _ = enqueue_crawl_job(db, esp_id, dn, 'https://collide.test/')
    run_one()
    check("a new page that 404s is failed, not 'completed' from a colliding file",
          job(jn)[0] == 'failed' and doc(dn)[0] == 'failed' and doc(dn)[3] is None)

    gfolder = os.path.join(base_path, 'docs', 'global')
    os.makedirs(gfolder, exist_ok=True)
    with open(os.path.join(gfolder, 'index.txt'), 'w') as f:
        f.write("Source URL: local://other-paste\n\nthe other paste")
    dq = add_doc('local://my-paste', esp=global_id, content='Source URL: local://my-paste\n\nmy paste')
    jq, _ = enqueue_crawl_job(db, global_id, dq, 'local://my-paste')
    script['local://my-paste'] = [FetchResult(PERMANENT, error="manually pasted content")]
    run_one()
    check("a pasted doc re-indexes from its own database copy, not a colliding file",
          job(jq)[0] == 'completed' and doc(dq)[3] == 'Source URL: local://my-paste\n\nmy paste')
    with open(os.path.join(gfolder, 'index.txt')) as f:
        check("…and the other document's file is left untouched", 'the other paste' in f.read())

    dk = add_doc('https://kept.test/page')
    with open(os.path.join(folder, 'page.txt'), 'w') as f:
        f.write("Source URL: https://kept.test/page\n\nolder crawl")
    script['https://kept.test/page'] = [FetchResult(PERMANENT, error='Access denied by kept.test (HTTP 403)', status_code=403)]
    jk, _ = enqueue_crawl_job(db, esp_id, dk, 'https://kept.test/page')
    run_one()
    states = {x['url']: x for x in list_document_states(db, esp_id)}
    check("a page with no DB backup is re-indexed from its own saved file, shown as saved_copy",
          job(jk)[0] == 'completed' and states['https://kept.test/page']['state'] == 'saved_copy'
          and '403' in states['https://kept.test/page']['detail'])

    print("\nColliding filenames on the success path")
    reset_queue()
    indexed_esps.clear()
    ca = add_doc('https://a-site.test/docs/setup')
    cb = add_doc('https://b-site.test/docs/setup')
    fixed_names['https://a-site.test/docs/setup'] = 'docs_setup.txt'
    fixed_names['https://b-site.test/docs/setup'] = 'docs_setup.txt'
    script['https://a-site.test/docs/setup'] = [FetchResult(OK, content='A text')]
    script['https://b-site.test/docs/setup'] = [FetchResult(OK, content='B text')]
    enqueue_crawl_job(db, esp_id, ca, 'https://a-site.test/docs/setup')
    enqueue_crawl_job(db, esp_id, cb, 'https://b-site.test/docs/setup')
    first, second = worker._claim_next_job(), worker._claim_next_job()
    # Both crawl (the second overwrites the shared file) before either indexes
    real_crawl = cw.crawl_single_url_result
    fetched = {}
    for claimed in (first, second):
        url = q("SELECT url FROM esp_documents WHERE id = %s", (claimed['document_id'],))[0][0]
        fetched[url] = real_crawl(url, 'testesp', base_path)
    with open(os.path.join(base_path, 'docs', 'testesp', 'docs_setup.txt')) as f:
        check("(setup) the shared file now holds only the second site's text", 'B text' in f.read())
    cw.crawl_single_url_result = lambda url, esp, base: fetched[url]
    worker._process_job(first)
    worker._process_job(second)
    cw.crawl_single_url_result = real_crawl
    check("each URL stores its own text even when their saved filenames collide",
          (doc(ca)[3] or '').endswith('A text') and (doc(cb)[3] or '').endswith('B text'))
    check("…and indexes its own text",
          indexed_text.get('https://a-site.test/docs/setup', '').endswith('A text')
          and indexed_text.get('https://b-site.test/docs/setup', '').endswith('B text'))
    check("the worker clears the chat retrieval cache once per indexed doc", indexed_esps == ['cleared', 'cleared'])
    fixed_names.clear()

    print("\nJobs the worker can't claim don't block the URL")
    from workers.crawl_queue import repair_queue
    reset_queue()
    dl = add_doc('https://Legacy.test:8443/a?b=1')
    legacy = str(uuid.uuid4())
    q("""INSERT INTO crawl_jobs (id, esp_id, document_id, priority) VALUES (%s, %s, %s, 10)
         RETURNING id""", (legacy, esp_id, dl))  # as the pre-pacing code queued it: no host
    q("UPDATE esp_documents SET is_crawling = TRUE, crawl_job_id = %s WHERE id = %s RETURNING id", (legacy, dl))
    check("a host-less legacy job is invisible to the claim query", worker._claim_next_job() is None)
    repair_queue(db)
    check("repair gives it the same host a new job would get, plus a gate",
          q("SELECT host FROM crawl_jobs WHERE id = %s", (legacy,))[0][0] == 'legacy.test'
          and q("SELECT count(*) FROM crawl_hosts WHERE host = 'legacy.test'")[0][0] == 1)
    check("…after which it is claimable", (worker._claim_next_job() or {}).get('id') is not None)

    reset_queue()
    dx = add_doc('https://exhausted.test/a')
    stuck = str(uuid.uuid4())
    q("""INSERT INTO crawl_jobs (id, esp_id, document_id, priority, host, attempts, max_attempts)
         VALUES (%s, %s, %s, 10, 'exhausted.test', 3, 3) RETURNING id""", (stuck, esp_id, dx))
    q("UPDATE esp_documents SET is_crawling = TRUE, crawl_job_id = %s WHERE id = %s RETURNING id", (stuck, dx))
    fresh, created = enqueue_crawl_job(db, esp_id, dx, 'https://exhausted.test/a')
    check("an out-of-attempts pending job is failed on re-enqueue and a new job queued",
          created and fresh != stuck and job(stuck)[0] == 'failed')

    dup_id = str(uuid.uuid4())
    try:
        q("""INSERT INTO crawl_jobs (id, esp_id, document_id, priority, host)
             VALUES (%s, %s, %s, 10, 'exhausted.test') RETURNING id""", (dup_id, esp_id, dx))
        dup_blocked = False
    except Exception as e:
        dup_blocked = getattr(e, 'pgcode', None) == '23505'
    check("the database refuses a second active job for one document", dup_blocked)

    print("\nAdmin routes (Flask test client)")
    from flask import Flask
    import app_admin_esp_routes_async as routes
    routes.check_admin_password = lambda: True
    flask_app = Flask('test')
    routes.register_esp_admin_routes_async(flask_app, base_path, vectorizer)
    client = flask_app.test_client()
    reset_queue()
    flask_app.config['CRAWL_WORKER_RUNNING'] = False
    r = client.post('/api/admin/esp/testesp/crawl-selected', json={'urls': ['https://route.test/a']})
    check("crawl-selected refuses (503) when no worker is running", r.status_code == 503 and 'worker' in r.get_json()['error'])
    flask_app.config['CRAWL_WORKER_RUNNING'] = True
    r = client.post('/api/admin/esp/testesp/crawl-selected', json={'urls': ['https://route.test/a', 'https://route.test/b'], 'product': 'shared'})
    body = r.get_json()
    check("crawl-selected queues jobs", r.status_code == 200 and len(body['job_ids']) == 2)
    r2 = client.post('/api/admin/esp/testesp/crawl-selected', json={'urls': ['https://route.test/a'], 'product': 'shared'})
    check("re-submitting returns the same job (no duplicate)",
          r2.get_json()['job_ids'] == body['job_ids'][:1] and r2.get_json()['skipped_count'] == 1)
    links = {l['url']: l for l in client.get('/api/admin/esp/testesp/links').get_json()['links']}
    check("links endpoint reports queued jobs as queued", links['https://route.test/a']['status'] == 'queued')
    check("links endpoint reports failures as failed with the reason (not 'pending')",
          links['https://outcome.test/gone']['status'] == 'failed' and '404' in links['https://outcome.test/gone']['detail'])
    status = client.post('/api/admin/crawl-status', json={'job_ids': body['job_ids']}).get_json()
    check("crawl-status (POST) carries host, error_kind and detail per job",
          all({'host', 'error_kind', 'detail'} <= set(j) for j in status['jobs'])
          and status['summary']['pending'] == 2 and not status['summary']['is_complete'])
    got = client.get('/api/admin/crawl-status?job_ids=' + ','.join(body['job_ids'])).get_json()
    check("crawl-status still answers GET (the async-support probe uses it)", got['summary']['total'] == 2)
    many = client.post('/api/admin/crawl-status', json={'job_ids': body['job_ids'] + [str(uuid.uuid4()) for _ in range(300)]})
    check("a 300-id status poll works (would overflow a query string)", many.status_code == 200)
    folder = os.path.join(base_path, 'docs', 'testesp')
    with open(os.path.join(folder, 'index.txt'), 'w') as f:
        f.write("Source URL: https://owner.test/\n\nthe owner's text")
    r = client.post('/api/admin/esp/testesp/paste-content',
                    json={'url': 'local://pasted-into-testesp', 'content': 'pasted text', 'product': 'shared'})
    with open(os.path.join(folder, 'index.txt')) as f:
        check("Paste Content never overwrites another URL's saved file",
              r.status_code == 200 and "the owner's text" in f.read())
    check("a malformed status body is a 400, not a 500",
          client.post('/api/admin/crawl-status', json=['x']).status_code == 400
          and client.post('/api/admin/crawl-status', json={'job_ids': 'x'}).status_code == 400)

    print("\nBoot migration on a database with existing duplicates")
    reset_queue()
    dd = add_doc('https://dupe.test/a')
    db.execute_query("DROP INDEX IF EXISTS idx_crawl_jobs_one_active")
    older, newer = str(uuid.uuid4()), str(uuid.uuid4())
    q("""INSERT INTO crawl_jobs (id, esp_id, document_id, priority, host, created_at)
         VALUES (%s, %s, %s, 10, 'dupe.test', NOW() - INTERVAL '1 hour'),
                (%s, %s, %s, 10, 'dupe.test', NOW()) RETURNING id""", (older, esp_id, dd, newer, esp_id, dd))
    db.initialize()
    check("boot keeps the newest active job per document and cancels the rest",
          job(older)[0] == 'cancelled' and job(newer)[0] == 'pending')
    check("…and the one-active-job index then exists",
          q("SELECT count(*) FROM pg_indexes WHERE schemaname = %s AND indexname = 'idx_crawl_jobs_one_active'",
            (TEST_SCHEMA,))[0][0] == 1)

    print("\nSaved copy exists but indexing it fails")
    reset_queue()
    dpi = add_doc('local://paste-index-down', esp=global_id, content='Source URL: local://paste-index-down\n\ntext')
    jpi, _ = enqueue_crawl_job(db, global_id, dpi, 'local://paste-index-down')
    script['local://paste-index-down'] = [FetchResult(PERMANENT, error="manually pasted content")]
    vectorizer.fail = True
    run_one()
    s = job(jpi)
    check("it is retried as an index failure, not failed with the crawl error",
          s[0] == 'pending' and s[3] == 'index' and 'search index' in s[4])
    for _ in range(2):
        q("UPDATE crawl_hosts SET next_allowed_at = NOW() - INTERVAL '1 second' RETURNING host")
        q("UPDATE crawl_jobs SET next_attempt_at = NOW() - INTERVAL '1 second' WHERE id = %s RETURNING id", (jpi,))
        run_one()
    vectorizer.fail = False
    s = job(jpi)
    gstates = {x['url']: x for x in list_document_states(db, global_id)}
    check("after retries it fails with the index reason, and doesn't claim the copy is in search",
          s[0] == 'failed' and s[3] == 'index'
          and 'not in search results' in gstates['local://paste-index-down']['detail'])

    print("\nStale-job recovery")
    reset_queue()
    ds = add_doc('https://stale.test/a')
    js, _ = enqueue_crawl_job(db, esp_id, ds, 'https://stale.test/a')
    q("""UPDATE crawl_jobs SET status = 'processing', attempts = max_attempts,
         started_at = NOW() - INTERVAL '30 minutes' WHERE id = %s RETURNING id""", (js,))
    cw.CrawlWorker.cleanup_stale_jobs(db, timeout_minutes=10)
    check("stale job with no attempts left fails instead of hanging in pending",
          job(js)[0] == 'failed' and doc(ds)[0] == 'failed' and doc(ds)[2] is False)
    ds2 = add_doc('https://stale.test/b')
    js2, _ = enqueue_crawl_job(db, esp_id, ds2, 'https://stale.test/b')
    q("""UPDATE crawl_jobs SET status = 'processing', attempts = 1,
         started_at = NOW() - INTERVAL '30 minutes' WHERE id = %s RETURNING id""", (js2,))
    cw.CrawlWorker.cleanup_stale_jobs(db, timeout_minutes=10)
    check("stale job with attempts left is re-queued", job(js2)[0] == 'pending')

    print("\nThe 50-URL burst from the incident")
    reset_queue()
    burst = [add_doc(f'https://burst.test/{i}') for i in range(5)]
    for i, d in enumerate(burst):
        enqueue_crawl_job(db, esp_id, d, f'https://burst.test/{i}')
    q("UPDATE crawl_hosts SET min_interval_ms = 3000 RETURNING host")
    # Daemon threads, stopped in `finally`: if this section dies (e.g. the
    # database link drops), live worker threads would otherwise keep the
    # process alive and keep claiming jobs from the NEXT run's test schema
    worker.running = True
    threads = [threading.Thread(target=worker._worker_loop, daemon=True) for _ in range(3)]
    t0 = time.time()
    [t.start() for t in threads]
    try:
        while time.time() - t0 < 90:
            if q("SELECT count(*) FROM crawl_jobs WHERE status = 'completed'")[0][0] == len(burst):
                break
            time.sleep(0.2)
    finally:
        worker.running = False
        [t.join(timeout=30) for t in threads]
    # Measured where the requests are made (the fake crawler's clock), not
    # from started_at, which comes from the same database clock the gate
    # uses. Allows 0.75s: the gap can shrink by the commit round trip, which
    # is ~0.3-0.6s from a laptop to Railway (milliseconds in production).
    starts = sorted(t for u, t in call_times.items() if u.startswith('https://burst.test/'))
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    check(f"3 threads, 5 URLs, one host: all completed ({len(starts)})",
          q("SELECT count(*) FROM crawl_jobs WHERE status = 'completed'")[0][0] == len(burst))
    check(f"requests went out ~min_interval (3s) apart (smallest gap {min(gaps):.2f}s)", min(gaps) >= 2.25)

    db.close()


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'pure'
    run_pure_checks()
    if mode == 'postgres':
        base_url, schema_url = setup_postgres()
        try:
            run_postgres_checks(schema_url)
        finally:
            teardown_postgres(base_url)

    failed = [name for name, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("FAILED:\n  " + "\n  ".join(failed))
        sys.exit(1)
