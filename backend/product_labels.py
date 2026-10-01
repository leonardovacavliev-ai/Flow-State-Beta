"""
Yotpo product-line labels on knowledge-base documents.

Each esp_documents row can carry `product`: which Yotpo product it documents.

    loyalty  Yotpo Loyalty & Referrals
    reviews  Yotpo Reviews
    shared   correct for both: the ESP's own documentation, or Yotpo platform
             documentation that belongs to neither product

Every document gets its label when it is added (ESPManager.add_document
refuses one without), and admins change it from the ESP management screen.

The label lives in two places, kept in step:
- the database row (esp_documents.product), the source of truth;
- every vector of that document (metadata `product`). Written by
  crawler.vectorize_single_document, which reads the row; the vector
  adapters refuse a write without it. A label edit here updates the row
  and then that URL's vectors (set_vector_product).
eval/audit_product_labels.py checks the two agree.

Chat reads labels in one place: whether an ESP has any Reviews
documentation, so a Reviews question on an ESP without it is told so instead
of being answered from Loyalty docs. Retrieval does not filter on labels
(PRODUCT_LINE_SPLIT_SCOPE.md, step 7).
"""
import re
import threading
import time
from typing import Optional

from flask import jsonify, request

# Same tuple as adapters.vector.base.PRODUCT_LABELS (a test keeps them equal);
# not imported from there, because the adapters package loads ChromaDB and Pinecone.
PRODUCTS = ('loyalty', 'reviews', 'shared')

PRODUCT_REQUIRED = ("Choose which Yotpo product this document covers: Loyalty, Reviews, "
                    "or Shared (correct for both).")

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


def require_product(value) -> str:
    """A valid document label, normalised; ValueError otherwise."""
    if isinstance(value, str) and value.strip().lower() in PRODUCTS:
        return value.strip().lower()
    raise ValueError(PRODUCT_REQUIRED)


def split_by_label(esp_mgr, esp_name: str, urls, product):
    """(urls that will end up labelled, [{'url', 'error'}] for the rest).

    An existing row must already carry a label; a URL with no row needs
    `product` (the label it will be created with). Callers crawl the first
    list and report the second, so one unlabelled link doesn't block a batch.
    """
    esp = esp_mgr.get_esp_by_name(esp_name)
    if not esp:
        return list(urls), []   # the caller reports the missing ESP its own way
    ok, refused = [], []
    for url in urls:
        doc = esp_mgr.get_document_by_url(esp['id'], url)
        if doc is None and product not in PRODUCTS:
            refused.append({'url': url, 'error': "No product label yet: pick Loyalty, Reviews or "
                                                 "Shared beside it, then try again."})
        elif doc is not None and doc.get('product') not in PRODUCTS:
            refused.append({'url': url, 'error': "No product label: pick Loyalty, Reviews or "
                                                 "Shared beside it, then crawl it again."})
        else:
            ok.append(url)
    return ok, refused


def label_problem(esp_mgr, esp_name: str, urls, product) -> Optional[str]:
    """The first reason a crawl or paste of `urls` would leave a document
    unlabelled, as "<url>: <reason>", or None."""
    _, refused = split_by_label(esp_mgr, esp_name, urls, product)
    return f"{refused[0]['url']}: {refused[0]['error']}" if refused else None


OUTDATED_PAGE = "This page is out of date. Reload it to choose a Yotpo product for the link."


def set_vector_product(vectorizer, esp: str, url: str, product: str) -> int:
    """Write `product` onto every vector of one document; how many it found.

    Errors propagate: the caller reports a label that reached the database
    but not the index, rather than claiming both are in step.
    """
    if vectorizer is None:
        return 0
    ids = vectorizer.ids_for_url(url, esp.lower())
    if ids:
        vectorizer.update_metadata(ids, {'product': product})
    return len(ids)


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

        Body: {"urls": [...], "product": "loyalty" | "reviews" | "shared"}
        Works for 'global' too: it is an ESP row. A label cannot be cleared:
        every document needs one, and its vectors carry it.

        Updates the rows, then those documents' vectors. If the index update
        fails the label is still saved, and the response says so (the admin
        screen offers a retry). A crawl that read the old label just before
        this edit can still write it afterwards; the audit catches that.
        """
        if not admin_request_ok():
            return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

        data = request.get_json(silent=True) or {}
        urls = data.get('urls')
        product = data.get('product')
        if not isinstance(urls, list) or not urls or not all(isinstance(u, str) for u in urls):
            return jsonify({'error': 'urls must be a non-empty list of URLs'}), 400
        if product is None:
            # Only an admin page from before labels were required offers "Unlabelled"
            return jsonify({'error': "A label can't be removed: every document needs one. "
                                     "If this page offers \"Unlabelled\", reload it."}), 400
        if product not in PRODUCTS:
            return jsonify({'error': f"product must be one of {', '.join(PRODUCTS)}"}), 400

        try:
            updated, missing = get_esp_manager().set_document_product(esp_name, urls, product)
            clear_coverage_cache()
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': f'Could not save the label: {e}'}), 500

        vectors, not_indexed, none_found = 0, [], []
        esp_mgr = get_esp_manager()
        esp = esp_mgr.get_esp_by_name(esp_name)
        for url in updated:
            try:
                n = set_vector_product(_vectorizer, esp_name, url, product)
            except Exception as e:
                print(f"[PRODUCT] Label saved but the index update failed for {url}: {e}")
                not_indexed.append(url)
                continue
            vectors += n
            if n == 0 and _vectorizer is not None and esp:
                doc = esp_mgr.get_document_by_url(esp['id'], url)
                if doc and doc.get('crawl_status') == 'completed':
                    # Crawled, yet nothing to update: just re-indexed (the
                    # index is eventually consistent) or never indexed
                    none_found.append(url)

        body = {'success': True, 'product': product, 'updated': updated,
                'missing': missing, 'vectors_updated': vectors}
        if not_indexed:
            body['index_failed'] = not_indexed
            body['warning'] = ("The label is saved, but the search index could not be updated for "
                               f"{len(not_indexed)} document(s), so its entries keep the old label.")
        elif none_found:
            body['no_vectors'] = none_found
            body['warning'] = ("The label is saved, but no search-index entries were found for "
                               f"{len(none_found)} crawled document(s). If it was re-crawled in the "
                               "last minute, choose another label and back once it settles; "
                               "eval/audit_product_labels.py shows any mismatch.")
        return jsonify(body)
