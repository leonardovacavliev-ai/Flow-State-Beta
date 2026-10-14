"""
Find a partner app's own "what this app does" articles.

A Yotpo guide explains the integration; it assumes the reader knows the other
app. Flow State answers better when it also has a few of the partner's own
general articles: what the app is, its main concepts, how to get started.
The catalog import uses this module to propose them, one help centre per
integration, a handful of articles each. Nothing is approved here: every
result becomes a proposal that an admin accepts or rejects URL by URL.

How a help centre is found, in order:
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

How articles are picked inside it:
  - Zendesk help centres: their public Help Center API (categories, then the
    articles of the overview-like categories). Many Zendesk centres show a bot
    check to page fetches but answer the API.
  - Anything else: the home page's links, scored on their text and address;
    the best one or two "Getting started"-like sections are opened and their
    first articles taken in the order the partner lists them.
  - If the pages gave nothing (centres that build their pages in the
    browser): the centre's llms.txt, a list of its articles with titles;
    then its sitemap, scored on the address alone.

The scoring is deliberately simple and visible (score_link). A wrong pick
costs one rejected proposal.

The network is injected: discover() takes a fetch(url) -> Page | None, so the
logic is tested on saved pages without touching the network.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Tuple
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from urls import normalize_url

DEFAULT_LIMIT = 3

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

# Overview-like wording, by weight. Text and address are both scored.
_STRONG = ('getting started', 'get started', 'start here', 'overview', 'introduction', 'intro to',
           'what is', 'welcome to', 'quick start', 'quickstart', 'basics', 'onboarding',
           'how it works', 'first steps', 'beginner', '101', 'new users', 'how to use')
_MEDIUM = ('features', 'key concepts', 'concepts', 'glossary', 'dashboard', 'navigating',
           'tour', 'set up your', 'setting up', 'setup guide', 'fundamentals', 'essentials', 'about')
# Not what this is for: account admin, legal, news, and the Yotpo integration
# itself (that one comes from the catalog, labelled by its own rules)
_NEGATIVE = ('api', 'changelog', 'release notes', "what's new", 'whats new', 'billing', 'invoice',
             'pricing', 'password', 'log in', 'login', 'sign in', 'gdpr', 'privacy', 'terms',
             'cookie', 'troubleshoot', 'error', 'faq', 'contact', 'status', 'careers', 'blog',
             'community', 'webinar', 'partner', 'legal', 'security', 'uninstall', 'cancel',
             'delete', 'yotpo', 'deprecated', 'legacy', 'migration', 'migrate', 'developer',
             'sdk', 'webhook', 'refund policy', 'accessibility', 'integration', 'integrations',
             ' x ')  # "Rebuy x Klaviyo": about another app


@dataclass
class Page:
    status: int
    url: str          # after redirects
    text: str
    content_type: str = ''


Fetch = Callable[[str], Optional[Page]]


@dataclass
class Candidate:
    url: str
    title: str
    score: int
    reason: str


@dataclass
class Overview:
    """What discover() found for one integration."""
    help_centre: Optional[str] = None     # root URL used
    found_via: Optional[str] = None       # override | catalog | guide | homepage | probe
    method: Optional[str] = None          # zendesk-api, pages, llms.txt, sitemap; joined by +
    candidates: List[Candidate] = field(default_factory=list)
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


def score_link(text: str, url: str, app_tokens: Iterable[str] = ()) -> Tuple[int, str]:
    """How much a link looks like a general overview of the app: (score, why).
    Below 1 means "not an overview"."""
    hay = _words(text) + _words(urlsplit(url).path)
    score, why = 0, []
    app_tokens = list(app_tokens)
    for w in _NEGATIVE:
        if _words(w) in hay and w.strip() not in app_tokens:
            return -5, f'skipped: "{w.strip()}"'
    for w in _STRONG:
        if _words(w) in hay:
            score += 3
            why.append(w)
            phrase = _words(w).strip()
            if any(re.search(rf' {re.escape(phrase)} (?:to |with |for |of |using )?{re.escape(t)} ', hay)
                   or f' {t} {phrase} ' in hay for t in app_tokens):
                score += 2  # "Introduction to Dixa", "Gorgias 101"
            break
    for w in _MEDIUM:
        if _words(w) in hay:
            score += 1
            why.append(w)
            break
    if score and any(f' {t} ' in hay for t in app_tokens):
        score += 1
        why.append('names the app')
    return score, ', '.join(why)


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


def _pick(cands: List[Candidate], limit: int) -> List[Candidate]:
    """Best first; on a tie, the partner's own order. One per URL and one per
    title (the same article in three languages is one article)."""
    seen, out = set(), []
    for _, c in sorted(enumerate(cands), key=lambda ic: (-ic[1].score, ic[0])):
        title = re.sub(r'\s+', ' ', c.title or '').strip().lower()
        if c.score > 0 and c.url not in seen and title not in seen and title not in _GENERIC_TITLES:
            seen.update((c.url, title))
            out.append(c)
    return out[:limit]


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


# ---------- picking articles ----------

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


def zendesk_candidates(root: str, fetch: Fetch, app_tokens: List[str]) -> List[Candidate]:
    """Overview articles through the Zendesk Help Center API: the overview-like
    categories, their first sections, and those sections' first articles, all
    in the partner's own order."""
    locale = _zendesk_locale(root) or 'en-us'
    base = f'https://{host_of(root)}/api/v2/help_center/{locale}'
    order = 'sort_by=position&sort_order=asc'
    cats_page = fetch(f'{base}/categories.json?per_page=100&{order}')
    cats = _json(cats_page)
    if not cats or 'categories' not in cats:
        return []
    # Where the centre really lives (help.attentivemobile.com -> help.attentive.com)
    public_host = host_of(cats_page.url) or host_of(root)
    cands = []
    scored = [(score_link(c.get('name', ''), '', app_tokens), c) for c in cats['categories']]
    for (cat_score, _), cat in [s for s in scored if s[0][0] > 0][:2]:
        secs = _json(fetch(f"{base}/categories/{cat['id']}/sections.json?per_page=100&{order}"))
        sections = (secs or {}).get('sections', [])
        # A "Getting started" section first; otherwise the category's first one
        sections.sort(key=lambda sec: -score_link(sec.get('name', ''), '', app_tokens)[0])
        taken = 0
        for sec in sections[:4]:
            if taken >= 6:
                break
            arts = (_json(fetch(f"{base}/sections/{sec['id']}/articles.json?per_page=30&{order}"))
                    or {}).get('articles', [])
            # Some centres leave every position at 0: then the order is just
            # "newest first", and only the titles say anything
            ordered = len({a.get('position') for a in arts}) > 1
            rank = 0
            for a in arts:
                s, w = score_link(a.get('title', ''), '', app_tokens)
                if a.get('draft') or s < 0:
                    continue
                rank += 1
                taken += 1
                if ordered and rank > 6:
                    break
                cands.append(Candidate(_on_host(a['html_url'], public_host), a.get('title', ''),
                                       cat_score + max(s, 0) + ((6 - rank) // 3 if ordered else 0),
                                       f'in "{cat.get("name")} › {sec.get("name")}"' + (f'; {w}' if w else '')))
    if not cands:
        app = app_tokens[0] if app_tokens else ''
        for query in ([f'getting started with {app}', f'{app} overview'] if app else []) + ['getting started']:
            found = _json(fetch(f'https://{host_of(root)}/api/v2/help_center/articles/search.json'
                                f'?query={quote(query)}&locale={locale}&per_page=10'))
            for a in (found or {}).get('results', []):
                s, w = score_link(a.get('title', ''), '', app_tokens)
                if s > 0:
                    cands.append(Candidate(_on_host(a['html_url'], public_host), a.get('title', ''), s,
                                           f'search "{query}"; {w}'))
    if not cands and cats['categories']:
        # No overview-like category: a centre's first section is usually its
        # introduction. Weak evidence, so it scores 1.
        first = cats['categories'][0]
        secs = _json(fetch(f"{base}/categories/{first['id']}/sections.json?per_page=100&{order}"))
        for sec in ((secs or {}).get('sections') or [])[:1]:
            arts = _json(fetch(f"{base}/sections/{sec['id']}/articles.json?per_page=30&{order}")) or {}
            for a in arts.get('articles', [])[:3]:
                if not a.get('draft') and score_link(a.get('title', ''), '', app_tokens)[0] >= 0:
                    cands.append(Candidate(_on_host(a['html_url'], public_host), a.get('title', ''), 1,
                                           f'first section of the help centre, "{sec.get("name")}"'))
    return cands


def llms_candidates(root: str, fetch: Fetch, app_tokens: List[str]) -> List[Candidate]:
    """Overview articles from the centre's llms.txt: a markdown list of its
    pages ("- [Title](url): description") that many help centres publish."""
    page = fetch(f'https://{host_of(root)}/llms.txt')
    if not page or page.status != 200 or '](' not in (page.text or ''):
        return []
    cands = []
    root_path = urlsplit(root).path.rstrip('/')
    for title, url in re.findall(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', page.text)[:3000]:
        url = normalize_url(re.sub(r'\.md$', '', url))
        if not _same_site(url, root) or not _is_article(url, root):
            continue
        if root_path and not urlsplit(url).path.startswith(root_path):
            continue  # another language
        s, w = score_link(title, url, app_tokens)
        if s > 0:
            cands.append(Candidate(url, title, s, w))
    return cands


def page_candidates(root: str, home: Page, fetch: Fetch, app_tokens: List[str]) -> List[Candidate]:
    """Overview articles from the help centre's own pages."""
    cands, listings = [], []
    for url, text, full in page_links(home.text, home.url):
        if not _same_site(url, root):
            continue
        score, why = score_link(text, url, app_tokens)
        if score <= 0:
            continue
        if _LISTING_PATH.search(urlsplit(url).path) or _COUNT_TEXT.search(full):
            listings.append((score, url, _clean_title(text)))
        elif _is_article(url, root):
            cands.append(Candidate(url, _clean_title(text), score, why))
    # Open the best one or two sections; their first articles are the
    # partner's own reading order for a newcomer
    for score, url, name in sorted(listings, key=lambda l: -l[0])[:2]:
        page = fetch(url)
        if not page or page.status != 200:
            continue
        rank = 0
        for a_url, text, _ in page_links(page.text, page.url):
            if not _same_site(a_url, root) or not _is_article(a_url, root) or a_url == url:
                continue
            s, why = score_link(text, a_url, app_tokens)
            if s < 0 or not text:
                continue
            rank += 1
            if rank > 6:
                break
            # Earlier in the section ranks higher, as the partner ordered it
            cands.append(Candidate(a_url, _clean_title(text), score + max(s, 0) + (6 - rank) // 3,
                                   f'in "{name}"' + (f'; {why}' if why else '')))
    return cands


def sitemap_candidates(root: str, fetch: Fetch, app_tokens: List[str]) -> List[Candidate]:
    """Overview articles from the sitemap's addresses, for centres whose pages
    are built in the browser."""
    host = host_of(root)
    sitemaps = []
    robots = fetch(f'https://{host}/robots.txt')
    if robots and robots.status == 200:
        sitemaps = re.findall(r'(?im)^\s*sitemap:\s*(\S+)', robots.text)
    sitemaps = [s for s in sitemaps if host_of(s) == host] or [f'https://{host}/sitemap.xml']
    # Prefer the root's own language: /en/sitemap.xml over /sitemap.xml
    root_path = urlsplit(root).path.rstrip('/')
    sitemaps.sort(key=lambda s: 0 if root_path and root_path in s else 1)

    urls, opened = [], 0
    queue = list(sitemaps)
    while queue and opened < 3:
        page = fetch(queue.pop(0))
        opened += 1
        if not page or page.status != 200:
            continue
        pages, children = sitemap_locs(page.text)
        urls.extend(pages)
        queue = [c for c in children if re.search(r'(^|[/_-])en([/_.-]|$)', c)] + \
            [c for c in children if not re.search(r'(^|[/_-])en([/_.-]|$)', c)] + queue
    cands = []
    for url in urls[:20000]:
        url = normalize_url(url)
        if not _same_site(url, root) or not _is_article(url, root):
            continue
        if root_path and not urlsplit(url).path.startswith(root_path):
            continue  # another language
        score, why = score_link('', url, app_tokens)
        if score > 0:
            slug = urlsplit(url).path.rstrip('/').split('/')[-1]
            title = re.sub(r'^\d+-', '', slug).replace('-', ' ').strip().capitalize()
            cands.append(Candidate(url, title, score, why))
    return cands


def discover(app_names: List[str], catalog_links: Iterable[str], guide_links: Iterable[str],
             fetch: Fetch, override: Optional[str] = None, limit: int = DEFAULT_LIMIT) -> Overview:
    """Up to `limit` general articles about the app, from its own help centre."""
    catalog_links, guide_links = list(catalog_links), list(guide_links)
    tokens = name_tokens(*app_names)
    result = Overview()
    root, via, problem = find_help_centre(tokens, catalog_links, guide_links, override, fetch)
    if not root:
        result.problem = problem
        return result
    result.help_centre, result.found_via = root, via

    cands, methods = [], []
    home = None
    if _zendesk_locale(root) is None:
        home = fetch(root)
        if home and home.status == 200 and home.url and not _same_site(home.url, root) \
                and host_matches_app(host_of(home.url), tokens):
            # support.judge.me -> judge.me/help/en: the centre moved
            root = help_centre_root(home.url)
            result.help_centre = root
    if _zendesk_locale(root) is not None or (home and _zendesk_locale(home.url) is not None):
        root = root if _zendesk_locale(root) is not None else help_centre_root(home.url)
        cands += zendesk_candidates(root, fetch, tokens)
        methods.append('zendesk-api')
    if len(_pick(cands, limit)) < limit and home and home.status == 200:
        cands += page_candidates(root, home, fetch, tokens)
        methods.append('pages')
    # Top up from the next source while too few were found
    for name, source in (('llms.txt', llms_candidates), ('sitemap', sitemap_candidates)):
        if len(_pick(cands, limit)) >= limit:
            break
        found = source(root, fetch, tokens)
        if found:
            cands += found
            methods.append(name)
    result.method = ' + '.join(methods) or None
    result.candidates = _pick(cands, limit)
    if not result.candidates:
        result.problem = (f'help centre {root} found, but none of its pages, llms.txt or sitemap '
                          f'offered an overview-like article; pick some by hand')
    return result
