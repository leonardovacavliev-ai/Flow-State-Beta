"""
Find a partner app's mechanics: its own articles on the functions a Yotpo
integration touches (Leo's design, 2026-10-14).

A Yotpo guide explains how to connect the integration. To answer well, Flow
State also needs the partner's documentation of its side: for Klaviyo, how
flows, triggers and profile properties work; for Recharge, how subscription
discount codes work. Per integration:

  1. Read what Yotpo and the partner wrote about the integration: the Yotpo
     guides and partner pages the catalog links (read by the caller), plus
     the partner help centre's own articles that mention Yotpo.
  2. A model lists the partner functions the integration touches, each with
     searches (backend/mechanics_ai.py).
  3. Code searches the partner's help centre for each function.
  4. Code reads every candidate article, and the model accepts only those
     whose text explains one of the functions.
The accepted articles are one list per integration, proposed with label
`shared`; a person approves the final list in the admin (C1.4). A candidate
is always a real page the code found and read; the model cannot add a link.

When the help centre blocks automated reading (a bot check, 403, 429), the
model is not asked to guess: the integration is marked blocked, for a person
to pick the articles. Zendesk centres are the exception: their search API
returns each article's text even when their pages show a bot check.

How the help centre is found, in order:
  1. an admin override (scripts/help_centres.json);
  2. a documentation link the catalog detail page itself gives;
  3. a link inside the Yotpo guide to the partner's documentation;
  4. when one of the links above gives the partner's domain: the help link
     on its homepage ("Help Center", "Support", "Docs"); failing that,
     probing help./support./docs./knowledge.<domain>.
A host only counts when its name carries the app's name, so a Shopify link
inside the Gorgias guide is never taken as Gorgias's help centre. Names are
never guessed into domains: "Rule" or "Target" would find someone else's site.

How a help centre is searched: Zendesk centres through their public search
API (many show a bot check to page fetches but answer the API); others
through the titles they list (home page and its sections, llms.txt, the
sitemap's addresses), matched against the function's search words.

Bounded: one help centre per integration, at most MAX_CANDIDATES articles
read, one request per second per host. The network is injected
(fetch(url) -> Page | None), so all of it is tested on saved pages.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Tuple
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from urls import normalize_url

MAX_CANDIDATES = 20      # articles read and shown to the model, per integration
PER_SEARCH = 4           # results kept from each search
YOTPO_ARTICLES = 3       # the partner's own Yotpo articles read in step 1

# Never a partner's own documentation: Yotpo, shorteners, social and video
# sites, app stores, form and page builders. Matched as a whole domain.
NOT_PARTNER_DOMAINS = (
    'yotpo.com', 'bit.ly', 'tinyurl.com', 'gorgias.page', 'facebook.com', 'linkedin.com',
    'twitter.com', 'x.com', 'instagram.com', 'youtube.com', 'youtu.be', 'vimeo.com', 'tiktok.com',
    'apps.shopify.com', 'google.com', 'goo.gl', 'notion.site', 'notion.so', 'typeform.com',
    'calendly.com', 'hubspot.net', 'hs-sites.com', 'medium.com', 'github.com', 'wistia.com',
    'loom.com', 'statuspage.io', 'productboard.com',
)
# Hosts by their first label: link shorteners and status pages
NOT_PARTNER_PREFIXES = ('link.', 'status.')

# A host or path shape that says "documentation"
_HELP_HOST_PREFIXES = ('help', 'support', 'docs', 'doc', 'kb', 'knowledge', 'knowledgebase',
                       'helpcenter', 'helpdesk', 'faq', 'guide', 'guides', 'learn', 'manual')
_HELP_HOST_SUFFIXES = ('.zendesk.com', '.intercom.help', '.helpscoutdocs.com', '.gitbook.io',
                       '.document360.io', '.freshdesk.com', '.readme.io', '.help', '.helpjuice.com',
                       '.groovehq.com', '.crisp.help', '.zohodesk.com')
_HELP_PATH = re.compile(r'/(hc|help|helpcenter|help-center|docs?|kb|knowledge(?:-?base)?|support|'
                        r'articles?|guides?|manual|academy)(/|$)', re.I)

# Listing pages: a section of articles, not an article
_LISTING_PATH = re.compile(r'/(categories|category|collections|sections|section|topics|tags?|folders)/'
                           r'|/solutions/\d+(?:-[^/]*)?$', re.I)
_ARTICLE_PATH = re.compile(r'/(articles?|docs?|hc/[^/]+/articles|kb|knowledge|guides?|manual|'
                           r'help)/[^/?#]+', re.I)
# Last path segments that are an index page, not an article
_INDEX_NAMES = {'articles', 'article', 'docs', 'doc', 'collections', 'categories', 'all', 'home',
                'search', 'help', 'kb', 'knowledge', 'support', 'faq', 'hc', 'sections', 'guides'}
# "8 articles" / "3 categories" in a link's text marks a listing card
_COUNT_TEXT = re.compile(r'\b\d+\s+(articles?|categor(y|ies)|sections?)\b', re.I)


@dataclass
class Page:
    status: int
    url: str          # after redirects
    text: str
    content_type: str = ''


Fetch = Callable[[str], Optional[Page]]


# Never proposed: news, account admin, legal
_EXCLUDE = ('changelog', 'release notes', "what's new", 'whats new', 'password', 'log in to',
            'careers', 'webinar', 'legal', 'terms of service', 'cookie', 'uninstall', 'status page',
            'yotpo', 'announcing', 'announcement', 'announcements', 'code freeze', 'laws', 'law',
            'trends', 'tax', 'taxes')
@dataclass
class Candidate:
    url: str
    title: str
    function: str = ''
    reason: str = ''


@dataclass
class Mechanics:
    """What discover() found for one integration."""
    help_centre: Optional[str] = None     # root URL used
    found_via: Optional[str] = None       # override | catalog | guide | homepage | probe
    method: Optional[str] = None          # zendesk-search, pages, llms.txt, sitemap; joined by +
    sources: List[str] = field(default_factory=list)      # what step 1 read
    functions: List[dict] = field(default_factory=list)   # step 2: name, yotpo_role, searches
    checked: int = 0                      # candidate articles read in step 4
    blocked: bool = False                 # the centre refuses automated reading: a person picks
    candidates: List[Candidate] = field(default_factory=list)   # accepted
    problem: Optional[str] = None         # why nothing was found, in plain words


# ---------- pure helpers ----------

def _words(text: str) -> str:
    """Lowercase, with address punctuation turned into spaces, so
    'getting-started' and 'Getting Started' read the same."""
    return ' ' + re.sub(r'[\s/_\-.?=&#%+]+', ' ', (text or '').lower()).strip() + ' '


def name_tokens(*names: str) -> List[str]:
    """Pieces of an app's name that its domain is likely to carry:
    'Loop Returns' -> ['loopreturns', 'loop', 'returns'] (pieces under 4
    letters are dropped, except the whole name joined up)."""
    tokens = []
    for name in names:
        parts = [p for p in re.split(r'[^a-z0-9]+', (name or '').lower()) if p]
        joined = ''.join(parts)
        for t in [joined] + parts:
            if t and (len(t) >= 4 or t == joined) and t not in tokens and t not in _GENERIC_NAME_PARTS:
                tokens.append(t)
    return tokens


# Words in catalog names that do not identify the partner
_GENERIC_NAME_PARTS = {'loyalty', 'reviews', 'review', 'yotpo', 'shop', 'store', 'app', 'apps',
                       'integration', 'commerce', 'plus', 'marketing', 'cloud', 'the',
                       'and', 'for', 'with', 'customer', 'customers', 'data', 'platform', 'point',
                       'sale', 'mobile'}


def host_of(url: str) -> str:
    return (urlsplit((url or '').strip()).hostname or '').lower()


def registered_domain(host: str) -> str:
    """'docs.gorgias.com' -> 'gorgias.com'; 'help.example.co.uk' -> 'example.co.uk'."""
    labels = [l for l in host.split('.') if l]
    if len(labels) >= 3 and len(labels[-1]) == 2 and labels[-2] in ('co', 'com', 'org', 'net', 'ac'):
        return '.'.join(labels[-3:])
    return '.'.join(labels[-2:])


def is_partner_url(url: str) -> bool:
    """An http(s) link to somewhere other than Yotpo, a shortener or a social site."""
    u = (url or '').strip()
    if not u.lower().startswith(('http://', 'https://')):
        return False
    host = host_of(u)
    return bool(host) and not host.startswith(NOT_PARTNER_PREFIXES) and \
        not any(host == d or host.endswith('.' + d) for d in NOT_PARTNER_DOMAINS)


def looks_like_help_host(host: str) -> bool:
    first = host.split('.')[0]
    return first in _HELP_HOST_PREFIXES or host.endswith(_HELP_HOST_SUFFIXES)


def is_doc_like(url: str) -> bool:
    """A partner link that is documentation rather than a homepage or ad."""
    if not is_partner_url(url):
        return False
    parts = urlsplit(url.strip())
    if parts.path in ('', '/') and not parts.query:
        return False  # a homepage, even on a help host, is not one document
    return looks_like_help_host(parts.hostname or '') or bool(_HELP_PATH.search(parts.path))


def host_matches_app(host: str, tokens: Iterable[str]) -> bool:
    """Whether a host carries the app's name: docs.gorgias.com for Gorgias,
    support.dixa.help for Dixa. Only the labels left of the public suffix count."""
    labels = registered_domain(host).split('.')[:1] + host.split('.')[:-2]
    hay = '.'.join(labels)
    return any(t in hay for t in tokens)


_LOCALE = re.compile(r'^[a-z]{2}(?:-[a-z]{2})?$', re.I)
# Leading path segments that name a help centre on a company's main site:
# mailchimp.com/help, braze.com/docs, drip.com/learn/docs
_ROOT_SEGMENTS = {'hc', 'help', 'docs', 'doc', 'support', 'kb', 'knowledge', 'knowledgebase',
                  'knowledge-base', 'learn', 'help-center', 'helpcenter', 'manual', 'academy'}


def help_centre_root(url: str) -> str:
    """The home page of the help centre a documentation link belongs to:
    https://x.zendesk.com/hc/en-us/articles/1 -> https://x.zendesk.com/hc/en-us,
    https://help.x.com/en/articles/2 -> https://help.x.com/en,
    https://docs.x.com/en-US/foo-1 -> https://docs.x.com/en-US,
    https://mailchimp.com/help/connect-x -> https://mailchimp.com/help."""
    parts = urlsplit(url.strip())
    segs = [s for s in parts.path.split('/') if s]
    keep = []
    for seg in segs[:3]:
        if seg.lower() in _ROOT_SEGMENTS or _LOCALE.match(seg):
            keep.append(seg)
        else:
            break
    path = '/' + '/'.join(keep) if keep else '/'
    return urlunsplit((parts.scheme.lower() or 'https', (parts.hostname or '').lower(), path, '', ''))


def _clean_title(text: str) -> str:
    """Link text minus the counts and dates help centres print under titles."""
    text = re.sub(r'\s+', ' ', text or '').strip()
    text = _COUNT_TEXT.split(text)[0] if _COUNT_TEXT.search(text) else text
    text = re.split(r'\s(?:Edited|Updated|Written by)\b', text)[0]
    return text.strip(' •·-')[:150]


def _same_site(url: str, root: str) -> bool:
    return host_of(url) == host_of(root)


def _is_article(url: str, root: Optional[str] = None) -> bool:
    """An article page: not a listing, and either shaped like one
    (/articles/…) or anything below the root of a dedicated help host
    (docs.gorgias.com/en-US/create-a-helpdesk-82010)."""
    parts = urlsplit(url)
    path = parts.path
    if _LISTING_PATH.search(path) or path.endswith(('.xml', '.txt', '.json', '.pdf')):
        return False
    last = path.rstrip('/').rsplit('/', 1)[-1].lower()
    if last in _INDEX_NAMES or _LOCALE.match(last):
        return False  # ".../articles", ".../en": an index of the centre
    if _ARTICLE_PATH.search(path):
        return True
    if root:
        root_path = urlsplit(root).path.rstrip('/')
        return looks_like_help_host(parts.hostname or '') and path.rstrip('/') != root_path and \
            path.startswith(root_path + '/') and not parts.query
    return False


def page_links(html: str, base_url: str) -> List[Tuple[str, str, str]]:
    """(absolute url, title, full text) for each link on a page, first
    occurrence only. The title is the card's heading when the link wraps a
    card, so an excerpt under it is not scored; the full text keeps the
    "8 articles" count that marks a section."""
    soup = BeautifulSoup(html or '', 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    seen, out = set(), []
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue
        url = normalize_url(urljoin(base_url, href))
        if url in seen:
            continue
        seen.add(url)
        full = a.get_text(' ', strip=True)
        heading = a.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong'])
        out.append((url, heading.get_text(' ', strip=True) if heading else full, full))
    return out


def sitemap_locs(xml: str) -> Tuple[List[str], List[str]]:
    """(page urls, child sitemap urls) from a sitemap or sitemap index."""
    soup = BeautifulSoup(xml or '', 'html.parser')
    pages, children = [], []
    for loc in soup.find_all('loc'):
        url = loc.get_text(strip=True)
        (children if loc.parent and loc.parent.name == 'sitemap' else pages).append(url)
    return pages, children


# Link text that is not a title
_GENERIC_TITLES = {'', 'read more', 'learn more', 'more', 'view all', 'see all', 'view more',
                   'see more', 'click here', 'here', 'documentation', 'docs'}


# ---------- finding the help centre ----------

def find_help_centre(app_tokens: List[str], catalog_links: Iterable[str],
                     guide_links: Iterable[str], override: Optional[str] = None,
                     fetch: Optional[Fetch] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """(root url, found_via, problem). See the module docstring for the order."""
    if override:
        return help_centre_root(override) if _HELP_PATH.search(urlsplit(override).path) \
            else normalize_url(override), 'override', None

    for via, links in (('catalog', catalog_links), ('guide', guide_links)):
        for url in links:
            host = host_of(url)
            # A help host (docs.gorgias.com), or a help path on the app's
            # main site (braze.com/docs, mailchimp.com/help)
            if is_doc_like(url) and host_matches_app(host, app_tokens) and \
                    (looks_like_help_host(host) or urlsplit(help_centre_root(url)).path != '/'):
                return help_centre_root(url), via, None

    domains = []
    for url in list(catalog_links) + list(guide_links):
        host = host_of(url)
        if is_partner_url(url) and host_matches_app(host, app_tokens):
            d = registered_domain(host)
            if d not in domains:
                domains.append(d)
    if not domains:
        return None, None, ("no link to the app's own site on its catalog page or in its Yotpo "
                            "guide; add its help centre to scripts/help_centres.json")
    if fetch is None:
        return None, None, f'no help centre linked; probing {domains[0]} was skipped'
    for d in domains[:2]:
        # The app's own homepage says where its help lives
        home = fetch(f'https://www.{d}/') or fetch(f'https://{d}/')
        if home and home.status == 200 and host_matches_app(host_of(home.url), app_tokens):
            for url, text, _ in page_links(home.text, home.url):
                if _HELP_LINK_TEXT.match(text.strip()) and is_partner_url(url) and \
                        host_matches_app(host_of(url), app_tokens):
                    return help_centre_root(url), 'homepage', None
    for d in domains[:2]:
        for candidate in (f'https://help.{d}/', f'https://support.{d}/', f'https://docs.{d}/',
                          f'https://knowledge.{d}/', f'https://{d}/help'):
            page = fetch(candidate)
            if page and page.status == 200 and _looks_like_help_page(page, app_tokens):
                return help_centre_root(page.url), 'probe', None
    return None, None, f"no help centre found at help./support./docs./knowledge.{domains[0]}"


# The words a site's header or footer uses for its help centre
_HELP_LINK_TEXT = re.compile(r'^(help( cent(er|re))?|support( cent(er|re))?|docs|documentation|'
                             r'knowledge ?base|help ?desk|resources? cent(er|re)|faqs?|guides?|'
                             r'learn|academy|customer support)$', re.I)


def _looks_like_help_page(page: Page, app_tokens: Iterable[str]) -> bool:
    if not host_matches_app(host_of(page.url), app_tokens):
        return False  # redirected to someone else's site
    head = (page.text or '')[:20000].lower()
    title = re.search(r'<title[^>]*>(.*?)</title>', head, re.S)
    title = title.group(1) if title else ''
    return any(w in title for w in ('help', 'support', 'docs', 'documentation', 'knowledge',
                                    'guide', 'academy', 'learn', 'faq')) \
        or 'zendesk' in head or 'intercom' in head


# ---------- the pool of articles a help centre lists ----------

def _zendesk_locale(root: str) -> Optional[str]:
    segs = [s for s in urlsplit(root).path.split('/') if s]
    if segs[:1] == ['hc']:
        return segs[1].lower() if len(segs) > 1 else 'en-us'
    return None


def _json(page: Optional[Page]):
    if not page or page.status != 200:
        return None
    try:
        return json.loads(page.text)
    except ValueError:
        return None


def _on_host(url: str, public_host: str) -> str:
    """A Zendesk API link on the centre's public host: the API can answer with
    x.zendesk.com links even when the centre lives at help.x.com."""
    parts = urlsplit(url)
    if (parts.hostname or '').endswith('.zendesk.com') and public_host:
        parts = parts._replace(netloc=public_host)
    return normalize_url(urlunsplit(parts))


def llms_pool(root: str, fetch: Fetch) -> List[Tuple[str, str]]:
    """(url, title) from the centre's llms.txt, a markdown list of its pages
    ("- [Title](url): description") that many help centres publish."""
    page = fetch(f'https://{host_of(root)}/llms.txt')
    if not page or page.status != 200 or '](' not in (page.text or ''):
        return []
    root_path = urlsplit(root).path.rstrip('/')
    pool = []
    for title, url in re.findall(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', page.text)[:5000]:
        url = normalize_url(re.sub(r'\.md$', '', url))
        if _same_site(url, root) and _is_article(url, root) and \
                (not root_path or urlsplit(url).path.startswith(root_path)):
            pool.append((url, title))
    return pool


def sitemap_pool(root: str, fetch: Fetch) -> List[Tuple[str, str]]:
    """(url, title from its slug) from the centre's sitemap, for centres
    whose pages are built in the browser."""
    host = host_of(root)
    sitemaps = []
    robots = fetch(f'https://{host}/robots.txt')
    if robots and robots.status == 200:
        sitemaps = re.findall(r'(?im)^\s*sitemap:\s*(\S+)', robots.text)
    sitemaps = [s for s in sitemaps if host_of(s) == host] or [f'https://{host}/sitemap.xml']
    root_path = urlsplit(root).path.rstrip('/')
    sitemaps.sort(key=lambda s: 0 if root_path and root_path in s else 1)
    english = re.compile(r'(^|[/_-])en([/_.-]|$)')
    urls, opened, queue = [], 0, list(sitemaps)
    while queue and opened < 3:
        page = fetch(queue.pop(0))
        opened += 1
        if not page or page.status != 200:
            continue
        pages, children = sitemap_locs(page.text)
        urls.extend(pages)
        queue = [c for c in children if english.search(c)] + \
            [c for c in children if not english.search(c)] + queue
    pool = []
    for url in urls[:20000]:
        url = normalize_url(url)
        if _same_site(url, root) and _is_article(url, root) and \
                (not root_path or urlsplit(url).path.startswith(root_path)):
            slug = urlsplit(url).path.rstrip('/').split('/')[-1]
            pool.append((url, re.sub(r'^\d+-', '', slug).replace('-', ' ').strip().capitalize()))
    return pool


# ---------- searching a help centre ----------

_QUERY_STOP = {'the', 'and', 'for', 'with', 'how', 'to', 'a', 'an', 'of', 'in', 'on', 'your', 'set',
               'up', 'use', 'using', 'create', 'creating', 'manage', 'managing'}


def query_words(query: str) -> List[str]:
    return [w for w in re.findall(r'[a-z0-9]+', query.lower()) if len(w) > 2 and w not in _QUERY_STOP]


def excluded(title: str, url: str) -> bool:
    """News, account admin, legal, Yotpo's own pages, other languages."""
    hay = _words(f'{title} {urlsplit(url).path}')
    if any(_words(w) in hay for w in _EXCLUDE):
        return True
    return bool(re.search(r'[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]', title or ''))


def match_titles(pool: List[Tuple[str, str]], query: str, n: int = PER_SEARCH) -> List[Tuple[str, str]]:
    """The pool's articles whose title or slug uses most of the query's words."""
    words = query_words(query)
    if not words:
        return []
    scored = []
    for i, (url, title) in enumerate(pool):
        slug = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ').replace('_', ' ')
        hay = _words(f'{title} {slug}')
        hits = sum(1 for w in words if f' {w}' in hay)   # prefix match: "trigger" finds "triggers"
        if hits >= max(1, (len(words) + 1) // 2):
            scored.append((-hits, i, url, title))
    scored.sort()
    return [(url, title) for _, _, url, title in scored[:n]]


def zendesk_search(root: str, fetch: Fetch, query: str, n: int = PER_SEARCH,
                   bodies: Optional[dict] = None) -> List[Tuple[str, str]]:
    """(url, title) from the Zendesk Help Center search API. Each article's
    text comes with it; it is kept in `bodies` (url -> text), so a centre
    whose pages show a bot check can still be read."""
    locale = _zendesk_locale(root) or 'en-us'
    page = fetch(f'https://{host_of(root)}/api/v2/help_center/articles/search.json'
                 f'?query={quote(query)}&locale={locale}&per_page=10')
    found = _json(page)
    if not found:
        return []
    public_host = host_of(page.url) or host_of(root)
    out = []
    for a in found.get('results', []):
        if a.get('draft') or not a.get('html_url'):
            continue
        url = _on_host(a['html_url'], public_host)
        if bodies is not None and a.get('body'):
            bodies[url] = html_text(a['body'], url)
        out.append((url, a.get('title', '')))
    return out[:n]


def pages_pool(root: str, home: Page, fetch: Fetch, sections: int = 6) -> List[Tuple[str, str]]:
    """(url, title) the centre lists on its home page and in its first
    sections."""
    pool, listings = [], []
    for url, text, full in page_links(home.text, home.url):
        if not _same_site(url, root):
            continue
        if _LISTING_PATH.search(urlsplit(url).path) or _COUNT_TEXT.search(full):
            listings.append(url)
        elif _is_article(url, root):
            pool.append((url, _clean_title(text)))
    for url in listings[:sections]:
        page = fetch(url)
        if page and page.status == 200:
            for a_url, text, _ in page_links(page.text, page.url):
                if _same_site(a_url, root) and _is_article(a_url, root) and a_url != url:
                    pool.append((a_url, _clean_title(text)))
    return pool


_BOT_CHECK = re.compile(r'just a moment|cf-chl|attention required|checking your browser|'
                        r'captcha|access denied|are you a robot', re.I)


def is_blocked(page: Optional[Page]) -> bool:
    """A bot check or refusal instead of the page."""
    if page is None:
        return False
    if page.status in (401, 403, 429, 503):
        return True
    return page.status == 200 and bool(_BOT_CHECK.search((page.text or '')[:5000])) \
        and len(page.text or '') < 60000


def html_text(html: str, url: str = '') -> str:
    from crawler import _extract_text

    class _Response:
        content = (html or '').encode('utf-8', 'replace')
    text, _ = _extract_text(url, _Response())
    return text or ''


def page_text(page: Optional[Page]) -> str:
    """A fetched article's text, as the crawler would store it."""
    if not page or page.status != 200:
        return ''
    if 'json' in (page.content_type or '') or is_blocked(page):
        return ''
    return html_text(page.text, page.url)


# ---------- the whole step ----------

def discover(app_names: List[str], catalog_links: Iterable[str], guide_links: Iterable[str],
             fetch: Fetch, model, sources: Iterable[Tuple[str, str]] = (),
             categories: Iterable[str] = (), override: Optional[str] = None) -> Mechanics:
    """The partner's articles on the functions this integration touches,
    found and confirmed as the module docstring says. `sources` are
    (label, text) the caller already read: the Yotpo guides and the
    catalog's partner pages."""
    catalog_links, guide_links = list(catalog_links), list(guide_links)
    categories, sources = list(categories), list(sources)
    tokens = name_tokens(*app_names)
    app = app_names[0] if app_names else ''
    result = Mechanics()
    root, via, problem = find_help_centre(tokens, catalog_links, guide_links, override, fetch)
    if not root:
        result.problem = problem
        return result
    result.help_centre, result.found_via = root, via

    home = None
    if _zendesk_locale(root) is None:
        home = fetch(root)
        if home and home.status == 200 and home.url and not _same_site(home.url, root) \
                and host_matches_app(host_of(home.url), tokens):
            root = help_centre_root(home.url)  # support.judge.me -> judge.me/help/en
        if home and home.status == 200 and _zendesk_locale(home.url) is not None:
            root = help_centre_root(home.url)
        result.help_centre = root
    zendesk = _zendesk_locale(root) is not None
    if not zendesk and is_blocked(home):
        result.blocked = True
        result.problem = (f'help centre {root} blocks automated reading (bot check); '
                          f'a person picks the articles')
        return result
    bodies = {}   # Zendesk article texts, from the search API

    # Titles a non-Zendesk centre lists: searched by matching words
    pool, methods = [], []
    if zendesk:
        methods.append('zendesk-search')
    else:
        for name, source in (('pages', lambda: pages_pool(root, home, fetch) if home and home.status == 200 else []),
                             ('llms.txt', lambda: llms_pool(root, fetch)),
                             ('sitemap', lambda: sitemap_pool(root, fetch))):
            found = source()
            if found:
                pool += found
                methods.append(name)
    result.method = ' + '.join(methods) or None

    # Step 1: the partner help centre's own articles about Yotpo join the sources
    own = zendesk_search(root, fetch, 'yotpo', 10, bodies) if zendesk else \
        [(u, t) for u, t in pool if 'yotpo' in f'{u} {t}'.lower()]
    for url, title in own[:YOTPO_ARTICLES]:
        text = bodies.get(url) or page_text(fetch(url))
        if text:
            sources.append((f'{app} help centre: {title}', text))
    result.sources = [label for label, _ in sources]

    # Step 2: the model lists the functions
    if model is None:
        result.problem = 'no model configured; nothing added'
        return result
    functions = model.extract_functions(app, categories, sources)
    if functions is None:
        result.problem = 'the model could not list the functions; nothing added'
        return result
    result.functions = [{'name': f.name, 'yotpo_role': f.yotpo_role, 'searches': f.searches}
                        for f in functions]
    if not functions:
        result.problem = 'the model found no partner function this integration touches'
        return result

    # Step 3: search for each function, alternating so every function gets
    # candidates. A centre with no search API: the model also picks from its
    # list of titles, since words alone miss ("Mim" is Dixa's sidebar).
    per_function = []
    for f in functions:
        found = []
        for q in f.searches:
            found += zendesk_search(root, fetch, q, bodies=bodies) if zendesk else match_titles(pool, q)
        per_function.append(found)
    if not zendesk and pool:
        titles, seen_urls = [], set()
        for url, title in pool:
            if url not in seen_urls and not excluded(title, url) and (title or '').strip():
                seen_urls.add(url)
                titles.append((url, title))
        chosen = model.shortlist(app, functions, [t for _, t in titles]) if titles else []
        per_function.insert(0, [titles[i] for i in chosen])
    picked, seen = [], set()
    for rank in range(max((len(x) for x in per_function), default=0)):
        for found in per_function:
            if rank < len(found) and len(picked) < MAX_CANDIDATES:
                url, title = found[rank]
                key = (url, re.sub(r'\s+', ' ', title or '').strip().lower())
                if url in seen or key[1] in seen or key[1] in _GENERIC_TITLES or excluded(title, url):
                    continue
                seen.update(key)
                picked.append((url, title))

    if not picked:
        # Not the model's judgement: this centre could not be searched or
        # listed (a login, a move, a page built in the browser)
        result.blocked = True
        result.problem = (f'the help centre at {root} could not be searched or listed '
                          f'(it may need a login, have moved, or need a browser); a person picks')
        return result

    # Step 4: read every candidate, and the model accepts or rejects it
    readable, refused = [], 0
    for url, title in picked:
        text = bodies.get(url, '')
        if not text:
            page = fetch(url)
            refused += is_blocked(page)
            text = page_text(page)
        if len(text) >= 200:
            readable.append((url, _clean_title(title) or url, text))
    result.checked = len(readable)
    if picked and not readable and not refused:
        result.blocked = True
        result.problem = (f'the articles at {root} show no text without a browser; '
                          f'a person picks the articles')
        return result
    if picked and refused > len(picked) // 2:
        result.blocked = True
        result.problem = (f'{refused} of {len(picked)} articles at {root} refused automated '
                          f'reading (bot check); a person picks the articles')
        return result
    if not readable:
        result.blocked = True
        result.problem = (f'the articles at {root} could not be read (no text without a '
                          f'browser, or refused); a person picks')
        return result
    verified = model.verify(app, functions, readable)
    if verified is None:
        result.problem = 'the model could not check the articles; nothing added'
        return result
    for i, function, why in verified:
        url, title, _ = readable[i]
        result.candidates.append(Candidate(url, title, function, why))
    if not result.candidates:
        result.problem = f'the model accepted none of the {len(readable)} articles it read'
    return result
