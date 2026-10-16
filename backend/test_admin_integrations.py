"""
The v2 admin's routes: integrations, proposals, crawl summary, roles (C1.4).

    python3 backend/test_admin_integrations.py            # SQLite (or pytest)
    python3 backend/test_admin_integrations.py postgres   # the route checks again on
                                                          #   TEST_DATABASE_URL, schema
                                                          #   admin_integrations_ci_test,
                                                          #   with the crawl queue on

Runs on throwaway databases with a fake vector store and a fake signed-in
admin. The postgres run needs TEST_DATABASE_URL (CI, local Docker) and never
falls back to .env, which is production.
"""
import json
import os
import shutil
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='admin-integrations-')
# Before anything reads them (app.py's load_dotenv does not override)
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(TMP, 'test.db')
os.environ['SESSION_PROVIDER'] = 'memory'
os.environ['USE_ASYNC_CRAWL'] = 'false'
os.environ['VECTOR_DB_PROVIDER'] = 'chromadb'
os.environ.pop('ADMIN_OWNER_EMAILS', None)
os.environ.pop('ADMIN_PASSWORD_FALLBACK', None)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))

import auth  # noqa: E402

# The signed-in user, as the routes see it
USER = {'admin': True, 'email': 'leo@yotpo.com'}
auth.current_user_is_admin = lambda: USER['admin']
auth.current_user = lambda: {'email': USER['email']} if USER['admin'] else None

import esp_manager  # noqa: E402
import admin_integrations_routes as air  # noqa: E402

TEST_SCHEMA = 'admin_integrations_ci_test'


def as_user(email='leo@yotpo.com', admin=True, owners=None):
    USER.update(admin=admin, email=email)
    if owners is None:
        os.environ.pop('ADMIN_OWNER_EMAILS', None)
    else:
        os.environ['ADMIN_OWNER_EMAILS'] = owners


# ---------- fixtures ----------

def esp(db, name, status='listed', ptype='messaging', categories=(), products=(), slugs=(),
        display=None):
    esp_id = str(uuid.uuid4())
    db.execute_query(
        "INSERT INTO esps (id, name, display_name, status, platform_type, categories, products, "
        "catalog_slugs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (esp_id, name, display or name.replace('_', ' ').title(), status, ptype,
         json.dumps(list(categories)), json.dumps(list(products)), json.dumps(list(slugs))))
    return esp_id


def doc(db, esp_id, url, product=None, status='completed', vectors=3, misses=0, content='text'):
    doc_id = str(uuid.uuid4())
    db.execute_query(
        "INSERT INTO esp_documents (id, esp_id, url, filename, crawl_status, product, vector_count, "
        "consecutive_misses, content) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (doc_id, esp_id, url, url.rsplit('/', 1)[-1], status, product, vectors, misses, content))
    return doc_id


def proposal(db, esp_id, url, source='catalog', label=None, **extra):
    pid = str(uuid.uuid4())
    db.execute_query(
        "INSERT INTO document_proposals (id, esp_id, url, source, suggested_label, state, note, title, "
        "partner_function, reason) VALUES (%s, %s, %s, %s, %s, 'open', %s, %s, %s, %s)",
        (pid, esp_id, url, source, label, extra.get('note', 'from a test'), extra.get('title'),
         extra.get('function'), extra.get('reason')))
    return pid


def setting(db, key, value):
    db.execute_query("DELETE FROM app_settings WHERE key = %s", (key,))
    db.execute_query("INSERT INTO app_settings (key, value) VALUES (%s, %s)", (key, json.dumps(value)))


def seed(db):
    """The awkward cases, plus enough filler to need a second page."""
    ids = {}
    ids['global'] = esp(db, 'global', status='active', ptype=None)
    ids['klaviyo'] = esp(db, 'klaviyo', status='active', categories=['email-marketing', 'sms-marketing',
                                                                       'data-automation'],
                         products=['loyalty', 'reviews'], slugs=['klaviyo'])
    doc(db, ids['klaviyo'], 'https://support.yotpo.com/docs/klaviyo-loyalty', 'loyalty')
    doc(db, ids['klaviyo'], 'https://help.klaviyo.com/flows', 'shared')
    doc(db, ids['klaviyo'], 'https://help.klaviyo.com/unlabelled', None)
    doc(db, ids['klaviyo'], 'https://help.klaviyo.com/broken', 'shared', status='failed')
    # messaging with a guide but no mechanics document: not Basic
    ids['drip'] = esp(db, 'drip', status='active', categories=['email-marketing'], products=['loyalty'])
    doc(db, ids['drip'], 'https://support.yotpo.com/docs/drip', 'loyalty')
    # indexed to nothing: not a guide
    ids['omnisend'] = esp(db, 'omnisend', status='active', categories=['email-marketing'],
                          products=['loyalty'])
    doc(db, ids['omnisend'], 'https://support.yotpo.com/docs/omnisend', 'loyalty', vectors=0)
    doc(db, ids['omnisend'], 'https://help.omnisend.com/flows', 'shared')
    # indexed before vector_count existed: still a guide
    ids['listrak'] = esp(db, 'listrak', status='active', categories=['email-marketing'],
                         products=['loyalty'])
    doc(db, ids['listrak'], 'https://support.yotpo.com/docs/listrak', 'loyalty', vectors=None)
    doc(db, ids['listrak'], 'https://help.listrak.com/flows', 'shared', vectors=None,
        misses=3)
    # storefront: a guide is enough, but only for a product the catalog lists
    ids['recharge'] = esp(db, 'recharge', ptype='storefront',
                          categories=['subscription-recurring-billing'], products=['loyalty'],
                          slugs=['recharge'])
    doc(db, ids['recharge'], 'https://support.yotpo.com/docs/recharge-reviews', 'reviews')
    ids['tapcart'] = esp(db, 'tapcart', ptype='storefront', categories=['mobile-app-builder'],
                         products=['loyalty', 'reviews'], slugs=['tapcart'])
    doc(db, ids['tapcart'], 'https://support.yotpo.com/docs/tapcart', 'reviews')
    ids['gorgias'] = esp(db, 'gorgias', ptype='service', categories=['help-desk-crm', 'onsite-chatbots', 'data-automation'],
                         products=['loyalty', 'reviews'], slugs=['gorgias', 'gorgias-loyalty'])
    ids['old_partner'] = esp(db, 'old_partner', status='archived', ptype='data', categories=['other'])
    for n in range(55):
        esp(db, f'filler_{n:02d}', ptype='data', categories=['other'], products=['reviews'])
    ids['p_guide'] = proposal(db, ids['gorgias'], 'https://support.yotpo.com/docs/gorgias-loyalty',
                              label='loyalty')
    ids['p_partner'] = proposal(db, ids['gorgias'], 'https://docs.gorgias.com/yotpo')
    ids['p_mech'] = proposal(db, ids['gorgias'], 'https://docs.gorgias.com/macros', source='mechanics',
                             label='shared', title='Macros', function='Macros',
                             reason='explains the macros the guide uses')
    ids['p_recharge'] = proposal(db, ids['recharge'], 'https://support.yotpo.com/docs/recharge',
                                 label='loyalty')
    setting(db, air.CATALOG_MECHANICS_KEY, {
        'gorgias': {'help_centre': 'https://docs.gorgias.com', 'functions': [{'name': 'Macros'}],
                    'blocked': False, 'problem': None, 'accepted': 1},
        'tapcart': {'help_centre': 'https://help.tapcart.com', 'functions': [], 'blocked': True,
                    'problem': 'bot check', 'accepted': 0},
        'recharge': {'help_centre': None, 'functions': [], 'blocked': False,
                     'problem': 'no help centre found', 'accepted': 0},
        'drip': {'help_centre': 'https://help.drip.com', 'functions': [{'name': 'Workflows'}],
                 'blocked': False, 'problem': 'the model accepted none of the 4 articles it read',
                 'accepted': 0},
        'gone_from_db': {'help_centre': None, 'blocked': True, 'accepted': 0},
    })
    return ids


class FakeVectors:
    def delete_by_url(self, url, esp):
        pass

    def add_document(self, text, metadata):
        return 1


def make_client(db, use_async):
    """A Flask app with the admin integrations routes on `db`."""
    from flask import Flask
    from adapters.database import db_manager
    db_manager.get_database_adapter = lambda: db
    mgr = esp_manager.ESPManager()
    mgr.db = db
    esp_manager._esp_manager = mgr
    app = Flask(__name__)
    air.register_admin_integrations_routes(app, use_async_crawl=use_async)
    return app.test_client()


# ---------- pure ----------

def test_patch_validation():
    cur = {'status': 'listed', 'platform_type': 'storefront'}
    v = air.validate_patch
    assert v({'status': 'active'}, cur, True)[2] == 409          # no storefront prompt yet
    assert v({'status': 'active', 'platform_type': 'messaging'}, cur, True)[1] is None
    assert v({'status': 'archived'}, cur, True)[2] == 400        # two states only (Leo, 2026-10-15)
    assert v({'status': 'active', 'platform_type': 'messaging'}, cur, False)[2] == 403   # editors can't change status
    assert v({'status': 'listed'}, cur, False)[1] is None        # unchanged status is not a change
    assert v({'name': 'x'}, cur, True)[2] == 400
    assert v({}, cur, True)[2] == 400
    assert v({'platform_type': 'email'}, cur, True)[2] == 400
    assert v({'products': ['ugc']}, cur, True)[2] == 400
    assert v({'display_name': '  '}, cur, True)[2] == 400
    changes = v({'categories': ['Ads', 'ads', 'other'], 'products': ['reviews', 'loyalty']}, cur, True)[0]
    assert changes == {'categories': ['ads', 'other'], 'products': ['loyalty', 'reviews']}
    # an active messaging integration can't be moved to a type that isn't in chat
    assert v({'platform_type': 'data'}, {'status': 'active', 'platform_type': 'messaging'}, True)[2] == 409


def test_approval_validation():
    ok = str(uuid.uuid4())
    v = air.validate_approvals
    assert v({'items': [{'id': ok}]})[1]                          # no product
    assert v({'items': [{'id': ok, 'product': 'ugc'}]})[1]
    assert v({'items': [{'id': 'nope', 'product': 'loyalty'}]})[1]
    assert v({'items': []})[1] and v(None)[1]
    assert v({'items': [{'id': ok, 'product': ' Shared '}]}) == ([(ok, 'shared')], None)


def test_needs_person():
    m = {'a': {'blocked': True, 'help_centre': 'x', 'accepted': 0},
         'b': {'help_centre': None, 'accepted': 0},
         'c': {'help_centre': 'x', 'accepted': 0, 'problem': 'none accepted'},
         'd': {'help_centre': 'x', 'accepted': 3},
         'e': {'blocked': True}}
    rows = air.needs_person(m, {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'})
    assert [(r['esp'], r['kind']) for r in rows] == [('a', 'blocked'), ('c', 'nothing_found'),
                                                     ('b', 'no_help_centre')]


# ---------- routes, on either database ----------

def check_admin_only(c, db, ids):
    as_user(admin=False)
    try:
        for path in ('/api/admin/integrations', '/api/admin/integrations/klaviyo',
                     '/api/admin/proposals', '/api/admin/crawl-summary', '/api/admin/catalog-import'):
            assert c.get(path).status_code == 403, path
        assert c.post('/api/admin/proposals/approve', json={'items': []}).status_code == 403
        assert c.patch('/api/admin/integrations/klaviyo', json={'platform_type': 'data'}).status_code == 403
    finally:
        as_user()


def check_list_pages_and_filters(c, db, ids):
    r = c.get('/api/admin/integrations').get_json()
    names = [i['name'] for i in r['integrations']]
    assert r['total'] == 63 and len(names) == 50 and r['facets']['total'] == 63
    assert 'global' not in names and names[0] == 'drip'          # by display name
    page2 = c.get('/api/admin/integrations?page=2').get_json()
    assert len(page2['integrations']) == 13
    assert not set(names) & {i['name'] for i in page2['integrations']}

    def found(query):
        body = c.get('/api/admin/integrations?' + query + '&per_page=200').get_json()
        return sorted(i['name'] for i in body['integrations'])
    assert found('q=GORG') == ['gorgias']
    assert found('q=help+desk') == ['gorgias']                   # category labels are searched
    assert found('category=subscription-recurring-billing') == ['recharge']
    assert found('type=storefront') == ['recharge', 'tapcart']
    assert c.get('/api/admin/integrations?status=archived').status_code == 400
    assert 'old_partner' in found('')                             # archived by older code: still listed
    assert found('flag=unlabelled') == ['klaviyo']
    assert found('flag=failed') == ['klaviyo']
    assert found('flag=proposals') == ['gorgias', 'recharge']
    assert found('flag=misses') == ['listrak']
    assert found('flag=mixed_types') == ['gorgias', 'klaviyo']
    assert found('status=active') == ['drip', 'klaviyo', 'listrak', 'omnisend']
    assert air.effective_products([], 0, 2) == ['reviews']
    assert air.effective_products(['reviews'], 1, 0) == ['loyalty', 'reviews']
    assert air.effective_products(['loyalty'], 0, 0) == ['loyalty']
    assert r['facets']['flags']['proposals'] == 2
    cats = {f['slug']: f for f in r['facets']['categories']}
    assert cats['help-desk-crm']['name'] == 'Help Desk & CRM' and cats['other']['count'] == 56
    assert c.get('/api/admin/integrations?type=email').status_code == 400
    assert c.get('/api/admin/integrations?per_page=0').status_code == 400
    rc = c.get('/api/admin/integrations?q=recharge').get_json()['integrations'][0]
    assert rc['products'] == ['loyalty', 'reviews'] and rc['products_from_documents'] == ['reviews']
    gor = c.get('/api/admin/integrations?q=gorgias').get_json()['integrations'][0]
    assert gor['products_from_documents'] == []           # no documents: only what is ticked
    k = c.get('/api/admin/integrations?q=klaviyo').get_json()['integrations'][0]
    assert k['documents'] == {'total': 4, 'loyalty': 1, 'reviews': 0, 'shared': 2, 'unlabelled': 1}
    assert k['type_choices'] == ['data', 'messaging'] and k['failed'] == 1 and k['not_crawled'] == 0


def check_detail(c, db, ids):
    r = c.get('/api/admin/integrations/gorgias')
    body = r.get_json()['integration']
    assert r.status_code == 200 and 'tier' not in body and body['open_proposals'] == 3
    assert [x['url'] for x in body['catalog_cards']] == [
        'https://www.yotpo.com/integrations/gorgias/', 'https://www.yotpo.com/integrations/gorgias-loyalty/']
    assert body['mechanics']['functions'] == [{'name': 'Macros'}]
    assert c.get('/api/admin/integrations/global').status_code == 404
    assert c.get('/api/admin/integrations/nope').status_code == 404


def check_patch(c, db, ids):
    as_user(owners='owner@yotpo.com')                             # leo is an editor now
    try:
        r = c.patch('/api/admin/integrations/klaviyo', json={'platform_type': 'messaging'})
        body = r.get_json()['integration']
        assert r.status_code == 200 and body['type_choices'] == [] and body['type_set_by'] == 'leo@yotpo.com'
        assert c.patch('/api/admin/integrations/gorgias', json={'status': 'active'}).status_code == 403
        r = c.patch('/api/admin/integrations/gorgias', json={'display_name': 'Gorgias ', 'products': ['reviews']})
        assert r.status_code == 200 and r.get_json()['integration']['display_name'] == 'Gorgias'
        as_user('owner@yotpo.com', owners='owner@yotpo.com')
        assert c.patch('/api/admin/integrations/gorgias', json={'status': 'active'}).status_code == 409
        mgr = esp_manager.get_esp_manager()
        assert not mgr.is_active_integration('drip_two')
        esp(db, 'drip_two', categories=['email-marketing'])
        assert c.patch('/api/admin/integrations/drip_two', json={'status': 'active'}).status_code == 200
        assert mgr.is_active_integration('drip_two')              # this process sees it at once
        assert c.patch('/api/admin/integrations/drip_two', json={'status': 'listed'}).status_code == 200
        assert not mgr.is_active_integration('drip_two')
        as_user(owners=None)                                      # unset, as in production today
        assert c.patch('/api/admin/integrations/drip_two', json={'status': 'active'}).status_code == 200
        assert c.patch('/api/admin/integrations/drip_two', json={'status': 'listed'}).status_code == 200
    finally:
        as_user()


def check_documents(c, db, ids):
    r = c.get('/api/admin/integrations/klaviyo/documents?per_page=3').get_json()
    assert r['total'] == 4 and len(r['documents']) == 3
    rest = c.get('/api/admin/integrations/klaviyo/documents?per_page=3&page=2').get_json()['documents']
    every = {d['url']: d for d in r['documents'] + rest}
    assert every['https://help.klaviyo.com/broken']['status'] == 'failed'
    assert every['https://help.klaviyo.com/unlabelled']['product'] is None
    assert every['https://help.klaviyo.com/unlabelled']['labelable']
    assert every['https://support.yotpo.com/docs/klaviyo-loyalty']['vector_count'] == 3
    lis = c.get('/api/admin/integrations/listrak/documents').get_json()['documents']
    assert {d['url']: d['consecutive_misses'] for d in lis}['https://help.listrak.com/flows'] == 3
    assert c.get('/api/admin/integrations/global/documents').status_code == 404


def check_proposals_inbox(c, db, ids):
    r = c.get('/api/admin/proposals').get_json()
    assert r['total'] == 4 and r['counts']['open'] == 4
    assert [p['esp'] for p in r['proposals']] == ['gorgias'] * 3 + ['recharge']
    assert [p['source'] for p in r['proposals'][:3]] == ['catalog', 'catalog', 'mechanics']
    mech = r['proposals'][2]
    assert (mech['title'], mech['partner_function'], mech['reason']) == (
        'Macros', 'Macros', 'explains the macros the guide uses')
    assert r['integrations']['gorgias']['functions'] == [{'name': 'Macros'}]
    assert r['sources']['mechanics'] == 1
    only = c.get('/api/admin/proposals?source=mechanics').get_json()
    assert [p['id'] for p in only['proposals']] == [ids['p_mech']]
    assert c.get('/api/admin/proposals?esp=recharge').get_json()['total'] == 1
    assert c.get('/api/admin/proposals?state=maybe').status_code == 400


def check_approve_and_reject(c, db, ids, use_async):
    def proposal_state(pid):
        return db.execute_query("SELECT state, decided_by FROM document_proposals WHERE id = %s",
                                (pid,), fetch=True)[0]
    # A product is required for every item, or nothing happens
    r = c.post('/api/admin/proposals/approve', json={'items': [
        {'id': ids['p_guide'], 'product': 'loyalty'}, {'id': ids['p_partner']}]})
    assert r.status_code == 400 and proposal_state(ids['p_guide'])[0] == 'open'
    r = c.post('/api/admin/proposals/approve', json={'items': [
        {'id': ids['p_guide'], 'product': 'loyalty'}, {'id': ids['p_mech'], 'product': 'shared'}]})
    body = r.get_json()
    assert r.status_code == 200 and body['approved'] == 2, body
    assert proposal_state(ids['p_guide']) == ('approved', 'leo@yotpo.com')
    # gorgias is listed: its documents can be added before it goes into chat
    mgr = esp_manager.get_esp_manager()
    assert mgr.get_document_product('gorgias', 'https://support.yotpo.com/docs/gorgias-loyalty') == 'loyalty'
    assert mgr.get_document_product('gorgias', 'https://docs.gorgias.com/macros') == 'shared'
    assert all(x['queued'] == use_async for x in body['results'])
    if use_async:
        n = db.execute_query("SELECT COUNT(*) FROM crawl_jobs WHERE status = 'pending'", fetch=True)[0][0]
        assert n == 2
    again = c.post('/api/admin/proposals/approve', json={'items': [{'id': ids['p_guide'], 'product': 'loyalty'}]})
    assert again.get_json()['results'][0]['error'] == 'Already approved'
    # A URL already in the knowledge base stays open, with the reason
    doc(db, ids['klaviyo'], 'https://support.yotpo.com/docs/recharge', 'loyalty')
    dup = c.post('/api/admin/proposals/approve', json={'items': [{'id': ids['p_recharge'], 'product': 'loyalty'}]})
    assert 'already exists in Klaviyo' in dup.get_json()['results'][0]['error']
    assert proposal_state(ids['p_recharge'])[0] == 'open'
    # Already this integration's document (added by hand, or an approve that
    # stopped half way): approved, and the label it has is kept
    doc(db, ids['recharge'], 'https://support.yotpo.com/docs/recharge-own', 'reviews')
    own = proposal(db, ids['recharge'], 'https://support.yotpo.com/docs/recharge-own', label='loyalty')
    r = c.post('/api/admin/proposals/approve', json={'items': [{'id': own.upper(), 'product': 'loyalty'}]})
    res = r.get_json()['results'][0]
    assert res['ok'] and 'already a document' in res['warning'], res
    assert proposal_state(own)[0] == 'approved'
    assert mgr.get_document_product('recharge', 'https://support.yotpo.com/docs/recharge-own') == 'reviews'
    r = c.post('/api/admin/proposals/reject', json={'ids': [ids['p_partner'], ids['p_guide']],
                                                    'note': 'a homepage'})
    assert r.get_json() == {'success': True, 'rejected': 1, 'skipped': 1}
    row = db.execute_query("SELECT state, decision_note, note FROM document_proposals WHERE id = %s",
                           (ids['p_partner'],), fetch=True)[0]
    assert row == ('rejected', 'a homepage', 'from a test')      # the import's note is kept
    assert c.post('/api/admin/proposals/reject', json={'ids': ['x']}).status_code == 400
    counts = c.get('/api/admin/proposals').get_json()['counts']
    assert counts == {'open': 1, 'approved': 3, 'rejected': 1}
    # the counts follow the integration filter
    assert c.get('/api/admin/proposals?esp=recharge').get_json()['counts'] == {
        'open': 1, 'approved': 1, 'rejected': 0}


def check_crawl_summary(c, db, ids, use_async):
    r = c.get('/api/admin/crawl-summary').get_json()
    assert r['queue'] == use_async
    assert r['states']['failed'] == 1
    hosts = {h['host']: h for h in r['hosts']}
    assert hosts['help.klaviyo.com']['failed'] == 1
    if use_async:
        # the two approvals above were queued
        assert r['active_jobs'] == 2 and len(r['jobs']) == 2 and r['states']['queued'] == 2
        assert {j['esp'] for j in r['jobs']} == {'gorgias'}
        assert hosts['support.yotpo.com']['queued'] == 1
    else:
        assert r['jobs'] == [] and r['active_jobs'] == 0 and r['states']['pending'] == 2


def check_crawled_since(c, db, ids):
    """The admin shows the crawl box for crawls made during the visit."""
    first = c.get('/api/admin/crawl-summary').get_json()
    assert first['now'] and first['crawled_since'] == 0
    assert c.get(f"/api/admin/crawl-summary?since={first['now']}").get_json()['crawled_since'] == 0
    doc_id = doc(db, ids['drip'], 'https://help.drip.com/crawled-now', 'shared', status='pending')
    esp_manager.get_esp_manager().update_document_crawl_status(doc_id, 'completed')
    r = c.get(f"/api/admin/crawl-summary?since={first['now']}").get_json()
    assert r['crawled_since'] == 1, r
    assert c.get('/api/admin/crawl-summary?since=yesterday').status_code == 400


def check_catalog_import(c, db, ids):
    setting(db, air.CATALOG_REPORT_KEY, {'applied_at': 'today', 'cards': 181, 'report': '# Report'})
    r = c.get('/api/admin/catalog-import').get_json()
    assert r['last_import']['cards'] == 181
    assert [(x['esp'], x['kind']) for x in r['needs_person']] == [
        ('tapcart', 'blocked'), ('drip', 'nothing_found'), ('recharge', 'no_help_centre')]


def run_route_checks(db, use_async, label):
    ids = seed(db)
    c = make_client(db, use_async)
    failed = 0
    checks = [check_admin_only, check_list_pages_and_filters, check_detail, check_documents,
              check_proposals_inbox,
              lambda c, db, ids: check_approve_and_reject(c, db, ids, use_async),
              lambda c, db, ids: check_crawl_summary(c, db, ids, use_async),
              check_crawled_since, check_catalog_import, check_patch]
    names = ['admin_only', 'list_pages_and_filters', 'detail', 'documents', 'proposals_inbox',
             'approve_and_reject', 'crawl_summary', 'crawled_since', 'catalog_import', 'patch']
    for name, check in zip(names, checks):
        try:
            check(c, db, ids)
            print(f"PASS {label} {name}")
        except Exception as e:
            failed += 1
            import traceback
            traceback.print_exc()
            print(f"FAIL {label} {name}: {type(e).__name__} {e}")
    return failed


_sqlite_ran = {}


def test_routes_on_sqlite():
    if 'failed' not in _sqlite_ran:
        from adapters.database.db_manager import get_database_adapter
        _sqlite_ran['failed'] = run_route_checks(get_database_adapter(), False, 'sqlite')
    assert _sqlite_ran['failed'] == 0


# ---------- the import's second run (SQLite) ----------

def test_import_skips_rejected_and_stores_notes():
    test_routes_on_sqlite()       # the rejection above
    import import_catalog as ic
    from adapters.database.db_manager import get_database_adapter
    db = get_database_adapter()
    plan = {'version': ic.PLAN_VERSION, 'guard': None, 'only': None,
            'snapshot': {'cards': 2, 'slugs': ['gorgias', 'zendesk']},
            'create': [], 'update': [],
            'proposals': [
                {'esp': 'gorgias', 'url': 'https://docs.gorgias.com/yotpo', 'source': 'catalog',
                 'suggested_label': None, 'note': 'partner page'},
                {'esp': 'gorgias', 'url': 'https://docs.gorgias.com/rules', 'source': 'mechanics',
                 'suggested_label': 'shared', 'note': 'Rules: "Rules". why'}],
            'mechanics': {'gorgias': {
                'help_centre': 'https://docs.gorgias.com', 'functions': [{'name': 'Rules', 'yotpo_role': 'x',
                                                                          'searches': ['rules']}],
                'blocked': False, 'problem': None, 'found_via': 'catalog', 'method': 'pages',
                'sources': ['Yotpo guide'], 'checked': 4,
                'accepted': [{'url': 'https://docs.gorgias.com/rules', 'title': 'Rules',
                              'function': 'Rules', 'reason': 'why'}]}},
            'clashes': [], 'removed_cards': [], 'gone': [], 'ambiguous_renames': [], 'nothing': [],
            'no_help_centre': [], 'already_documents': [], 'already_proposed': [], 'duplicates': [],
            'unreachable': [], 'blocked': [], 'integrations': 2, 'ai': None}
    store = ic.Store(write=True)
    try:
        counts = ic.apply_plan(store, plan)
    finally:
        store.close()
    assert counts['proposals'] == 1 and counts['skipped'] == 1    # the rejected one is not back
    row = db.execute_query("SELECT title, partner_function, reason, source FROM document_proposals "
                           "WHERE url = %s", ('https://docs.gorgias.com/rules',), fetch=True)[0]
    assert row == ('Rules', 'Rules', 'why', 'mechanics')
    notes = json.loads(db.execute_query("SELECT value FROM app_settings WHERE key = %s",
                                        (ic.MECHANICS_KEY,), fetch=True)[0][0])
    assert notes['gorgias'] == {'help_centre': 'https://docs.gorgias.com', 'found_via': 'catalog',
                                'functions': [{'name': 'Rules', 'yotpo_role': 'x'}],
                                'blocked': False, 'problem': None, 'accepted': 1}
    report = json.loads(db.execute_query("SELECT value FROM app_settings WHERE key = %s",
                                         (ic.REPORT_KEY,), fetch=True)[0][0])
    assert report['cards'] == 2 and report['counts']['proposals'] == 1 and report['report']
    # A later plan made with --no-mechanics keeps the notes it has none of
    plan = dict(plan, mechanics={}, proposals=[])
    store = ic.Store(write=True)
    try:
        ic.apply_plan(store, plan)
    finally:
        store.close()
    notes = json.loads(db.execute_query("SELECT value FROM app_settings WHERE key = %s",
                                        (ic.MECHANICS_KEY,), fetch=True)[0][0])
    assert notes['gorgias']['accepted'] == 1 and 'tapcart' in notes


# ---------- roles on app.py's routes ----------

_app = None


def app_client():
    """app.py on a fake vectorizer (as in test_product_write_paths)."""
    global _app
    if _app is None:
        os.chdir(HERE)
        from adapters.vector import vector_manager
        vector_manager.get_vector_adapter = lambda *a, **kw: FakeVectors()
        import app as app_module
        _app = app_module
    return _app.app.test_client()


def test_roles():
    c = app_client()
    try:
        as_user(owners=None)                                      # unset: every admin owns
        assert c.post('/api/admin/verify').get_json() == {'valid': True, 'role': 'owner'}
        assert c.get('/api/admin/settings/system-prompt').status_code == 200
        as_user(owners='owner@yotpo.com, Other@Yotpo.com')
        assert c.post('/api/admin/verify').get_json() == {'valid': True, 'role': 'editor'}
        for method, path in (('get', '/api/admin/settings/system-prompt'),
                             ('post', '/api/admin/settings/system-prompt'),
                             ('get', '/api/admin/settings/ai-model'),
                             ('get', '/api/admin/settings/audit-log'),
                             ('post', '/api/admin/settings/restore'),
                             ('post', '/api/admin/refresh'),
                             ('post', '/api/admin/rebuild-vectors'),
                             ('get', '/api/admin/debug/pinecone-sample')):
            r = getattr(c, method)(path, json={})
            assert r.status_code == 403 and 'owner' in r.get_json()['error'], path
        r = c.post('/api/admin/esp/create', json={'name': 'editor_made'})
        assert r.status_code == 403                               # it would be in chat at once
        # editors keep documents and analytics
        assert c.get('/api/admin/analytics?time_range=all_time').status_code == 200
        as_user('other@yotpo.com', owners='owner@yotpo.com, Other@Yotpo.com')
        assert c.post('/api/admin/verify').get_json()['role'] == 'owner'
        assert c.get('/api/admin/settings/system-prompt').status_code == 200
        as_user(admin=False, owners='owner@yotpo.com')
        assert c.post('/api/admin/verify').get_json() == {'valid': False, 'role': None}
        # the break-glass password is an owner
        auth.ADMIN_PASSWORD_FALLBACK = True
        os.environ['ADMIN_PASSWORD'] = 'test-only'
        r = c.post('/api/admin/verify', headers={'X-Admin-Password': 'test-only'})
        assert r.get_json() == {'valid': True, 'role': 'owner'}
    finally:
        auth.ADMIN_PASSWORD_FALLBACK = False
        os.environ.pop('ADMIN_PASSWORD', None)
        as_user()


def test_create_needs_a_kind():
    """Create New Integration refuses an integration without its kind of
    platform (Leo, 2026-10-16); only a kind whose prompt is in chat goes in."""
    c = app_client()
    as_user(owners=None)
    mgr = esp_manager.get_esp_manager()
    for body in ({'name': 'nokind_t'}, {'name': 'nokind_t', 'platform_type': ''},
                 {'name': 'nokind_t', 'platform_type': 'email'}):
        r = c.post('/api/admin/esp/create', json=body)
        assert r.status_code == 400 and 'kind of platform' in r.get_json()['error'], body
    assert mgr.get_esp_by_name('nokind_t', include_archived=True) is None
    r = c.post('/api/admin/esp/create', json={'name': 'Mail Kind T', 'platform_type': 'messaging'})
    body = r.get_json()
    assert r.status_code == 200 and body['in_chat'] is True and body['esp']['status'] == 'active'
    r = c.post('/api/admin/esp/create', json={'name': 'Store Kind T', 'platform_type': 'storefront'})
    body = r.get_json()
    assert r.status_code == 200 and body['in_chat'] is False and body['esp']['status'] == 'listed'
    row = mgr.get_esp_by_name('store_kind_t')
    assert row['status'] == 'listed' and not mgr.is_active_integration('store_kind_t')
    # The create route still makes an empty docs/<name> folder in the repo
    for name in ('mail_kind_t', 'store_kind_t'):
        try:
            os.rmdir(os.path.join(os.path.dirname(HERE), 'docs', name))
        except OSError:
            pass


def test_owner_checks_in_the_async_routes():
    """Production registers the async ESP routes; their owner checks too."""
    from flask import Flask
    from app_admin_esp_routes_async import register_esp_admin_routes_async
    app = Flask('async_routes')
    register_esp_admin_routes_async(app, TMP, FakeVectors())
    c = app.test_client()
    try:
        as_user(owners='owner@yotpo.com')
        for path, body in (('/api/admin/rebuild-vectors', {}), ('/api/admin/esp/create', {'name': 'x'})):
            r = c.post(path, json=body)
            assert r.status_code == 403 and 'owner' in r.get_json()['error'], path
    finally:
        as_user()


def test_listed_integrations_stay_out_of_chat():
    """I4, now that admin lookups find listed rows."""
    c = app_client()
    from adapters.database.db_manager import get_database_adapter
    db = get_database_adapter()
    esp(db, 'listed_only', categories=['email-marketing'])
    mgr = esp_manager.get_esp_manager()
    assert mgr.get_esp_by_name('listed_only')                     # admin paths find it
    assert 'listed_only' not in [e['name'] for e in mgr.list_esps()]
    assert 'listed_only' not in [e['name'] for e in c.get('/api/admin/esps').get_json()['esps']]
    assert not mgr.is_active_integration('listed_only')
    sid = c.post('/api/session/init', json={}).get_json()['session_id']
    r = c.post('/api/chat', json={'session_id': sid, 'message': 'hi', 'esp': 'listed_only',
                                  'product': 'loyalty'})
    assert r.status_code == 400 and 'Unknown integration' in r.get_json()['error']


# ---------- Postgres ----------

def run_postgres():
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
    try:
        if db.execute_query("SELECT current_schema()", fetch=True)[0][0] != TEST_SCHEMA:
            print("FAIL: not connected to the test schema; refusing to run")
            return 1
        db.initialize()
        return run_route_checks(db, True, 'postgres')
    finally:
        db.close()
        conn = psycopg2.connect(url)
        conn.autocommit = True
        conn.cursor().execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        conn.close()


if __name__ == '__main__':
    if sys.argv[1:] == ['postgres']:
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
