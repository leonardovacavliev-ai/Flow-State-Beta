"""
Keeping documents current (C1.3): refresh.py, the Yotpo guide extraction
rule (crawler.py), the worker's unchanged-skip, misses, header fields and
Replace, the sitemap job (sitemap_refresh.py) and its routes.

    python3 backend/test_refresh_pipeline.py     # or pytest

No network and no Postgres: throwaway SQLite databases, a fake crawler and
a fake vector store. The worker's queue (claiming jobs) is Postgres-only and
tested in test_crawl_pacing.py postgres; here its job processing runs on
SQLite through a wrapper that spells NOW() the SQLite way.
"""
import json
import os
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='refresh-')
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(TMP, 'test.db')
os.environ['SESSION_PROVIDER'] = 'memory'
os.environ['USE_ASYNC_CRAWL'] = 'false'
os.environ['VECTOR_DB_PROVIDER'] = 'chromadb'
os.environ.pop('ADMIN_OWNER_EMAILS', None)
sys.path.insert(0, HERE)

import auth  # noqa: E402

USER = {'admin': True, 'email': 'leo@yotpo.com'}
auth.current_user_is_admin = lambda: USER['admin']
auth.current_user = lambda: {'email': USER['email']} if USER['admin'] else None

import crawler  # noqa: E402
import doc_header  # noqa: E402
import esp_manager  # noqa: E402
import refresh  # noqa: E402
import sitemap_refresh as sm  # noqa: E402
from crawler import FetchResult, OK, PERMANENT, TRANSIENT  # noqa: E402
from workers.crawl_queue import describe_link  # noqa: E402

D360 = os.path.join(HERE, 'fixtures', 'document360')
GUIDE = 'https://support.yotpo.com/docs/recharge-integration-guide-for-yotpo-loyalty-referrals'


def _read(path):
    with open(path) as f:
        return f.read()


class Response:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.content = f.read()


# ---------- databases ----------

class SQLiteWorkerDB:
    """A SQLite adapter as the worker's job processing expects Postgres:
    NOW() is CURRENT_TIMESTAMP there."""

    def __init__(self, inner):
        self.inner = inner

    def execute_query(self, query, params=None, fetch=False):
        return self.inner.execute_query(query.replace('NOW()', 'CURRENT_TIMESTAMP'), params, fetch)


def boot_db():
    from adapters.database.sqlite_adapter import SQLiteAdapter
    db = SQLiteAdapter(db_path=os.path.join(TMP, f'{uuid.uuid4().hex}.db'))
    db.initialize()
    # The queue's own columns, which only Postgres has (the queue is
    # Postgres-only): enough for the worker's job processing here
    for column in ('error_kind TEXT', 'host TEXT', 'rate_limited_count INTEGER DEFAULT 0',
                   'next_attempt_at DATETIME'):
        db.execute_query(f"ALTER TABLE crawl_jobs ADD COLUMN {column}")
    from adapters.database import db_manager
    db_manager.get_database_adapter = lambda *a, **k: db
    db_manager._adapter_instance = db
    mgr = esp_manager.ESPManager()
    mgr.db = db
    esp_manager._esp_manager = mgr
    return db


def esp(db, name='recharge', status='listed', ptype='storefront'):
    esp_id = str(uuid.uuid4())
    db.execute_query("INSERT INTO esps (id, name, display_name, status, platform_type) VALUES (%s, %s, %s, %s, %s)",
                     (esp_id, name, name.title(), status, ptype))
    return esp_id


def doc(db, esp_id, url, product='loyalty', **cols):
    doc_id = str(uuid.uuid4())
    names = ['id', 'esp_id', 'url', 'filename', 'product'] + list(cols)
    values = [doc_id, esp_id, url, url.rsplit('/', 1)[-1] + '.txt', product] + list(cols.values())
    db.execute_query(f"INSERT INTO esp_documents ({', '.join(names)}) VALUES ({', '.join(['%s'] * len(names))})",
                     tuple(values))
    return doc_id


def row(db, doc_id, *columns):
    return db.execute_query(f"SELECT {', '.join(columns)} FROM esp_documents WHERE id = %s", (doc_id,),
                            fetch=True)[0]


class FakeVectors:
    def __init__(self):
        self.indexed, self.deleted = [], []

    def delete_by_url(self, url, esp):
        self.deleted.append(url)

    def add_document(self, text, metadata):
        self.indexed.append(metadata['source_url'])
        return 4


# ---------- pure ----------

def test_unchanged_needs_the_same_text_and_chunks():
    h = refresh.content_hash('abc')
    assert refresh.unchanged(h, 3, 'abc')
    assert not refresh.unchanged(h, 3, 'abcd')
    assert not refresh.unchanged(h, 0, 'abc')          # indexed to nothing: index it
    assert not refresh.unchanged(h, None, 'abc')       # count unknown: index once, which records it
    assert not refresh.unchanged(None, 3, 'abc')


def test_only_a_gone_page_is_a_miss():
    assert refresh.is_miss(PERMANENT, 404) and refresh.is_miss(PERMANENT, 410)
    assert not refresh.is_miss(PERMANENT, 403)
    assert not refresh.is_miss(TRANSIENT, 404)
    assert not refresh.is_miss(PERMANENT, None)


def test_header_fields_only_for_yotpo_guides():
    text = _read(os.path.join(D360, 'recharge-integration-guide-for-yotpo-loyalty-referrals.txt'))
    f = refresh.header_fields(GUIDE, text, ' Recharge - Integration Guide ')
    assert f['title'] == 'Recharge - Integration Guide'
    assert f['supported_plans'] == ['Pro', 'Premium', 'Enterprise']
    assert 'Shopify' in f['supported_platforms']
    assert refresh.header_fields('https://help.recharge.com/x', text, 'T') == {}


def test_describe_link_says_retired_and_unchanged():
    from workers.crawl_queue import UNCHANGED
    assert describe_link('retired', True, None)[0] == 'retired'
    state, detail = describe_link('completed', True, None, 'completed', UNCHANGED, refresh.UNCHANGED_NOTE)
    assert state == 'crawled' and detail == refresh.UNCHANGED_NOTE


# ---------- the Yotpo guide rule ----------

def test_yotpo_guides_keep_header_and_body_and_drop_boilerplate():
    for name in sorted(os.listdir(D360)):
        if not name.endswith('.html'):
            continue
        html = os.path.join(D360, name)
        new, error = crawler._extract_text('https://support.yotpo.com/docs/x', Response(html))
        old = _read(os.path.join(D360, 'general', name[:-5] + '.txt'))
        assert not error
        assert doc_header.parse_header(new) == doc_header.parse_header(old), name
        assert new.startswith('Products\n'), name                     # header stays first
        assert 'Change this text for' not in new, name
        assert 'Contact our support team' not in new, name
        # every other site is read exactly as before
        assert crawler._extract_text('https://example.com/x', Response(html))[0] == old, name
    gorgias = crawler._extract_text('https://support.yotpo.com/docs/x', Response(
        os.path.join(D360, 'gorgias-integration-guide-for-reviews-and-loyalty-referrals.html')))[0]
    assert 'Gorgias is a customer support helpdesk' in gorgias      # spaces around links kept
    tapcart = crawler._extract_text('https://support.yotpo.com/docs/x', Response(
        os.path.join(D360, 'tapcart-yotpo-integration-guide.html')))[0]
    assert 'help@tapcart.co' in tapcart                              # a partner's own support box stays


def test_page_title():
    assert crawler.page_title(Response(os.path.join(D360, 'tapcart-yotpo-integration-guide.html')).content) \
        == 'Tapcart - Integration Guide'
    assert crawler.page_title(b'<html><head><title> A \n B </title></head></html>') == 'A B'
    assert crawler.page_title(b'<p>no title</p>') is None


# ---------- the worker ----------

def make_worker(db, vectors, script):
    """The crawl worker's job processing on `db`, with a scripted crawler."""
    import workers.crawl_worker as cw
    base = tempfile.mkdtemp(dir=TMP)

    def fake_crawl(url, esp_name, base_path):
        result = script[url].pop(0) if len(script[url]) > 1 else script[url][0]
        if result.kind != OK:
            return None, result
        folder = os.path.join(base_path, 'docs', esp_name)
        os.makedirs(folder, exist_ok=True)
        name = url.rsplit('/', 1)[-1] + '.txt'
        with open(os.path.join(folder, name), 'w') as f:
            f.write(crawler.saved_text(url, result.content))
        return name, result

    def fake_vectorize(vec, esp_name, url, path, name, content=None):
        count = vec.add_document(content, {'source_url': url})
        db.execute_query("UPDATE esp_documents SET vector_count = %s WHERE url = %s", (count, url))

    cw.crawl_single_url_result = fake_crawl
    cw.vectorize_single_document = fake_vectorize
    cw.clear_mechanics_cache = lambda: None
    worker = object.__new__(cw.CrawlWorker)
    worker.worker_id, worker.max_workers, worker.running, worker.threads = 'test', 1, False, []
    worker.base_path, worker.db, worker.vectorizer = base, SQLiteWorkerDB(db), vectors
    return worker


def run_job(db, worker, esp_id, doc_id):
    job_id = str(uuid.uuid4())
    db.execute_query("INSERT INTO crawl_jobs (id, esp_id, document_id, status, attempts, max_attempts) "
                     "VALUES (%s, %s, %s, 'processing', 1, 3)", (job_id, esp_id, doc_id))
    db.execute_query("UPDATE esp_documents SET crawl_job_id = %s, is_crawling = 1 WHERE id = %s", (job_id, doc_id))
    worker._process_job({'id': job_id, 'esp_id': esp_id, 'document_id': doc_id, 'attempts': 1,
                         'max_attempts': 3, 'host': None, 'rate_limited_count': 0})
    return db.execute_query("SELECT status, error_kind, error_message FROM crawl_jobs WHERE id = %s",
                            (job_id,), fetch=True)[0]


def test_unchanged_content_is_not_reindexed():
    db, vectors = boot_db(), FakeVectors()
    esp_id = esp(db)
    d = doc(db, esp_id, 'https://help.example.com/a', product='shared')
    script = {'https://help.example.com/a': [FetchResult(OK, content='same text')]}
    worker = make_worker(db, vectors, script)
    assert run_job(db, worker, esp_id, d)[0] == 'completed'
    assert vectors.indexed == ['https://help.example.com/a']
    first_crawl = row(db, d, 'last_crawled_at')[0]
    db.execute_query("UPDATE esp_documents SET last_crawled_at = '2000-01-01 00:00:00' WHERE id = %s", (d,))
    status, kind, note = run_job(db, worker, esp_id, d)
    assert (status, kind, note) == ('completed', 'unchanged', refresh.UNCHANGED_NOTE)
    assert vectors.indexed == ['https://help.example.com/a'] and vectors.deleted == []
    assert row(db, d, 'crawl_status')[0] == 'completed'
    assert row(db, d, 'last_crawled_at')[0] > '2000-01-01' and first_crawl
    script['https://help.example.com/a'] = [FetchResult(OK, content='new text')]
    run_job(db, worker, esp_id, d)
    assert vectors.indexed == ['https://help.example.com/a'] * 2


def test_a_yotpo_guide_crawl_stores_its_header():
    db, vectors = boot_db(), FakeVectors()
    esp_id = esp(db)
    d = doc(db, esp_id, GUIDE)
    text = _read(os.path.join(D360, 'recharge-integration-guide-for-yotpo-loyalty-referrals.txt'))
    worker = make_worker(db, vectors, {GUIDE: [FetchResult(OK, content=text, title='Recharge - Integration Guide')]})
    run_job(db, worker, esp_id, d)
    title, plans, platforms, product = row(db, d, 'title', 'supported_plans', 'supported_platforms', 'product')
    assert title == 'Recharge - Integration Guide' and json.loads(plans) == ['Pro', 'Premium', 'Enterprise']
    assert 'BigCommerce' in json.loads(platforms)
    assert product == 'loyalty'                                    # never a label (I1)


def test_misses_count_up_and_reset():
    db, vectors = boot_db(), FakeVectors()
    esp_id = esp(db)
    d = doc(db, esp_id, 'https://help.example.com/gone', content='old', content_hash='x')
    gone = FetchResult(PERMANENT, error='Page not found (HTTP 404)', status_code=404)
    script = {'https://help.example.com/gone': [gone]}
    worker = make_worker(db, vectors, script)
    for _ in range(3):
        assert run_job(db, worker, esp_id, d)[0] == 'failed'
    assert row(db, d, 'consecutive_misses')[0] == refresh.MISS_LIMIT
    # a 403 is not a miss
    script['https://help.example.com/gone'] = [FetchResult(PERMANENT, error='denied', status_code=403)]
    run_job(db, worker, esp_id, d)
    assert row(db, d, 'consecutive_misses')[0] == refresh.MISS_LIMIT
    script['https://help.example.com/gone'] = [FetchResult(OK, content='back')]
    run_job(db, worker, esp_id, d)
    assert row(db, d, 'consecutive_misses')[0] == 0


def test_replace_retires_the_old_document_once_the_new_one_is_indexed():
    db, vectors = boot_db(), FakeVectors()
    esp_id = esp(db)
    old = doc(db, esp_id, 'https://help.example.com/old', content='old', vector_count=3, consecutive_misses=3)
    new = doc(db, esp_id, 'https://help.example.com/new')
    db.execute_query("UPDATE esp_documents SET replaced_by = %s WHERE id = %s", (new, old))
    script = {'https://help.example.com/new': [FetchResult(TRANSIENT, error='down')]}
    worker = make_worker(db, vectors, script)
    worker._schedule_retry = lambda job, fetch, decision: None     # a retry would use make_interval
    run_job(db, worker, esp_id, new)
    assert row(db, old, 'retired_at')[0] is None                    # not until the new one is indexed
    script['https://help.example.com/new'] = [FetchResult(OK, content='new page')]
    run_job(db, worker, esp_id, new)
    retired_at, status, count = row(db, old, 'retired_at', 'crawl_status', 'vector_count')
    assert retired_at and status == 'retired' and count == 0
    assert vectors.deleted[-1] == 'https://help.example.com/old'


def test_crawling_a_retired_document_brings_it_back():
    db, vectors = boot_db(), FakeVectors()
    esp_id = esp(db)
    d = doc(db, esp_id, 'https://help.example.com/r', content='x', vector_count=2)
    assert refresh.retire(db, vectors, 'recharge', ['https://help.example.com/r'])['retired']
    worker = make_worker(db, vectors, {'https://help.example.com/r': [FetchResult(OK, content='y')]})
    run_job(db, worker, esp_id, d)
    assert row(db, d, 'retired_at', 'crawl_status') == (None, 'completed')


# ---------- retired documents are left out ----------

def test_retired_documents_are_left_out_everywhere():
    db, vectors = boot_db(), FakeVectors()
    esp_id = esp(db, 'klaviyo', status='active', ptype='messaging')
    keep = doc(db, esp_id, 'https://help.example.com/keep', product='reviews', content='k', crawl_status='completed')
    gone = doc(db, esp_id, 'https://help.example.com/old', product='reviews', content='o', crawl_status='completed')
    db.execute_query("INSERT INTO crawl_jobs (id, esp_id, document_id, status) VALUES (%s, %s, %s, 'pending')",
                     (str(uuid.uuid4()), esp_id, gone))
    out = refresh.retire(db, vectors, 'klaviyo', ['https://help.example.com/old', 'https://help.example.com/nope'])
    assert out['retired'] == ['https://help.example.com/old'] and out['skipped'][0]['url'].endswith('nope')
    assert vectors.deleted == ['https://help.example.com/old']
    assert db.execute_query("SELECT status FROM crawl_jobs WHERE document_id = %s", (gone,),
                            fetch=True)[0][0] == 'cancelled'
    assert refresh.retire(db, vectors, 'klaviyo', ['https://help.example.com/old'])['skipped'][0]['error'] \
        == 'Already retired'
    mgr = esp_manager.get_esp_manager()
    assert [x['url'] for x in mgr.list_documents('klaviyo')] == ['https://help.example.com/keep']
    assert len(mgr.list_documents('klaviyo', include_retired=True)) == 2
    assert [x['url'] for x in mgr.get_documents_with_content('klaviyo')] == ['https://help.example.com/keep']
    assert mgr.reviews_documents() == [('klaviyo', 'https://help.example.com/keep')]
    assert mgr.get_esp_stats('klaviyo')['total_docs'] == 1
    assert [e['doc_count'] for e in mgr.list_esps() if e['name'] == 'klaviyo'] == [1]
    # the admin lists it last, as retired
    import admin_integrations_routes as air
    rows = air.document_rows(db, esp_id, use_async=False)
    assert [r['status'] for r in rows] == ['crawled', 'retired'] and rows[1]['retired']
    assert air._integration_row(db, 'klaviyo')['documents']['total'] == 1
    # a document being crawled is left alone
    busy = doc(db, esp_id, 'https://help.example.com/busy')
    db.execute_query("INSERT INTO crawl_jobs (id, esp_id, document_id, status) VALUES (%s, %s, %s, 'processing')",
                     (str(uuid.uuid4()), esp_id, busy))
    assert 'crawled right now' in refresh.retire(db, vectors, 'klaviyo', ['https://help.example.com/busy'])['skipped'][0]['error']
    assert keep


# ---------- the sitemap ----------

SITEMAP = """<?xml version="1.0"?><urlset>
<url><loc>https://support.yotpo.com/docs/a</loc><lastmod>2026-10-01T10:00:00+02:00</lastmod></url>
<url><loc>https://support.yotpo.com/docs/b</loc><lastmod>2026-10-02</lastmod></url>
<url><loc>https://support.yotpo.com/docs/c/</loc></url>
</urlset>"""


class Page:
    def __init__(self, text, status=200):
        self.text, self.status = text, status


def fake_fetch(pages):
    return lambda url: pages.get(url)


def test_lastmod_and_the_diff():
    assert sm.parse_lastmod('2026-10-01T10:00:00+02:00') == datetime(2026, 10, 1, 8, 0)
    assert sm.parse_lastmod('2026-10-02') == datetime(2026, 10, 2)
    assert sm.parse_lastmod('nonsense') is None and sm.parse_lastmod(None) is None
    entries = sm.read_entries(SITEMAP)
    assert set(entries) == {'https://support.yotpo.com/docs/a', 'https://support.yotpo.com/docs/b',
                            'https://support.yotpo.com/docs/c'}
    t = datetime(2026, 10, 1)
    previous = {'https://support.yotpo.com/docs/a': (t, None),
                'https://support.yotpo.com/docs/b': (datetime(2026, 10, 2), None),
                'https://support.yotpo.com/docs/old': (t, None),
                'https://support.yotpo.com/docs/c': (None, t)}
    d = sm.diff(previous, entries)
    assert d == {'new': [], 'changed': ['https://support.yotpo.com/docs/a'],
                 'vanished': ['https://support.yotpo.com/docs/old'], 'back': ['https://support.yotpo.com/docs/c']}
    assert sm.too_small(100, 79) and not sm.too_small(100, 80) and not sm.too_small(0, 1)
    assert sm.due(datetime(2026, 10, 2), datetime(2026, 10, 1))
    assert not sm.due(datetime(2026, 10, 1), datetime(2026, 10, 2))
    assert not sm.due(datetime(2026, 10, 2), None)                 # never crawled: the admin's call


def test_a_run_records_changes_and_queues_changed_guides():
    db = boot_db()
    esp_id = esp(db)
    held = doc(db, esp_id, 'https://support.yotpo.com/docs/a', last_crawled_at='2026-09-01 00:00:00')
    fresh = doc(db, esp_id, 'https://support.yotpo.com/docs/b', last_crawled_at='2026-10-05 00:00:00')
    unlabelled = doc(db, esp_id, 'https://support.yotpo.com/docs/c', product=None,
                     last_crawled_at='2000-01-01 00:00:00')
    queued = []
    import workers.crawl_queue as cq
    real = cq.enqueue_crawl_job
    cq.enqueue_crawl_job = lambda db_, e, d, u, priority=10: (queued.append((d, priority)), ('job', True))[1]
    try:
        first = sm.run(db, fake_fetch({sm.SITEMAP_URL: Page(SITEMAP)}), use_queue=True, log=lambda m: None)
    finally:
        cq.enqueue_crawl_job = real
    assert first['ok'] and first['urls'] == 3 and first['new'] == 3
    assert queued == [(held, sm.PRIORITY)]                          # changed since its crawl, labelled
    assert first['queued'] == 1 and first['not_queued'] == 0        # c has no lastmod: not due
    assert row(db, held, 'sitemap_lastmod')[0].startswith('2026-10-01 08:00')
    assert fresh and unlabelled
    # the first read's articles are not "new" to the admin
    changes = sm.changes_since(db, datetime(2000, 1, 1))
    assert changes['new'] == [] and changes['last_run']['urls'] == 3
    # an article vanishes, a new one appears
    later = SITEMAP.replace('docs/b</loc>', 'docs/d</loc>')
    db.execute_query("UPDATE sitemap_urls SET first_seen_at = '2026-01-01 00:00:00'")
    second = sm.run(db, fake_fetch({sm.SITEMAP_URL: Page(later)}), use_queue=False, log=lambda m: None)
    assert second['new'] == 1 and second['vanished'] == 1
    changes = sm.changes_since(db, datetime(2026, 6, 1))
    assert [x['url'] for x in changes['new']] == ['https://support.yotpo.com/docs/d']
    gone = changes['vanished']
    assert [x['url'] for x in gone] == ['https://support.yotpo.com/docs/b'] and gone[0]['document']['esp'] == 'recharge'
    # a sitemap far smaller than the last marks nothing gone
    tiny = '<urlset><url><loc>https://support.yotpo.com/docs/a</loc></url></urlset>'
    third = sm.run(db, fake_fetch({sm.SITEMAP_URL: Page(tiny)}), use_queue=False, log=lambda m: None)
    assert third['shrunk'] and third['vanished'] == 0
    assert db.execute_query("SELECT COUNT(*) FROM sitemap_urls WHERE gone_at IS NULL", fetch=True)[0][0] == 3
    # an unreadable sitemap changes nothing and says so
    broken = sm.run(db, fake_fetch({}), use_queue=False, log=lambda m: None)
    assert not broken['ok'] and 'could not be read' in broken['problem']


def test_the_sitemap_is_read_monthly():
    """Leo, 2026-10-16: once a month. On the 1st at 03:17, and at boot when
    the last read is over a month old (a restart on the 1st skips nothing)."""
    now = datetime(2026, 11, 20, 12, 0)
    assert sm.overdue(None, now)
    assert sm.overdue({'started_at': '2026-10-01T03:17:00Z'}, now)          # 50 days
    assert not sm.overdue({'started_at': '2026-11-01T03:17:05Z'}, now)      # 19 days
    assert sm.overdue({'started_at': 'garbage'}, now)
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(lambda: None, trigger='cron', day=1, hour=3, minute=17)
    assert isinstance(job.trigger, CronTrigger)
    from datetime import timezone as tz
    fire = job.trigger.get_next_fire_time(None, datetime(2026, 11, 2, tzinfo=tz.utc))
    assert (fire.month, fire.day, fire.hour, fire.minute) == (12, 1, 3, 17)
    # the boot check reads only when overdue
    import refresh_routes
    calls = []
    real = refresh_routes.run_sitemap_refresh
    refresh_routes.run_sitemap_refresh = lambda use_queue: calls.append(use_queue) or 'ran'
    try:
        db = boot_db()
        assert refresh_routes.run_sitemap_refresh_if_overdue(True) == 'ran'
        sm._save(db, {'started_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')})
        assert refresh_routes.run_sitemap_refresh_if_overdue(True) is None and calls == [True]
    finally:
        refresh_routes.run_sitemap_refresh = real


# ---------- routes ----------

def make_client(db):
    from flask import Flask
    import refresh_routes
    app = Flask(f'refresh_{uuid.uuid4().hex}')
    vectors = FakeVectors()
    refresh_routes.register_refresh_routes(app, vectors, use_async_crawl=False)
    return app.test_client(), vectors


def test_retire_and_replace_routes():
    db = boot_db()
    esp_id = esp(db)
    doc(db, esp_id, 'https://help.example.com/old', product='shared', content='o')
    doc(db, esp_id, 'https://help.example.com/nolabel', product=None)
    c, vectors = make_client(db)
    as_user()
    r = c.post('/api/admin/esp/recharge/replace', json={'old_url': 'https://help.example.com/old',
                                                        'new_url': 'https://help.example.com/new#x'})
    body = r.get_json()
    assert r.status_code == 200 and body['product'] == 'shared' and body['new_url'] == 'https://help.example.com/new'
    mgr = esp_manager.get_esp_manager()
    new = mgr.get_document_by_url(esp_id, 'https://help.example.com/new')
    assert new['product'] == 'shared'
    old_id = mgr.get_document_by_url(esp_id, 'https://help.example.com/old')['id']
    assert row(db, old_id, 'replaced_by', 'retired_at') == (new['id'], None)
    for payload, code in (({'old_url': 'https://help.example.com/old', 'new_url': 'https://help.example.com/new'}, 409),
                          ({'old_url': 'https://help.example.com/old', 'new_url': 'ftp://x'}, 400),
                          ({'old_url': 'https://help.example.com/x', 'new_url': 'https://help.example.com/y'}, 404),
                          ({'old_url': 'https://help.example.com/nolabel', 'new_url': 'https://help.example.com/z'}, 400),
                          ({}, 400)):
        assert c.post('/api/admin/esp/recharge/replace', json=payload).status_code == code, payload
    r = c.post('/api/admin/esp/recharge/retire', json={'urls': ['https://help.example.com/old']})
    assert r.status_code == 200 and r.get_json()['retired'] == ['https://help.example.com/old']
    assert c.post('/api/admin/esp/nobody/retire', json={'urls': ['x']}).status_code == 404
    assert c.post('/api/admin/esp/recharge/retire', json={}).status_code == 400
    as_user(admin=False)
    assert c.post('/api/admin/esp/recharge/retire', json={'urls': ['x']}).status_code == 403
    as_user()


def test_sitemap_routes():
    db = boot_db()
    c, _ = make_client(db)
    as_user()
    r = c.get('/api/admin/sitemap-changes')
    body = r.get_json()
    assert r.status_code == 200 and body['last_run'] is None and body['scheduled'] is False
    assert c.get('/api/admin/sitemap-changes?since=yesterday').status_code == 400
    assert c.get('/api/admin/sitemap-changes?since=2026-01-01').get_json()['since'] == '2026-01-01'
    as_user(owners='someone.else@yotpo.com')                       # an editor
    assert c.post('/api/admin/sitemap-refresh', json={}).status_code == 403
    as_user(admin=False)
    assert c.get('/api/admin/sitemap-changes').status_code == 403
    as_user()


def as_user(email='leo@yotpo.com', admin=True, owners=None):
    USER.update(admin=admin, email=email)
    if owners is None:
        os.environ.pop('ADMIN_OWNER_EMAILS', None)
    else:
        os.environ['ADMIN_OWNER_EMAILS'] = owners


if __name__ == '__main__':
    tests = [v for k, v in dict(globals()).items() if k.startswith('test_')]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            import traceback
            traceback.print_exc()
            print(f"FAIL {t.__name__}: {type(e).__name__} {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1 if failed else 0)
