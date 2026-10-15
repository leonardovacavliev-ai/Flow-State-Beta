#!/usr/bin/env python3
"""
Turn yotpo.com/integrations into integrations and document proposals.

    python3 scripts/import_catalog.py --plan /tmp/catalog_plan.json --report /tmp/catalog.md
        # dry run: reads the catalog, the detail pages, the guides and the
        # partners' help centres; writes nothing to the database. Saves the
        # plan it would apply, and the report for a human to read.
    python3 scripts/import_catalog.py --apply --plan /tmp/catalog_plan.json
        # write that plan (production: Leo, checkpoint C1.9)

Options:
    --html FILE         parse a saved catalog page instead of fetching it
    --cache DIR         keep every fetched page in DIR; a re-run reads from it
    --no-mechanics      skip the partners' own help-centre articles
    --ai-model NAME     the Gemini model for them (default: the app's,
                        gemini-flash-latest; needs GEMINI_API_KEY)
    --only a,b          only these integrations (esps.name), for trying things

What it proposes, per integration (ALL_INTEGRATIONS_UPDATE.md §4.3):
  - each Yotpo guide its detail page links (source `catalog`), label pre-filled
    from the guide's own header when it names one product;
  - a guide that 404s, re-found in the help centre's sitemap under a renamed
    slug (note "renamed from …"); one with no match is reported as gone;
  - each documentation-like partner page the detail page links (`catalog`);
  - the partner's own articles on the functions the integration touches,
    e.g. Klaviyo flow triggers, Recharge subscription discount codes (source
    `mechanics`, label pre-filled `shared`; Leo, 2026-10-14). A model reads
    the Yotpo guides and the partner's Yotpo pages, lists those functions,
    and confirms each article the code found by reading it
    (backend/app_mechanics.py, backend/mechanics_ai.py). Help centres that
    block automated reading are listed for a person instead.
Every proposal waits for an admin: a person approves each integration's final
list in the admin (C1.4). Nothing is crawled or labelled here.

--apply writes the saved plan, never a fresh fetch, so what is written is what
the report showed. It creates new integrations as `listed` (invisible to chat
and to older code, I4), updates catalog fields on existing ones (never
status, name, display name or an already-set type), inserts proposals
(skipping URLs that are already documents or proposals in any state:
rejections are remembered), stores the catalog snapshot, and deletes nothing.
It also stores what the admin's Proposals tab shows: each mechanics
article's title, function and reason on its proposal, the per-integration
notes (functions found, help centre, why nothing was found) and the report.
Safe to run twice: the second run changes nothing.

The guard: fewer than 90% of the last import's cards, or no categories ->
nothing is planned or written, exit 2.

Database: DATABASE_PROVIDER=sqlite uses SQLITE_DB_PATH; otherwise Postgres at
DATABASE_URL (environment, then .env). A dry run opens a read-only session.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import uuid
from dataclasses import asdict
from typing import Dict, List, Optional
from urllib.parse import urlsplit

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'backend'))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))

import app_mechanics  # noqa: E402
import catalog_import as ci  # noqa: E402
import doc_header  # noqa: E402
import mechanics_ai  # noqa: E402

SITEMAP_URL = 'https://support.yotpo.com/sitemap-en.xml'
OVERRIDES_PATH = os.path.join(BASE, 'scripts', 'help_centres.json')
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
PLAN_VERSION = 1
MAX_SECONDS = 20
MAX_BYTES = 5_000_000


# ---------- network ----------

class Fetcher:
    """GET with the crawler's headers, one request per second per host, one
    retry on a network error, and an optional on-disk cache."""

    def __init__(self, cache_dir: Optional[str] = None, delay: float = 1.0):
        import requests
        self.session = requests.Session()
        self.session.headers['User-Agent'] = USER_AGENT
        self.cache_dir = cache_dir
        self.delay = delay
        self.last_at: Dict[str, float] = {}
        self.requests = 0
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def _cache_path(self, url):
        return os.path.join(self.cache_dir, hashlib.sha1(url.encode()).hexdigest() + '.json')

    def _get(self, url: str) -> app_mechanics.Page:
        """One GET, at most MAX_BYTES and MAX_SECONDS in all: a server that
        sends a byte at a time never trips the per-read timeout."""
        started = time.time()
        with self.session.get(url, timeout=10, stream=True) as r:
            body = b''
            for chunk in r.iter_content(65536):
                body += chunk
                if len(body) > MAX_BYTES or time.time() - started > MAX_SECONDS:
                    raise TimeoutError(f'gave up after {MAX_SECONDS}s or {MAX_BYTES} bytes')
            r._content = body
            return app_mechanics.Page(r.status_code, r.url, r.text, r.headers.get('content-type', ''))

    def __call__(self, url: str) -> Optional[app_mechanics.Page]:
        if self.cache_dir and os.path.exists(self._cache_path(url)):
            with open(self._cache_path(url)) as f:
                page = app_mechanics.Page(**json.load(f))
            return page if page.status else None  # 0: unreachable when cached
        page = None
        for attempt in range(2):
            host = urlsplit(url).hostname or ''
            wait = self.delay - (time.time() - self.last_at.get(host, 0))
            if wait > 0:
                time.sleep(wait)
            self.last_at[host] = time.time()
            self.requests += 1
            try:
                page = self._get(url)
                break
            except Exception as e:  # network: retry once, then report as unreachable
                print(f'  [fetch] {url}: {type(e).__name__}', file=sys.stderr)
        if self.cache_dir:
            with open(self._cache_path(url), 'w') as f:
                json.dump(asdict(page or app_mechanics.Page(0, url, '')), f)
        return page


# ---------- database ----------

class Store:
    """The few reads and writes the import needs, on Postgres or SQLite."""

    def __init__(self, write: bool):
        self.provider = os.environ.get('DATABASE_PROVIDER', 'postgres').lower()
        if self.provider == 'sqlite':
            path = os.environ.get('SQLITE_DB_PATH', os.path.join(BASE, 'backend', 'analytics.db'))
            if write:
                self.conn = sqlite3.connect(path)
            else:
                self.conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
            self.ph = '?'
        else:
            import psycopg2
            url = os.environ.get('DATABASE_URL')
            if not url:
                raise SystemExit('DATABASE_URL is not set')
            self.conn = psycopg2.connect(url)
            if not write:
                self.conn.set_session(readonly=True)
            self.ph = '%s'

    def q(self, sql: str, params=(), fetch=True):
        cur = self.conn.cursor()
        cur.execute(sql.replace('%s', self.ph), params)
        return cur.fetchall() if fetch else None

    def integrations(self) -> Dict[str, Dict]:
        rows = self.q("SELECT id, name, status, platform_type, catalog_slugs, categories, products, "
                      "catalog_description FROM esps")
        out = {}
        for r in rows:
            out[r[1]] = {'id': str(r[0]), 'status': r[2], 'platform_type': r[3],
                         'catalog_slugs': _list(r[4]), 'categories': _list(r[5]),
                         'products': _list(r[6]), 'catalog_description': r[7]}
        return out

    def document_urls(self) -> Dict[str, str]:
        rows = self.q("SELECT d.url, e.name FROM esp_documents d JOIN esps e ON e.id = d.esp_id")
        return {r[0]: r[1] for r in rows}

    def proposal_urls(self) -> Dict[str, str]:
        return {r[0]: r[1] for r in self.q("SELECT url, state FROM document_proposals")}

    def snapshot(self) -> Optional[Dict]:
        return self.setting(ci.SNAPSHOT_KEY)

    def setting(self, key) -> Optional[Dict]:
        rows = self.q("SELECT value FROM app_settings WHERE key = %s", (key,))
        if not rows or not rows[0][0]:
            return None
        try:
            return json.loads(rows[0][0])
        except ValueError:
            return None

    def close(self):
        self.conn.close()


def _list(value):
    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []


def _overrides() -> Dict[str, Optional[str]]:
    if not os.path.exists(OVERRIDES_PATH):
        return {}
    with open(OVERRIDES_PATH) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith('_')}


# ---------- planning ----------

def build_plan(html: str, store_view: Dict, fetch, mechanics: bool = True,
               only: Optional[List[str]] = None, overrides: Optional[Dict] = None,
               log=print, chooser=None) -> Dict:
    """Everything the import would do, as plain data. Reads the network
    through `fetch`; never touches the database (store_view is what was read)."""
    cards = ci.parse_catalog(html)
    problem = ci.guard(cards, store_view['snapshot'])
    plan = {'version': PLAN_VERSION, 'snapshot': ci.snapshot(cards), 'guard': problem,
            'create': [], 'update': [], 'proposals': [], 'clashes': [], 'removed_cards': [],
            'gone': [], 'ambiguous_renames': [], 'nothing': [], 'no_help_centre': [],
            'already_documents': [], 'already_proposed': [], 'duplicates': [], 'unreachable': [],
            'mechanics': {}, 'blocked': [], 'integrations': 0, 'only': only, 'ai': None}
    if problem:
        return plan
    existing = store_view['integrations']
    overrides = overrides if overrides is not None else {}
    integrations, plan['clashes'] = ci.group_cards(cards, existing.keys())
    plan['integrations'] = len(integrations)
    previous = set((store_view['snapshot'] or {}).get('slugs', []))
    plan['removed_cards'] = sorted(previous - {c.slug for c in cards})

    sitemap_page = fetch(SITEMAP_URL)
    sitemap = ci.sitemap_entries(sitemap_page.text) if sitemap_page and sitemap_page.status == 200 else {}
    if not sitemap:
        log('  the support.yotpo.com sitemap could not be read: renamed guides are not looked up')

    documents = store_view['documents']
    proposals = store_view['proposals']
    claimed: Dict[str, str] = {}   # url -> integration, inside this plan

    def propose(name, url, source, label, note):
        if url in documents:
            plan['already_documents'].append({'esp': name, 'url': url, 'owner': documents[url]})
        elif url in proposals:
            plan['already_proposed'].append({'esp': name, 'url': url, 'state': proposals[url]})
        elif url in claimed:
            if claimed[url] != name:
                plan['duplicates'].append({'esp': name, 'url': url, 'proposed_for': claimed[url]})
        else:
            claimed[url] = name
            plan['proposals'].append({'esp': name, 'url': url, 'source': source,
                                      'suggested_label': label, 'note': note})

    for n, integ in enumerate(integrations, 1):
        if only and integ.name not in only:
            continue
        log(f'[{n}/{len(integrations)}] {integ.name}')
        row = _integration_row(integ)
        if integ.name in existing:
            change = _catalog_changes(existing[integ.name], row)
            if change:
                plan['update'].append({'name': integ.name, 'changes': change})
        else:
            plan['create'].append(row)

        links = ci.DetailLinks()
        for slug in integ.slugs:
            page = fetch(f'https://www.yotpo.com/integrations/{slug}/')
            if not page or page.status != 200:
                plan['unreachable'].append(f'https://www.yotpo.com/integrations/{slug}/')
                continue
            d = ci.detail_links(page.text)
            for mine, theirs in ((links.yotpo, d.yotpo), (links.partner_docs, d.partner_docs),
                                 (links.partner_other, d.partner_other)):
                mine += [u for u in theirs if u not in mine]

        outbound = []
        # What Yotpo and the partner wrote about this integration: the model
        # reads it to list the partner functions involved
        sources = [('Yotpo catalog card', integ.description)] if integ.description else []
        for url in links.yotpo:
            page = fetch(url)
            if page and page.status == 200:
                text = _guide_text(url, page)
                sources.append((f'Yotpo guide {url}', text))
                label = doc_header.suggested_label(text)
                final = ci.clean_link(page.url or url)
                if final != url and ci.is_yotpo_doc(final):
                    # The guide moved and Yotpo redirects: store it where it lives
                    propose(integ.name, final, 'catalog', label, f'redirected from {url}')
                else:
                    propose(integ.name, url, 'catalog', label, 'Yotpo guide linked from the catalog')
                outbound += [u for u in ci.guide_outbound_links(page.text) if u not in outbound]
            elif page and page.status in (404, 410):
                matches = ci.find_renamed(url, sitemap, app_mechanics.name_tokens(
                    integ.display_name, integ.name, *integ.slugs))
                if len(matches) == 1:
                    page2 = fetch(matches[0])
                    text = _guide_text(matches[0], page2) if page2 and page2.status == 200 else ''
                    propose(integ.name, matches[0], 'catalog', doc_header.suggested_label(text),
                            f'renamed from {url}')
                elif matches:
                    plan['ambiguous_renames'].append({'esp': integ.name, 'url': url,
                                                      'matches': matches})
                else:
                    plan['gone'].append({'esp': integ.name, 'url': url})
            else:
                plan['unreachable'].append(url)

        for url in links.partner_docs:
            propose(integ.name, url, 'catalog', None, 'partner page linked from the catalog')

        if not links.yotpo and not links.partner_docs:
            plan['nothing'].append(integ.name)

        if mechanics:
            for url in links.partner_docs:
                text = app_mechanics.page_text(fetch(url))
                if text:
                    sources.append((f'{integ.display_name} page about Yotpo {url}', text))
        if mechanics and integ.name in overrides and overrides[integ.name] is None:
            plan['mechanics'][integ.name] = {'help_centre': None, 'problem': 'skipped in scripts/help_centres.json'}
        elif mechanics:
            found = app_mechanics.discover(
                [integ.display_name, integ.name] + integ.slugs,
                links.partner_docs + links.partner_other, outbound, fetch, chooser,
                sources=sources, categories=integ.categories, override=overrides.get(integ.name))
            plan['mechanics'][integ.name] = {
                'help_centre': found.help_centre, 'found_via': found.found_via,
                'method': found.method, 'sources': found.sources, 'functions': found.functions,
                'checked': found.checked, 'blocked': found.blocked, 'problem': found.problem,
                'accepted': [asdict(c) for c in found.candidates]}
            if found.help_centre is None:
                plan['no_help_centre'].append({'esp': integ.name, 'why': found.problem})
            if found.blocked:
                plan['blocked'].append({'esp': integ.name, 'why': found.problem})
            for c in found.candidates:
                propose(integ.name, c.url, 'mechanics', 'shared',
                        f'{c.function}: "{c.title}". {c.reason}')
    if chooser is not None:
        plan['ai'] = {'model': chooser.model_name, **chooser.usage}
    return plan


def _guide_text(url, page) -> str:
    from crawler import _extract_text

    class _Response:
        content = page.text.encode('utf-8', 'replace')
    text, _ = _extract_text(url, _Response())
    return text or ''


def _integration_row(integ: ci.Integration) -> Dict:
    return {'name': integ.name, 'display_name': integ.display_name, 'platform_type': integ.platform_type,
            'catalog_slugs': integ.slugs, 'categories': integ.categories, 'products': integ.products,
            'catalog_description': integ.description, 'matched_by': integ.matched_by,
            'type_conflict': integ.type_conflict}


def _catalog_changes(current: Dict, row: Dict) -> Dict:
    """Catalog fields that differ on an existing integration. platform_type is
    only ever filled in, never changed."""
    changes = {}
    for field in ('catalog_slugs', 'categories', 'products', 'catalog_description'):
        if (current.get(field) or ([] if field != 'catalog_description' else None)) != row[field]:
            changes[field] = {'from': current.get(field), 'to': row[field]}
    if current.get('platform_type') is None and row['platform_type'] and current.get('status') != 'archived':
        changes['platform_type'] = {'from': None, 'to': row['platform_type']}
    return changes


# ---------- applying ----------

# What the admin shows from the import (backend/admin_integrations_routes.py)
MECHANICS_KEY = 'catalog_mechanics'
REPORT_KEY = 'catalog_last_report'


def _accepted_articles(plan: Dict) -> Dict[str, Dict]:
    """url -> the accepted mechanics article (title, function, reason)."""
    return {a['url']: a for m in plan.get('mechanics', {}).values()
            for a in m.get('accepted') or []}


def mechanics_notes(plan: Dict) -> Dict[str, Dict]:
    """Per integration, what the partner-articles search found: the
    functions the model listed, the help centre, and why nothing was found.
    The Proposals tab shows it beside each integration's list."""
    return {name: {'help_centre': m.get('help_centre'), 'found_via': m.get('found_via'),
                   'functions': [{'name': f.get('name'), 'yotpo_role': f.get('yotpo_role')}
                                 for f in m.get('functions') or [] if isinstance(f, dict)],
                   'blocked': bool(m.get('blocked')), 'problem': m.get('problem'),
                   'accepted': len(m.get('accepted') or [])}
            for name, m in plan.get('mechanics', {}).items()}


def apply_plan(store: Store, plan: Dict) -> Dict[str, int]:
    """Write a saved plan in one transaction. Re-checks every row against the
    database as it is now, so a second run, or a row added since the dry run,
    is skipped rather than duplicated."""
    if plan.get('version') != PLAN_VERSION:
        raise SystemExit('This plan was made by a different version of the script; run the dry run again.')
    if plan.get('guard'):
        raise SystemExit(f"The plan's guard stopped it: {plan['guard']}")
    if plan.get('only'):
        raise SystemExit('This plan covers only some integrations (--only); it is for trying '
                         'things, not for applying. Run the dry run without --only.')
    problem = ci.guard([ci.Card(s, '', '', '', [], ['x']) for s in plan['snapshot']['slugs']],
                       store.snapshot())
    if problem:
        raise SystemExit(f'Not applied: {problem}')

    counts = {'created': 0, 'updated': 0, 'proposals': 0, 'skipped': 0}
    articles = _accepted_articles(plan)
    existing = store.integrations()
    documents = store.document_urls()
    proposed = store.proposal_urls()
    js = json.dumps
    try:
        for row in plan['create']:
            if row['name'] in existing:
                counts['skipped'] += 1
                continue
            esp_id = str(uuid.uuid4())
            store.q("INSERT INTO esps (id, name, display_name, description, status, platform_type, "
                    "catalog_slugs, categories, products, catalog_description) "
                    "VALUES (%s, %s, %s, %s, 'listed', %s, %s, %s, %s, %s)",
                    (esp_id, row['name'], row['display_name'], '', row['platform_type'],
                     js(row['catalog_slugs']), js(row['categories']), js(row['products']),
                     row['catalog_description']), fetch=False)
            existing[row['name']] = {'id': esp_id}
            counts['created'] += 1
        for upd in plan['update']:
            current = existing.get(upd['name'])
            if not current:
                counts['skipped'] += 1
                continue
            ch = upd['changes']
            sets, params = [], []
            for field in ('catalog_slugs', 'categories', 'products'):
                if field in ch:
                    sets.append(f'{field} = %s')
                    params.append(js(ch[field]['to']))
            if 'catalog_description' in ch:
                sets.append('catalog_description = %s')
                params.append(ch['catalog_description']['to'])
            if sets:
                store.q(f"UPDATE esps SET {', '.join(sets)} WHERE name = %s",
                        tuple(params) + (upd['name'],), fetch=False)
            if 'platform_type' in ch:
                store.q("UPDATE esps SET platform_type = %s WHERE name = %s AND platform_type IS NULL",
                        (ch['platform_type']['to'], upd['name']), fetch=False)
            counts['updated'] += 1
        for p in plan['proposals']:
            esp = existing.get(p['esp'])
            if not esp or p['url'] in documents or p['url'] in proposed:
                counts['skipped'] += 1
                continue
            art = articles.get(p['url']) if p['source'] == 'mechanics' else None
            store.q("INSERT INTO document_proposals (id, esp_id, url, source, suggested_label, state, "
                    "note, title, partner_function, reason) "
                    "VALUES (%s, %s, %s, %s, %s, 'open', %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING",
                    (str(uuid.uuid4()), esp['id'], p['url'], p['source'], p['suggested_label'],
                     p['note'], (art or {}).get('title'), (art or {}).get('function'),
                     (art or {}).get('reason')), fetch=False)
            proposed[p['url']] = 'open'
            counts['proposals'] += 1
        # Merged per integration: a plan made with --no-mechanics has none, and
        # must not wipe the notes of the last run that looked
        notes = store.setting(MECHANICS_KEY) or {}
        notes.update(mechanics_notes(plan))
        for key, value in ((ci.SNAPSHOT_KEY, plan['snapshot']),
                           (MECHANICS_KEY, notes),
                           (REPORT_KEY, {'applied_at': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()),
                                         'cards': plan['snapshot']['cards'],
                                         'counts': counts,
                                         # written by the dry run; this is what was applied
                                         'report': render_report(plan).replace(
                                             '# Catalog import: dry run', '# Catalog import: applied', 1)})):
            store.q("INSERT INTO app_settings (key, value) VALUES (%s, %s) "
                    "ON CONFLICT (key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                    (key, js(value)), fetch=False)
        store.conn.commit()
    except Exception:
        store.conn.rollback()
        raise
    return counts


# ---------- report ----------

def render_report(plan: Dict) -> str:
    L = []
    w = L.append
    w('# Catalog import: dry run\n')
    if plan['guard']:
        w(f"**Stopped by the guard:** {plan['guard']}. Nothing would be written.\n")
        return '\n'.join(L)
    snap = plan['snapshot']
    props = plan['proposals']
    by_source = {}
    for p in props:
        by_source.setdefault(p['source'], []).append(p)
    yotpo = [p for p in by_source.get('catalog', []) if ci.is_yotpo_doc(p['url'])]
    partner = [p for p in by_source.get('catalog', []) if not ci.is_yotpo_doc(p['url'])]
    renamed = [p for p in props if p['note'].startswith('renamed from')]
    w('## Summary\n')
    w('| | count |\n|---|---:|')
    for label, n in (('catalog cards (detail pages)', snap['cards']),
                     ('integrations in the catalog', plan['integrations']),
                     ('integrations to create (as `listed`)', len(plan['create'])),
                     ('existing integrations whose catalog fields change', len(plan['update'])),
                     ('proposals: Yotpo guides', len(yotpo)),
                     ('  of which renamed guides', len(renamed)),
                     ('proposals: partner pages from the catalog', len(partner)),
                     ('proposals: partner mechanics articles (new)', len(by_source.get('mechanics', []))),
                     ('help centres that could not be read automatically (a person picks)', len(plan['blocked'])),
                     ('guides gone (404, no renamed match)', len(plan['gone'])),
                     ('detail pages with nothing documentary', len(plan['nothing'])),
                     ('integrations with no help centre found', len(plan['no_help_centre'])),
                     ('links already in the knowledge base (skipped)', len(plan['already_documents'])),
                     ('links already proposed (skipped)', len(plan['already_proposed'])),
                     ('cards removed since the last import', len(plan['removed_cards'])),
                     ('name clashes', len(plan['clashes']))):
        w(f'| {label} | {n} |')
    w('')

    w('## Integrations to create, by default type\n')
    by_type = {}
    for row in plan['create']:
        by_type.setdefault(row['platform_type'] or '(no type)', []).append(row)
    for t in sorted(by_type):
        rows = by_type[t]
        w(f'**{t}** ({len(rows)}): ' + ', '.join(
            f"{r['display_name']} (`{r['name']}`)" for r in sorted(rows, key=lambda r: r['name'])) + '\n')

    conflicts = [r for r in plan['create'] if r['type_conflict']]
    w(f'## Type conflicts ({len(conflicts)})\n')
    w('Categories of more than one type. The default is the first of messaging → service → '
      'storefront → content → data; an admin can change it.\n')
    w('| integration | default | categories point to |\n|---|---|---|')
    for r in sorted(conflicts, key=lambda r: r['name']):
        w(f"| {r['display_name']} | {r['platform_type']} | {', '.join(r['type_conflict'])} |")
    w('')

    if plan['update']:
        w('## Existing integrations whose catalog fields would change\n')
        for u in plan['update']:
            w(f"- `{u['name']}`: " + '; '.join(
                f"{k}: {_short(v['from'])} → {_short(v['to'])}" for k, v in u['changes'].items()))
        w('')

    w('## Proposals\n')
    w('Labels: Yotpo guides are pre-filled from their own header when it names one product '
      '(empty when it names both, or none). Partner pages are left empty. Mechanics articles are '
      'pre-filled `shared`: they explain the partner\'s features, not a Yotpo product. An admin '
      'confirms every label.\n')
    for title, rows in (('Yotpo guides', yotpo), ('Partner pages from the catalog', partner)):
        w(f'### {title} ({len(rows)})\n')
        w('| integration | link | label | note |\n|---|---|---|---|')
        for p in sorted(rows, key=lambda p: (p['esp'], p['url'])):
            w(f"| `{p['esp']}` | {p['url']} | {p['suggested_label'] or '—'} | {_cell(p['note'])} |")
        w('')

    if plan['mechanics']:
        w('## Partner mechanics, per integration\n')
        ai = plan.get('ai') or {}
        if ai:
            w(f"The model (`{ai['model']}`, {ai['calls']} calls, {ai['input_tokens']:,} input and "
              f"{ai['output_tokens']:,} output tokens, {ai['failures']} failed) read what Yotpo and "
              f"the partner wrote about each integration, listed the partner functions it touches, "
              f"and accepted only articles whose text explains one. A person approves each "
              f"integration's final list in the admin.\n")
        for name, o in sorted(plan['mechanics'].items()):
            if not o.get('functions'):
                continue
            w(f"### `{name}`\n")
            w(f"Read: {', '.join(o['sources']) or 'nothing'}. Help centre: {o['help_centre']} "
              f"({o['method'] or '—'}); {o['checked']} articles read.\n")
            w('Functions:')
            for f in o['functions']:
                w(f"- **{f['name']}**: {f['yotpo_role']}")
            w('')
            if o['accepted']:
                w('Accepted:')
                for c in o['accepted']:
                    w(f"- [{c['title']}]({c['url']}) ({c['function']}): {c['reason']}")
            else:
                w(f"Accepted: none. {o['problem'] or ''}")
            w('')
    if plan['blocked']:
        w(f"## Needs a person: the help centre could not be read automatically ({len(plan['blocked'])})\n")
        for r in sorted(plan['blocked'], key=lambda r: r['esp']):
            w(f"- `{r['esp']}`: {r['why']}")
        w('')
    if plan['no_help_centre']:
        w(f"## No help centre found ({len(plan['no_help_centre'])})\n")
        w('Add a line to `scripts/help_centres.json` (`"name": "https://help.example.com"`) and run '
          'the dry run again, or `null` to skip an integration on purpose.\n')
        for r in sorted(plan['no_help_centre'], key=lambda r: r['esp']):
            w(f"- `{r['esp']}`: {r['why']}")
        w('')
    nothing = [(n, o) for n, o in plan['mechanics'].items()
               if o.get('help_centre') and not o.get('accepted') and not o.get('blocked')]
    if nothing:
        w(f'## Help centre read, nothing accepted ({len(nothing)})\n')
        for n, o in sorted(nothing):
            w(f"- `{n}`: {o['problem']}")
        w('')

    for title, rows, fmt in (
            ('Guides that are gone', plan['gone'], lambda r: f"`{r['esp']}`: {r['url']}"),
            ('Dead guides with more than one possible new name', plan['ambiguous_renames'],
             lambda r: f"`{r['esp']}`: {r['url']} → " + ', '.join(r['matches'])),
            ('Detail pages with nothing documentary', plan['nothing'], lambda r: f'`{r}`'),
            ('Links proposed for two integrations (kept on the first)', plan['duplicates'],
             lambda r: f"{r['url']}: `{r['proposed_for']}`, also `{r['esp']}`"),
            ('Already in the knowledge base', plan['already_documents'],
             lambda r: f"{r['url']} (in `{r['owner']}`)"),
            ('Already proposed', plan['already_proposed'], lambda r: f"{r['url']} ({r['state']})"),
            ('Could not be fetched', plan['unreachable'], lambda r: r),
            ('Cards removed since the last import (reported, never deleted)', plan['removed_cards'],
             lambda r: f'`{r}`'),
            ('Name clashes', plan['clashes'], lambda r: r)):
        if rows:
            w(f'## {title} ({len(rows)})\n')
            for r in rows:
                w(f'- {fmt(r)}')
            w('')
    return '\n'.join(L)


def _short(v):
    s = json.dumps(v) if not isinstance(v, str) else v
    return s if len(s) <= 60 else s[:57] + '…'


def _cell(s):
    return (s or '').replace('|', '\\|')


# ---------- main ----------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--plan', required=True, help='plan file: written by a dry run, read by --apply')
    ap.add_argument('--report')
    ap.add_argument('--html')
    ap.add_argument('--cache')
    ap.add_argument('--no-mechanics', action='store_true')
    ap.add_argument('--ai-model', default=mechanics_ai.DEFAULT_MODEL)
    ap.add_argument('--only')
    args = ap.parse_args(argv)

    if args.apply:
        with open(args.plan) as f:
            plan = json.load(f)
        store = Store(write=True)
        try:
            counts = apply_plan(store, plan)
        finally:
            store.close()
        print(f"Applied: {counts['created']} integrations created, {counts['updated']} updated, "
              f"{counts['proposals']} proposals added, {counts['skipped']} skipped (already there).")
        return 0

    store = Store(write=False)
    try:
        view = {'integrations': store.integrations(), 'documents': store.document_urls(),
                'proposals': store.proposal_urls(), 'snapshot': store.snapshot()}
    finally:
        store.close()
    fetch = Fetcher(args.cache)
    if args.html:
        with open(args.html) as f:
            html = f.read()
    else:
        page = fetch(ci.CATALOG_URL)
        if not page or page.status != 200:
            print('The catalog page could not be fetched. Nothing written.')
            return 2
        html = page.text
    only = [s.strip() for s in args.only.split(',')] if args.only else None
    chooser = None
    if not args.no_mechanics:
        try:
            chooser = mechanics_ai.GeminiChooser(args.ai_model)
        except RuntimeError as e:
            print(f'{e}: set it, or run with --no-mechanics.')
            return 2
    plan = build_plan(html, view, fetch, mechanics=not args.no_mechanics, only=only, overrides=_overrides(),
                      log=lambda m: print(m, file=sys.stderr), chooser=chooser)
    with open(args.plan, 'w') as f:
        json.dump(plan, f, indent=1)
    report = render_report(plan)
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
    print(report)
    print(f'\nDry run: nothing written. {fetch.requests} requests. Plan saved to {args.plan}.',
          file=sys.stderr)
    return 2 if plan['guard'] else 0


if __name__ == '__main__':
    sys.exit(main())
