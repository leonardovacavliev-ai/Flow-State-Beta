"""
Find one integration's documentation links (roadmap C1.10).

The search the yotpo.com import runs per integration, in one place, so the
import (scripts/import_catalog.py) and the admin's "Find links" button
(find_links_job.py) find the same links the same way:

  1. its yotpo.com/integrations detail pages -> the Yotpo guides and the
     partner's own pages about Yotpo they link;
  2. a guide that 404s, re-found in the support.yotpo.com sitemap under a
     renamed slug;
  3. for an integration with no yotpo.com page (created by hand): Yotpo
     guides whose address carries its name, from the same sitemap. Names
     collide with ordinary words (Rule, Drip, Target); that is fine here,
     because a person approves every suggestion;
  4. the partner's own help articles on the functions the integration
     touches (backend/app_mechanics.py discover, with the model).

Network only through `fetch`; no database. Everything found is a suggestion
for a person to approve: nothing here creates documents or labels.
"""

import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Callable, Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlsplit

import app_mechanics
import catalog_import as ci
import doc_header

SITEMAP_URL = 'https://support.yotpo.com/sitemap-en.xml'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
MAX_SECONDS = 20
MAX_BYTES = 5_000_000
# Yotpo guides found by name (step 3) per run: a common word for a name
# could match many, and each one is fetched to read its header
NAME_GUIDES_MAX = 8

# The notes a suggestion carries; the admin turns them into words
# (admin-integrations.js noteText)
NOTE_CATALOG_GUIDE = 'Yotpo guide linked from the catalog'
NOTE_PARTNER_PAGE = 'partner page linked from the catalog'
NOTE_NAME_GUIDE = 'Yotpo guide found by its name on support.yotpo.com'


# ---------- network ----------

# How host names are resolved; tests replace it (they run with no network)
RESOLVE = socket.getaddrinfo
MAX_REDIRECTS = 5


def public_address_problem(url: str) -> Optional[str]:
    """Why the server must not fetch this address, or None. Find links
    fetches addresses typed by an admin and links found on other sites, so
    only public web addresses on the standard ports: never this server, a
    private network or a cloud metadata service, however the address is
    written (0x7f.0.0.1, localhost., a name that resolves to 10.x)."""
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https'):
        return 'not a web address'
    host = (parts.hostname or '').rstrip('.').lower()
    try:
        port = parts.port
    except ValueError:
        return 'not a web address'
    if not host or port not in (None, 80, 443) or parts.username or parts.password:
        return 'not a public web address'
    try:
        infos = RESOLVE(host, port or 443, proto=socket.IPPROTO_TCP)
    except (OSError, UnicodeError):
        return "that address can't be found"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split('%')[0])
        if not ip.is_global or ip.is_multicast:
            return 'not a public web address'
    return None

class Fetcher:
    """GET with the crawler's headers, one request per second per host, one
    retry on a network error, and an optional on-disk cache (the import's
    --cache; the admin never uses one)."""

    def __init__(self, cache_dir: Optional[str] = None, delay: float = 1.0, log=None,
                 public_only: bool = False):
        import requests
        self.session = requests.Session()
        self.session.headers['User-Agent'] = USER_AGENT
        self.cache_dir = cache_dir
        self.delay = delay
        self.last_at: Dict[str, float] = {}
        self.requests = 0
        self.log = log or (lambda m: print(m, file=sys.stderr))
        # Find links: every address and every redirect is checked first
        # (public_address_problem); the import, which reads only the
        # catalog's own links, keeps the plain behaviour
        self.public_only = public_only
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def _cache_path(self, url):
        return os.path.join(self.cache_dir, hashlib.sha1(url.encode()).hexdigest() + '.json')

    def _get(self, url: str) -> app_mechanics.Page:
        """One GET, at most MAX_BYTES and MAX_SECONDS in all: a server that
        sends a byte at a time never trips the per-read timeout. With
        public_only, redirects are followed here, one checked hop at a time."""
        started = time.time()
        for _ in range(MAX_REDIRECTS + 1):
            if self.public_only:
                problem = public_address_problem(url)
                if problem:
                    raise PermissionError(f'{problem}: {url}')
            with self.session.get(url, timeout=10, stream=True,
                                  allow_redirects=not self.public_only) as r:
                if self.public_only and r.is_redirect:
                    url = urljoin(url, r.headers.get('location', ''))
                    continue
                body = b''
                for chunk in r.iter_content(65536):
                    body += chunk
                    if len(body) > MAX_BYTES or time.time() - started > MAX_SECONDS:
                        raise TimeoutError(f'gave up after {MAX_SECONDS}s or {MAX_BYTES} bytes')
                r._content = body
                return app_mechanics.Page(r.status_code, r.url, r.text, r.headers.get('content-type', ''))
        raise TimeoutError(f'more than {MAX_REDIRECTS} redirects')

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
                self.log(f'  [fetch] {url}: {type(e).__name__}')
        if self.cache_dir:
            with open(self._cache_path(url), 'w') as f:
                json.dump(asdict(page or app_mechanics.Page(0, url, '')), f)
        return page


def read_sitemap(fetch) -> Dict[str, Optional[str]]:
    """{url: lastmod} of support.yotpo.com, or {} when it can't be read."""
    page = fetch(SITEMAP_URL)
    return ci.sitemap_entries(page.text) if page and page.status == 200 else {}


def load_overrides(path: str) -> Dict[str, Optional[str]]:
    """scripts/help_centres.json: {esps.name: help centre, or None to skip}."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith('_')}


# ---------- pure helpers ----------

def mechanics_note(m: Dict) -> Dict:
    """What the help-article search found for one integration, as the
    admin shows it (app_settings `catalog_mechanics`): the functions the
    model listed, the help centre, and why nothing was found."""
    return {'help_centre': m.get('help_centre'), 'found_via': m.get('found_via'),
            'functions': [{'name': f.get('name'), 'yotpo_role': f.get('yotpo_role')}
                          for f in m.get('functions') or [] if isinstance(f, dict)],
            'blocked': bool(m.get('blocked')), 'problem': m.get('problem'),
            'accepted': len(m.get('accepted') or [])}


def guide_text(url, page) -> str:
    """A Yotpo guide's text as the crawler would store it (header first)."""
    from crawler import _extract_text

    class _Response:
        content = page.text.encode('utf-8', 'replace')
    text, _ = _extract_text(url, _Response())
    return text or ''


def _name_parts(*names: str) -> List[List[str]]:
    """Each name as its lowercase words: 'Loop Returns' -> ['loop', 'returns']."""
    out = []
    for name in names:
        parts = [p for p in re.split(r'[^a-z0-9]+', (name or '').lower()) if p]
        if parts and parts not in out:
            out.append(parts)
    return out


def slug_names(slug: str, names: Iterable[List[str]]) -> bool:
    """Whether a guide's slug carries one of the names as whole words
    ('…-with-loop-returns', '…-loopreturns-…'), so 'rule' does not match
    'earning-rules' and 'returns' alone does not match 'loop-returns'."""
    slug = slug.lower()
    words = slug.split('-')
    joined = slug.replace('-', '')
    for parts in names:
        n = len(parts)
        if any(words[i:i + n] == parts for i in range(len(words) - n + 1)):
            return True
        # written as one word in the address ('loopreturns', 'brevopushowl')
        if n > 1 and ''.join(parts) in words:
            return True
        if n > 1 and len(''.join(parts)) >= 8 and ''.join(parts) in joined:
            return True
    return False


def guides_by_name(sitemap: Iterable[str], *names: str, limit: int = NAME_GUIDES_MAX) -> List[str]:
    """Yotpo guides in the sitemap whose address carries the integration's
    name: integration guides first, then the rest, each in address order."""
    parts = [p for p in _name_parts(*names) if p != ['global']]
    if not parts:
        return []
    found = sorted(u for u in sitemap if ci.is_yotpo_doc(u) and
                   urlsplit(u).hostname == 'support.yotpo.com' and slug_names(ci.slug_from_url(u), parts))
    guides = [u for u in found if re.search(r'integrat|guide|connect', ci.slug_from_url(u))]
    return (guides + [u for u in found if u not in guides])[:limit]


def website_links(website: Optional[str]):
    """(help centre override, trusted links) for an address an admin typed:
    a help site is used as the help centre; anything else (its homepage)
    is the partner's own site, trusted even when its domain doesn't carry
    the name (shop.app for "Shop App"), so its "Help Center" link is
    followed."""
    if not website:
        return None, []
    host = app_mechanics.host_of(website)
    if app_mechanics.looks_like_help_host(host) or app_mechanics.is_doc_like(website):
        return website, []
    return None, [website]


# ---------- the search ----------

@dataclass
class Found:
    """What find_links found for one integration. `proposals` are in the
    order they were found: {url, source, suggested_label, note}, plus
    title, partner_function and reason for a help article."""
    proposals: List[Dict] = field(default_factory=list)
    unreachable: List[str] = field(default_factory=list)
    gone: List[str] = field(default_factory=list)                 # dead guides, no new address
    ambiguous_renames: List[Dict] = field(default_factory=list)   # {url, matches}
    nothing: bool = False             # its detail pages link nothing documentary
    mechanics: Optional[Dict] = None  # the help-article search, as the plan stores it
    no_help_centre: bool = False      # the help-article search found no help centre
    blocked: bool = False             # its help centre refuses automated reading
    by_name: bool = False             # step 3 ran (no yotpo.com page)


def find_links(integ: ci.Integration, fetch, sitemap: Dict[str, Optional[str]], *,
               chooser=None, mechanics: bool = True, overrides: Optional[Dict] = None,
               website: Optional[str] = None,
               progress: Callable[[str], None] = lambda step: None) -> Found:
    """Every link worth suggesting for one integration (module docstring).

    `overrides` is scripts/help_centres.json: a help centre per integration,
    or None to skip its help articles on purpose. `website` is an address an
    admin gave (find_links_job); the import never passes one."""
    out = Found()
    overrides = overrides if overrides is not None else {}

    def propose(url, source, label, note, **extra):
        out.proposals.append({'url': url, 'source': source, 'suggested_label': label,
                              'note': note, **extra})

    progress('yotpo.com')
    links = ci.DetailLinks()
    for slug in integ.slugs:
        page = fetch(f'https://www.yotpo.com/integrations/{slug}/')
        if not page or page.status != 200:
            out.unreachable.append(f'https://www.yotpo.com/integrations/{slug}/')
            continue
        d = ci.detail_links(page.text)
        for mine, theirs in ((links.yotpo, d.yotpo), (links.partner_docs, d.partner_docs),
                             (links.partner_other, d.partner_other)):
            mine += [u for u in theirs if u not in mine]

    outbound = []
    # What Yotpo and the partner wrote about this integration: the model
    # reads it to list the partner functions involved
    sources = [('Yotpo catalog card', integ.description)] if integ.description else []
    progress('yotpo_guides')
    for url in links.yotpo:
        page = fetch(url)
        if page and page.status == 200:
            text = guide_text(url, page)
            sources.append((f'Yotpo guide {url}', text))
            label = doc_header.suggested_label(text)
            final = ci.clean_link(page.url or url)
            if final != url and ci.is_yotpo_doc(final):
                # The guide moved and Yotpo redirects: store it where it lives
                propose(final, 'catalog', label, f'redirected from {url}')
            else:
                propose(url, 'catalog', label, NOTE_CATALOG_GUIDE)
            outbound += [u for u in ci.guide_outbound_links(page.text) if u not in outbound]
        elif page and page.status in (404, 410):
            matches = ci.find_renamed(url, sitemap, app_mechanics.name_tokens(
                integ.display_name, integ.name, *integ.slugs))
            if len(matches) == 1:
                page2 = fetch(matches[0])
                text = guide_text(matches[0], page2) if page2 and page2.status == 200 else ''
                propose(matches[0], 'catalog', doc_header.suggested_label(text), f'renamed from {url}')
            elif matches:
                out.ambiguous_renames.append({'url': url, 'matches': matches})
            else:
                out.gone.append(url)
        else:
            out.unreachable.append(url)

    if not integ.slugs:
        # Not on yotpo.com: Yotpo's guides that carry its name
        out.by_name = True
        for url in guides_by_name(sitemap, integ.display_name, integ.name):
            page = fetch(url)
            if not page or page.status != 200:
                out.unreachable.append(url)
                continue
            text = guide_text(url, page)
            sources.append((f'Yotpo guide {url}', text))
            propose(url, 'catalog', doc_header.suggested_label(text), NOTE_NAME_GUIDE)
            outbound += [u for u in ci.guide_outbound_links(page.text) if u not in outbound]

    for url in links.partner_docs:
        propose(url, 'catalog', None, NOTE_PARTNER_PAGE)

    if integ.slugs and not links.yotpo and not links.partner_docs:
        out.nothing = True

    if not mechanics:
        return out
    progress('help_site')
    for url in links.partner_docs:
        text = app_mechanics.page_text(fetch(url))
        if text:
            sources.append((f'{integ.display_name} page about Yotpo {url}', text))
    if integ.name in overrides and overrides[integ.name] is None:
        out.mechanics = {'help_centre': None, 'problem': 'skipped in scripts/help_centres.json'}
        return out
    typed_centre, trusted = website_links(website)
    found = app_mechanics.discover(
        [integ.display_name, integ.name] + integ.slugs,
        links.partner_docs + links.partner_other, outbound, fetch, chooser,
        sources=sources, categories=integ.categories,
        override=overrides.get(integ.name) or typed_centre, trusted=trusted)
    out.mechanics = {
        'help_centre': found.help_centre, 'found_via': found.found_via,
        'method': found.method, 'sources': found.sources, 'functions': found.functions,
        'checked': found.checked, 'blocked': found.blocked, 'problem': found.problem,
        'accepted': [asdict(c) for c in found.candidates]}
    out.no_help_centre = found.help_centre is None
    out.blocked = found.blocked
    for c in found.candidates:
        propose(c.url, 'mechanics', 'shared', f'{c.function}: "{c.title}". {c.reason}',
                title=c.title, partner_function=c.function, reason=c.reason)
    return out
