"""
The v2 admin: integrations list and detail, the proposals inbox, the crawl
summary (ALL_INTEGRATIONS_ROADMAP.md C1.4).

ESP Management fetched every integration's links one request at a time and
rendered them all. With ~160 integrations that can't work, so the list here
is one summary query, filtered and paged in Python (160 rows), and an
integration's documents load only when it is opened.

Every route needs an admin. Changing an integration's status needs an owner
(auth.current_admin_role). The queries run on Postgres and SQLite alike,
except the parts that read the crawl queue, which exists only with
USE_ASYNC_CRAWL (Postgres): those are skipped without it, as the old link
lists did.
"""

import json
import uuid
from typing import Dict, List, Optional

from flask import jsonify, request

from esp_manager import get_esp_manager, DuplicateURLError, _json_list, _iso
from integration_types import (PLATFORM_TYPES, TYPE_LABELS, CATEGORY_DEFAULT_TYPE, category_types,
                               category_name)

PER_PAGE = 50
MAX_PER_PAGE = 200
STATUSES = ('active', 'listed', 'archived')
TIERS = ('basic', 'listed')
FLAGS = ('unlabelled', 'failed', 'proposals', 'misses', 'mixed_types')
CATALOG_PRODUCTS = ('loyalty', 'reviews')
PROPOSAL_STATES = ('open', 'approved', 'rejected')
PROPOSAL_SOURCES = ('catalog', 'sitemap', 'manual', 'mechanics')
# A document missing this many crawls in a row is flagged to retire or
# replace (C1.3 counts the misses)
MISS_LIMIT = 3
# Platform types whose integrations may be active. Every other type still
# answers with the email/SMS prompt until C1.7 gives it its own, and goes
# into chat only in its wave (plan §4.6), so activating one now is refused.
TYPES_IN_CHAT = ('messaging',)
MAX_ITEMS = 200
ACTIVE_JOBS_SHOWN = 50

# The import's notes for the inbox, stored by scripts/import_catalog.py --apply
CATALOG_MECHANICS_KEY = 'catalog_mechanics'
CATALOG_REPORT_KEY = 'catalog_last_report'

# Indexed: crawled, and the last index wrote chunks. vector_count is NULL on
# documents indexed before it was recorded (C1.1); those count as indexed,
# since they were in search results then and nothing has removed them.
_INDEXED = "crawl_status = 'completed' AND (vector_count IS NULL OR vector_count > 0)"

SUMMARY_SQL = f"""
    SELECT e.id, e.name, e.display_name, e.status, e.platform_type, e.categories,
           e.products, e.catalog_slugs, e.platform_type_set_by,
           COALESCE(d.total, 0), COALESCE(d.loyalty, 0), COALESCE(d.reviews, 0),
           COALESCE(d.shared, 0), COALESCE(d.unlabelled, 0), COALESCE(d.failed, 0),
           COALESCE(d.misses, 0), COALESCE(d.indexed_loyalty, 0),
           COALESCE(d.indexed_reviews, 0), COALESCE(d.indexed_shared, 0),
           COALESCE(p.open_count, 0), COALESCE(d.not_crawled, 0)
    FROM esps e
    LEFT JOIN (
        SELECT esp_id, COUNT(*) AS total,
               SUM(CASE WHEN product = 'loyalty' THEN 1 ELSE 0 END) AS loyalty,
               SUM(CASE WHEN product = 'reviews' THEN 1 ELSE 0 END) AS reviews,
               SUM(CASE WHEN product = 'shared' THEN 1 ELSE 0 END) AS shared,
               SUM(CASE WHEN product IS NULL THEN 1 ELSE 0 END) AS unlabelled,
               SUM(CASE WHEN crawl_status = 'failed' THEN 1 ELSE 0 END) AS failed,
               SUM(CASE WHEN consecutive_misses >= {MISS_LIMIT} THEN 1 ELSE 0 END) AS misses,
               SUM(CASE WHEN product = 'loyalty' AND {_INDEXED} THEN 1 ELSE 0 END) AS indexed_loyalty,
               SUM(CASE WHEN product = 'reviews' AND {_INDEXED} THEN 1 ELSE 0 END) AS indexed_reviews,
               SUM(CASE WHEN product = 'shared' AND {_INDEXED} THEN 1 ELSE 0 END) AS indexed_shared,
               SUM(CASE WHEN crawl_status IS NULL OR crawl_status NOT IN ('completed', 'failed')
                        THEN 1 ELSE 0 END) AS not_crawled
        FROM esp_documents
        WHERE retired_at IS NULL
        GROUP BY esp_id
    ) d ON d.esp_id = e.id
    LEFT JOIN (
        SELECT esp_id, COUNT(*) AS open_count
        FROM document_proposals
        WHERE state = 'open'
        GROUP BY esp_id
    ) p ON p.esp_id = e.id
    WHERE e.name <> 'global'
"""


# ---------- pure ----------

def canonical_uuid(value) -> Optional[str]:
    """A proposal id as stored (lowercase, hyphenated), or None if it isn't
    one: anything else would not match, or be a database error."""
    if not isinstance(value, str) or len(value) != 36:
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def coverage_tier(platform_type: Optional[str], products: List[str], indexed_loyalty: int,
                  indexed_reviews: int, indexed_shared: int) -> str:
    """'basic' or 'listed', from documents only (plan §4.1).

    Basic: at least one labelled, indexed guide for a Yotpo product the
    catalog lists for the integration (any product when the catalog lists
    none, as for integrations created by hand). Messaging also needs a
    `shared` document, the platform's own mechanics: the checklist depends
    on them.
    """
    wanted = [p for p in products if p in CATALOG_PRODUCTS] or list(CATALOG_PRODUCTS)
    guides = sum(n for p, n in (('loyalty', indexed_loyalty), ('reviews', indexed_reviews))
                 if p in wanted)
    if not guides:
        return 'listed'
    if platform_type == 'messaging' and not indexed_shared:
        return 'listed'
    return 'basic'


def summary_row(row) -> Dict:
    """One SUMMARY_SQL row as the list shows it."""
    (esp_id, name, display_name, status, platform_type, categories, products, slugs,
     type_set_by, total, loyalty, reviews, shared, unlabelled, failed, misses,
     indexed_loyalty, indexed_reviews, indexed_shared, open_proposals, not_crawled) = row
    categories, products = _json_list(categories), _json_list(products)
    types = category_types(categories)
    return {
        'id': str(esp_id),
        'name': name,
        'display_name': display_name or name,
        'status': status,
        'platform_type': platform_type,
        'categories': categories,
        'category_names': [category_name(c) for c in categories],
        'products': products,
        'catalog_slugs': _json_list(slugs),
        'documents': {'total': int(total), 'loyalty': int(loyalty), 'reviews': int(reviews),
                      'shared': int(shared), 'unlabelled': int(unlabelled)},
        'failed': int(failed),
        'not_crawled': int(not_crawled),
        'misses': int(misses),
        'open_proposals': int(open_proposals),
        'tier': coverage_tier(platform_type, products, int(indexed_loyalty),
                              int(indexed_reviews), int(indexed_shared)),
        # loaded documents with chunks in search, by label: what the tier counts
        'indexed': {'loyalty': int(indexed_loyalty), 'reviews': int(indexed_reviews),
                    'shared': int(indexed_shared)},
        # Categories that default to different types, until an admin picks one
        'type_choices': types if len(types) > 1 and not type_set_by else [],
        'type_set_by': type_set_by,
        # each category with the type it defaults to, so the admin can say why
        'category_kinds': [{'name': category_name(c), 'type': CATEGORY_DEFAULT_TYPE.get(c)}
                           for c in categories],
        # an admin should look at its type: unset, or its categories disagree
        'needs_type': not platform_type or (len(types) > 1 and not type_set_by),
    }


def matches(item: Dict, q: str = '', category: str = '', ptype: str = '', status: str = '',
            tier: str = '', flag: str = '') -> bool:
    """The list's filters. q searches the name, display name and category labels."""
    if q:
        hay = ' '.join([item['name'], item['display_name']] + item['category_names']).lower()
        if q.lower() not in hay:
            return False
    if category and category not in item['categories']:
        return False
    if ptype and item['platform_type'] != ptype:
        return False
    if status and item['status'] != status:
        return False
    if tier and item['tier'] != tier:
        return False
    if flag == 'unlabelled' and not item['documents']['unlabelled']:
        return False
    if flag == 'failed' and not item['failed']:
        return False
    if flag == 'proposals' and not item['open_proposals']:
        return False
    if flag == 'misses' and not item['misses']:
        return False
    if flag == 'mixed_types' and not item['needs_type']:
        return False
    return True


def paginate(items: List, page: int, per_page: int):
    start = (page - 1) * per_page
    return items[start:start + per_page]


def _page_args(default_per_page=PER_PAGE):
    """(page, per_page) from the query string, or a 400 message."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', default_per_page))
    except ValueError:
        return None, None, 'page and per_page must be numbers'
    if page < 1 or not 1 <= per_page <= MAX_PER_PAGE:
        return None, None, f'page must be 1 or more, per_page 1 to {MAX_PER_PAGE}'
    return page, per_page, None


def validate_patch(body, current: Dict, is_owner: bool):
    """(changes, error, status) for a PATCH body against the current row.

    changes maps column -> new value; JSON lists are still Python lists.
    """
    allowed = {'platform_type', 'display_name', 'categories', 'products', 'status'}
    if not isinstance(body, dict) or not body:
        return None, 'Send the fields to change as JSON', 400
    unknown = set(body) - allowed
    if unknown:
        return None, f"These can't be changed here: {', '.join(sorted(unknown))}", 400
    changes = {}
    if 'display_name' in body:
        name = body['display_name']
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
            return None, 'The display name must be 1 to 200 characters', 400
        changes['display_name'] = name.strip()
    if 'platform_type' in body:
        if body['platform_type'] not in PLATFORM_TYPES:
            return None, f"Kind of platform must be one of: {', '.join(PLATFORM_TYPES)}", 400
        changes['platform_type'] = body['platform_type']
    if 'categories' in body:
        cats = body['categories']
        if (not isinstance(cats, list) or len(cats) > 40
                or not all(isinstance(c, str) and 0 < len(c.strip()) <= 64 for c in cats)):
            return None, 'Categories must be a list of category names', 400
        seen = []
        for c in cats:
            c = c.strip().lower()
            if c not in seen:
                seen.append(c)
        changes['categories'] = seen
    if 'products' in body:
        prods = body['products']
        if not isinstance(prods, list) or not all(p in CATALOG_PRODUCTS for p in prods):
            return None, 'Products must be a list of: loyalty, reviews', 400
        changes['products'] = [p for p in CATALOG_PRODUCTS if p in prods]
    if 'status' in body:
        if body['status'] not in STATUSES:
            return None, f"Status must be one of: {', '.join(STATUSES)}", 400
        if not is_owner and body['status'] != current['status']:
            from auth import OWNER_ONLY_ERROR
            return None, OWNER_ONLY_ERROR, 403
        changes['status'] = body['status']
    status = changes.get('status', current['status'])
    ptype = changes.get('platform_type', current['platform_type'])
    if status == 'active' and ptype not in TYPES_IN_CHAT:
        kind = TYPE_LABELS.get(ptype, 'this kind of')
        return None, (f"{kind} platforms can't be in chat yet: the AI's instructions for them "
                      f"aren't written. Keep it \"Not in chat yet\"."), 409
    return changes, None, None


def validate_approvals(body):
    """([(id, product)], error) for POST /proposals/approve."""
    from product_labels import PRODUCTS, PRODUCT_REQUIRED
    items = body.get('items') if isinstance(body, dict) else None
    if not isinstance(items, list) or not items:
        return None, 'Send {"items": [{"id": ..., "product": ...}]}'
    if len(items) > MAX_ITEMS:
        return None, f'Approve at most {MAX_ITEMS} at a time'
    out = []
    for item in items:
        pid = canonical_uuid(item.get('id')) if isinstance(item, dict) else None
        if not pid:
            return None, 'Every item needs the id of a proposal'
        product = item.get('product')
        product = product.strip().lower() if isinstance(product, str) else product
        if product not in PRODUCTS:
            return None, PRODUCT_REQUIRED
        out.append((pid, product))
    return out, None


# ---------- database ----------

def _setting(db, key) -> Optional[Dict]:
    rows = db.execute_query("SELECT value FROM app_settings WHERE key = %s", (key,), fetch=True)
    if not rows or not rows[0][0]:
        return None
    try:
        return json.loads(rows[0][0])
    except ValueError:
        return None


def _integration_row(db, name) -> Optional[Dict]:
    """Any integration but 'global', whatever its status."""
    rows = db.execute_query(SUMMARY_SQL + " AND e.name = %s", (name,), fetch=True)
    return summary_row(rows[0]) if rows else None


def _decide(db, proposal_id, state, actor, note=None):
    db.execute_query("""
        UPDATE document_proposals
        SET state = %s, decided_by = %s, decided_at = CURRENT_TIMESTAMP,
            decision_note = COALESCE(%s, decision_note)
        WHERE id = %s AND state = 'open'
    """, (state, actor, note, proposal_id))


def _actor() -> str:
    """Who decided, for decided_by and platform_type_set_by."""
    from auth import current_user
    user = current_user()
    return (user or {}).get('email') or 'admin password'


def document_rows(db, esp_id, use_async: bool) -> List[Dict]:
    """Every document of one integration with its crawl state and the v2
    fields, newest first: the old link list's rows, plus title, source,
    plans, platforms and the index and miss counts."""
    from product_labels import header_label, HEADER_SCAN_CHARS
    from workers.crawl_queue import list_document_states, describe_link
    if use_async:
        docs = list_document_states(db, esp_id)
    else:
        rows = db.execute_query("""
            SELECT url, filename, crawl_status, last_crawled_at, error_message,
                   content IS NOT NULL AS has_content
            FROM esp_documents WHERE esp_id = %s ORDER BY created_at DESC
        """, (esp_id,), fetch=True) or []
        docs = []
        for url, filename, crawl_status, last_crawled_at, error, has_content in rows:
            state, detail = describe_link(crawl_status, bool(has_content), error)
            docs.append({'url': url, 'filename': filename, 'crawl_status': crawl_status,
                         'last_crawled_at': _iso(last_crawled_at), 'error_message': error,
                         'has_content': bool(has_content), 'is_crawling': False,
                         'state': state, 'detail': detail})
    extra = {r[0]: r for r in db.execute_query(f"""
        SELECT url, product, substr(content, 1, {HEADER_SCAN_CHARS}), title, source_kind,
               supported_plans, supported_platforms, vector_count, consecutive_misses, retired_at
        FROM esp_documents WHERE esp_id = %s
    """, (esp_id,), fetch=True) or []}
    out = []
    for doc in docs:
        e = extra.get(doc['url'])
        out.append({
            'url': doc['url'],
            'filename': doc['filename'],
            'status': doc['state'],
            'detail': doc['detail'],
            'crawl_status': doc['crawl_status'],
            'last_crawled_at': doc['last_crawled_at'],
            'error_message': doc['error_message'],
            'crawled': doc['crawl_status'] == 'completed',
            'is_crawling': doc['is_crawling'],
            'needs_backfill': doc['crawl_status'] == 'completed' and not doc['has_content'],
            # the same three fields product_labels.merge_labels adds
            'labelable': e is not None,
            'product': e[1] if e else None,
            'suggested_product': header_label(e[2]) if e else None,
            'title': e[3] if e else None,
            'source_kind': e[4] if e else None,
            'supported_plans': _json_list(e[5]) if e else [],
            'supported_platforms': _json_list(e[6]) if e else [],
            'vector_count': e[7] if e else None,
            'consecutive_misses': (e[8] or 0) if e else 0,
            'retired': bool(e and e[9]),
        })
    return out


_CRAWL_STATE_SQL_ASYNC = """
    SELECT d.url, d.crawl_status, d.content IS NOT NULL, d.error_message,
           j.status, j.error_kind, j.error_message,
           EXTRACT(EPOCH FROM (
               GREATEST(COALESCE(j.next_attempt_at, NOW()),
                        COALESCE(h.backoff_until, NOW())) - NOW()
           ))
    FROM esp_documents d
    JOIN esps e ON e.id = d.esp_id
    LEFT JOIN crawl_jobs j ON j.id = d.crawl_job_id
    LEFT JOIN crawl_hosts h ON h.host = j.host
    WHERE e.status <> 'archived' AND d.retired_at IS NULL
"""
_CRAWL_STATE_SQL_SYNC = """
    SELECT d.url, d.crawl_status, d.content IS NOT NULL, d.error_message
    FROM esp_documents d
    JOIN esps e ON e.id = d.esp_id
    WHERE e.status <> 'archived' AND d.retired_at IS NULL
"""
_ACTIVE_JOBS_SQL = f"""
    SELECT j.status, j.error_kind, j.error_message, j.host, d.url, e.name, e.display_name,
           EXTRACT(EPOCH FROM (
               GREATEST(COALESCE(j.next_attempt_at, NOW()),
                        COALESCE(h.backoff_until, NOW())) - NOW()
           ))
    FROM crawl_jobs j
    JOIN esp_documents d ON d.id = j.document_id
    JOIN esps e ON e.id = d.esp_id
    LEFT JOIN crawl_hosts h ON h.host = j.host
    WHERE j.status IN ('pending', 'processing')
    ORDER BY CASE WHEN j.status = 'processing' THEN 0 ELSE 1 END, j.priority, j.created_at
    LIMIT {ACTIVE_JOBS_SHOWN}
"""
IN_QUEUE = ('queued', 'crawling', 'waiting', 'retrying')


def crawl_summary(db, use_async: bool) -> Dict:
    """Documents by crawl state, the sites with queued or failed crawls, and
    the jobs running or waiting now (the first ACTIVE_JOBS_SHOWN)."""
    from crawler import url_host
    from workers.crawl_queue import describe_link
    states: Dict[str, int] = {}
    hosts: Dict[str, Dict[str, int]] = {}
    sql = _CRAWL_STATE_SQL_ASYNC if use_async else _CRAWL_STATE_SQL_SYNC
    for row in db.execute_query(sql, fetch=True) or []:
        url, crawl_status, has_content, error = row[:4]
        if use_async:
            job_status, kind, job_error, wait = row[4:]
            state, _ = describe_link(crawl_status, bool(has_content), error, job_status, kind,
                                     job_error, float(wait) if wait is not None else None, url)
        else:
            state, _ = describe_link(crawl_status, bool(has_content), error)
        states[state] = states.get(state, 0) + 1
        if state in IN_QUEUE or state == 'failed':
            h = hosts.setdefault(url_host(url), {'queued': 0, 'failed': 0})
            h['queued' if state in IN_QUEUE else 'failed'] += 1
    jobs, active = [], 0
    if use_async:
        from workers.crawl_queue import format_wait, RATE_LIMITED
        active = int(db.execute_query(
            "SELECT COUNT(*) FROM crawl_jobs WHERE status IN ('pending', 'processing')",
            fetch=True)[0][0])
        for status, kind, error, host, url, name, display, wait in \
                db.execute_query(_ACTIVE_JOBS_SQL, fetch=True) or []:
            wait = float(wait) if wait is not None else None
            if status == 'processing':
                state, detail = 'crawling', None
            elif kind:
                state = 'waiting' if kind == RATE_LIMITED else 'retrying'
                detail = f"{error} — retrying {format_wait(wait)}"
            else:
                state = 'queued'
                detail = f"starts {format_wait(wait)}" if wait and wait >= 5 else None
            jobs.append({'state': state, 'detail': detail, 'host': host, 'url': url,
                         'esp': name, 'display_name': display or name})
    host_rows = sorted(({'host': h, **n} for h, n in hosts.items()),
                       key=lambda r: (-r['queued'], -r['failed'], r['host']))
    return {'states': states, 'hosts': host_rows, 'jobs': jobs, 'active_jobs': active,
            'queue': use_async}


def needs_person(mechanics: Optional[Dict], names: Dict[str, str]) -> List[Dict]:
    """Integrations the import found no partner articles for, from its
    stored notes, so an admin picks them by hand: the help centre blocks
    automated reading (`blocked`), none was found (`no_help_centre`), or the
    model accepted none of what it read (`nothing_found`)."""
    out = []
    for name, m in sorted((mechanics or {}).items()):
        if name not in names:
            continue
        if m.get('blocked'):
            kind = 'blocked'
        elif not m.get('help_centre'):
            kind = 'no_help_centre'
        elif not m.get('accepted'):
            kind = 'nothing_found'
        else:
            continue
        out.append({'esp': name, 'display_name': names[name], 'kind': kind,
                    'help_centre': m.get('help_centre'), 'why': m.get('problem')})
    out.sort(key=lambda r: (('blocked', 'nothing_found', 'no_help_centre').index(r['kind']),
                            r['display_name'].lower()))
    return out


# ---------- routes ----------

def register_admin_integrations_routes(app, use_async_crawl: bool):
    from adapters.database.db_manager import get_database_adapter
    from auth import admin_request_ok, owner_request_ok

    def denied():
        if not admin_request_ok():
            return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403
        return None

    def db():
        return get_database_adapter()

    @app.route('/api/admin/integrations', methods=['GET'])
    def admin_list_integrations():
        """GET ?q=&category=&type=&status=&tier=&flag=&page=&per_page=

        One summary query for every integration; filters and pages in Python.
        `facets` counts the whole list, so the filters can say how many match.
        """
        stop = denied()
        if stop:
            return stop
        page, per_page, problem = _page_args()
        if problem:
            return jsonify({'error': problem}), 400
        args = {k: (request.args.get(k) or '').strip() for k in
                ('q', 'category', 'type', 'status', 'tier', 'flag')}
        for key, allowed in (('type', PLATFORM_TYPES), ('status', STATUSES), ('tier', TIERS),
                             ('flag', FLAGS)):
            if args[key] and args[key] not in allowed:
                return jsonify({'error': f"{key} must be one of: {', '.join(allowed)}"}), 400
        items = [summary_row(r) for r in db().execute_query(SUMMARY_SQL, fetch=True) or []]
        items.sort(key=lambda i: (i['display_name'].lower(), i['name']))
        cats: Dict[str, int] = {}
        for i in items:
            for c in i['categories']:
                cats[c] = cats.get(c, 0) + 1
        facets = {
            'categories': sorted(({'slug': c, 'name': category_name(c), 'count': n}
                                  for c, n in cats.items()), key=lambda c: c['name'].lower()),
            'flags': {f: sum(1 for i in items if matches(i, flag=f)) for f in FLAGS},
            'total': len(items),
            # for the Proposals tab's label, without a request of its own
            'open_proposals': sum(i['open_proposals'] for i in items),
        }
        found = [i for i in items if matches(i, args['q'], args['category'], args['type'],
                                             args['status'], args['tier'], args['flag'])]
        return jsonify({'integrations': paginate(found, page, per_page), 'total': len(found),
                        'page': page, 'per_page': per_page, 'facets': facets})

    @app.route('/api/admin/integrations/<name>', methods=['GET'])
    def admin_get_integration(name):
        """Its facts, catalog cards and coverage, and the import's notes on it."""
        stop = denied()
        if stop:
            return stop
        d = db()
        item = _integration_row(d, name)
        if not item:
            return jsonify({'error': 'No such integration'}), 404
        extra = d.execute_query("SELECT catalog_description, description FROM esps WHERE name = %s",
                                (name,), fetch=True)[0]
        item['catalog_description'] = extra[0]
        item['catalog_cards'] = [{'slug': s, 'url': f'https://www.yotpo.com/integrations/{s}/'}
                                 for s in item['catalog_slugs']]
        item['mechanics'] = (_setting(d, CATALOG_MECHANICS_KEY) or {}).get(name)
        item['in_chat_types'] = list(TYPES_IN_CHAT)
        return jsonify({'integration': item})

    @app.route('/api/admin/integrations/<name>', methods=['PATCH'])
    def admin_patch_integration(name):
        """Body: any of platform_type, display_name, categories, products,
        status (owner only). Sending platform_type, even unchanged, records
        that an admin chose it."""
        stop = denied()
        if stop:
            return stop
        d = db()
        current = _integration_row(d, name)
        if not current:
            return jsonify({'error': 'No such integration'}), 404
        changes, problem, code = validate_patch(request.get_json(silent=True), current,
                                                owner_request_ok())
        if problem:
            return jsonify({'error': problem}), code
        sets, params = [], []
        for column, value in changes.items():
            sets.append(f'{column} = %s')
            params.append(json.dumps(value) if column in ('categories', 'products') else value)
        if 'platform_type' in changes:
            sets.append('platform_type_set_by = %s')
            params.append(_actor())
        sets.append('updated_at = CURRENT_TIMESTAMP')
        d.execute_query(f"UPDATE esps SET {', '.join(sets)} WHERE name = %s",
                        tuple(params) + (name,))
        if 'status' in changes:
            # This process's chat check sees it at once; others within
            # esp_manager.ACTIVE_CACHE_SECONDS
            get_esp_manager()._active_names = None
        return jsonify({'success': True, 'integration': _integration_row(d, name)})

    @app.route('/api/admin/integrations/<name>/documents', methods=['GET'])
    def admin_integration_documents(name):
        """GET ?page=&per_page= : one integration's documents, newest first."""
        stop = denied()
        if stop:
            return stop
        page, per_page, problem = _page_args()
        if problem:
            return jsonify({'error': problem}), 400
        d = db()
        rows = d.execute_query("SELECT id FROM esps WHERE name = %s AND name <> 'global'",
                               (name,), fetch=True)
        if not rows:
            return jsonify({'error': 'No such integration'}), 404
        docs = document_rows(d, rows[0][0], use_async_crawl)
        return jsonify({'documents': paginate(docs, page, per_page), 'total': len(docs),
                        'page': page, 'per_page': per_page})

    @app.route('/api/admin/proposals', methods=['GET'])
    def admin_list_proposals():
        """GET ?esp=&source=&state=open&page=&per_page=100

        Ordered by integration, so a page shows whole groups but for the
        last one. `integrations` holds the import's notes for the ones on
        this page; `counts` counts each state and each source of `state`.
        """
        stop = denied()
        if stop:
            return stop
        page, per_page, problem = _page_args(default_per_page=100)
        if problem:
            return jsonify({'error': problem}), 400
        state = request.args.get('state', 'open')
        source = request.args.get('source', '')
        esp = request.args.get('esp', '')
        if state not in PROPOSAL_STATES:
            return jsonify({'error': f"state must be one of: {', '.join(PROPOSAL_STATES)}"}), 400
        if source and source not in PROPOSAL_SOURCES:
            return jsonify({'error': f"source must be one of: {', '.join(PROPOSAL_SOURCES)}"}), 400
        where, params = ['p.state = %s'], [state]
        if source:
            where.append('p.source = %s')
            params.append(source)
        if esp:
            where.append('e.name = %s')
            params.append(esp)
        d = db()
        cond = ' AND '.join(where)
        total = int(d.execute_query(f"""
            SELECT COUNT(*) FROM document_proposals p LEFT JOIN esps e ON e.id = p.esp_id
            WHERE {cond}""", tuple(params), fetch=True)[0][0])
        rows = d.execute_query(f"""
            SELECT p.id, p.url, p.source, p.suggested_label, p.state, p.note, p.title,
                   p.partner_function, p.reason, p.decision_note, p.created_at,
                   p.decided_by, p.decided_at, e.name, e.display_name, e.status, e.products
            FROM document_proposals p
            LEFT JOIN esps e ON e.id = p.esp_id
            WHERE {cond}
            ORDER BY LOWER(COALESCE(e.display_name, e.name, '')), e.name,
                     CASE p.source WHEN 'catalog' THEN 0 WHEN 'sitemap' THEN 1
                                   WHEN 'manual' THEN 2 ELSE 3 END,
                     p.url
            LIMIT %s OFFSET %s
        """, tuple(params) + (per_page, (page - 1) * per_page), fetch=True) or []
        mechanics = _setting(d, CATALOG_MECHANICS_KEY) or {}
        proposals, integrations = [], {}
        for r in rows:
            proposals.append({
                'id': str(r[0]), 'url': r[1], 'source': r[2], 'suggested_label': r[3],
                'state': r[4], 'note': r[5], 'title': r[6], 'partner_function': r[7],
                'reason': r[8], 'decision_note': r[9], 'created_at': _iso(r[10]),
                'decided_by': r[11], 'decided_at': _iso(r[12]), 'esp': r[13],
            })
            if r[13] and r[13] not in integrations:
                m = mechanics.get(r[13]) or {}
                integrations[r[13]] = {
                    'display_name': r[14] or r[13], 'status': r[15],
                    'products': _json_list(r[16]),
                    'functions': m.get('functions') or [],
                    'help_centre': m.get('help_centre'),
                }
        # Both follow the integration filter, so they match the list shown
        scope, scope_params = ('AND e.name = %s', (esp,)) if esp else ('', ())
        counts = {s: 0 for s in PROPOSAL_STATES}
        for s, n in d.execute_query(f"""
                SELECT p.state, COUNT(*) FROM document_proposals p LEFT JOIN esps e ON e.id = p.esp_id
                WHERE 1 = 1 {scope} GROUP BY p.state""", scope_params, fetch=True) or []:
            if s in counts:
                counts[s] = int(n)
        sources = {s: 0 for s in PROPOSAL_SOURCES}
        for s, n in d.execute_query(f"""
                SELECT p.source, COUNT(*) FROM document_proposals p LEFT JOIN esps e ON e.id = p.esp_id
                WHERE p.state = %s {scope} GROUP BY p.source""", (state,) + scope_params,
                fetch=True) or []:
            if s in sources:
                sources[s] = int(n)
        return jsonify({'proposals': proposals, 'integrations': integrations, 'total': total,
                        'page': page, 'per_page': per_page, 'counts': counts, 'sources': sources})

    @app.route('/api/admin/proposals/approve', methods=['POST'])
    def admin_approve_proposals():
        """Body: {"items": [{"id", "product"}]}. A product is required for
        every item, or nothing is approved. Each approved link becomes a
        labelled document and, with the crawl queue on, is queued."""
        stop = denied()
        if stop:
            return stop
        items, problem = validate_approvals(request.get_json(silent=True))
        if problem:
            return jsonify({'error': problem}), 400
        d, mgr, actor = db(), get_esp_manager(), _actor()
        results = []
        for proposal_id, product in items:
            rows = d.execute_query("""
                SELECT p.url, p.state, e.name, e.id
                FROM document_proposals p LEFT JOIN esps e ON e.id = p.esp_id
                WHERE p.id = %s
            """, (proposal_id,), fetch=True)
            if not rows:
                results.append({'id': proposal_id, 'ok': False, 'error': 'No such proposal'})
                continue
            url, state, esp_name, esp_id = rows[0]
            if state != 'open':
                results.append({'id': proposal_id, 'url': url, 'ok': False,
                                'error': f'Already {state}'})
                continue
            if not esp_name:
                results.append({'id': proposal_id, 'url': url, 'ok': False,
                                'error': 'This proposal has no integration'})
                continue
            try:
                doc = mgr.add_document(esp_name, url, product=product)
            except DuplicateURLError as e:
                if any(o['esp_name'] == esp_name for o in e.owners):
                    # Already this integration's document: added by hand, or an
                    # earlier approve stopped before recording it. Nothing to add;
                    # its label stays as it is.
                    _decide(d, proposal_id, 'approved', actor,
                            'Already a document of this integration; its label was kept')
                    results.append({'id': proposal_id, 'url': url, 'esp': esp_name, 'ok': True,
                                    'queued': False, 'warning': 'It was already a document here; '
                                    'nothing was added and its label was kept.'})
                else:
                    results.append({'id': proposal_id, 'url': url, 'ok': False, 'error': e.notice})
                continue
            except ValueError as e:
                results.append({'id': proposal_id, 'url': url, 'ok': False, 'error': str(e)})
                continue
            _decide(d, proposal_id, 'approved', actor)
            result = {'id': proposal_id, 'url': doc['url'], 'esp': esp_name, 'ok': True,
                      'queued': False}
            if use_async_crawl:
                from workers.crawl_queue import enqueue_crawl_job
                try:
                    enqueue_crawl_job(d, esp_id, doc['id'], doc['url'])
                    result['queued'] = True
                except Exception as e:
                    result['warning'] = (f'Added, but its crawl was not queued ({e}). '
                                         f'Select it and use Crawl Selected.')
            results.append(result)
        approved = sum(1 for r in results if r['ok'])
        return jsonify({'success': True, 'approved': approved, 'results': results})

    @app.route('/api/admin/proposals/reject', methods=['POST'])
    def admin_reject_proposals():
        """Body: {"ids": [...], "note": "..."}. A rejected link is never
        proposed again (the import skips every URL it has seen)."""
        stop = denied()
        if stop:
            return stop
        body = request.get_json(silent=True)
        ids = body.get('ids') if isinstance(body, dict) else None
        note = body.get('note') if isinstance(body, dict) else None
        ids = [canonical_uuid(i) for i in ids] if isinstance(ids, list) else None
        if not ids or not all(ids):
            return jsonify({'error': 'Send {"ids": [...]} with the ids of proposals'}), 400
        if len(ids) > MAX_ITEMS:
            return jsonify({'error': f'Reject at most {MAX_ITEMS} at a time'}), 400
        if note is not None and (not isinstance(note, str) or len(note) > 500):
            return jsonify({'error': 'The note must be text, up to 500 characters'}), 400
        d = db()
        marks = ','.join(['%s'] * len(ids))
        open_ids = [str(r[0]) for r in d.execute_query(
            f"SELECT id FROM document_proposals WHERE id IN ({marks}) AND state = 'open'",
            tuple(ids), fetch=True) or []]
        if open_ids:
            marks = ','.join(['%s'] * len(open_ids))
            d.execute_query(f"""
                UPDATE document_proposals
                SET state = 'rejected', decision_note = %s, decided_by = %s,
                    decided_at = CURRENT_TIMESTAMP
                WHERE id IN ({marks}) AND state = 'open'
            """, ((note or '').strip() or None, _actor()) + tuple(open_ids))
        return jsonify({'success': True, 'rejected': len(open_ids),
                        'skipped': len(ids) - len(open_ids)})

    @app.route('/api/admin/crawl-summary', methods=['GET'])
    def admin_crawl_summary():
        """Documents by crawl state and site, and the active jobs."""
        stop = denied()
        if stop:
            return stop
        return jsonify(crawl_summary(db(), use_async_crawl))

    @app.route('/api/admin/catalog-import', methods=['GET'])
    def admin_catalog_import():
        """The last import's report, and the integrations whose partner
        articles an admin has to pick by hand."""
        stop = denied()
        if stop:
            return stop
        d = db()
        names = {r[0]: r[1] or r[0] for r in d.execute_query(
            "SELECT name, display_name FROM esps WHERE status <> 'archived'", fetch=True) or []}
        return jsonify({'last_import': _setting(d, CATALOG_REPORT_KEY),
                        'needs_person': needs_person(_setting(d, CATALOG_MECHANICS_KEY), names)})
