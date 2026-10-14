"""
yotpo.com/integrations -> integrations and document proposals.

The pure half of scripts/import_catalog.py: parsing, grouping, the shrink
guard, link sorting, renamed-guide lookup and the report. No network and no
database here, so every rule is tested on saved pages
(ALL_INTEGRATIONS_UPDATE.md §4.3, roadmap C1.2).

Only Yotpo Loyalty & Referrals and Yotpo Reviews (incl. UGC) are in scope
(I9): the catalog tags no other product, and a card with neither is skipped.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app_overview import is_doc_like, is_partner_url
from integration_types import CATEGORY_DEFAULT_TYPE, default_type
from urls import normalize_url

CATALOG_URL = 'https://www.yotpo.com/integrations/'
SNAPSHOT_KEY = 'catalog_last_import'
SHRINK_LIMIT = 0.9

# Catalog product tags -> our products. Visual UGC counts as Reviews.
PRODUCT_TAGS = {'loyalty': 'loyalty', 'reviews': 'reviews', 'reviews-ugc': 'reviews'}

# Existing esps.name -> the catalog slugs it already covers. Without this the
# import would propose a second integration for every live one whose name is
# not its slug. Every live row except `global` and `other_webhook` (not catalog
# integrations) is here, plus C0.4's 13 under the names it plans for them.
KNOWN_MATCHES = {
    'klaviyo': ['klaviyo', 'klaviyo-loyalty'],
    'attentive': ['attentive', 'attentive-loyalty'],
    'dotdigital': ['dotdigital', 'dotdigital-loyalty'],
    'emarsys': ['emarsys', 'emarsys-loyalty'],
    'listrak': ['listrak', 'listrak-loyalty'],
    'ometria': ['ometria', 'ometria-loyalty'],
    'omnisend': ['omnisend', 'omnisend-loyalty'],
    'postscript': ['postscript', 'postscript-loyalty'],
    'bloomreach': ['bloomreach', 'bloomreach-loyalty'],
    'brevo_pushowl': ['brevo-pushowl', 'brevo-pushowl-loyalty'],
    # C0.4
    'braze': ['braze', 'braze-loyalty'],
    'cordial': ['cordial', 'cordial-loyalty'],
    'drip': ['drip', 'drip-loyalty'],
    'hubspot': ['hubspot', 'hubspot-loyalty'],
    'insider': ['insider', 'insider-loyalty'],
    'mailchimp': ['mailchimp', 'mailchimp-loyalty'],
    'optimizely': ['optimizely', 'optimizely-loyalty', 'zaius', 'zaius-loyalty'],
    'optimove': ['optimove', 'optimove-loyalty'],
    'remarkety': ['remarkety', 'remarkety-loyalty'],
    'retention_science': ['retention-science', 'retention-science-loyalty'],
    'rule': ['rule', 'rule-loyalty'],
    'sailthru': ['sailthru', 'sailthru-loyalty'],
    'salesforce_marketing_cloud': ['salesforce-marketing-cloud', 'salesforce-marketing-cloud-loyalty'],
}

YOTPO_DOC_HOSTS = ('support.yotpo.com', 'develop.yotpo.com')


@dataclass
class Card:
    slug: str
    url: str
    title: str
    description: str
    products: List[str]
    categories: List[str]


@dataclass
class Integration:
    name: str                       # esps.name
    display_name: str
    slugs: List[str]
    categories: List[str]
    products: List[str]
    description: str
    platform_type: Optional[str]
    existing: bool = False
    matched_by: str = 'new'         # known | name | new
    type_conflict: List[str] = field(default_factory=list)  # types its categories disagree on


# ---------- catalog page ----------

def _split(value: Optional[str]) -> List[str]:
    return [v.strip().lower() for v in (value or '').split(',') if v.strip()]


def slug_from_url(url: str) -> str:
    return urlsplit(url.strip()).path.rstrip('/').split('/')[-1]


def parse_catalog(html: str) -> List[Card]:
    """One Card per detail page. The page repeats some cards in a "Featured"
    strip; the first copy of each detail page wins."""
    soup = BeautifulSoup(html or '', 'html.parser')
    cards, seen = [], set()
    for div in soup.select('div.integration-card'):
        a = div.find('a', href=True)
        if not a:
            continue
        url = normalize_url(a['href'])
        slug = slug_from_url(url)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        title = div.find('h3')
        desc = div.find(class_='integration-card__description')
        products = []
        for tag in _split(div.get('data-products')):
            p = PRODUCT_TAGS.get(tag)
            if p and p not in products:
                products.append(p)
        cards.append(Card(
            slug=slug, url=url,
            title=title.get_text(' ', strip=True) if title else slug,
            description=desc.get_text(' ', strip=True) if desc else '',
            products=products,
            categories=_split(div.get('data-categories')),
        ))
    return cards


def snapshot(cards: List[Card]) -> Dict:
    return {'cards': len(cards), 'slugs': sorted(c.slug for c in cards)}


def guard(cards: List[Card], previous: Optional[Dict]) -> Optional[str]:
    """Why this parse must not be written, or None. A redesigned or half-loaded
    page parses to fewer cards; writing it would look like mass removals."""
    if not cards:
        return 'the catalog page has no integration cards'
    if not any(c.categories for c in cards):
        return 'the catalog cards have no categories'
    if previous and previous.get('cards'):
        if len(cards) < SHRINK_LIMIT * previous['cards']:
            return (f"the catalog has {len(cards)} cards, fewer than 90% of the "
                    f"{previous['cards']} at the last import")
    return None


def slug_base(slug: str) -> str:
    """'gorgias-loyalty' -> 'gorgias': the second card a partner has for
    Loyalty. 'reamaze-2' -> 'reamaze': WordPress's suffix for a reused slug."""
    slug = slug[:-len('-loyalty')] if slug.endswith('-loyalty') else slug
    return re.sub(r'-\d+$', '', slug)


def name_for(slug: str) -> str:
    return slug_base(slug).replace('-', '_')


def _display_name(titles: List[str]) -> str:
    """The shortest card title, without a trailing 'Loyalty' ('Gorgias Loyalty'
    and 'Gorgias' -> 'Gorgias')."""
    cleaned = [re.sub(r'\s+(?:for\s+)?loyalty(?:\s*&\s*referrals)?$', '', t, flags=re.I).strip() or t
               for t in titles]
    return min(cleaned, key=len)


def group_cards(cards: List[Card], existing: Iterable[str],
                known: Optional[Dict[str, List[str]]] = None) -> Tuple[List[Integration], List[str]]:
    """(integrations, clashes). Cards for one partner become one integration:
    by KNOWN_MATCHES first, then by slug base. A card whose derived name is
    already the name of a known integration covering other slugs is a clash
    for Leo: it is left out rather than merged into the wrong row."""
    known = KNOWN_MATCHES if known is None else known
    existing = set(existing)
    slug_owner = {s: name for name, slugs in known.items() for s in slugs}
    groups: Dict[str, List[Card]] = {}
    how: Dict[str, str] = {}
    clashes = []
    for card in cards:
        if card.slug in slug_owner:
            name = slug_owner[card.slug]
            how[name] = 'known'
        else:
            name = name_for(card.slug)
            if name in known:
                clashes.append(f'{card.slug}: would be named "{name}", which is the integration '
                               f'for {", ".join(known[name])}')
                continue
            how.setdefault(name, 'name' if name in existing else 'new')
        groups.setdefault(name, []).append(card)

    out = []
    for name, group in groups.items():
        categories, products = [], []
        for c in group:
            categories += [x for x in c.categories if x not in categories]
            products += [p for p in c.products if p not in products]
        types = sorted({CATEGORY_DEFAULT_TYPE[c] for c in categories if c in CATEGORY_DEFAULT_TYPE})
        out.append(Integration(
            name=name,
            display_name=_display_name([c.title for c in group]),
            slugs=[c.slug for c in group],
            categories=categories,
            products=products,
            description=max((c.description for c in group), key=len, default=''),
            platform_type=default_type(categories),
            existing=name in existing,
            matched_by=how.get(name, 'new'),
            type_conflict=types if len(types) > 1 else [],
        ))
    out.sort(key=lambda i: i.name)
    return out, clashes


# ---------- detail pages ----------

def strip_tracking(url: str) -> str:
    """Drop utm_* parameters: they never pick a different page."""
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith('utm_')]
    return urlunsplit(parts._replace(query=urlencode(query)))


def clean_link(href: str) -> str:
    """normalize_url, minus tracking parameters; Yotpo's own docs always on
    https (one catalog card links a guide over http)."""
    url = normalize_url(strip_tracking(normalize_url(href)))
    if url.startswith('http://') and (urlsplit(url).hostname or '') in YOTPO_DOC_HOSTS:
        url = 'https://' + url[len('http://'):]
    return url


def is_yotpo_doc(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or '').lower()
    if host == 'support.yotpo.com':
        return parts.path.startswith('/docs/')
    return host == 'develop.yotpo.com' and parts.path not in ('', '/')


# A partner page whose address names Yotpo is usually its article about the
# integration (addglow.com/yotpo-integration, harborloyalty.com/yotpo-setup),
# unless it is an install button, a settings screen or company news.
_NOT_A_GUIDE = re.compile(r'install|/auth/|settings|login|signup|admin|contact|referral|award|'
                          r'announce|named|case-study|partnership|/meet|news|spotlight', re.I)


def is_partner_yotpo_page(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return is_partner_url(url) and 'yotpo' in path and not _NOT_A_GUIDE.search(path)


@dataclass
class DetailLinks:
    yotpo: List[str] = field(default_factory=list)          # guides on support/develop.yotpo.com
    partner_docs: List[str] = field(default_factory=list)   # documentation-like partner pages
    partner_other: List[str] = field(default_factory=list)  # homepages, blogs, shortlinks


def detail_links(html: str) -> DetailLinks:
    """Links from a detail page's Resources box and body, sorted. The site's
    header and footer (Help Center, API reference, social) are left out."""
    soup = BeautifulSoup(html or '', 'html.parser')
    for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
        tag.decompose()
    area = soup.select_one('section.main_content_wrapper') or soup.find('main') or soup
    out = DetailLinks()
    for a in area.find_all('a', href=True):
        raw = a['href']
        if 'integrations-center.yotpo.com' in raw or 'login.yotpo.com' in raw:
            continue  # "Install" buttons
        url = clean_link(raw)
        if is_yotpo_doc(url):
            bucket = out.yotpo
        elif is_doc_like(url) or is_partner_yotpo_page(url):
            bucket = out.partner_docs
        elif is_partner_url(url):
            bucket = out.partner_other
        else:
            continue
        if url not in bucket:
            bucket.append(url)
    return out


def guide_outbound_links(html: str) -> List[str]:
    """Partner links inside a Yotpo guide's article body, for finding the
    partner's help centre."""
    soup = BeautifulSoup(html or '', 'html.parser')
    for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
        tag.decompose()
    area = soup.find('article') or soup.find('main') or soup
    out = []
    for a in area.find_all('a', href=True):
        url = clean_link(a['href'])
        if is_partner_url(url) and url not in out:
            out.append(url)
    return out


# ---------- renamed guides ----------

_STOP = {'a', 'an', 'the', 'and', 'for', 'with', 'to', 'of', 'in', 'on', 'yotpo', 'how'}


def _stems(slug: str) -> List[str]:
    words = [w for w in slug.lower().split('-') if w and w not in _STOP]
    return [w[:-1] if len(w) > 3 and w.endswith('s') else w for w in words]


def find_renamed(dead_url: str, sitemap_urls: Iterable[str], name_tokens: Iterable[str] = ()) -> List[str]:
    """Live guides that are probably the dead one under a new slug.

    First: slugs sharing the dead one's first two stem words. Given the
    partner's name tokens, those must also carry the name: 'integrating-yotpo-
    loyalty-referrals-with-optimove' shares its first words with a dozen other
    partners' guides. If that finds nothing, a guide whose slug carries the
    name and says integration or guide (builder-integration-guide ->
    builderio-integration-guide)."""
    tokens = [t for t in name_tokens if t]
    dead = normalize_url(dead_url)
    live = [normalize_url(u) for u in sitemap_urls]
    live = [u for u in live if u != dead and urlsplit(u).path.startswith('/docs/')]

    def named(url):
        slug = slug_from_url(url).lower()
        return any(t in slug or t in slug.replace('-', '') for t in tokens)

    stems = _stems(slug_from_url(dead_url))[:2]
    out = [u for u in live if len(stems) == 2 and _stems(slug_from_url(u))[:2] == stems]
    if tokens:
        out = [u for u in out if named(u)]
        if not out:
            out = [u for u in live if named(u) and re.search(r'integrat|guide', slug_from_url(u))]
    return out


def sitemap_entries(xml: str) -> Dict[str, Optional[str]]:
    """{url: lastmod} from support.yotpo.com/sitemap-en.xml."""
    soup = BeautifulSoup(xml or '', 'html.parser')
    out = {}
    for u in soup.find_all('url'):
        loc = u.find('loc')
        if loc:
            lastmod = u.find('lastmod')
            out[normalize_url(loc.get_text(strip=True))] = lastmod.get_text(strip=True) if lastmod else None
    return out
