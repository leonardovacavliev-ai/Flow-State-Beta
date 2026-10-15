"""
Platform types: which kind of system an integration is, and so which prompt
answers questions about it (ALL_INTEGRATIONS_UPDATE.md).

Pure: no database, no network. The catalog import uses default_type() to
propose a type from the integration's yotpo.com/integrations categories; an
admin can override it, which is the only way conflicts get settled.
"""

from typing import Iterable, Optional

PLATFORM_TYPES = ('messaging', 'storefront', 'service', 'data', 'content')

# What the admin calls each type: what kind of platform it is
TYPE_LABELS = {
    'messaging': 'Email & SMS',
    'storefront': 'Store & checkout',
    'service': 'Customer service',
    'data': 'Data & automation',
    'content': 'Reviews & content',
}

# Catalog category slug -> platform type
CATEGORY_DEFAULT_TYPE = {
    # messaging: the platform sends the emails and texts
    'email-marketing': 'messaging',
    'sms-marketing': 'messaging',
    'whatsapp-social-dms': 'messaging',
    # storefront: where shoppers browse, pay and see the program
    'ecommerce-platform': 'storefront',
    'in-store-pos': 'storefront',
    'mobile-app-builder': 'storefront',
    'mobile-wallet-pass': 'storefront',
    'page-builder-pwa': 'storefront',
    'payment-checkout': 'storefront',
    'subscription-recurring-billing': 'storefront',
    'on-site-engagement': 'storefront',
    'search': 'storefront',
    'personalization-and-product-recs': 'storefront',
    'quiz-and-gamification': 'storefront',
    # service: agents and bots answering customers
    'help-desk-crm': 'service',
    'onsite-chatbots': 'service',
    # content: reviews and other customer content flowing in or out
    'reviews-and-visual-ugc': 'content',
    'retailers-and-review-syndication': 'content',
    'product-sampling': 'content',
    'influencer-marketing': 'content',
    'consumer-platform': 'content',
    # data: data moving between systems with no customer-facing surface
    'data-automation': 'data',
    'bi-analytics': 'data',
    'ads': 'data',
    'privacy-and-data-subject-requests': 'data',
    'other': 'data',
    'gift-cards': 'data',
    'sustainability-and-donations': 'data',
    'shipping-returns': 'data',
    'loyalty-referrals': 'data',
}

# When an integration sits in categories of several types, the first type
# here wins: a platform that sends messages is answered as messaging even if
# it also syncs data, and so on down.
TYPE_PRIORITY = ('messaging', 'service', 'storefront', 'content', 'data')


def default_type(categories: Optional[Iterable[str]]) -> Optional[str]:
    """The proposed platform type for these catalog categories, or None when
    none of them is known."""
    types = {CATEGORY_DEFAULT_TYPE.get((c or '').strip().lower()) for c in (categories or ())}
    for platform_type in TYPE_PRIORITY:
        if platform_type in types:
            return platform_type
    return None


def category_types(categories: Optional[Iterable[str]]) -> list:
    """The platform types these categories default to, sorted. More than one
    means the catalog can't decide the type, and an admin has to."""
    return sorted({CATEGORY_DEFAULT_TYPE[c] for c in
                   ((c or '').strip().lower() for c in (categories or ()))
                   if c in CATEGORY_DEFAULT_TYPE})


# Catalog category slug -> the label yotpo.com/integrations shows for it
# (the page's filter list, backend/fixtures/catalog/catalog.html)
CATEGORY_NAMES = {
    'ads': 'Ads',
    'bi-analytics': 'BI & Analytics',
    'consumer-platform': 'Social Platforms',
    'data-automation': 'Data & Automation',
    'ecommerce-platform': 'eCommerce Platform',
    'email-marketing': 'Email Marketing',
    'gift-cards': 'Gift Cards',
    'help-desk-crm': 'Help Desk & CRM',
    'in-store-pos': 'In-store & POS',
    'influencer-marketing': 'Influencer Marketing',
    'loyalty-referrals': 'Loyalty & Referrals',
    'mobile-app-builder': 'Mobile App Builder',
    'mobile-wallet-pass': 'Mobile Wallet Pass',
    'on-site-engagement': 'On-site Engagement',
    'onsite-chatbots': 'On-site Chatbots',
    'other': 'Other',
    'page-builder-pwa': 'Page Builder & PWA',
    'payment-checkout': 'Payment & Checkout',
    'personalization-and-product-recs': 'Personalization and Product Recs',
    'privacy-and-data-subject-requests': 'Privacy & Data Subject Requests',
    'product-sampling': 'Product Sampling',
    'quiz-and-gamification': 'Quiz & Gamification',
    'retailers-and-review-syndication': 'Retailers & Review Syndication',
    'reviews-and-visual-ugc': 'Reviews & Visual UGC',
    'search': 'On-site Search',
    'shipping-returns': 'Shipping & Returns',
    'sms-marketing': 'SMS Marketing',
    'subscription-recurring-billing': 'Subscription & Recurring Billing',
    'sustainability-and-donations': 'Sustainability & Donations',
    'whatsapp-social-dms': 'WhatsApp & Social DMs',
}


def category_name(slug: str) -> str:
    """The catalog's label for a category; an unknown slug reads as words."""
    return CATEGORY_NAMES.get(slug) or (slug or '').replace('-', ' ').capitalize()
