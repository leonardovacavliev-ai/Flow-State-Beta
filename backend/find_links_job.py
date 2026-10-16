"""
"Find links" for one integration, run in the background (roadmap C1.10).

An admin presses Find links on an integration's page, or creates an
integration in the Add integration dialog, which starts it at once. The
search (link_finder.find_links) reads yotpo.com, support.yotpo.com and the
partner's help centre at one request per second per site, and asks the model
to list and check the partner's help articles: a minute or more, so it runs
in a thread, never in the request, and the page polls GET for its progress.

What it writes, and only that (Leo, 2026-10-15):
  - suggestions in document_proposals (sources `catalog` and `mechanics`),
    skipping links that are already documents or were ever suggested, in any
    state: a rejected link is never suggested again;
  - this integration's entry in app_settings `catalog_mechanics` (what the
    help-article search found, as the import stores it), when the model ran;
  - the run itself in app_settings `find_links:<name>`: who, when, each step,
    what was suggested and why nothing else was.
It never creates documents, integrations or labels, and never changes an
integration's own fields.

One run per integration at a time, and at most MAX_RUNNING in all. The
running set lives in this process: the app runs one web process (Procfile,
Dockerfile: --workers 1), so it is exact there; a run left "running" by a
restart reads as interrupted, and may be started again.

The model step uses the app's GEMINI_API_KEY (Leo, 2026-10-15: the live
chat's prepaid key, for now). Without a key the run still finds the
yotpo.com and Yotpo-guide links, and says the help-article step was skipped.
"""

import json
import os
import threading
import time
import traceback
import uuid
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

import catalog_import as ci
import link_finder
from esp_manager import _json_list
from integration_types import TYPE_LABELS

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERRIDES_PATH = os.path.join(BASE, 'scripts', 'help_centres.json')
RUN_KEY = 'find_links:'            # + esps.name, in app_settings
MECHANICS_KEY = 'catalog_mechanics'
MAX_RUNNING = 2
MAX_WEBSITE = 500
# The steps a run goes through, in order (the admin shows them)
STEPS = ('starting', 'yotpo.com', 'yotpo_guides', 'help_site', 'saving')

_lock = threading.Lock()          # the running set
_notes_lock = threading.Lock()    # this process's writes of catalog_mechanics
_running: set = set()


# ---------- pure ----------

def clean_website(value) -> Tuple[Optional[str], Optional[str]]:
    """(address, error) for the optional website an admin typed. Only a
    public web address: it is fetched from the server."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, None
    if not isinstance(value, str) or len(value.strip()) > MAX_WEBSITE:
        return None, 'The website must be a web address'
    url = value.strip()
    if '://' not in url:
        url = 'https://' + url
    host = (urlsplit(url).hostname or '').rstrip('.').lower()
    problem = link_finder.public_address_problem(url) if '.' in host else 'not a public web address'
    if problem == "that address can't be found":
        return None, f"The website {host} can't be found: check the address"
    if problem:
        return None, 'The website must be a public web address, like https://www.example.com'
    from urls import normalize_url
    return normalize_url(url), None


def run_view(run: Optional[Dict], active: bool) -> Optional[Dict]:
    """A stored run as the admin sees it: one left "running" that no thread
    here is running was cut short by a restart."""
    if not run:
        return None
    run = dict(run)
    if run.get('state') == 'running' and not active:
        run['state'] = 'interrupted'
    return run


def summarise(found: link_finder.Found, added: List[Dict], already: List[Dict]) -> Dict:
    """The run's result, in counts and short lists the admin can show."""
    m = found.mechanics or {}
    return {
        'added': added,
        'already': already,
        'counts': {
            'yotpo_guides': sum(1 for p in added if p['source'] == 'catalog' and ci.is_yotpo_doc(p['url'])),
            'partner_pages': sum(1 for p in added if p['source'] == 'catalog' and not ci.is_yotpo_doc(p['url'])),
            'help_articles': sum(1 for p in added if p['source'] == 'mechanics'),
            'already': len(already),
        },
        'by_name': found.by_name,
        'gone': found.gone,
        'unreachable': len(found.unreachable),
        'help_centre': m.get('help_centre'),
        'help_problem': m.get('problem'),
        'blocked': bool(m.get('blocked')),
        'functions': [f.get('name') for f in m.get('functions') or [] if isinstance(f, dict)],
    }


# ---------- database ----------

def _setting(db, key) -> Optional[Dict]:
    rows = db.execute_query("SELECT value FROM app_settings WHERE key = %s", (key,), fetch=True)
    if not rows or not rows[0][0]:
        return None
    try:
        return json.loads(rows[0][0])
    except ValueError:
        return None


def _save_setting(db, key, value):
    db.execute_query("INSERT INTO app_settings (key, value) VALUES (%s, %s) "
                     "ON CONFLICT (key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                     (key, json.dumps(value)))


def last_run(db, name) -> Optional[Dict]:
    # A membership test needs no lock; every page load and poll asks
    return run_view(_setting(db, RUN_KEY + name), name in _running)


def load_integration(db, name) -> Optional[Dict]:
    rows = db.execute_query("""
        SELECT id, name, display_name, status, platform_type, catalog_slugs, categories,
               products, catalog_description
        FROM esps WHERE name = %s AND name <> 'global'
    """, (name,), fetch=True)
    if not rows:
        return None
    r = rows[0]
    return {'id': str(r[0]), 'name': r[1], 'display_name': r[2] or r[1], 'status': r[3],
            'platform_type': r[4], 'catalog_slugs': _json_list(r[5]), 'categories': _json_list(r[6]),
            'products': _json_list(r[7]), 'catalog_description': r[8]}


def _now() -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


# ---------- the run ----------

def catalog_match(fetch, name: str) -> Optional[ci.Integration]:
    """This integration as yotpo.com/integrations lists it, for one created
    by hand that has no yotpo.com page recorded yet (an email platform added
    from docs/integrations/messaging_sources.md is on yotpo.com, under the
    name the import expects). Grouped exactly as the import groups cards."""
    page = fetch(ci.CATALOG_URL)
    if not page or page.status != 200:
        return None
    integrations, _ = ci.group_cards(ci.parse_catalog(page.text), [name])
    return next((i for i in integrations if i.name == name), None)


def search_target(row: Dict, fetch) -> Tuple[ci.Integration, Optional[List[str]]]:
    """(what to search for, the yotpo.com pages found by name or None).

    Uses the integration's recorded yotpo.com pages; with none, looks it up
    in the catalog. The model is told its category when it has no
    yotpo.com categories, so it knows what sort of platform it reads about."""
    slugs, categories, description = row['catalog_slugs'], row['categories'], row['catalog_description']
    matched = None
    if not slugs:
        match = catalog_match(fetch, row['name'])
        if match:
            slugs, matched = match.slugs, match.slugs
            categories = categories or match.categories
            description = description or match.description
    if not categories and row['platform_type'] in TYPE_LABELS:
        categories = [f"category: {TYPE_LABELS[row['platform_type']]}"]
    integ = ci.Integration(name=row['name'], display_name=row['display_name'], slugs=list(slugs),
                           categories=list(categories), products=row['products'],
                           description=description or '', platform_type=row['platform_type'])
    return integ, matched


def save_suggestions(db, row: Dict, found: link_finder.Found) -> Tuple[List[Dict], List[Dict]]:
    """(added, already): each link found becomes an open proposal, unless it
    is a document already or was ever suggested (any integration, any state)."""
    documents = {r[0]: r[1] or r[2] for r in db.execute_query("""
        SELECT d.url, e.display_name, e.name FROM esp_documents d JOIN esps e ON e.id = d.esp_id
    """, fetch=True) or []}
    proposed = {r[0]: (r[1], r[2] or r[3]) for r in db.execute_query("""
        SELECT p.url, p.state, e.display_name, e.name
        FROM document_proposals p LEFT JOIN esps e ON e.id = p.esp_id
    """, fetch=True) or []}
    added, already, seen = [], [], set()
    for p in found.proposals:
        url = p['url']
        if url in seen:
            continue
        seen.add(url)
        if url in documents:
            already.append({'url': url, 'why': 'document', 'where': documents[url]})
            continue
        if url in proposed:
            state, where = proposed[url]
            already.append({'url': url, 'why': state or 'open', 'where': where})
            continue
        pid = str(uuid.uuid4())
        db.execute_query("""
            INSERT INTO document_proposals (id, esp_id, url, source, suggested_label, state, note,
                                            title, partner_function, reason)
            VALUES (%s, %s, %s, %s, %s, 'open', %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING
        """, (pid, row['id'], url, p['source'], p['suggested_label'], p['note'],
              p.get('title'), p.get('partner_function'), p.get('reason')))
        if not db.execute_query("SELECT 1 FROM document_proposals WHERE id = %s", (pid,), fetch=True):
            # Another run suggested it a moment ago
            already.append({'url': url, 'why': 'open', 'where': None})
            continue
        added.append({'url': url, 'source': p['source'], 'suggested_label': p['suggested_label'],
                      'note': p['note'], 'title': p.get('title')})
    return added, already


def run_once(db, name: str, actor: str, website: Optional[str], fetch, chooser,
             overrides: Optional[Dict] = None, run_id: Optional[str] = None) -> Dict:
    """One whole run, in the calling thread; saves its progress as it goes
    and returns the finished run. The thread in start() calls this; tests
    call it directly with a fake fetch and model."""
    run = {'id': run_id or str(uuid.uuid4()), 'state': 'running', 'step': 'starting',
           'requested_by': actor, 'started_at': _now(), 'finished_at': None,
           'website': website,
           # no model: the partner's help articles were not looked for,
           # because GEMINI_API_KEY is unset (no_key) or the model wouldn't start
           'model_skipped': chooser is None,
           'model_problem': None if chooser is not None else
           ('no_key' if not os.environ.get('GEMINI_API_KEY') else 'unavailable')}
    key = RUN_KEY + name

    def progress(step):
        run['step'] = step
        _save_setting(db, key, run)

    progress('starting')
    try:
        row = load_integration(db, name)
        if not row:
            raise LookupError('the integration was removed')
        if overrides is None:
            overrides = link_finder.load_overrides(OVERRIDES_PATH)
        integ, matched = search_target(row, fetch)
        run['catalog_slugs'] = integ.slugs
        run['matched_on_yotpo_com'] = matched
        sitemap = link_finder.read_sitemap(fetch)
        run['sitemap_read'] = bool(sitemap)
        found = link_finder.find_links(integ, fetch, sitemap, chooser=chooser, overrides=overrides,
                                       website=website, progress=progress)
        progress('saving')
        added, already = save_suggestions(db, row, found)
        if chooser is not None and found.mechanics is not None:
            # The import's notes for this integration, as it would write them
            with _notes_lock:
                notes = _setting(db, MECHANICS_KEY) or {}
                notes[name] = link_finder.mechanics_note(found.mechanics)
                _save_setting(db, MECHANICS_KEY, notes)
        run.update(summarise(found, added, already))
        if chooser is not None:
            run['usage'] = dict(getattr(chooser, 'usage', {}) or {})
        run['state'] = 'done'
    except Exception as e:
        traceback.print_exc()
        run['state'] = 'failed'
        run['error'] = f'{type(e).__name__}: {str(e)[:300]}'
    run['finished_at'] = _now()
    _save_setting(db, key, run)
    return run


def _default_chooser():
    """The model for the help-article step, or None without a key."""
    if not os.environ.get('GEMINI_API_KEY'):
        return None
    import mechanics_ai
    try:
        return mechanics_ai.GeminiChooser(mechanics_ai.DEFAULT_MODEL)
    except Exception as e:
        print(f'[FIND LINKS] model unavailable: {type(e).__name__}: {e}')
        return None


def start(db_factory: Callable, name: str, actor: str, website: Optional[str],
          fetch_factory: Callable = None, chooser_factory: Callable = None) -> Tuple[Optional[Dict], Optional[str]]:
    """Start a run in a thread: (the run as first saved, None) or (None,
    why not). Refuses while this integration's last run is going, or
    MAX_RUNNING runs are."""
    fetch_factory = fetch_factory or (lambda: link_finder.Fetcher(log=print, public_only=True))
    chooser_factory = chooser_factory or _default_chooser
    with _lock:
        if name in _running:
            return None, 'Already looking for its links: wait for that search to finish.'
        if len(_running) >= MAX_RUNNING:
            return None, (f'{MAX_RUNNING} searches are running already. Try again in a minute or two.')
        _running.add(name)
    run_id = str(uuid.uuid4())
    db = db_factory()
    try:
        first = {'id': run_id, 'state': 'running', 'step': 'starting', 'requested_by': actor,
                 'started_at': _now(), 'finished_at': None, 'website': website}
        _save_setting(db, RUN_KEY + name, first)
    except Exception:
        with _lock:
            _running.discard(name)
        raise

    def work():
        try:
            print(f'[FIND LINKS] {name}: started by {actor}')
            done = run_once(db_factory(), name, actor, website, fetch_factory(), chooser_factory(),
                            run_id=run_id)
            print(f"[FIND LINKS] {name}: {done['state']}, {len(done.get('added') or [])} links suggested")
        except Exception as e:
            # Before or after run_once's own handling: say so, rather than
            # leave a "running" record that reads as a restart
            traceback.print_exc()
            try:
                _save_setting(db_factory(), RUN_KEY + name, dict(
                    first, state='failed', finished_at=_now(), error=f'{type(e).__name__}: {str(e)[:300]}'))
            except Exception:
                traceback.print_exc()
        finally:
            with _lock:
                _running.discard(name)

    try:
        threading.Thread(target=work, name=f'find-links-{name}', daemon=True).start()
    except Exception:
        with _lock:
            _running.discard(name)
        raise
    return first, None
