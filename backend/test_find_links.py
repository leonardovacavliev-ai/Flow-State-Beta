"""
"Find links" for one integration (C1.10): backend/link_finder.py,
backend/find_links_job.py and the routes that start and follow it.

    python3 backend/test_find_links.py     # or pytest

No network: pages come from the catalog import's fixtures through a fake
fetch, and a fake model stands in for Gemini. Runs on a throwaway SQLite
database with a fake signed-in admin.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='find-links-')
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(TMP, 'test.db')
os.environ['SESSION_PROVIDER'] = 'memory'
os.environ['USE_ASYNC_CRAWL'] = 'false'
os.environ['VECTOR_DB_PROVIDER'] = 'chromadb'
os.environ.pop('ADMIN_OWNER_EMAILS', None)
os.environ.pop('GEMINI_API_KEY', None)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))

import auth  # noqa: E402

USER = {'admin': True, 'email': 'leo@yotpo.com'}
auth.current_user_is_admin = lambda: USER['admin']
auth.current_user = lambda: {'email': USER['email']} if USER['admin'] else None

import app_mechanics as am  # noqa: E402
import catalog_import as ci  # noqa: E402
import esp_manager  # noqa: E402
import find_links_job as job  # noqa: E402
import link_finder as lf  # noqa: E402
import test_catalog_import as tci  # noqa: E402  (its fixtures and fake model)

MAILCHIMP_GUIDE = 'https://support.yotpo.com/docs/mailchimp-integration-guide-for-reviews'
# A real Reviews guide's page (its header says Reviews), served at that address
GUIDE_HTML = tci._read(os.path.join(HERE, 'fixtures', 'document360',
                                    'zendesk-integration-guide-for-reviews.html'))


def fixture_fetch(extra=None, log=None):
    """The import tests' fetch (catalog, detail pages, guides, help
    centres), plus `extra` pages; records every address asked for."""
    base = tci._detail_fetch()
    catalog = tci._read(os.path.join(tci.CATALOG, 'catalog.html'))
    extra = extra or {}

    def fetch(url):
        if log is not None:
            log.append(url)
        if url in extra:
            return extra[url]
        if url == ci.CATALOG_URL:
            return am.Page(200, url, catalog, 'text/html')
        return base(url)
    return fetch


def boot_db():
    from adapters.database.sqlite_adapter import SQLiteAdapter
    path = os.path.join(TMP, f'{uuid.uuid4().hex}.db')
    db = SQLiteAdapter(db_path=path)
    db.initialize()
    return db


def esp(db, name, status='listed', ptype='messaging', slugs=(), categories=(), display=None):
    esp_id = str(uuid.uuid4())
    db.execute_query(
        "INSERT INTO esps (id, name, display_name, status, platform_type, catalog_slugs, categories) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (esp_id, name, display or name.title(), status, ptype, json.dumps(list(slugs)),
         json.dumps(list(categories))))
    return esp_id


def proposals(db, name=None):
    sql = ("SELECT p.url, p.source, p.suggested_label, p.state, e.name, p.title, p.partner_function "
           "FROM document_proposals p JOIN esps e ON e.id = p.esp_id")
    rows = db.execute_query(sql + (" WHERE e.name = %s" if name else ""), (name,) if name else (),
                            fetch=True) or []
    return {r[0]: r for r in rows}


# ---------- pure ----------

def test_names_match_whole_words():
    names = lf._name_parts('Rule')
    assert lf.slug_names('integrating-yotpo-loyalty-with-rule', names)
    assert not lf.slug_names('setting-earning-rules', names)          # 'rules' is not Rule
    loop = lf._name_parts('Loop Returns')
    assert lf.slug_names('loop-returns-integration-guide', loop)
    assert lf.slug_names('loopreturns-integration-guide', loop)        # written as one word
    assert not lf.slug_names('returns-and-refunds', loop)              # one of its words alone
    sfmc = lf._name_parts('Salesforce Marketing Cloud')
    assert lf.slug_names('integrating-yotpo-loyalty-referrals-with-salesforce-marketing-cloud', sfmc)


def test_guides_by_name_from_the_sitemap():
    sitemap = ci.sitemap_entries(tci._read(os.path.join(tci.CATALOG, 'sitemap-en.xml')))
    found = lf.guides_by_name(sitemap, 'Mailchimp', 'mailchimp')
    assert MAILCHIMP_GUIDE in found and len(found) == 6
    # integration guides come first
    assert all('migrating' not in u for u in found[:3])
    assert lf.guides_by_name(sitemap, 'Mailchimp', limit=2) == found[:2]
    assert lf.guides_by_name(sitemap, 'Nobody Here') == []
    assert lf.guides_by_name(sitemap, '') == []


def test_website_is_checked():
    ok = job.clean_website
    assert ok(None) == (None, None) and ok('  ') == (None, None)
    assert ok('help.acme.io/en') == ('https://help.acme.io/en', None)
    assert ok('https://www.Acme.io/')[0] == 'https://www.acme.io/'
    for bad in ('http://localhost:5000', 'http://127.0.0.1/', 'ftp://acme.io', 'acme', 'http://[::1]/',
                'https://intranet.local/', 12, 'https://x.io/' + 'a' * 600):
        assert ok(bad)[1], bad
    # a help site is the help centre; a homepage only names the domain
    assert lf.website_links('https://help.acme.io/en') == ('https://help.acme.io/en', [])
    assert lf.website_links('https://www.acme.io/') == (None, ['https://www.acme.io/'])


def test_a_run_cut_short_reads_as_interrupted():
    assert job.run_view({'state': 'running'}, active=False)['state'] == 'interrupted'
    assert job.run_view({'state': 'running'}, active=True)['state'] == 'running'
    assert job.run_view({'state': 'done'}, active=False)['state'] == 'done'
    assert job.run_view(None, active=False) is None


# ---------- one run ----------

def test_hand_made_integration_finds_guides_by_name():
    """Not on yotpo.com: Yotpo guides that carry its name are suggested,
    their labels read from their headers; nothing else is written."""
    db = boot_db()
    esp(db, 'mailchimp', status='active', ptype='messaging')
    pages = {MAILCHIMP_GUIDE: am.Page(200, MAILCHIMP_GUIDE, GUIDE_HTML, 'text/html')}
    run = job.run_once(db, 'mailchimp', 'leo@yotpo.com', None, fixture_fetch(pages), chooser=None,
                       overrides={})
    assert run['state'] == 'done', run
    assert run['model_skipped'] is True and run['by_name'] is True
    found = proposals(db, 'mailchimp')
    assert MAILCHIMP_GUIDE in found and found[MAILCHIMP_GUIDE][1] == 'catalog'
    assert found[MAILCHIMP_GUIDE][2] == 'reviews'           # from the guide's own header
    assert all(r[3] == 'open' for r in found.values())
    # the other five guides 404 in the fixtures: reported, not suggested
    assert len(found) == 1 and run['unreachable'] == 5
    assert run['counts']['yotpo_guides'] == 1
    # never a document, a label or a change to the integration itself
    assert not db.execute_query("SELECT 1 FROM esp_documents", fetch=True)
    row = job.load_integration(db, 'mailchimp')
    assert row['status'] == 'active' and row['catalog_slugs'] == []
    # without a model, the import's notes are left alone
    assert job._setting(db, job.MECHANICS_KEY) is None
    assert job.last_run(db, 'mailchimp')['state'] == 'done'


def test_second_run_adds_nothing_and_rejections_stay():
    db = boot_db()
    esp_id = esp(db, 'mailchimp', ptype='messaging')
    pages = {MAILCHIMP_GUIDE: am.Page(200, MAILCHIMP_GUIDE, GUIDE_HTML, 'text/html')}
    job.run_once(db, 'mailchimp', 'a', None, fixture_fetch(pages), None, overrides={})
    db.execute_query("UPDATE document_proposals SET state = 'rejected'")
    again = job.run_once(db, 'mailchimp', 'a', None, fixture_fetch(pages), None, overrides={})
    assert again['added'] == [] and again['already'] == [
        {'url': MAILCHIMP_GUIDE, 'why': 'rejected', 'where': 'Mailchimp'}]
    assert proposals(db)[MAILCHIMP_GUIDE][3] == 'rejected'
    # a link that is already a document is skipped too
    db.execute_query("DELETE FROM document_proposals")
    db.execute_query("INSERT INTO esp_documents (id, esp_id, url, filename, product) "
                     "VALUES (%s, %s, %s, 'x', 'reviews')", (str(uuid.uuid4()), esp_id, MAILCHIMP_GUIDE))
    third = job.run_once(db, 'mailchimp', 'a', None, fixture_fetch(pages), None, overrides={})
    assert third['added'] == [] and third['already'][0]['why'] == 'document'
    assert not proposals(db)


def test_catalog_integration_proposes_what_the_import_would():
    """Created by hand under the import's name, Recharge is found on
    yotpo.com and gets the import's own suggestions, help articles included."""
    import import_catalog as ic
    db = boot_db()
    esp(db, 'recharge', ptype='storefront')
    fetched = []
    run = job.run_once(db, 'recharge', 'a', None, fixture_fetch(log=fetched), tci.PlanModel(),
                       overrides={})
    assert run['state'] == 'done', run
    assert run['matched_on_yotpo_com'] == ['recharge'] and ci.CATALOG_URL in fetched
    view = {'integrations': {}, 'documents': {}, 'proposals': {}, 'snapshot': None}
    plan = ic.build_plan(tci._read(os.path.join(tci.CATALOG, 'catalog.html')), view, tci._detail_fetch(),
                         only=['recharge'], log=lambda m: None, chooser=tci.PlanModel(), overrides={})
    expected = [(p['url'], p['source'], p['suggested_label'], p['note']) for p in plan['proposals']]
    got = [(p['url'], p['source'], p['suggested_label'], p['note']) for p in run['added']]
    assert got == expected and any(s == 'mechanics' for _, s, _, _ in got)
    mech = proposals(db, 'recharge')
    article = next(r for r in mech.values() if r[1] == 'mechanics')
    assert article[2] == 'shared' and article[5] and article[6]      # title and function kept
    # the model ran: this integration's notes are stored as the import stores them
    notes = job._setting(db, job.MECHANICS_KEY)
    assert notes['recharge']['accepted'] == len([g for g in got if g[1] == 'mechanics'])
    assert notes['recharge'] == ic.mechanics_notes(plan)['recharge']
    assert run['usage'] == tci.PlanModel.usage


def test_recorded_yotpo_pages_skip_the_catalog_page():
    db = boot_db()
    esp(db, 'recharge', ptype='storefront', slugs=['recharge'],
        categories=['subscription-recurring-billing'])
    fetched = []
    run = job.run_once(db, 'recharge', 'a', None, fixture_fetch(log=fetched), None, overrides={})
    assert ci.CATALOG_URL not in fetched and run['matched_on_yotpo_com'] is None
    assert any(p['url'].endswith('recharge-integration-guide-for-yotpo-loyalty-referrals')
               for p in run['added'])


def test_the_kind_reaches_the_model_and_the_website_the_search():
    """No yotpo.com page and no categories: the model is told its kind of
    platform; the website an admin gave is where its help centre is looked for."""
    db = boot_db()
    esp(db, 'acme', ptype='service', display='Acme Desk')
    seen = {}

    class Model(tci.PlanModel):
        def extract_functions(self, app, categories, sources):
            seen['categories'] = categories
            return []
    home = am.Page(200, 'https://www.acmedesk.io/', '<a href="https://help.acmedesk.io/en">Help Center</a>')
    help_home = am.Page(200, 'https://help.acmedesk.io/en', '<title>Acme Desk Help</title>')
    fetch = fixture_fetch({'https://www.acmedesk.io/': home, 'https://help.acmedesk.io/en': help_home})
    run = job.run_once(db, 'acme', 'a', 'https://www.acmedesk.io/', fetch, Model(), overrides={})
    assert run['state'] == 'done', run
    assert seen['categories'] == ['kind of platform: Customer service']
    assert run['help_centre'] == 'https://help.acmedesk.io/en' and run['website'] == 'https://www.acmedesk.io/'
    assert run['added'] == []


def test_a_failure_is_recorded():
    db = boot_db()
    esp(db, 'mailchimp')

    def broken(url):
        raise RuntimeError('boom')
    run = job.run_once(db, 'mailchimp', 'a', None, broken, None, overrides={})
    assert run['state'] == 'failed' and 'boom' in run['error']
    assert job.last_run(db, 'mailchimp')['state'] == 'failed'
    run = job.run_once(db, 'nobody', 'a', None, fixture_fetch(), None, overrides={})
    assert run['state'] == 'failed' and 'removed' in run['error']


# ---------- routes ----------

def make_app(db):
    """The admin integrations routes and the create route on `db`."""
    from flask import Flask
    from adapters.database import db_manager
    import admin_integrations_routes as air
    from app_admin_esp_routes import register_esp_admin_routes
    db_manager.get_database_adapter = lambda: db
    mgr = esp_manager.ESPManager()
    mgr.db = db
    esp_manager._esp_manager = mgr
    app = Flask(f'find_links_{uuid.uuid4().hex}')
    air.register_admin_integrations_routes(app, use_async_crawl=False)
    register_esp_admin_routes(app, TMP, tci_vectors())
    return app


def tci_vectors():
    class FakeVectors:
        def delete_by_url(self, url, esp):
            pass

        def add_document(self, text, metadata):
            return 1
    return FakeVectors()


def wait_for(c, name, seconds=10):
    end = time.time() + seconds
    while time.time() < end:
        run = c.get(f'/api/admin/integrations/{name}/find-links').get_json()['run']
        if run and run['state'] != 'running':
            return run
        time.sleep(0.05)
    raise AssertionError('the run did not finish')


def test_routes_start_and_follow_a_run():
    db = boot_db()
    esp(db, 'mailchimp', status='active')
    esp(db, 'old_partner', status='archived', ptype='data')
    gate = threading.Event()
    pages = {MAILCHIMP_GUIDE: am.Page(200, MAILCHIMP_GUIDE, GUIDE_HTML, 'text/html')}
    plain = fixture_fetch(pages)

    def slow(url):
        gate.wait(5)
        return plain(url)
    app = make_app(db)
    app.config['FIND_LINKS_FETCH'] = lambda: slow
    app.config['FIND_LINKS_CHOOSER'] = lambda: None
    c = app.test_client()
    try:
        as_user(owners='owner@yotpo.com')                     # an editor may run it
        r = c.post('/api/admin/integrations/mailchimp/find-links', json={'website': 'mailchimp.com'})
        assert r.status_code == 202 and r.get_json()['run']['state'] == 'running'
        assert r.get_json()['run']['requested_by'] == 'leo@yotpo.com'
        again = c.post('/api/admin/integrations/mailchimp/find-links', json={})
        assert again.status_code == 409 and 'Already' in again.get_json()['error']
        detail = c.get('/api/admin/integrations/mailchimp').get_json()['integration']
        assert detail['find_links']['state'] == 'running'
        gate.set()
        run = wait_for(c, 'mailchimp')
        assert run['state'] == 'done' and run['website'] == 'https://mailchimp.com'
        assert MAILCHIMP_GUIDE in proposals(db, 'mailchimp')
        # without "website", the last one is used again; "" clears it
        assert c.post('/api/admin/integrations/mailchimp/find-links', json={}).status_code == 202
        assert wait_for(c, 'mailchimp')['website'] == 'https://mailchimp.com'
        assert c.post('/api/admin/integrations/mailchimp/find-links', json={'website': ''}).status_code == 202
        assert wait_for(c, 'mailchimp')['website'] is None
        for path, body, code in (('nobody', {}, 404), ('global', {}, 404), ('old_partner', {}, 409),
                                 ('mailchimp', {'website': 'http://localhost/'}, 400)):
            r = c.post(f'/api/admin/integrations/{path}/find-links', json=body)
            assert r.status_code == code, (path, r.get_json())
        assert c.get('/api/admin/integrations/nobody/find-links').status_code == 404
        as_user(admin=False)
        assert c.post('/api/admin/integrations/mailchimp/find-links', json={}).status_code == 403
        assert c.get('/api/admin/integrations/mailchimp/find-links').status_code == 403
    finally:
        gate.set()
        as_user()


def test_at_most_two_at_once():
    db = boot_db()
    for n in ('one', 'two', 'three'):
        esp(db, n)
    gate = threading.Event()
    app = make_app(db)
    app.config['FIND_LINKS_FETCH'] = lambda: (lambda url: gate.wait(5) and None)
    app.config['FIND_LINKS_CHOOSER'] = lambda: None
    c = app.test_client()
    try:
        assert c.post('/api/admin/integrations/one/find-links', json={}).status_code == 202
        assert c.post('/api/admin/integrations/two/find-links', json={}).status_code == 202
        r = c.post('/api/admin/integrations/three/find-links', json={})
        assert r.status_code == 409 and 'running already' in r.get_json()['error']
    finally:
        gate.set()
    for n in ('one', 'two'):
        wait_for(c, n)


def test_create_starts_find_links():
    """The Add integration dialog sends find_links: the search starts with
    the integration; a bad website stops before anything is created."""
    db = boot_db()
    pages = {MAILCHIMP_GUIDE: am.Page(200, MAILCHIMP_GUIDE, GUIDE_HTML, 'text/html')}
    app = make_app(db)
    app.config['FIND_LINKS_FETCH'] = lambda: fixture_fetch(pages)
    app.config['FIND_LINKS_CHOOSER'] = lambda: None
    c = app.test_client()
    as_user(owners=None)
    try:
        r = c.post('/api/admin/esp/create', json={'name': 'Mailchimp', 'platform_type': 'messaging',
                                                  'find_links': True, 'website': 'localhost'})
        assert r.status_code == 400 and not job.load_integration(db, 'mailchimp')
        r = c.post('/api/admin/esp/create', json={'name': 'Mailchimp', 'platform_type': 'messaging',
                                                  'find_links': True})
        body = r.get_json()
        assert r.status_code == 200 and body['find_links']['state'] == 'running', body
        assert wait_for(c, 'mailchimp')['state'] == 'done'
        assert MAILCHIMP_GUIDE in proposals(db, 'mailchimp')
        # without find_links, nothing starts
        r = c.post('/api/admin/esp/create', json={'name': 'Quiet One', 'platform_type': 'data'})
        assert r.status_code == 200 and 'find_links' not in r.get_json()
        assert job.last_run(db, 'quiet_one') is None
    finally:
        for name in ('mailchimp', 'quiet_one'):
            try:
                os.rmdir(os.path.join(TMP, 'docs', name))
            except OSError:
                pass


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
