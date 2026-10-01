"""
Yotpo product-line labels on knowledge-base documents.

Each esp_documents row can carry `product`: which Yotpo product it documents.

    loyalty  Yotpo Loyalty & Referrals
    reviews  Yotpo Reviews
    shared   correct for both: the ESP's own documentation, or Yotpo platform
             documentation that belongs to neither product

Admins set labels from the ESP management screen. Chat reads them in one
place: whether an ESP has any Reviews documentation, so a Reviews question on
an ESP without it is told so instead of being answered from Loyalty docs.
Retrieval does not filter on labels (PRODUCT_LINE_SPLIT_SCOPE.md, step 7).

Labels live on the database row only. Vector metadata does not carry them
yet -- when it does, a label edit here must also update that URL's vectors.
"""
import re
import threading
import time
from typing import Optional

from flask import jsonify, request

PRODUCTS = ('loyalty', 'reviews', 'shared')

# The two product lines a chat user can pick. 'shared' is a document label,
# not something a user asks about.
CHAT_PRODUCTS = ('loyalty', 'reviews')
DEFAULT_CHAT_PRODUCT = 'loyalty'

# ESPs with Reviews documentation, read on every Reviews chat request, so
# cached. Cleared when a label changes; the TTL covers crawls that finish or
# fail without a label edit. `gen` stops a clear that lands while a lookup is
# in flight from being overwritten by that lookup's older answer.
COVERAGE_TTL_SECONDS = 300
_coverage_cache = {'at': 0.0, 'esps': None, 'gen': 0}
_coverage_lock = threading.Lock()
_vectorizer = None   # set by register_product_label_routes


def _in_index(esp: str, url: str, probe=None) -> bool:
    """Whether a document has at least one vector. Fails open on errors.

    probe: a precomputed query vector, so a scan embeds once, not per doc.
    """
    v = _vectorizer
    if v is None:
        return True
    try:
        index = getattr(v, 'index', None)
        if index is None:
            # ChromaDB. Not ChromaAdapter.url_exists, which swallows errors
            # and reports them as "not indexed" -- that would fail closed.
            got = v.collection.get(where={"$and": [{"esp": esp}, {"source_url": url}]}, limit=1)
            return bool(got.get('ids'))
        # Pinecone. Not PineconeAdapter.url_exists, for the same reason.
        if probe is None:
            probe = _probe_vector(v)
        res = index.query(vector=probe, top_k=1, include_metadata=False,
                          filter={"esp": {"$eq": esp}, "source_url": {"$eq": url}})
        return bool(res.get('matches'))
    except Exception as e:
        print(f"[PRODUCT] Could not check the index for {url}: {e}")
        return True


def _probe_vector(v):
    """Any valid non-zero vector will do: the query is answered by its
    metadata filter, not by similarity. A constant avoids loading the
    embedding model (~250MB, lazy on purpose) inside a public request."""
    dim = getattr(v, 'dimension', 384)
    return [1.0] + [0.0] * (dim - 1)


_coverage_fill_lock = threading.Lock()   # one scan at a time; others wait for it
# How long a request waits for someone else's scan. A stuck index query must
# not tie up the server's few threads: after this, chat fails open and the
# endpoint reports coverage as unavailable.
COVERAGE_WAIT_SECONDS = 5
_last_known = {'esps': None}             # survives clears; used only on timeout


class CoverageUnavailable(Exception):
    pass


def esps_with_reviews_coverage() -> set:
    """Names of ESPs with a Reviews-labelled document that is in the index.

    A miss scans the Reviews documents (one index query each, stopping at
    the first hit per ESP). Concurrent misses wait for one scan instead of
    each running their own -- for at most COVERAGE_WAIT_SECONDS, then they
    get the last known answer or CoverageUnavailable.
    """
    def cached():
        with _coverage_lock:
            fresh = time.time() - _coverage_cache['at'] < COVERAGE_TTL_SECONDS
            if _coverage_cache['esps'] is not None and fresh:
                return _coverage_cache['esps']
        return None

    hit = cached()
    if hit is not None:
        return hit
    if not _coverage_fill_lock.acquire(timeout=COVERAGE_WAIT_SECONDS):
        if _last_known['esps'] is not None:
            return _last_known['esps']
        raise CoverageUnavailable("a coverage scan is still running")
    try:
        hit = cached()                    # filled while we waited
        if hit is not None:
            return hit
        with _coverage_lock:
            gen = _coverage_cache['gen']
        now = time.time()
        from esp_manager import get_esp_manager
        v = _vectorizer
        probe = _probe_vector(v) if v is not None and getattr(v, 'index', None) is not None else None
        esps = set()
        for esp, url in get_esp_manager().reviews_documents():
            if esp not in esps and _in_index(esp, url, probe):
                esps.add(esp)
        with _coverage_lock:
            if _coverage_cache['gen'] == gen:
                _coverage_cache.update(at=now, esps=esps)
        _last_known['esps'] = esps
        return esps
    finally:
        _coverage_fill_lock.release()


def clear_coverage_cache():
    with _coverage_lock:
        _coverage_cache.update(at=0.0, esps=None, gen=_coverage_cache['gen'] + 1)


def esp_display_name(esp: str) -> str:
    """The ESP's name as users see it ("Other/Webhook"), or its key."""
    try:
        from esp_manager import get_esp_manager
        row = get_esp_manager().get_esp_by_name(esp)
        return (row or {}).get('display_name') or esp
    except Exception:
        return esp


def has_reviews_coverage(esp: str) -> bool:
    """Whether this ESP has Reviews documentation. Fails open (True) if the
    lookup breaks: a missing note is safer than falsely telling every Reviews
    user that nothing is documented."""
    try:
        return esp in esps_with_reviews_coverage()
    except Exception as e:
        print(f"[PRODUCT] Could not read Reviews coverage: {e}")
        return True


def chat_product(value) -> str:
    """The product a chat request is about. Anything unrecognised -- including
    a missing value from an older browser tab -- is Loyalty, today's behaviour."""
    value = (value or '').strip().lower() if isinstance(value, str) else ''
    return value if value in CHAT_PRODUCTS else DEFAULT_CHAT_PRODUCT

# Yotpo support pages open with "Products" (or "YotpoProducts") on its own line,
# followed by the product name. The chunker drops sections under 20 words, so
# this header never reaches a vector -- it can only be read from stored content.
_HEADER = re.compile(r"^\s*(?:Yotpo)?Products?\s*$", re.I | re.M)
HEADER_SCAN_CHARS = 1500


def header_label(text: Optional[str]) -> Optional[str]:
    """The product a Yotpo support page declares in its header, or None.

    Only a suggestion for the admin: most documents (ESP help centres, Yotpo
    developer pages) have no header, and those need a human decision.
    """
    if not text:
        return None
    m = _HEADER.search(text[:HEADER_SCAN_CHARS])
    if not m:
        return None
    following = [l.strip() for l in text[m.end():m.end() + 120].split("\n") if l.strip()]
    for line in following[:2]:
        low = line.lower()
        if "loyalty" in low or "referral" in low:
            return "loyalty"
        if "review" in low:
            return "reviews"
    return None


def merge_labels(links, labels):
    """Add `product`, `suggested_product` and `labelable` to link dicts, in place.

    labels: {url: {'product': ..., 'suggested_product': ...}} for URLs that
    have a database row. A link without a row (a global CSV entry that was
    never crawled) cannot be labelled until it has one.
    """
    for link in links:
        entry = labels.get(link['url'])
        link['labelable'] = entry is not None
        link['product'] = entry['product'] if entry else None
        link['suggested_product'] = entry['suggested_product'] if entry else None
    return links


def register_product_label_routes(app, vectorizer=None):
    from auth import admin_request_ok
    from esp_manager import get_esp_manager

    global _vectorizer
    _vectorizer = vectorizer

    @app.route('/api/reviews-coverage', methods=['GET'])
    def reviews_coverage():
        """ESPs with Yotpo Reviews documentation, for the chat intro. Public:
        the sidebar that uses it is shown to guests too."""
        try:
            return jsonify({'esps': sorted(esps_with_reviews_coverage())})
        except Exception as e:
            # Public endpoint: the reason stays in the log, not the response
            print(f"[PRODUCT] Could not read Reviews coverage: {e}")
            return jsonify({'error': 'Reviews coverage is unavailable right now.'}), 503

    @app.route('/api/admin/esp/<esp_name>/set-product', methods=['POST'])
    def set_document_product(esp_name):
        """Label documents with a Yotpo product line.

        Body: {"urls": [...], "product": "loyalty" | "reviews" | "shared" | null}
        null clears the label. Works for 'global' too: it is an ESP row.
        """
        if not admin_request_ok():
            return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

        data = request.get_json(silent=True) or {}
        urls = data.get('urls')
        product = data.get('product')
        if not isinstance(urls, list) or not urls or not all(isinstance(u, str) for u in urls):
            return jsonify({'error': 'urls must be a non-empty list of URLs'}), 400
        if product is not None and product not in PRODUCTS:
            return jsonify({'error': f"product must be one of {', '.join(PRODUCTS)}, or null"}), 400

        try:
            updated, missing = get_esp_manager().set_document_product(esp_name, urls, product)
            clear_coverage_cache()
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': f'Could not save the label: {e}'}), 500

        return jsonify({'success': True, 'product': product,
                        'updated': updated, 'missing': missing})
