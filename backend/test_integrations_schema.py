"""
The v2 integration schema, key validation and URL identity (C1.1).

    python3 backend/test_integrations_schema.py            # SQLite (or pytest)
    python3 backend/test_integrations_schema.py postgres   # only the schema checks, on
                                                           #   TEST_DATABASE_URL, in
                                                           #   schema integrations_ci_test

Runs on throwaway databases with fake vector stores. The postgres run needs
TEST_DATABASE_URL (CI, local Docker) and never falls back to .env, which is
production.
"""
import os
import shutil
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='integrations-schema-')
# Before anything reads them (app.py's load_dotenv does not override)
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(TMP, 'test.db')
os.environ['SESSION_PROVIDER'] = 'memory'
os.environ['USE_ASYNC_CRAWL'] = 'false'
os.environ['VECTOR_DB_PROVIDER'] = 'chromadb'
sys.path.insert(0, HERE)

import esp_manager  # noqa: E402
from esp_manager import get_esp_manager  # noqa: E402
from integration_types import PLATFORM_TYPES, CATEGORY_DEFAULT_TYPE, default_type  # noqa: E402
from urls import normalize_url  # noqa: E402
from adapters.database.seeds import PLATFORM_TYPE_SEED_KEY  # noqa: E402

TEST_SCHEMA = 'integrations_ci_test'

NEW_ESP_COLUMNS = {'catalog_slugs', 'categories', 'products', 'platform_type', 'catalog_description'}
NEW_DOC_COLUMNS = {'title', 'source_kind', 'supported_plans', 'supported_platforms', 'vector_count',
                   'sitemap_lastmod', 'consecutive_misses', 'retired_at'}


class FakeVectors:
    def __init__(self, chunks=3):
        self.chunks = chunks

    def delete_by_url(self, url, esp):
        pass

    def add_document(self, text, metadata):
        return self.chunks


# ---------- schema, on any adapter ----------

def _columns(db, table):
    if db.__class__.__name__ == 'SQLiteAdapter':
        return {r[1] for r in db.execute_query(f"PRAGMA table_info({table})", fetch=True)}
    return {r[0] for r in db.execute_query(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = %s", (table,), fetch=True)}


def _insert_esp(db, name, status='active', platform_type=None):
    db.execute_query("INSERT INTO esps (id, name, display_name, status, platform_type) "
                     "VALUES (%s, %s, %s, %s, %s)",
                     (str(uuid.uuid4()), name, name.title(), status, platform_type))


def _type_of(db, name):
    return db.execute_query("SELECT platform_type FROM esps WHERE name = %s", (name,), fetch=True)[0][0]


def check_schema(db):
    """Booting twice is a no-op; the new columns, table and index exist."""
    db.initialize()
    db.initialize()
    assert NEW_ESP_COLUMNS <= _columns(db, 'esps')
    assert NEW_DOC_COLUMNS <= _columns(db, 'esp_documents')
    assert {'id', 'esp_id', 'url', 'source', 'suggested_label', 'state', 'note', 'created_at',
            'decided_by', 'decided_at'} <= _columns(db, 'document_proposals')


def check_seed(db):
    """Existing rows become messaging once; global stays NULL; later rows are left alone."""
    db.execute_query("DELETE FROM app_settings WHERE key = %s", (PLATFORM_TYPE_SEED_KEY,))
    _insert_esp(db, 'seed_old')
    _insert_esp(db, 'other_webhook')
    _insert_esp(db, 'global')
    _insert_esp(db, 'seed_typed', platform_type='storefront')
    db.initialize()
    assert _type_of(db, 'seed_old') == 'messaging'
    assert _type_of(db, 'other_webhook') == 'messaging'   # moves to data only in C2.4
    assert _type_of(db, 'global') is None
    assert _type_of(db, 'seed_typed') == 'storefront'
    _insert_esp(db, 'seed_catalog_later', status='listed')
    db.initialize()
    assert _type_of(db, 'seed_catalog_later') is None    # the seed ran once


def check_proposal_url_is_unique(db):
    esp_id = db.execute_query("SELECT id FROM esps WHERE name = 'seed_old'", fetch=True)[0][0]
    sql = ("INSERT INTO document_proposals (id, esp_id, url, source) VALUES (%s, %s, %s, 'manual')")
    db.execute_query(sql, (str(uuid.uuid4()), esp_id, 'https://x.test/p'))
    try:
        db.execute_query(sql, (str(uuid.uuid4()), esp_id, 'https://x.test/p'))
    except Exception:
        return
    raise AssertionError("a URL was proposed twice")


SCHEMA_CHECKS = (check_schema, check_seed, check_proposal_url_is_unique)


# ---------- SQLite: schema ----------

def _fresh_sqlite():
    from adapters.database.sqlite_adapter import SQLiteAdapter
    return SQLiteAdapter(os.path.join(TMP, f'{uuid.uuid4().hex}.db'))


def test_sqlite_schema_and_seed():
    db = _fresh_sqlite()
    for check in SCHEMA_CHECKS:
        check(db)


def test_messages_index_exists():
    db = _fresh_sqlite()
    db.initialize()
    names = {r[0] for r in db.execute_query(
        "SELECT name FROM sqlite_master WHERE type = 'index'", fetch=True)}
    assert {'idx_messages_timestamp_esp', 'idx_proposals_state_esp'} <= names


# ---------- the manager ----------

def mgr():
    return get_esp_manager()


def test_new_integrations_need_a_kind():
    """No integration is added without its category (Leo, 2026-10-16)."""
    m = mgr()
    m.create_esp('mailchimp_t', 'Mailchimp', platform_type='messaging')
    assert _type_of(m.db, 'mailchimp_t') == 'messaging'
    m.create_esp('shopify_t', 'Shopify', platform_type='storefront', status='listed')
    assert _type_of(m.db, 'shopify_t') == 'storefront'
    _app_module()._ensure_global_esp(m)
    assert _type_of(m.db, 'global') is None
    for kind in (None, '', 'email'):
        try:
            m.create_esp('bad_t', 'Bad', platform_type=kind)
        except ValueError:
            continue
        raise AssertionError(f"kind {kind!r} was accepted")
    try:
        m.create_esp('bad_t', 'Bad')
    except TypeError:
        pass
    else:
        raise AssertionError("a create without a kind was accepted")
    assert m.get_esp_by_name('bad_t', include_archived=True) is None


def test_listed_rows_are_invisible_to_list_esps():
    m = mgr()
    _insert_esp(m.db, 'catalog_only', status='listed', platform_type='data')
    assert 'catalog_only' not in {e['name'] for e in m.list_esps()}
    assert 'catalog_only' not in {e['name'] for e in m.list_integrations()}
    listed = {e['name']: e for e in m.list_integrations(statuses=('listed',))}
    assert listed['catalog_only']['platform_type'] == 'data'
    assert listed['catalog_only']['categories'] == []


def test_list_integrations_reads_json_lists():
    m = mgr()
    m.create_esp('braze_t', 'Braze', platform_type='messaging')
    m.db.execute_query("UPDATE esps SET categories = %s, products = %s WHERE name = 'braze_t'",
                       ('["email-marketing", "sms-marketing"]', '["loyalty", "reviews"]'))
    braze = {e['name']: e for e in m.list_integrations()}['braze_t']
    assert braze['categories'] == ['email-marketing', 'sms-marketing']
    assert braze['products'] == ['loyalty', 'reviews']


def test_is_active_integration_follows_status():
    m = mgr()
    m.create_esp('active_t', 'Active', platform_type='messaging')
    esp_manager.ACTIVE_CACHE_SECONDS = -1   # no caching inside this test
    try:
        assert m.is_active_integration('active_t')
        assert not m.is_active_integration('nope_t')
        m.archive_esp(m.get_esp_by_name('active_t')['id'])
        assert not m.is_active_integration('active_t')
    finally:
        esp_manager.ACTIVE_CACHE_SECONDS = 60


def test_documents_are_stored_under_one_url():
    m = mgr()
    m.create_esp('urls_t', 'URLs', platform_type='messaging')
    doc = m.add_document('urls_t', ' HTTPS://Help.X.test:443/Guide/#setup ', product='loyalty')
    assert doc['url'] == 'https://help.x.test/Guide'
    esp = m.get_esp_by_name('urls_t')
    assert m.get_document_by_url(esp['id'], 'https://help.x.test/Guide/')['id'] == doc['id']
    assert m.find_documents_by_url('https://HELP.x.test/Guide#top')[0]['esp_name'] == 'urls_t'
    try:
        m.add_document('urls_t', 'https://help.x.test/Guide/', product='loyalty')
    except esp_manager.DuplicateURLError:
        return
    raise AssertionError("a second spelling of the same page was added")


def test_vector_count_is_stored():
    import crawler
    m = mgr()
    m.create_esp('count_t', 'Count', platform_type='messaging')
    m.add_document('count_t', 'https://x.test/count', product='shared')
    n = crawler.vectorize_single_document(FakeVectors(chunks=4), 'count_t', 'https://x.test/count',
                                          None, 'count.txt', content='words')
    assert n == 4
    row = m.db.execute_query("SELECT vector_count FROM esp_documents WHERE url = %s",
                             ('https://x.test/count',), fetch=True)
    assert row[0][0] == 4


def test_real_chroma_adapter_counts_its_chunks():
    from adapters.vector.chroma_adapter import ChromaDBAdapter
    a = ChromaDBAdapter(persist_directory=os.path.join(TMP, 'chroma'))
    text = '\n\n'.join(' '.join(f'p{p}w{i}' for i in range(250)) for p in range(4))
    n = a.add_document(text, {'esp': 'klaviyo', 'filename': 'f.txt', 'source_url': 'https://u',
                              'filepath': '', 'product': 'loyalty'})
    assert n == len(a.chunk_text(text)) == a.collection.count() and n > 1


# ---------- pure ----------

def test_normalize_url():
    cases = {
        ' HTTPS://Help.Example.com:443/Docs/A/#top ': 'https://help.example.com/Docs/A',
        'http://x.test:80/a?b=1#c': 'http://x.test/a?b=1',
        'https://x.test:8443/a/': 'https://x.test:8443/a',
        'https://x.test/': 'https://x.test/',
        'https://x.test': 'https://x.test',
        'https://x.test/a?q=/': 'https://x.test/a?q=/',
        'local://Yotpo': 'local://Yotpo',
        '': '',
    }
    for raw, want in cases.items():
        assert normalize_url(raw) == want, (raw, normalize_url(raw))
        assert normalize_url(want) == want   # idempotent


def test_default_type():
    assert default_type(['email-marketing', 'sms-marketing']) == 'messaging'    # Klaviyo
    assert default_type(['help-desk-crm']) == 'service'                          # Gorgias
    assert default_type(['retailers-and-review-syndication', 'ads']) == 'content'  # Google
    assert default_type(['help-desk-crm', 'ecommerce-platform']) == 'service'
    assert default_type(['data-automation', 'email-marketing']) == 'messaging'
    assert default_type(['Ecommerce-Platform ']) == 'storefront'
    assert default_type(['unknown']) is None and default_type(None) is None
    assert set(CATEGORY_DEFAULT_TYPE.values()) == set(PLATFORM_TYPES)


# ---------- app.py ----------

_app = None


def app_client():
    """app.py on a fake vectorizer; nothing reaches an AI provider."""
    global _app
    if _app is None:
        os.chdir(HERE)
        from adapters.vector import vector_manager
        fake = FakeVectors()
        vector_manager.get_vector_adapter = lambda *a, **kw: fake
        import app as app_module
        assert app_module.vectorizer is fake, "app.py must use the stubbed vectorizer"
        app_module.BASE_PATH = TMP
        _app = app_module
    return _app.app.test_client()


def _app_module():
    app_client()
    return _app


def test_unknown_integration_is_refused():
    c = app_client()
    r = c.post('/api/chat', json={'message': 'hi', 'session_id': 's1', 'esp': 'not_a_platform'})
    assert r.status_code == 400
    assert r.get_json()['error'] == 'Unknown integration. Reload the page.'


def test_archived_integration_is_refused():
    c = app_client()
    m = mgr()
    m.create_esp('gone_t', 'Gone', platform_type='messaging')
    m.archive_esp(m.get_esp_by_name('gone_t')['id'])
    esp_manager.ACTIVE_CACHE_SECONDS = -1
    try:
        r = c.post('/api/chat', json={'message': 'hi', 'session_id': 's1', 'esp': 'gone_t'})
    finally:
        esp_manager.ACTIVE_CACHE_SECONDS = 60
    assert r.status_code == 400


def test_integration_key_is_normalised():
    app_client()
    assert _app.integration_key('Other/Webhook ') == 'other_webhook'
    assert _app.integration_key(None) is None


# ---------- Postgres ----------

def run_postgres():
    """The schema checks on TEST_DATABASE_URL, isolated in TEST_SCHEMA."""
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        print("FAIL: TEST_DATABASE_URL is not set (this test never uses .env, which is production)")
        return 1
    import psycopg2
    conn = psycopg2.connect(url)
    conn.autocommit = True
    conn.cursor().execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
    conn.cursor().execute(f"CREATE SCHEMA {TEST_SCHEMA}")
    conn.close()
    sep = '&' if '?' in url else '?'
    from adapters.database.postgres_adapter import PostgresAdapter
    db = PostgresAdapter(f"{url}{sep}options=-csearch_path%3D{TEST_SCHEMA}")
    failed = 0
    try:
        if db.execute_query("SELECT current_schema()", fetch=True)[0][0] != TEST_SCHEMA:
            print("FAIL: not connected to the test schema; refusing to run")
            return 1
        for check in SCHEMA_CHECKS:
            try:
                check(db)
                print(f"PASS postgres {check.__name__}")
            except Exception as e:
                failed += 1
                print(f"FAIL postgres {check.__name__}: {type(e).__name__} {e}")
        idx = {r[0] for r in db.execute_query(
            "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema()", fetch=True)}
        ok = {'idx_messages_timestamp_esp', 'idx_proposals_state_esp'} <= idx
        print(f"{'PASS' if ok else 'FAIL'} postgres indexes")
        failed += 0 if ok else 1
    finally:
        db.close()
        conn = psycopg2.connect(url)
        conn.autocommit = True
        conn.cursor().execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        conn.close()
    return failed


if __name__ == '__main__':
    if sys.argv[1:] == ['postgres']:
        # The rest runs in CI's unit job, which has the embedding model
        failed = run_postgres()
        shutil.rmtree(TMP, ignore_errors=True)
        sys.exit(1 if failed else 0)
    tests = [v for k, v in dict(globals()).items() if k.startswith('test_')]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__} {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1 if failed else 0)
