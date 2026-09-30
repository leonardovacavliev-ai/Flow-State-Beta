"""
Yotpo product-line labels on knowledge-base documents.

Each esp_documents row can carry `product`: which Yotpo product it documents.

    loyalty  Yotpo Loyalty & Referrals
    reviews  Yotpo Reviews
    shared   correct for both: the ESP's own documentation, or Yotpo platform
             documentation that belongs to neither product

Admins set labels from the ESP management screen. Nothing reads them in chat
yet; they feed the retrieval experiment (eval/product_eval.py) and are the
first step of splitting the knowledge base (PRODUCT_LINE_SPLIT_SCOPE.md).

Labels live on the database row only. Vector metadata does not carry them
yet -- when it does, a label edit here must also update that URL's vectors.
"""
import re
from typing import Optional

from flask import jsonify, request

PRODUCTS = ('loyalty', 'reviews', 'shared')

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


def register_product_label_routes(app):
    from auth import admin_request_ok
    from esp_manager import get_esp_manager

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
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': f'Could not save the label: {e}'}), 500

        return jsonify({'success': True, 'product': product,
                        'updated': updated, 'missing': missing})
