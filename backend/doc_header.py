"""
The header at the top of a Yotpo support guide (support.yotpo.com, Document360).

Stored content of a guide opens like this:

    Products

    Reviews

    Loyalty & Referrals

    ####### Supported plans

    Premium, Enterprise

    ####### eCommerce Platform

    Shopify, Shopify Plus

with one "Supported plans" / "eCommerce Platform" pair per product slot of the
Document360 template. Slots the guide does not use keep the template's
placeholder, "Change this text for SMS & Email", which is not content.

Pure: no database, no network. The header is only ever a suggestion for a
human (I1): an admin labels every document. Only Loyalty & Referrals and
Reviews (incl. Visual UGC) are in scope (I9); the other Yotpo products are
read past, never returned.
"""

import re
from typing import Dict, List, Optional

HEADER_SCAN_CHARS = 1500

# "Products" (or "YotpoProducts") alone on its line opens the header
_PRODUCTS_LINE = re.compile(r"^\s*(?:Yotpo)?\s*Products?\s*:?\s*$", re.I)
# A markdown heading, which is how _extract_text writes the plans/platform labels
_HEADING = re.compile(r"^#+\s*")
_PLACEHOLDER = re.compile(r"^change this text for\b", re.I)
_PLANS_LABEL = re.compile(r"^supported plans?$", re.I)
_PLATFORMS_LABEL = re.compile(r"^(?:e-?commerce platforms?|supported platforms?|platforms?)$", re.I)

# Product names as the header writes them -> our label. None = a Yotpo product
# outside v2's scope, recognised so it is not mistaken for the end of the list.
_PRODUCT_NAMES = {
    'loyalty': 'loyalty',
    'loyalty & referrals': 'loyalty',
    'loyalty and referrals': 'loyalty',
    'referrals': 'loyalty',
    'reviews': 'reviews',
    'visual ugc': 'reviews',
    'ugc': 'reviews',
    'reviews & ugc': 'reviews',
    'sms & email': None,
    'sms and email': None,
    'sms': None,
    'email': None,
    'subscriptions': None,
}


def _lines(text: str) -> List[str]:
    return [l.strip() for l in text[:HEADER_SCAN_CHARS].split('\n') if l.strip()]


def _split_values(line: str) -> List[str]:
    return [v.strip() for v in line.split(',') if v.strip()]


def parse_header(text: Optional[str]) -> Dict:
    """{products: set, plans: list, platforms: list} from a guide's header.

    Empty when there is no header. plans and platforms are the union over the
    product slots, in first-seen order, without template placeholders.
    """
    result = {'products': set(), 'plans': [], 'platforms': []}
    if not text:
        return result
    lines = _lines(text)
    start = next((i for i, l in enumerate(lines) if _PRODUCTS_LINE.match(l)), None)
    if start is None:
        return result

    i = start + 1
    # Product names: every line until the first labelled block. A line that is
    # not a product name ends the list, so prose never becomes a product.
    while i < len(lines) and not _HEADING.match(lines[i]):
        name = lines[i].lower()
        if name not in _PRODUCT_NAMES:
            break
        if _PRODUCT_NAMES[name]:
            result['products'].add(_PRODUCT_NAMES[name])
        i += 1

    # Labelled blocks: "####### Supported plans" then its value line
    while i + 1 < len(lines) and _HEADING.match(lines[i]):
        label = _HEADING.sub('', lines[i]).strip()
        value = lines[i + 1]
        if _HEADING.match(value):
            i += 1
            continue
        if _PLANS_LABEL.match(label):
            target = result['plans']
        elif _PLATFORMS_LABEL.match(label):
            target = result['platforms']
        else:
            break  # the article's first real heading: the header is over
        if not _PLACEHOLDER.match(value):
            for v in _split_values(value):
                if v not in target:
                    target.append(v)
        i += 2
    return result


def suggested_label(text: Optional[str]) -> Optional[str]:
    """'loyalty' | 'reviews' when the header names exactly one in-scope
    product; None when it names both (the admin applies the majority rule) or
    neither."""
    products = parse_header(text)['products']
    return next(iter(products)) if len(products) == 1 else None
