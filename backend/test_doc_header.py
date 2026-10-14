"""
The Yotpo guide header parser (C1.2): backend/doc_header.py.

    python3 backend/test_doc_header.py     # or pytest

Pure: reads the saved guides in fixtures/document360/. The .txt files are the
crawler's own _extract_text output for the .html next to them, so the parser
is tested on exactly what is stored in esp_documents.content.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import doc_header  # noqa: E402

FIXTURES = os.path.join(HERE, 'fixtures', 'document360')


def _text(slug):
    with open(os.path.join(FIXTURES, slug + '.txt')) as f:
        return f.read()


def test_fixture_text_is_what_the_crawler_stores():
    """The .txt fixtures must stay the crawler's output for the .html ones;
    if _extract_text changes, regenerate them rather than edit by hand."""
    from crawler import _extract_text

    class Response:
        def __init__(self, content):
            self.content = content

    for name in os.listdir(FIXTURES):
        if name.endswith('.html'):
            with open(os.path.join(FIXTURES, name), 'rb') as f:
                text, error = _extract_text('https://support.yotpo.com/docs/x', Response(f.read()))
            assert error is None
            assert text == _text(name[:-5]), name


def test_one_product():
    h = doc_header.parse_header(_text('recharge-integration-guide-for-yotpo-loyalty-referrals'))
    assert h['products'] == {'loyalty'}
    assert h['plans'] == ['Pro', 'Premium', 'Enterprise']
    assert h['platforms'] == ['Shopify', 'Shopify Plus', 'BigCommerce', 'Adobe Commerce (Magento)']
    assert doc_header.suggested_label(_text('integrating-loyalty-and-referrals-with-shopify-point-of-sale-pos')) == 'loyalty'
    assert doc_header.suggested_label(_text('google-seller-ratings')) == 'reviews'
    assert doc_header.suggested_label(_text('zendesk-integration-guide-for-reviews')) == 'reviews'


def test_both_products_suggest_nothing():
    """Gorgias names Reviews and Loyalty: the admin applies the majority rule."""
    text = _text('gorgias-integration-guide-for-reviews-and-loyalty-referrals')
    assert doc_header.parse_header(text)['products'] == {'loyalty', 'reviews'}
    assert doc_header.suggested_label(text) is None


def test_template_leftovers_are_ignored():
    """'Change this text for SMS & Email' is Document360's placeholder, not a plan."""
    h = doc_header.parse_header(_text('gorgias-integration-guide-for-reviews-and-loyalty-referrals'))
    assert h['plans'] == ['Premium', 'Enterprise']
    assert not any('change this text' in v.lower() for v in h['plans'] + h['platforms'])


def test_visual_ugc_counts_as_reviews():
    """Tapcart lists Reviews, Loyalty & Referrals and Visual UGC: two products."""
    text = _text('tapcart-yotpo-integration-guide')
    assert doc_header.parse_header(text)['products'] == {'loyalty', 'reviews'}
    assert doc_header.suggested_label(text) is None
    assert doc_header.parse_header("Products\n\nVisual UGC\n\n####### Supported plans\n\nPro\n")['products'] == {'reviews'}


def test_out_of_scope_products_are_read_past():
    """SMS & Email and Subscriptions are not v2 products (I9)."""
    text = "Products\n\nSMS & Email\n\nLoyalty & Referrals\n\n####### Supported plans\n\nPro\n"
    assert doc_header.parse_header(text)['products'] == {'loyalty'}
    assert doc_header.parse_header("Products\n\nSubscriptions\n\n####### Supported plans\n\nPro\n")['products'] == set()


def test_a_plans_line_is_never_a_product():
    """A header with no product line goes straight to its plans."""
    text = "Products\n\n####### Supported plans\n\nPro, Premium\n\n####### eCommerce Platform\n\nShopify\n"
    h = doc_header.parse_header(text)
    assert h['products'] == set()
    assert h['plans'] == ['Pro', 'Premium'] and h['platforms'] == ['Shopify']
    assert doc_header.suggested_label(text) is None


def test_no_header():
    assert doc_header.parse_header(None) == {'products': set(), 'plans': [], 'platforms': []}
    assert doc_header.suggested_label("## Create a flow\n\nKlaviyo flows send …") is None
    # A heading named "Products" deep in an article is outside the header scan
    assert doc_header.suggested_label("x\n" * 1000 + "Products\n\nLoyalty\n") is None


def test_product_labels_delegates():
    """The admin picker's pre-fill (product_labels.header_label) is this parser."""
    from product_labels import header_label
    assert header_label(_text('google-seller-ratings')) == 'reviews'
    assert header_label(_text('gorgias-integration-guide-for-reviews-and-loyalty-referrals')) is None


if __name__ == '__main__':
    tests = [v for k, v in dict(globals()).items() if k.startswith('test_')]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__} {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
