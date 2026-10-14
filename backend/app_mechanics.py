"""
Find a partner app's mechanics: its own articles on the features a Yotpo
integration plugs into.

A Yotpo guide explains how to connect the integration. To answer well, Flow
State also needs to know how the partner's side behaves: for an email
platform, how its flows, triggers, delays and segments work; for Recharge, how
discount codes apply to subscriptions. Leo picked exactly such articles for
the email platforms already in the knowledge base. The catalog import uses
this module to propose them for every integration: a few per integration,
each tied to a topic. Nothing is approved here: every result becomes a
proposal that an admin accepts or rejects URL by URL.

What to look for comes from backend/mechanics_topics.py: topics per catalog
category (flows, discount codes, customer sidebar…), ranked by what the
integration's own Yotpo guide and partner pages talk about.

How the help centre is found, in order:
  1. an admin override (scripts/help_centres.json);
  2. a documentation link the catalog detail page itself gives;
  3. a link inside the Yotpo guide to the partner's documentation;
  4. when one of the links above gives the partner's domain: the help link
     on its homepage ("Help Center", "Support", "Docs"); failing that,
     probing help./support./docs./knowledge.<domain>.
A host only counts when its name carries the app's name (docs.gorgias.com for
Gorgias), so a Shopify link inside the Gorgias guide is never taken as
Gorgias's help centre. Names are never guessed into domains: "Rule" or
"Target" would find someone else's site.

How articles are found inside it, for each top topic:
  - Zendesk help centres: their public search API, with the topic's searches.
    Many Zendesk centres show a bot check to page fetches but answer the API.
  - Anything else: the titles the centre lists itself (home page, the
    sections named like a topic, llms.txt) and the addresses in its sitemap.
An article is on topic when its title (or address) uses the topic's words;
explanations ("Managing…", "How … works") rank above troubleshooting.

Bounded: one help centre per integration, about ten requests, one per second
per host. Not a crawler.

The network is injected: discover() takes a fetch(url) -> Page | None, so the
logic is tested on saved pages without touching the network.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Tuple
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from mechanics_topics import Topic, mentions, rank_topics, topics_for
from urls import normalize_url

DEFAULT_LIMIT = 3
TOPICS_TRIED = 4

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
# Usually not how the feature works: problems, money, other integrations
_DOWNRANK = ('troubleshoot', 'troubleshooting', 'error', 'errors', 'issue', 'issues', 'not working',
             'faq', 'faqs', 'billing', 'pricing', 'invoice', 'migration', 'migrate', 'integration',
             'integrations', 'api', 'developer', 'developers', 'sdk', 'legacy', 'deprecated', 'why',
             'warning', ' x ', 'not', "isn't", "doesn't", "don't", "can't", 'cannot', 'unable',
             'failed', 'fails', 'compliance', 'webhook', 'webhooks', 'video')
# Explanations of a feature
_EXPLAINS = ('how', 'managing', 'manage', 'creating', 'create', 'understanding', 'understand',
             'about', 'overview', 'setting up', 'set up', 'using', 'use', 'guide', 'getting started',
             'introduction', 'works', 'configure', 'configuring', 'adding', 'add', 'build', 'building')


@dataclass
class Candidate:
    url: str
    title: str
    score: int
    reason: str
    topic: str = ''


@dataclass
class Mechanics:
    """What discover() found for one integration."""
    help_centre: Optional[str] = None     # root URL used
    found_via: Optional[str] = None       # override | catalog | guide | homepage | probe
    method: Optional[str] = None          # zendesk-search, pages, llms.txt, sitemap; joined by +
    topics: List[str] = field(default_factory=list)   # the topics searched, best first
    candidates: List[Candidate] = field(default_factory=list)
    problem: Optional[str] = None         # why nothing was found, in plain words


def score_article(title: str, url: str, topic: Topic) -> int:
    """How well an article explains one topic. 0 or less: not for this topic."""
    path = urlsplit(url).path
    slug = path.rstrip('/').rsplit('/', 1)[-1]
    text = f'{title} {slug.replace("-", " ").replace("_", " ")}'
    # The whole address counts against an article (/developer/, /video/), only
    # its title and slug for it
    hay = _words(f'{text} {path}')
    if any(_words(w) in hay for w in _EXCLUDE):
        return -1
    if re.search(r'[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]', title or ''):
        return -1  # a Japanese, Chinese or Korean copy of an article
    hits = mentions(text, topic.words)
    if not hits:
        return 0
    score = 3 + min(hits - 1, 2)
    if any(_words(w) in hay for w in _EXPLAINS):
        score += 1
    if any(_words(w) in hay for w in _DOWNRANK):
        score -= 3
    return score


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


def zendesk_pool(root: str, fetch: Fetch, topics: List[Topic]) -> List[Tuple[str, str]]:
    """(url, title) from the Help Center search API, two searches per topic."""
    locale = _zendesk_locale(root) or 'en-us'
    pool = []
    for topic in topics:
        for query in topic.queries[:2]:
            page = fetch(f'https://{host_of(root)}/api/v2/help_center/articles/search.json'
                         f'?query={quote(query)}&locale={locale}&per_page=10')
            found = _json(page)
            if not found:
                continue
            public_host = host_of(page.url) or host_of(root)
            for a in found.get('results', []):
                if not a.get('draft') and a.get('html_url'):
                    pool.append((_on_host(a['html_url'], public_host), a.get('title', '')))
    return pool


def pages_pool(root: str, home: Page, fetch: Fetch, topics: List[Topic]) -> List[Tuple[str, str]]:
    """(url, title) the centre lists on its home page, plus the articles of
    the one or two sections named like a topic (a "Flows" or "Discounts"
    section)."""
    pool, sections = [], []
    for url, text, full in page_links(home.text, home.url):
        if not _same_site(url, root):
            continue
        if _LISTING_PATH.search(urlsplit(url).path) or _COUNT_TEXT.search(full):
            best = max((mentions(text, t.words) for t in topics), default=0)
            if best:
                sections.append((best, url))
        elif _is_article(url, root):
            pool.append((url, _clean_title(text)))
    for _, url in sorted(sections, key=lambda s: -s[0])[:2]:
        page = fetch(url)
        if page and page.status == 200:
            for a_url, text, _ in page_links(page.text, page.url):
                if _same_site(a_url, root) and _is_article(a_url, root) and a_url != url:
                    pool.append((a_url, _clean_title(text)))
    return pool


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


# ---------- picking ----------

def pick(pool: List[Tuple[str, str]], ranked: List[Tuple[Topic, int]],
         limit: int = DEFAULT_LIMIT) -> List[Candidate]:
    """The best article for each topic in turn, best topic first, then a
    second round, until `limit`. One per URL and per title."""
    best_by_topic = []
    for topic, mentioned in ranked[:TOPICS_TRIED]:
        cands = []
        for i, (url, title) in enumerate(pool):
            score = score_article(title, url, topic)
            if score >= 3:
                why = f'{topic.name}' + (' (the Yotpo guide or partner pages mention it)'
                                         if mentioned else '')
                cands.append((score, i, Candidate(url, title, score, why, topic.name)))
        cands.sort(key=lambda c: (-c[0], c[1]))
        best_by_topic.append([c for _, _, c in cands])
    seen, out = set(), []
    for round_ in range(limit):
        for cands in best_by_topic:
            for c in cands[round_:]:
                key_title = re.sub(r'\s+', ' ', c.title or '').strip().lower()
                if c.url in seen or key_title in seen or key_title in _GENERIC_TITLES:
                    continue
                seen.update((c.url, key_title))
                out.append(c)
                break
            if len(out) >= limit:
                return out
    return out


def discover(app_names: List[str], catalog_links: Iterable[str], guide_links: Iterable[str],
             fetch: Fetch, categories: Iterable[str] = (), platform_type: Optional[str] = None,
             context: str = '', override: Optional[str] = None,
             limit: int = DEFAULT_LIMIT) -> Mechanics:
    """Up to `limit` articles on how the partner's side of the integration
    works, from its own help centre."""
    catalog_links, guide_links = list(catalog_links), list(guide_links)
    tokens = name_tokens(*app_names)
    ranked = rank_topics(topics_for(categories, platform_type), context)
    result = Mechanics(topics=[t.name for t, _ in ranked[:TOPICS_TRIED]])
    root, via, problem = find_help_centre(tokens, catalog_links, guide_links, override, fetch)
    if not root:
        result.problem = problem
        return result
    result.help_centre, result.found_via = root, via
    top = [t for t, _ in ranked[:TOPICS_TRIED]]

    home = None
    if _zendesk_locale(root) is None:
        home = fetch(root)
        if home and home.status == 200 and home.url and not _same_site(home.url, root) \
                and host_matches_app(host_of(home.url), tokens):
            root = help_centre_root(home.url)  # support.judge.me -> judge.me/help/en
            result.help_centre = root
        if home and home.status == 200 and _zendesk_locale(home.url) is not None:
            root = help_centre_root(home.url)
            result.help_centre = root

    pool, methods = [], []
    sources = []
    if _zendesk_locale(root) is not None:
        sources.append(('zendesk-search', lambda: zendesk_pool(root, fetch, top)))
    if home and home.status == 200:
        sources.append(('pages', lambda: pages_pool(root, home, fetch, top)))
    sources += [('llms.txt', lambda: llms_pool(root, fetch)), ('sitemap', lambda: sitemap_pool(root, fetch))]
    for name, source in sources:
        if len(pick(pool, ranked, limit)) >= limit:
            break
        found = source()
        if found:
            pool += found
            methods.append(name)
    result.method = ' + '.join(methods) or None
    result.candidates = pick(pool, ranked, limit)
    if not result.candidates:
        result.problem = (f'help centre {root} found, but no article on '
                          f'{", ".join(result.topics[:3])}; pick some by hand')
    return result
