"""
The catalog import (C1.2): backend/catalog_import.py, backend/app_overview.py
and scripts/import_catalog.py.

    python3 backend/test_catalog_import.py     # or pytest

No network: pages come from fixtures/catalog/ and fixtures/app_overview/
(saved from the live sites on 2026-10-14) through a fake fetch. The --apply
test writes to a throwaway SQLite database.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='catalog-import-')
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(TMP, 'test.db')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))

import app_overview as ao  # noqa: E402
import catalog_import as ci  # noqa: E402

CATALOG = os.path.join(HERE, 'fixtures', 'catalog')
OVERVIEW = os.path.join(HERE, 'fixtures', 'app_overview')


def _read(path):
    with open(path) as f:
        return f.read()


def _cards():
    return ci.parse_catalog(_read(os.path.join(CATALOG, 'catalog.html')))


def _overview_fetch():
    """fetch() over the recorded help-centre pages; anything else is offline."""
    manifest = json.loads(_read(os.path.join(OVERVIEW, 'manifest.json')))

    def fetch(url):
        entry = manifest['pages'].get(url)
        if not entry:
            return None
        return ao.Page(entry['status'], entry['url'], _read(os.path.join(OVERVIEW, entry['file'])),
                       entry['content_type'])
    return fetch, manifest['expected']


# ---------- catalog page ----------

def test_parse_catalog():
    cards = {c.slug: c for c in _cards()}
    # The "Featured" strip repeats Attentive: one card per detail page
    assert len(cards) == len(_cards()) == 17
    att = cards['attentive']
    assert att.url == 'https://www.yotpo.com/integrations/attentive'
    assert att.categories == ['email-marketing', 'sms-marketing']
    assert att.products == ['loyalty', 'reviews']
    assert att.title == 'Attentive' and att.description.startswith('Yotpo and Attentive')
    # Dixa is tagged `reviews`, not `reviews-ugc`: both are Reviews
    assert 'reviews' in cards['dixa'].products
    assert cards['gorgias'].categories == ['help-desk-crm', 'onsite-chatbots']


def test_guard():
    cards = _cards()
    assert ci.guard(cards, None) is None
    assert ci.guard(cards, {'cards': 18}) is None             # 17 of 18 is above 90%
    assert 'fewer than 90%' in ci.guard(cards, {'cards': 20})
    assert ci.guard([], None) == 'the catalog page has no integration cards'
    no_cats = [ci.Card(c.slug, c.url, c.title, '', c.products, []) for c in cards]
    assert ci.guard(no_cats, None) == 'the catalog cards have no categories'


def test_grouping():
    existing = ['klaviyo', 'attentive', 'brevo_pushowl', 'global', 'other_webhook']
    integ, clashes = ci.group_cards(_cards(), existing)
    by = {i.name: i for i in integ}
    assert clashes == []
    # Second cards join the first: gorgias + gorgias-loyalty
    assert by['gorgias'].slugs == ['gorgias', 'gorgias-loyalty']
    assert by['gorgias'].display_name == 'Gorgias'
    assert by['gorgias'].platform_type == 'service' and not by['gorgias'].existing
    # KNOWN_MATCHES maps live rows whose name is not the slug
    assert set(by['brevo_pushowl'].slugs) == {'brevo-pushowl', 'brevo-pushowl-loyalty'}
    assert by['brevo_pushowl'].existing and by['brevo_pushowl'].matched_by == 'known'
    assert by['klaviyo'].existing and 'klaviyo-customer-hub' not in by['klaviyo'].slugs
    assert by['klaviyo_customer_hub'].platform_type == 'messaging'
    assert set(by['shopify'].slugs) == {'shopify', 'shopify-loyalty'}
    assert by['reamaze'].slugs == ['reamaze-2']
    # Help desk and chatbots are both service: no conflict to settle
    assert by['gorgias'].type_conflict == []
    assert by["klaviyo_customer_hub"].type_conflict == ["messaging", "storefront"]
    assert len(integ) == 12


def test_name_clash_is_listed():
    """'rule' is the known integration for the slug 'rule-io'; a new card
    'rule' must not be merged into it silently."""
    cards = [ci.Card('rule-io', 'u', 'Rule', '', ['loyalty'], ['email-marketing']),
             ci.Card('rule', 'u', 'Rule', '', ['reviews'], ['other'])]
    integ, clashes = ci.group_cards(cards, ['rule'], known={'rule': ['rule-io']})
    assert [i.slugs for i in integ] == [['rule-io']]
    assert len(clashes) == 1 and clashes[0].startswith('rule: ')


# ---------- detail pages ----------

def test_detail_links_yotpo_guide():
    d = ci.detail_links(_read(os.path.join(CATALOG, 'detail-recharge.html')))
    assert d.yotpo == ['https://support.yotpo.com/docs/recharge-integration-guide-for-yotpo-loyalty-referrals']
    assert d.partner_docs == []
    # The site's own header/footer links (Help Center, API reference) are not the integration's
    assert not any('core-api.yotpo.com' in u or 'status.yotpo.com' in u for u in d.partner_other)


def test_detail_links_partner_only():
    d = ci.detail_links(_read(os.path.join(CATALOG, 'detail-dixa.html')))
    assert d.yotpo == []
    assert d.partner_docs == ['https://support.dixa.help/en/articles/1879-yotpo-integration']


def test_detail_links_nothing():
    d = ci.detail_links(_read(os.path.join(CATALOG, 'detail-bazaarvoice.html')))
    assert d.yotpo == [] and d.partner_docs == []


def test_trailing_space_href_is_normalised():
    """shopify-loyalty links its guide as '…online-store-20 ' (a real case)."""
    d = ci.detail_links(_read(os.path.join(CATALOG, 'detail-shopify-loyalty.html')))
    assert d.yotpo == ['https://support.yotpo.com/docs/setting-up-loyalty-referrals-on-shopify-online-store-20']


def test_clean_link():
    assert ci.clean_link(' http://support.yotpo.com/docs/a/?utm_source=x#top ') == 'https://support.yotpo.com/docs/a'
    assert ci.clean_link('https://Help.Example.com/a?id=2&utm_medium=y') == 'https://help.example.com/a?id=2'


# ---------- renamed guides ----------

def test_renamed_guide_lookup():
    sitemap = ci.sitemap_entries(_read(os.path.join(CATALOG, 'sitemap-en.xml')))
    assert len(sitemap) == 30
    dead = 'https://support.yotpo.com/docs/gorgias-integration-guide-for-reviews'
    assert ci.find_renamed(dead, sitemap) == [
        'https://support.yotpo.com/docs/gorgias-integration-guide-for-reviews-and-loyalty-referrals']
    assert ci.find_renamed('https://support.yotpo.com/docs/yieldify-integration-guide', sitemap) == []
    # One stem word is not enough to call it the same guide
    assert ci.find_renamed('https://support.yotpo.com/docs/gorgias', sitemap) == []


def test_renamed_guide_needs_the_partner_name():
    """'integrating-yotpo-loyalty-referrals-with-…' starts a dozen partners'
    guides: the partner's name decides (a real case, Optimove, 2026-10-14)."""
    live = ['https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-klaviyo',
            'https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-cordial',
            'https://support.yotpo.com/docs/optimove-integration-guide-for-yotpo-loyalty-referrals',
            'https://support.yotpo.com/docs/builderio-integration-guide',
            'https://support.yotpo.com/docs/rewards-page-builder']
    dead = 'https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-optimove'
    assert len(ci.find_renamed(dead, live)) == 2  # without the name: ambiguous
    assert ci.find_renamed(dead, live, ['optimove']) == [live[2]]
    assert ci.find_renamed('https://support.yotpo.com/docs/builder-integration-guide', live,
                           ao.name_tokens('Builder.io', 'builder_io')) == [live[3]]


def test_partner_page_about_yotpo_is_documentation():
    assert ci.is_partner_yotpo_page('https://www.addglow.com/yotpo-integration')
    assert ci.is_partner_yotpo_page('https://www.harborloyalty.com/yotpo-setup')
    assert not ci.is_partner_yotpo_page('https://api.rush.app/auth/yotpo/install')
    assert not ci.is_partner_yotpo_page('https://www.attentive.com/blog/attentive-named-yotpos-preferred-sms-and-email-partner')
    assert not ci.is_partner_yotpo_page('https://www.addglow.com/')


def test_help_centre_from_the_homepage():
    """Only the partner's homepage is known: its "Help Center" link says where."""
    home = ('<a href="/pricing">Pricing</a><a href="https://help.acme.io/en">Help Center</a>'
            '<a href="https://docs.other.com/">Docs</a>')
    pages = {'https://www.acme.io/': ao.Page(200, 'https://www.acme.io/', home)}
    root, via, _ = ao.find_help_centre(ao.name_tokens('Acme'), ['https://www.acme.io/yotpo-integration'], [],
                                       fetch=pages.get)
    assert (root, via) == ('https://help.acme.io/en', 'homepage')


# ---------- partner app overviews ----------

def test_overview_scoring():
    assert ao.score_link('Getting started with Dixa', '', ['dixa'])[0] >= 5
    assert ao.score_link('Team overview', '', ['dixa'])[0] == 3
    assert ao.score_link('Yotpo integration overview', '', ['dixa'])[0] < 0
    assert ao.score_link('API overview', '', [])[0] < 0
    assert ao.score_link('Create a segment', '', [])[0] == 0
    assert ao.score_link('', 'https://x.help/en/articles/12-getting-started-with-x', ['x'])[0] > 0


def test_help_centre_root():
    assert ao.help_centre_root('https://x.zendesk.com/hc/en-us/articles/1-a') == 'https://x.zendesk.com/hc/en-us'
    assert ao.help_centre_root('https://help.x.com/en/articles/2-b') == 'https://help.x.com/en'
    assert ao.help_centre_root('https://docs.gorgias.com/en-US/foo-1') == 'https://docs.gorgias.com/en-US'
    assert ao.help_centre_root('https://mailchimp.com/help/connect-disconnect-yotpo') == 'https://mailchimp.com/help'
    assert ao.help_centre_root('https://www.braze.com/docs/partners/x/yotpo') == 'https://www.braze.com/docs'


def test_help_centre_must_carry_the_apps_name():
    """A Shopify link inside the Gorgias guide is not Gorgias's help centre."""
    tokens = ao.name_tokens('Gorgias', 'gorgias')
    root, via, _ = ao.find_help_centre(tokens, [], ['https://help.shopify.com/en/manual/apps'])
    assert root is None
    root, via, _ = ao.find_help_centre(tokens, [], ['https://help.shopify.com/en/manual/apps',
                                                    'https://docs.gorgias.com/en-US/some-guide-1'])
    assert (root, via) == ('https://docs.gorgias.com/en-US', 'guide')
    # An admin override wins
    root, via, _ = ao.find_help_centre(tokens, ['https://docs.gorgias.com/en-US/x-1'], [],
                                       override='https://help.example.com')
    assert (root, via) == ('https://help.example.com', 'override')


def test_no_link_no_guess():
    """Names are never turned into domains: 'Target' would find target.com."""
    root, via, problem = ao.find_help_centre(ao.name_tokens('Target'), [], [], fetch=lambda u: None)
    assert root is None and 'help_centres.json' in problem


def test_overview_discovery_on_saved_help_centres():
    fetch, expected = _overview_fetch()
    cases = {
        'gorgias': (['Gorgias', 'gorgias'], [], ['https://docs.gorgias.com/en-US/articles/some-guide-123']),
        'attentive': (['Attentive', 'attentive'],
                      ['https://help.attentivemobile.com/hc/en-us/articles/41245602462740-Yotpo-Reviews'], []),
        'rebuy': (['Rebuy', 'rebuy'],
                  ['https://help.rebuyengine.com/en/articles/6399623-adding-yotpo-product-reviews-to-rebuy-widgets'], []),
        'dixa': (['Dixa', 'dixa'], ['https://support.dixa.help/en/articles/1879-yotpo-integration'], []),
    }
    for name, (names, catalog_links, guide_links) in cases.items():
        o = ao.discover(names, catalog_links, guide_links, fetch, limit=3)
        assert o.help_centre == expected[name]['help_centre'], name
        assert o.method == expected[name]['method'], name
        assert [c.url for c in o.candidates] == expected[name]['picked'], name
    # And what they are, read by a human on 2026-10-14
    o = ao.discover(*cases['gorgias'][:3], fetch, limit=3)
    assert o.method == 'pages'  # a home page section opened, its articles taken
    assert o.candidates[0].url == 'https://docs.gorgias.com/en-US/how-to-use-gorgias-a-quick-start-guide-5705504'
    o = ao.discover(*cases['attentive'][:3], fetch, limit=3)
    assert o.method == 'zendesk-api'
    assert o.candidates[0].title == '(1/8) Welcome to Attentive'
    # The API answered from help.attentive.com: links stay on the real host
    assert all(c.url.startswith('https://help.attentive.com/hc/en-us/articles/') for c in o.candidates)
    o = ao.discover(*cases['dixa'][:3], fetch, limit=3)
    assert 'sitemap' in o.method  # its pages are built in the browser
    assert o.candidates[0].title.lower() == 'an introduction to dixa messenger'


def test_overview_never_proposes_the_yotpo_article():
    fetch, _ = _overview_fetch()
    o = ao.discover(['Dixa', 'dixa'], ['https://support.dixa.help/en/articles/1879-yotpo-integration'], [],
                    fetch, limit=10)
    assert all('yotpo' not in c.url for c in o.candidates)


# ---------- the plan and --apply ----------

def _detail_fetch():
    """Detail pages from fixtures; Yotpo guides from fixtures/document360."""
    d360 = os.path.join(HERE, 'fixtures', 'document360')
    sitemap = _read(os.path.join(CATALOG, 'sitemap-en.xml'))
    overview_fetch, _ = _overview_fetch()

    def fetch(url):
        if url == 'https://support.yotpo.com/sitemap-en.xml':
            return ao.Page(200, url, sitemap, 'application/xml')
        if url.startswith('https://www.yotpo.com/integrations/'):
            slug = url.rstrip('/').split('/')[-1]
            path = os.path.join(CATALOG, f'detail-{slug}.html')
            return ao.Page(200, url, _read(path), 'text/html') if os.path.exists(path) else ao.Page(404, url, '')
        if url.startswith('https://support.yotpo.com/docs/'):
            path = os.path.join(d360, url.rsplit('/', 1)[-1] + '.html')
            return ao.Page(200, url, _read(path), 'text/html') if os.path.exists(path) else ao.Page(404, url, '')
        return overview_fetch(url)
    return fetch


def _boot_db():
    from adapters.database.sqlite_adapter import SQLiteAdapter
    db = SQLiteAdapter(db_path=os.environ['SQLITE_DB_PATH'])
    db.initialize()
    import uuid
    for name in ('klaviyo', 'brevo_pushowl', 'global'):
        db.execute_query("INSERT INTO esps (id, name, display_name, status, platform_type) "
                         "VALUES (%s, %s, %s, 'active', %s)",
                         (str(uuid.uuid4()), name, name.title(), None if name == 'global' else 'messaging'))
    return db


def test_plan_and_apply_is_idempotent():
    import import_catalog as ic
    db = _boot_db()
    store = ic.Store(write=False)
    view = {'integrations': store.integrations(), 'documents': store.document_urls(),
            'proposals': store.proposal_urls(), 'snapshot': store.snapshot()}
    store.close()
    html = _read(os.path.join(CATALOG, 'catalog.html'))
    plan = ic.build_plan(html, view, _detail_fetch(), only=['recharge', 'dixa', 'shopify', 'bazaarvoice'],
                         log=lambda m: None)
    assert plan['guard'] is None
    created = {r['name']: r for r in plan['create']}
    assert created['recharge']['platform_type'] == 'storefront'
    props = {p['url']: p for p in plan['proposals']}
    guide = props['https://support.yotpo.com/docs/recharge-integration-guide-for-yotpo-loyalty-referrals']
    assert guide['source'] == 'catalog' and guide['suggested_label'] == 'loyalty'
    assert props['https://support.dixa.help/en/articles/1879-yotpo-integration']['suggested_label'] is None
    overviews = [p for p in plan['proposals'] if p['source'] == 'overview']
    assert overviews and all(p['esp'] == 'dixa' and p['suggested_label'] == 'shared' for p in overviews)
    assert 'bazaarvoice' in plan['nothing']
    assert ic.render_report(plan).startswith('# Catalog import: dry run')

    store = ic.Store(write=True)
    try:
        ic.apply_plan(store, plan)
        raise AssertionError('a plan made with --only was applied')
    except SystemExit as e:
        assert '--only' in str(e)
    plan['only'] = None  # as if the dry run had covered the whole catalog
    first = ic.apply_plan(store, plan)
    second = ic.apply_plan(store, plan)
    store.close()
    assert first['created'] == len(plan['create']) and first['proposals'] == len(plan['proposals'])
    assert second['created'] == 0 and second['proposals'] == 0

    rows = db.execute_query("SELECT name, status, platform_type, catalog_slugs FROM esps "
                            "WHERE name = 'recharge'", fetch=True)
    assert rows[0][1] == 'listed' and rows[0][2] == 'storefront' and json.loads(rows[0][3]) == ['recharge']
    # A listed row never reaches chat or older code (I4)
    from esp_manager import get_esp_manager
    assert 'recharge' not in [e['name'] for e in get_esp_manager().list_esps()]
    n = db.execute_query("SELECT COUNT(*) FROM document_proposals WHERE state = 'open'", fetch=True)[0][0]
    assert n == len(plan['proposals'])
    snap = db.execute_query("SELECT value FROM app_settings WHERE key = %s", (ci.SNAPSHOT_KEY,), fetch=True)
    assert json.loads(snap[0][0])['cards'] == 17


def test_apply_never_overwrites_a_set_type_or_status():
    import import_catalog as ic
    store = ic.Store(write=False)
    current = store.integrations()
    store.close()
    row = {'catalog_slugs': ['klaviyo'], 'categories': ['email-marketing'], 'products': ['loyalty'],
           'catalog_description': 'd', 'platform_type': 'data'}
    changes = ic._catalog_changes(current['klaviyo'], row)
    assert 'platform_type' not in changes and 'catalog_slugs' in changes


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
