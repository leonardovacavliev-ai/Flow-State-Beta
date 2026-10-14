"""
What to read about a partner app: the features a Yotpo integration plugs into.

A Yotpo guide says how to connect the integration. To answer well, Flow State
also needs to know how the partner's side of it behaves: for an email
platform, how flows, triggers, delays and segments work (the Klaviyo, Braze
and Dotdigital articles already in the knowledge base); for a subscription
app, how discount codes apply to subscriptions (Recharge's "Managing
subscription discount codes"). These are the platform's mechanics.

This module lists those features as topics, per catalog category, and ranks
them for one integration by what its Yotpo guide and partner pages talk about.
backend/app_mechanics.py then searches the partner's help centre for the top
topics. Pure data and arithmetic: no network.

The topic lists are product knowledge, not code. Edit them freely: a topic is
a name, the searches to run in a help centre, and the words that show an
article (or a guide) is about it.
"""

import re
from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class Topic:
    name: str                  # shown to the admin: why an article was picked
    queries: Tuple[str, ...]   # help-centre searches, best first
    words: Tuple[str, ...]     # an article title or guide mentioning these is on topic


def T(name, queries, words):
    return Topic(name, tuple(queries), tuple(words))


# --- topics by kind of app, in default order (most often what Yotpo touches first) ---

MESSAGING = (
    T('flows and their triggers', ['flow triggers', 'create a flow', 'automation triggers', 'journeys'],
      ['flow', 'flows', 'journey', 'journeys', 'automation', 'automations', 'trigger', 'triggers',
       'triggered', 'canvas', 'workflow', 'workflows', 'stream', 'orchestration']),
    T('delays, filters and re-entry', ['time delay', 're-entry', 'flow filters', 'exit conditions'],
      ['delay', 'delays', 'wait', 're-entry', 'reentry', 're-enter', 'enrollment', 'exit', 'exits',
       'filter', 'filters', 'split']),
    T('custom properties and events', ['custom properties', 'custom events', 'profile properties'],
      ['property', 'properties', 'event', 'events', 'metric', 'metrics', 'attribute', 'attributes',
       'custom field', 'custom fields', 'data field']),
    T('segments and lists', ['create a segment', 'segments'],
      ['segment', 'segments', 'segmentation', 'list', 'lists', 'audience', 'audiences']),
    T('personalisation in messages', ['dynamic content', 'personalization tags', 'template variables'],
      ['dynamic', 'personalization', 'personalisation', 'personalize', 'variable', 'variables',
       'merge tag', 'merge tags', 'template tags', 'liquid']),
)

SUBSCRIPTIONS = (
    T('discount codes on subscriptions', ['subscription discount codes', 'discount codes',
                                          'apply discount to subscription'],
      ['discount', 'discounts', 'coupon', 'coupons', 'discount code', 'discount codes',
       'promo code', 'promo codes']),
    T('recurring orders and renewals', ['recurring orders', 'subscription renewal', 'upcoming charges'],
      ['recurring', 'renewal', 'renewals', 'charge', 'charges', 'rebill', 'billing cycle']),
    T('customer portal', ['customer portal'], ['portal', 'customer portal']),
    T('subscription products and plans', ['subscription products', 'selling plans'],
      ['subscription product', 'selling plan', 'selling plans', 'plan', 'plans']),
)

STOREFRONT = (
    T('discount codes', ['discount codes', 'combining discounts'],
      ['discount', 'discounts', 'coupon', 'coupons', 'discount code', 'discount codes',
       'promo code', 'promo codes']),
    T('customer accounts', ['customer accounts'], ['customer account', 'customer accounts',
                                                     'customer login', 'customer sign in']),
    T('apps in the theme', ['app blocks', 'theme app extensions', 'add an app to your theme'],
      ['theme', 'app block', 'app blocks', 'app embed', 'section', 'sections', 'widget', 'widgets',
       'extension', 'extensions']),
    T('refunds and cancelled orders', ['refunds', 'cancel an order'],
      ['refund', 'refunds', 'return', 'returns', 'cancel', 'cancelled', 'canceled']),
    T('checkout', ['checkout'], ['checkout']),
)

POS = (
    T('discounts at the point of sale', ['apply a discount point of sale', 'discounts'],
      ['discount', 'discounts', 'coupon', 'coupons', 'discount code', 'discount codes']),
    T('customers at the point of sale', ['add a customer to a sale', 'customer profiles'],
      ['customer', 'customers', 'profile', 'lookup']),
    T('apps on the point of sale', ['pos apps', 'pos ui extensions', 'smart grid'],
      ['app', 'apps', 'tile', 'tiles', 'extension', 'smart grid']),
)

APP_BUILDER = (
    T('blocks and components', ['blocks', 'custom code block', 'components'],
      ['block', 'blocks', 'component', 'components', 'widget', 'widgets', 'section', 'sections',
       'custom code']),
    T('product pages', ['product page'], ['product page', 'product detail', 'pdp']),
    T('customer accounts and login', ['customer login', 'account page'],
      ['customer account', 'customer accounts', 'customer login', 'account page', 'profile page']),
    T('push notifications', ['push notifications'], ['push', 'notification', 'notifications']),
)

WALLET = (
    T('passes and their fields', ['pass fields', 'pass design'], ['pass', 'passes', 'field', 'fields',
                                                                  'design', 'template']),
    T('updating passes', ['update passes', 'push notifications'], ['update', 'updates', 'push',
                                                                 'notification', 'notifications']),
)

ON_SITE = (
    T('widgets and templates', ['widgets', 'templates', 'campaign templates'],
      ['widget', 'widgets', 'template', 'templates', 'block', 'blocks', 'popup', 'pop-up', 'form', 'forms']),
    T('targeting and display rules', ['targeting', 'display rules', 'segments'],
      ['target', 'targeting', 'segment', 'segments', 'audience', 'rule', 'rules', 'trigger', 'triggers']),
    T('custom data and code', ['custom attributes', 'custom code', 'variables'],
      ['custom', 'attribute', 'attributes', 'variable', 'variables', 'javascript', 'code']),
)

SEARCH = (
    T('results, badges and merchandising', ['product badges', 'merchandising rules', 'search results'],
      ['badge', 'badges', 'result', 'results', 'merchandising', 'ranking', 'boost', 'sort', 'sorting']),
    T('filters and facets', ['filters', 'facets'], ['filter', 'filters', 'facet', 'facets']),
    T('recommendation widgets', ['recommendation widgets', 'recommendations'],
      ['recommendation', 'recommendations', 'widget', 'widgets', 'bundle', 'bundles', 'upsell']),
)

SERVICE = (
    T('customer profile in the sidebar', ['customer sidebar', 'customer profile', 'widgets'],
      ['sidebar', 'widget', 'widgets', 'profile', 'customer profile', 'customer data']),
    T('macros and replies', ['macros', 'canned responses', 'templates'],
      ['macro', 'macros', 'canned', 'saved reply', 'saved replies', 'response template', 'snippet']),
    T('rules and automations', ['rules', 'automations', 'triggers'],
      ['rule', 'rules', 'automation', 'automations', 'trigger', 'triggers', 'workflow', 'workflows']),
    T('AI agent knowledge and actions', ['ai agent actions', 'knowledge sources'],
      ['knowledge', 'action', 'actions', 'ai agent', 'bot', 'chatbot', 'guidance']),
)

CONTENT = (
    T('review collection and requests', ['review requests', 'collect reviews'],
      ['review request', 'review requests', 'request reviews', 'collect reviews', 'collecting reviews',
       'review collection', 'review emails', 'review email']),
    T('campaigns', ['create a campaign', 'campaigns'], ['campaign', 'campaigns']),
    T('product catalog and feeds', ['product feed', 'product catalog'],
      ['feed', 'feeds', 'catalog', 'catalogue', 'product data', 'gtin', 'sku', 'syndication']),
    T('content, rights and galleries', ['content library', 'content rights', 'galleries'],
      ['content', 'ugc', 'rights', 'gallery', 'galleries', 'media']),
    T('creators and affiliates', ['creators', 'affiliate commission', 'referrals'],
      ['creator', 'creators', 'influencer', 'influencers', 'affiliate', 'affiliates', 'commission',
       'ambassador', 'ambassadors']),
)

DATA = (
    T('workflows: triggers and actions', ['triggers', 'actions', 'workflows'],
      ['trigger', 'triggers', 'action', 'actions', 'workflow', 'workflows', 'recipe', 'recipes',
       'automation', 'automations', 'step', 'steps']),
    T('data sync and connectors', ['data sources', 'sync', 'connectors'],
      ['sync', 'syncing', 'source', 'sources', 'connector', 'connectors', 'import', 'export', 'schedule']),
    T('dashboards and reports', ['dashboards', 'custom reports'],
      ['dashboard', 'dashboards', 'report', 'reports', 'reporting', 'metric', 'metrics']),
)

ADS = (
    T('audiences', ['audiences', 'custom audiences'], ['audience', 'audiences', 'segment', 'segments']),
    T('product feeds', ['product feed', 'catalog'], ['feed', 'feeds', 'catalog', 'product']),
    T('campaigns', ['campaigns'], ['campaign', 'campaigns']),
)

LOYALTY_APPS = (
    T('points and rewards', ['points', 'rewards'], ['point', 'points', 'reward', 'rewards', 'redeem',
                                                   'redemption']),
    T('importing customers and balances', ['import points', 'migrate customers'],
      ['import', 'importing', 'balance', 'balances', 'migrate', 'migration']),
    T('referrals and VIP tiers', ['referrals', 'vip tiers'], ['referral', 'referrals', 'vip', 'tier',
                                                             'tiers']),
)

GIFT_CARDS = (
    T('gift cards and store credit', ['gift cards', 'store credit'],
      ['gift card', 'gift cards', 'store credit', 'balance', 'balances']),
    T('rewards and incentives', ['rewards', 'incentives'], ['reward', 'rewards', 'incentive', 'incentives',
                                                         'payout', 'payouts']),
)

DONATIONS = (
    T('donations', ['donations', 'donate'], ['donation', 'donations', 'donate', 'charity', 'nonprofit',
                                            'offset', 'impact']),
)

SHIPPING_RETURNS = (
    T('returns, exchanges and store credit', ['store credit', 'exchanges', 'return policy'],
      ['credit', 'exchange', 'exchanges', 'return', 'returns', 'refund', 'refunds']),
    T('tracking and notifications', ['tracking page', 'notifications'],
      ['tracking', 'notification', 'notifications', 'delivery', 'shipment']),
)

PRIVACY = (
    T('data subject requests', ['data subject requests', 'deletion requests'],
      ['request', 'requests', 'deletion', 'delete', 'access', 'dsr', 'dsar', 'erasure']),
)

# Catalog category slug -> topics. A category missing here uses its platform
# type's default below.
CATEGORY_TOPICS = {
    'email-marketing': MESSAGING,
    'sms-marketing': MESSAGING,
    'whatsapp-social-dms': MESSAGING,
    'subscription-recurring-billing': SUBSCRIPTIONS,
    'ecommerce-platform': STOREFRONT,
    'payment-checkout': STOREFRONT,
    'in-store-pos': POS,
    'mobile-app-builder': APP_BUILDER,
    'page-builder-pwa': APP_BUILDER,
    'mobile-wallet-pass': WALLET,
    'on-site-engagement': ON_SITE,
    'quiz-and-gamification': ON_SITE,
    'personalization-and-product-recs': SEARCH,
    'search': SEARCH,
    'help-desk-crm': SERVICE,
    'onsite-chatbots': SERVICE,
    'reviews-and-visual-ugc': CONTENT,
    'retailers-and-review-syndication': CONTENT,
    'product-sampling': CONTENT,
    'influencer-marketing': CONTENT,
    'consumer-platform': CONTENT,
    'data-automation': DATA,
    'bi-analytics': DATA,
    'other': DATA,
    'ads': ADS,
    'loyalty-referrals': LOYALTY_APPS,
    'gift-cards': GIFT_CARDS,
    'sustainability-and-donations': DONATIONS,
    'shipping-returns': SHIPPING_RETURNS,
    'privacy-and-data-subject-requests': PRIVACY,
}

TYPE_TOPICS = {'messaging': MESSAGING, 'storefront': STOREFRONT, 'service': SERVICE,
               'content': CONTENT, 'data': DATA}


def _words(text: str) -> str:
    return ' ' + re.sub(r'[^a-z0-9]+', ' ', (text or '').lower()).strip() + ' '


def mentions(text: str, words: Iterable[str]) -> int:
    """How many of `words` appear in `text`, as whole words or phrases."""
    hay = _words(text)
    return sum(1 for w in words if _words(w) in hay)


def topics_for(categories: Iterable[str], platform_type: str = None) -> List[Topic]:
    """The integration's candidate topics, its first category's first."""
    out: List[Topic] = []
    for c in categories or ():
        for t in CATEGORY_TOPICS.get(c, ()):
            if t not in out:
                out.append(t)
    if not out:
        out = list(TYPE_TOPICS.get(platform_type or '', DATA))
    return out


def rank_topics(topics: List[Topic], context: str) -> List[Tuple[Topic, int]]:
    """Topics ordered by how much the integration's own documents (its Yotpo
    guide, partner pages) talk about them; the default order breaks ties.
    The Recharge guide is about coupon codes on subscriptions, so 'discount
    codes on subscriptions' comes first."""
    scored = [(t, mentions(context, t.words), i) for i, t in enumerate(topics)]
    scored.sort(key=lambda x: (-x[1], x[2]))
    return [(t, n) for t, n, _ in scored]
