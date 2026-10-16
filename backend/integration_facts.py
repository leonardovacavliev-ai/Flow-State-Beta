"""
The integration facts block: what the database knows about an integration,
placed at the top of the chat context for the non-messaging platform types
(ALL_INTEGRATIONS_UPDATE.md §4.6.5):

    ## Integration
    Name: Gorgias
    Type: Help Desk & CRM (platform type: service)
    Works with: Yotpo Loyalty & Referrals, Yotpo Reviews
    Yotpo plans: Premium, Enterprise
    Store platforms: Shopify, Shopify Plus
    Documentation: 1 Yotpo guide, 2 partner articles
    Yotpo guide: https://support.yotpo.com/...

The model checks eligibility (step 1 of every non-messaging checklist)
against these lines instead of guessing what kind of tool it is dealing
with. It lives in the context, not the system prompt, so the five prompts
stay static. Messaging chats don't get it until a before/after run of the
messaging eval shows no regression; until then their context stays
byte-identical (I3).

facts_block() and source_kind() are pure. load_facts() reads the database,
cached per integration for FACTS_CACHE_SECONDS.
"""

import time
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

from doc_header import HEADER_SCAN_CHARS, parse_header
from integration_types import TYPE_LABELS, category_name
from prompt_template import PRODUCT_NAMES

FACTS_CACHE_SECONDS = 60

# esp_documents.source_kind (plan §4.2). Nothing writes the column yet, so a
# document without one is classified from its address.
SOURCE_KINDS = ('yotpo_support', 'yotpo_developer', 'partner', 'pasted')

# How a source header names each kind (rag_context, source_style='integration')
SOURCE_LABELS = {
    'yotpo_support': 'Yotpo guide',
    'yotpo_developer': 'Yotpo developer documentation',
    'partner': 'partner documentation',
    'pasted': 'text pasted by a Yotpo admin',
}

# How the Documentation line counts each kind: (one, many)
_COUNT_NOUNS = {
    'yotpo_support': ('Yotpo guide', 'Yotpo guides'),
    'yotpo_developer': ('Yotpo developer page', 'Yotpo developer pages'),
    'partner': ('partner article', 'partner articles'),
    'pasted': ('pasted text', 'pasted texts'),
}

# At most this many guide links in the block; one is the usual case
MAX_GUIDE_LINKS = 3


def source_kind(url: Optional[str], stored: Optional[str] = None) -> str:
    """The document's source kind: the stored one, or one read from its
    address. support.yotpo.com is Yotpo's help centre; other yotpo.com hosts
    are its developer documentation; local:// is text an admin pasted."""
    if stored in SOURCE_KINDS:
        return stored
    url = (url or '').strip()
    if url.startswith('local://'):
        return 'pasted'
    host = (urlparse(url).hostname or '').lower()
    if host == 'support.yotpo.com':
        return 'yotpo_support'
    if host == 'yotpo.com' or host.endswith('.yotpo.com'):
        return 'yotpo_developer'
    return 'partner'


def _indexed(doc: Dict) -> bool:
    """In the index: crawled, not retired, and not indexed to nothing.
    vector_count NULL is a document indexed before counts were recorded."""
    return (doc.get('crawl_status') == 'completed' and not doc.get('retired_at')
            and (doc.get('vector_count') is None or doc.get('vector_count') > 0))


def _union(lists: Iterable[Iterable[str]]) -> List[str]:
    """Values in first-seen order, without repeats (case-insensitive)."""
    out, seen = [], set()
    for values in lists:
        for v in values or ():
            v = (v or '').strip()
            if v and v.lower() not in seen:
                seen.add(v.lower())
                out.append(v)
    return out


def facts_block(esp_row: Dict, documents: List[Dict]) -> str:
    """The block for one integration. Lines with no data are left out.

    esp_row: display_name (or name), platform_type, categories and products
        (lists of catalog slugs and product labels).
    documents: its esp_documents rows as dicts: url, product, source_kind,
        supported_plans, supported_platforms, content_head (the first
        HEADER_SCAN_CHARS of its text), crawl_status, vector_count, retired_at.
    """
    platform_type = esp_row.get('platform_type')
    lines = ['## Integration', f"Name: {esp_row.get('display_name') or esp_row.get('name')}"]

    kind = ', '.join(category_name(c) for c in esp_row.get('categories') or [])
    kind = kind or TYPE_LABELS.get(platform_type, '')
    if kind and platform_type:
        lines.append(f"Type: {kind} (platform type: {platform_type})")
    elif kind or platform_type:
        lines.append(f"Type: {kind or platform_type}")

    indexed = [d for d in documents if _indexed(d)]

    # The same rule as the admin's product ticks (admin_integrations_routes.
    # effective_products): the catalog's products plus any a document is
    # labelled with. Shared documents don't count.
    products = set(esp_row.get('products') or [])
    products |= {d.get('product') for d in indexed}
    works_with = [PRODUCT_NAMES[p] for p in ('loyalty', 'reviews') if p in products]
    if works_with:
        lines.append(f"Works with: {', '.join(works_with)}")

    # Plans and platforms come from the header of Yotpo's own guides: the
    # stored fields when the crawl wrote them, otherwise read from the text
    guides = [d for d in indexed if source_kind(d.get('url'), d.get('source_kind')) == 'yotpo_support']
    headers = [None if (d.get('supported_plans') and d.get('supported_platforms'))
               else parse_header(d.get('content_head')) for d in guides]
    plans = _union(d.get('supported_plans') or (h or {}).get('plans') for d, h in zip(guides, headers))
    platforms = _union(d.get('supported_platforms') or (h or {}).get('platforms')
                       for d, h in zip(guides, headers))
    if plans:
        lines.append(f"Yotpo plans: {', '.join(plans)}")
    if platforms:
        lines.append(f"Store platforms: {', '.join(platforms)}")

    counts = {}
    for d in indexed:
        k = source_kind(d.get('url'), d.get('source_kind'))
        counts[k] = counts.get(k, 0) + 1
    parts = [f"{counts[k]} {_COUNT_NOUNS[k][counts[k] != 1]}" for k in SOURCE_KINDS if counts.get(k)]
    if parts:
        lines.append(f"Documentation: {', '.join(parts)}")
    for d in guides[:MAX_GUIDE_LINKS]:
        lines.append(f"Yotpo guide: {d.get('url')}")
    return '\n'.join(lines) + '\n\n'


_cache: Dict[str, tuple] = {}


def load_facts(db, name: str, use_cache: bool = True) -> Optional[Dict]:
    """{'block', 'display_name', 'platform_type'} for the integration called
    `name`, or None when there is no such row. Cached for
    FACTS_CACHE_SECONDS: chat asks on every message for a non-messaging
    integration. The admin's preview reads fresh (use_cache=False)."""
    now = time.monotonic()
    hit = _cache.get(name)
    if use_cache and hit and now - hit[0] <= FACTS_CACHE_SECONDS:
        return hit[1]
    from esp_manager import _json_list
    rows = db.execute_query("""
        SELECT id, name, display_name, platform_type, categories, products
        FROM esps WHERE name = %s
    """, (name,), fetch=True)
    if not rows:
        result = None
    else:
        esp_id, key, display, ptype, categories, products = rows[0]
        esp_row = {'name': key, 'display_name': display, 'platform_type': ptype,
                   'categories': _json_list(categories), 'products': _json_list(products)}
        docs = db.execute_query(f"""
            SELECT url, product, source_kind, supported_plans, supported_platforms,
                   substr(content, 1, {HEADER_SCAN_CHARS}), crawl_status, vector_count, retired_at
            FROM esp_documents WHERE esp_id = %s ORDER BY created_at, url
        """, (esp_id,), fetch=True) or []
        documents = [{
            'url': r[0], 'product': r[1], 'source_kind': r[2],
            'supported_plans': _json_list(r[3]), 'supported_platforms': _json_list(r[4]),
            'content_head': r[5], 'crawl_status': r[6], 'vector_count': r[7], 'retired_at': r[8],
        } for r in docs]
        result = {'block': facts_block(esp_row, documents), 'display_name': display or key,
                  'platform_type': ptype}
    _cache[name] = (now, result)
    return result
