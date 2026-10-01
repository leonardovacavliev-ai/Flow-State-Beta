"""
Every write path labels what it writes: database rows, vectors, label edits.

    python3 backend/test_product_write_paths.py        # (or pytest)

Runs on a throwaway SQLite file with fake vector stores, plus one real local
ChromaDB collection in a temp folder. Nothing touches production: the app.py
checks swap in a fake vectorizer and a temp copy of the links CSV before any
request is made.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='product-write-paths-')
# Before anything reads them (app.py's load_dotenv does not override)
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(TMP, 'test.db')
os.environ['SESSION_PROVIDER'] = 'memory'
os.environ['USE_ASYNC_CRAWL'] = 'false'
os.environ['VECTOR_DB_PROVIDER'] = 'chromadb'   # belt and braces; the stub below is the guard
sys.path.insert(0, HERE)

import auth  # noqa: E402
auth.current_user_is_admin = lambda: True   # admin_request_ok looks it up per call

from esp_manager import get_esp_manager  # noqa: E402
import crawler  # noqa: E402
import product_labels  # noqa: E402
from adapters.vector.base import PRODUCT_LABELS, require_product_metadata  # noqa: E402

ESP = 'testesp'


class FakeVectors:
    """Records vector writes; ids_for_url answers from what was added."""

    def __init__(self, fail_updates=False):
        self.added, self.deleted, self.updates = [], [], []
        self.fail_updates = fail_updates

    def delete_by_url(self, url, esp):
        self.deleted.append((esp, url))

    def add_document(self, text, metadata):
        require_product_metadata(metadata)
        self.added.append(dict(metadata))

    def ids_for_url(self, url, esp):
        return [f"{m['esp']}_{m['filename']}_{i}" for m in self.added
                if m['esp'] == esp and m['source_url'] == url for i in range(2)]

    def update_metadata(self, ids, patch):
        if self.fail_updates:
            raise RuntimeError("index unavailable")
        self.updates.append((list(ids), dict(patch)))


def mgr():
    m = get_esp_manager()
    if not m.get_esp_by_name(ESP):
        m.create_esp(ESP, 'Test ESP')
    return m


def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return e
    raise AssertionError(f"expected {exc.__name__}")


def unlabelled_row(url):
    """A row from before labels were required."""
    m = mgr()
    esp = m.get_esp_by_name(ESP)
    m.db.execute_query("INSERT INTO esp_documents (id, esp_id, url, filename, crawl_status) "
                       "VALUES (%s, %s, %s, %s, 'completed')",
                       (url[-12:], esp['id'], url, 'old.txt'))


# ---------- labels ----------

def test_label_tuples_agree():
    assert product_labels.PRODUCTS == PRODUCT_LABELS


def test_add_document_requires_a_product():
    m = mgr()
    for bad in (None, '', 'ugc'):
        e = raises(ValueError, lambda: m.add_document(ESP, f'https://x.test/{bad}', product=bad))
        assert 'Yotpo product' in str(e)
    # keyword-only: an old positional filename can't pass as the product
    raises(TypeError, lambda: m.add_document(ESP, 'https://x.test/pos', 'file.txt'))
    assert m.get_document_product(ESP, 'https://x.test/None') is None


def test_add_document_stores_the_product():
    m = mgr()
    doc = m.add_document(ESP, 'https://x.test/a', product=' Reviews ')
    assert doc['product'] == 'reviews'
    assert m.get_document_product(ESP, 'https://x.test/a') == 'reviews'
    esp = m.get_esp_by_name(ESP)
    assert m.get_document_by_url(esp['id'], 'https://x.test/a')['product'] == 'reviews'


# ---------- vectors ----------

def test_vectors_carry_the_rows_label():
    m = mgr()
    m.add_document(ESP, 'https://x.test/b', product='loyalty')
    v = FakeVectors()
    crawler.vectorize_single_document(v, ESP, 'https://x.test/b', None, 'b.txt', content='text')
    assert v.added[0]['product'] == 'loyalty'


def test_explicit_product_skips_the_lookup():
    v = FakeVectors()
    crawler.vectorize_single_document(v, ESP, 'https://x.test/nowhere', None, 'n.txt',
                                      content='text', product='shared')
    assert v.added[0]['product'] == 'shared'


def test_unlabelled_document_keeps_its_old_vectors():
    unlabelled_row('https://x.test/legacy-doc')
    v = FakeVectors()
    e = raises(ValueError, lambda: crawler.vectorize_single_document(
        v, ESP, 'https://x.test/legacy-doc', None, 'old.txt', content='text'))
    assert 'no product label' in str(e)
    assert v.deleted == [] and v.added == []   # refused before deleting anything


def test_adapters_refuse_unlabelled_metadata():
    from adapters.vector.pinecone_adapter import PineconeAdapter
    from adapters.vector.chroma_adapter import ChromaDBAdapter
    for cls in (PineconeAdapter, ChromaDBAdapter):
        a = object.__new__(cls)   # no client: the check runs before any I/O
        e = raises(ValueError, lambda: a.add_document('text', {'esp': 'x', 'filename': 'f',
                                                               'source_url': 'u'}))
        assert 'no product label' in str(e)


def test_pinecone_ids_and_updates():
    from adapters.vector.pinecone_adapter import PineconeAdapter

    class FakeIndex:
        def __init__(self):
            self.queries, self.updates = [], []

        def query(self, **kw):
            self.queries.append(kw)
            return {'matches': [{'id': 'a'}, {'id': 'b'}]}

        def update(self, **kw):
            self.updates.append(kw)

    a = object.__new__(PineconeAdapter)
    a.index, a.dimension = FakeIndex(), 4
    assert a.ids_for_url('https://u', 'Klaviyo') == ['a', 'b']
    q = a.index.queries[0]
    assert q['filter'] == {'esp': {'$eq': 'klaviyo'}, 'source_url': {'$eq': 'https://u'}}
    assert q['vector'] == [1.0, 0.0, 0.0, 0.0] and q['top_k'] == 10000
    a.update_metadata(['a', 'b'], {'product': 'reviews'})
    assert a.index.updates == [{'id': 'a', 'set_metadata': {'product': 'reviews'}},
                               {'id': 'b', 'set_metadata': {'product': 'reviews'}}]


def test_chroma_update_keeps_other_metadata():
    from adapters.vector.chroma_adapter import ChromaDBAdapter
    a = ChromaDBAdapter(persist_directory=os.path.join(TMP, 'chroma'))
    words = ' '.join(f'word{i}' for i in range(60))
    a.add_document(words, {'esp': 'klaviyo', 'filename': 'f.txt', 'source_url': 'https://u',
                           'filepath': '/x', 'product': 'loyalty'})
    ids = a.ids_for_url('https://u', 'Klaviyo')
    assert ids == ['klaviyo_f.txt_0']
    a.update_metadata(ids, {'product': 'reviews'})
    md = a.collection.get(ids=ids, include=['metadatas', 'documents'])
    assert md['metadatas'][0]['product'] == 'reviews'
    assert md['metadatas'][0]['source_url'] == 'https://u' and md['metadatas'][0]['chunk_index'] == 0
    assert md['documents'][0] == words


def test_bulk_reindex_refuses_before_deleting():
    from adapters.vector.pinecone_adapter import PineconeAdapter
    from adapters.vector.chroma_adapter import ChromaDBAdapter

    class Exploding:
        def __getattr__(self, name):
            raise AssertionError(f"touched the store: {name}")

    for cls in (PineconeAdapter, ChromaDBAdapter):
        a = object.__new__(cls)
        a.index = a.collection = Exploding()
        for call in (lambda: a.refresh_esp('omnisend', '/docs'), lambda: a.vectorize_all_docs('/docs')):
            e = raises(RuntimeError, call)
            assert 'rebuild-vectors' in str(e)


# ---------- ESP admin routes ----------

_client = None


def client():
    """A Flask app with the sync ESP routes and the label route, on fakes."""
    global _client
    if _client is None:
        from flask import Flask
        from app_admin_esp_routes import register_esp_admin_routes
        app = Flask(__name__)
        app.vectors = FakeVectors()
        register_esp_admin_routes(app, TMP, app.vectors)
        product_labels.register_product_label_routes(app, app.vectors)
        _client = app.test_client()
        _client.vectors = app.vectors
    return _client


def test_add_link_requires_a_product():
    c = client()
    r = c.post(f'/api/admin/esp/{ESP}/add-link', json={'url': 'https://x.test/c', 'product': ''})
    assert r.status_code == 400 and 'Yotpo product' in r.get_json()['error']
    assert mgr().get_document_product(ESP, 'https://x.test/c') is None
    r = c.post(f'/api/admin/esp/{ESP}/add-link', json={'url': 'https://x.test/c', 'product': 'reviews'})
    assert r.status_code == 200
    assert mgr().get_document_product(ESP, 'https://x.test/c') == 'reviews'


def test_crawl_refuses_unlabelled_before_crawling():
    c = client()
    r = c.post(f'/api/admin/esp/{ESP}/crawl-selected', json={'urls': ['https://x.test/new']})
    assert r.status_code == 400 and 'no product label yet' in r.get_json()['error'].lower()
    esp = mgr().get_esp_by_name(ESP)
    assert mgr().get_document_by_url(esp['id'], 'https://x.test/new') is None   # nothing created
    unlabelled_row('https://x.test/legacy-crawl')
    r = c.post(f'/api/admin/esp/{ESP}/crawl-selected', json={'urls': ['https://x.test/legacy-crawl']})
    assert r.status_code == 400 and 'no product label' in r.get_json()['error'].lower()


def test_one_unlabelled_link_does_not_block_the_batch():
    c = client()
    unlabelled_row('https://x.test/legacy-batch')
    m = mgr()
    m.add_document(ESP, 'https://x.test/ok-batch', product='loyalty')
    import app_admin_esp_routes as routes
    real = routes.crawl_single_url_detailed
    routes.crawl_single_url_detailed = lambda url, esp, base: (None, 'offline in tests')
    try:
        r = c.post(f'/api/admin/esp/{ESP}/crawl-selected',
                   json={'urls': ['https://x.test/legacy-batch', 'https://x.test/ok-batch']})
    finally:
        routes.crawl_single_url_detailed = real
    failed = {f['url']: f['error'] for f in r.get_json()['results']['failed']}
    assert r.status_code == 200
    assert 'No product label' in failed['https://x.test/legacy-batch']
    assert failed['https://x.test/ok-batch'] == 'offline in tests'   # it was attempted


def test_old_admin_page_is_told_to_reload():
    r = client().post(f'/api/admin/esp/{ESP}/add-link', json={'url': 'https://x.test/old-tab'})
    assert r.status_code == 400 and 'Reload' in r.get_json()['error']
    r = client().post(f'/api/admin/esp/{ESP}/set-product', json={'urls': ['https://x.test/a'], 'product': None})
    assert r.status_code == 400 and 'reload' in r.get_json()['error']


def test_paste_labels_new_links_and_their_vectors():
    c = client()
    r = c.post(f'/api/admin/esp/{ESP}/paste-content',
               json={'url': 'https://x.test/p', 'content': 'pasted text'})
    assert r.status_code == 400
    r = c.post(f'/api/admin/esp/{ESP}/paste-content',
               json={'url': 'https://x.test/p', 'content': 'pasted text', 'product': 'shared'})
    assert r.status_code == 200, r.get_json()
    assert mgr().get_document_product(ESP, 'https://x.test/p') == 'shared'
    assert c.vectors.added[-1]['source_url'] == 'https://x.test/p'
    assert c.vectors.added[-1]['product'] == 'shared'


def test_label_edit_updates_the_vectors():
    c = client()
    c.post(f'/api/admin/esp/{ESP}/paste-content',
           json={'url': 'https://x.test/e', 'content': 'text', 'product': 'loyalty'})
    r = c.post(f'/api/admin/esp/{ESP}/set-product', json={'urls': ['https://x.test/e'], 'product': 'reviews'})
    body = r.get_json()
    assert r.status_code == 200 and body['vectors_updated'] == 2 and 'warning' not in body
    ids, patch = c.vectors.updates[-1]
    assert patch == {'product': 'reviews'} and len(ids) == 2
    assert mgr().get_document_product(ESP, 'https://x.test/e') == 'reviews'


def test_label_cannot_be_cleared():
    r = client().post(f'/api/admin/esp/{ESP}/set-product', json={'urls': ['https://x.test/e'], 'product': None})
    assert r.status_code == 400
    assert mgr().get_document_product(ESP, 'https://x.test/e') == 'reviews'


def test_label_edit_warns_when_a_crawled_doc_has_no_vectors():
    m = mgr()
    doc = m.add_document(ESP, 'https://x.test/novec', product='loyalty')
    m.update_document_crawl_status(doc['id'], 'completed', content='text')
    r = client().post(f'/api/admin/esp/{ESP}/set-product',
                      json={'urls': ['https://x.test/novec'], 'product': 'reviews'})
    body = r.get_json()
    assert body['vectors_updated'] == 0 and body['no_vectors'] == ['https://x.test/novec']
    assert 'no search-index entries' in body['warning']


def test_failed_index_update_is_reported_not_hidden():
    c = client()
    c.vectors.fail_updates = True
    try:
        r = c.post(f'/api/admin/esp/{ESP}/set-product', json={'urls': ['https://x.test/e'], 'product': 'shared'})
    finally:
        c.vectors.fail_updates = False
    body = r.get_json()
    assert r.status_code == 200 and body['index_failed'] == ['https://x.test/e'] and 'warning' in body
    assert mgr().get_document_product(ESP, 'https://x.test/e') == 'shared'   # the row is the source of truth


def test_rebuild_passes_each_rows_label():
    from app_admin_esp_routes import rebuild_esp_vectors
    m = mgr()
    m.create_esp('rebuildesp', 'Rebuild ESP')
    doc = m.add_document('rebuildesp', 'https://x.test/r', product='reviews')
    m.update_document_crawl_status(doc['id'], 'completed', content='stored text')
    v = FakeVectors()
    rebuilt, skipped, unlabelled = rebuild_esp_vectors('rebuildesp', v, TMP)
    assert rebuilt == ['https://x.test/r'] and v.added[0]['product'] == 'reviews'


# ---------- global knowledge (app.py) ----------

_app = None


def app_client():
    """app.py on a fake vectorizer and a temp copy of the links CSV."""
    global _app
    if _app is None:
        os.chdir(HERE)
        # app.py builds its vectorizer at import, from .env (production
        # Pinecone), and hands it to the routes it registers. Stub the
        # factory first so no live adapter is ever created.
        from adapters.vector import vector_manager
        fake = FakeVectors()
        fake.url_exists = lambda url, esp: False
        vector_manager.get_vector_adapter = lambda *a, **kw: fake
        import app as app_module
        assert app_module.vectorizer is fake, "app.py must use the stubbed vectorizer"
        repo = os.path.dirname(HERE)
        shutil.copy(os.path.join(repo, 'esp_support_links.csv'), os.path.join(TMP, 'esp_support_links.csv'))
        app_module.BASE_PATH = TMP
        assert product_labels._vectorizer is fake
        _app = app_module
    c = _app.app.test_client()
    c.vectors = _app.vectorizer
    return c


def test_global_add_link_creates_a_labelled_row():
    c = app_client()
    r = c.post('/api/admin/global-knowledge/add-link', json={'url': 'https://g.test/1', 'product': None})
    assert r.status_code == 400 and 'Yotpo product' in r.get_json()['error']
    r = c.post('/api/admin/global-knowledge/add-link', json={'url': 'https://g.test/1', 'product': 'loyalty'})
    assert r.status_code == 200
    assert mgr().get_document_product('global', 'https://g.test/1') == 'loyalty'
    r = c.post('/api/admin/global-knowledge/add-link', json={'url': 'https://g.test/1', 'product': 'loyalty'})
    assert r.status_code == 409 and r.get_json()['duplicate']


def test_global_list_shows_rows_missing_from_the_csv():
    c = app_client()
    c.post('/api/admin/global-knowledge/add-link', json={'url': 'https://g.test/2', 'product': 'shared'})
    with open(os.path.join(TMP, 'esp_support_links.csv')) as f:
        text = f.read()
    with open(os.path.join(TMP, 'esp_support_links.csv'), 'w') as f:
        f.write(text.replace('https://g.test/2\n', ''))   # as after a redeploy
    links = {l['url']: l for l in c.get('/api/admin/global-knowledge/links').get_json()['links']}
    assert links['https://g.test/2']['product'] == 'shared' and links['https://g.test/2']['labelable']


def test_csv_only_global_link_is_labelled_from_its_picker():
    c = app_client()
    csv = os.path.join(TMP, 'esp_support_links.csv')
    with open(csv) as f:
        text = f.read()
    with open(csv, 'w') as f:   # a link in the CSV with no row, as after a redeploy
        f.write(text.replace('Global Knowledge URLs\n', 'Global Knowledge URLs\nhttps://g.test/csv-only\n'))
    links = {l['url']: l for l in c.get('/api/admin/global-knowledge/links').get_json()['links']}
    assert links['https://g.test/csv-only']['labelable'] is False
    r = c.post('/api/admin/global-knowledge/crawl-selected', json={'urls': ['https://g.test/csv-only']})
    assert r.status_code == 400 and 'beside it' in r.get_json()['error']
    # what the picker sends
    r = c.post('/api/admin/global-knowledge/add-link', json={'url': 'https://g.test/csv-only', 'product': 'reviews'})
    assert r.status_code == 200
    assert mgr().get_document_product('global', 'https://g.test/csv-only') == 'reviews'
    with open(csv) as f:
        assert f.read().count('https://g.test/csv-only') == 1   # not listed twice


def test_global_crawl_of_another_esps_link_creates_nothing():
    c = app_client()
    mgr().add_document(ESP, 'https://x.test/owned', product='shared')
    r = c.post('/api/admin/global-knowledge/crawl-selected',
               json={'urls': ['https://g.test/fresh', 'https://x.test/owned'], 'product': 'shared'})
    assert r.status_code == 409
    assert mgr().get_document_product('global', 'https://g.test/fresh') is None


def test_global_paste_labels_the_vectors():
    c = app_client()
    r = c.post('/api/admin/global-knowledge/paste-content', json={'url': 'local://new.pdf', 'content': 'x'})
    assert r.status_code == 400
    r = c.post('/api/admin/global-knowledge/paste-content',
               json={'url': 'local://new.pdf', 'content': 'x', 'product': 'loyalty'})
    assert r.status_code == 200, r.get_json()
    assert c.vectors.added[-1]['product'] == 'loyalty' and c.vectors.added[-1]['esp'] == 'global'
    assert r.get_json()['backed_up']


def test_sync_refresh_all_is_disabled():
    r = app_client().post('/api/admin/refresh', json={})
    assert r.status_code == 409 and 'Crawl Selected' in r.get_json()['error']


# ---------- the audit ----------

def test_audit_finds_each_problem():
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'eval'))
    from audit_product_labels import find_problems, plan_backfill
    labels = {('k', 'u1'): 'loyalty', ('k', 'u2'): 'reviews', ('k', 'u3'): None}
    vectors = {
        'k_a_0': {'esp': 'k', 'source_url': 'u1', 'filename': 'a', 'chunk_index': 0, 'total_chunks': 1, 'product': 'loyalty'},
        'k_a_1': {'esp': 'k', 'source_url': 'u1', 'filename': 'a', 'chunk_index': 1, 'total_chunks': 2, 'product': 'loyalty'},
        'k_b_0': {'esp': 'k', 'source_url': 'u2', 'filename': 'b', 'chunk_index': 0, 'total_chunks': 1, 'product': 'loyalty'},
        'k_c_0': {'esp': 'k', 'source_url': 'u3', 'filename': 'c', 'chunk_index': 0, 'total_chunks': 1},
        'k_d_0': {'esp': 'k', 'source_url': 'gone', 'filename': 'd', 'chunk_index': 0, 'total_chunks': 1},
    }
    p = find_problems(vectors, labels)
    assert [x.split()[0] for x in p['orphan chunk']] == ['k_a_1']
    assert len(p['label differs from row']) == 1 and len(p['row has no label']) == 1
    assert len(p['no database row']) == 1
    assert plan_backfill(vectors, labels) == [('k_b_0', 'reviews')]
    clean = {'k_a_0': vectors['k_a_0']}
    assert not find_problems(clean, {('k', 'u1'): 'loyalty'})


if __name__ == '__main__':
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
