"""
The monthly read of support.yotpo.com's sitemap (roadmap C1.3; monthly, not
daily: Leo, 2026-10-16). It runs on the 1st at 03:17 UTC, and at boot when the
last read is over OVERDUE_DAYS old (app.py).

Each run:
  1. reads sitemap-en.xml, every article's address and when it last changed;
  2. records them in `sitemap_urls`: new addresses, changed dates, and the
     ones that vanished (gone_at);
  3. queues a re-crawl of every Yotpo guide we hold (not retired, labelled)
     whose sitemap date is newer than its last crawl, at the lowest priority;
     an unchanged text is then not re-indexed (refresh.py). Not on the very
     first read, which only records the sitemap and counts those guides:
     re-crawling many guides at once is Leo's call;
  4. notes the sitemap index's child sitemaps, so a new one is reported.

New and vanished articles are listed for an admin, unassigned
(GET /api/admin/sitemap-changes): names collide with ordinary words (Rule,
Target, Drip), so an article is never matched to an integration here.

A sitemap that reads as much smaller than the last one (a half-loaded or
redesigned file) marks nothing gone, so one bad read can't flag half of
Yotpo's guides as deleted.
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from urls import normalize_url

SITEMAP_URL = 'https://support.yotpo.com/sitemap-en.xml'
INDEX_URL = 'https://support.yotpo.com/sitemap_index.xml'
HOST = 'support.yotpo.com'
LAST_RUN_KEY = 'sitemap_last_run'
# Below this share of the previous read, nothing is marked gone
SHRINK_LIMIT = 0.8
# Re-crawls the sitemap queues wait behind anything an admin asked for
PRIORITY = 0
# A read older than this is overdue (monthly schedule, plus slack)
OVERDUE_DAYS = 32
# What the admin's list covers by default: more than a month, so the last
# monthly read's finds are still on it
CHANGES_DAYS = 45


# ---------- pure ----------

def parse_lastmod(value: Optional[str]) -> Optional[datetime]:
    """A sitemap <lastmod> as naive UTC (how the database stores times), or None."""
    if not value:
        return None
    text = value.strip().replace('Z', '+00:00')
    # Python before 3.11 reads a fraction of a second only as 3 or 6 digits
    # ("12:27:50.22" is in the live sitemap): pad it to 6
    text = re.sub(r'(T\d{2}:\d{2}:\d{2})\.(\d{1,6})', lambda m: f'{m.group(1)}.{m.group(2).ljust(6, "0")}', text)
    for parse in (datetime.fromisoformat,
                  lambda t: datetime.strptime(t[:10], '%Y-%m-%d')):
        try:
            dt = parse(text)
            break
        except ValueError:
            continue
    else:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def read_entries(xml: str) -> Dict[str, Optional[datetime]]:
    """{url: lastmod} from a sitemap."""
    soup = BeautifulSoup(xml or '', 'html.parser')
    out = {}
    for u in soup.find_all('url'):
        loc = u.find('loc')
        if loc and loc.get_text(strip=True):
            lastmod = u.find('lastmod')
            out[normalize_url(loc.get_text(strip=True))] = parse_lastmod(
                lastmod.get_text(strip=True) if lastmod else None)
    return out


def child_sitemaps(xml: str) -> List[str]:
    soup = BeautifulSoup(xml or '', 'html.parser')
    return sorted({normalize_url(s.find('loc').get_text(strip=True))
                   for s in soup.find_all('sitemap') if s.find('loc')})


def diff(previous: Dict[str, Tuple[Optional[datetime], Optional[datetime]]],
         current: Dict[str, Optional[datetime]]) -> Dict[str, List[str]]:
    """What changed between the stored sitemap ({url: (lastmod, gone_at)})
    and this read: new, changed (newer lastmod), vanished, back (vanished
    before, listed again)."""
    live = {u for u, (_, gone) in previous.items() if gone is None}
    out = {'new': [], 'changed': [], 'vanished': [], 'back': []}
    for url, lastmod in sorted(current.items()):
        if url not in previous:
            out['new'].append(url)
            continue
        old_lastmod, gone = previous[url]
        if gone is not None:
            out['back'].append(url)
        elif lastmod and (old_lastmod is None or lastmod > old_lastmod):
            out['changed'].append(url)
    out['vanished'] = sorted(live - set(current))
    return out


def too_small(previous_live: int, current: int) -> bool:
    return previous_live > 0 and current < SHRINK_LIMIT * previous_live


def due(lastmod: Optional[datetime], last_crawled: Optional[datetime]) -> bool:
    """A document whose article changed after its last crawl. Never crawled
    ones are left to the admin (they may not be labelled or wanted yet)."""
    return lastmod is not None and last_crawled is not None and lastmod > last_crawled


def overdue(last_run: Optional[Dict], now: Optional[datetime] = None) -> bool:
    """No read yet, or the last one started more than OVERDUE_DAYS ago."""
    started = parse_lastmod((last_run or {}).get('started_at'))
    now = now or datetime.utcnow()
    return started is None or now - started > timedelta(days=OVERDUE_DAYS)


def _as_datetime(value) -> Optional[datetime]:
    """A timestamp column: datetime from Postgres, text from SQLite."""
    if value is None or isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).replace(tzinfo=None)
    except ValueError:
        return None


# ---------- the run ----------

def run(db, fetch, use_queue: bool, log=print) -> Dict:
    """One read of the sitemap, as the module docstring says. `fetch` returns
    an object with .status and .text (link_finder.Fetcher, or a fake).
    Returns the summary, also stored in app_settings for the admin."""
    started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    summary = {'started_at': started, 'ok': False}
    page = fetch(SITEMAP_URL)
    current = read_entries(page.text) if page and page.status == 200 else {}
    if not current:
        summary['problem'] = "support.yotpo.com's sitemap could not be read"
        _save(db, summary)
        log(f"[SITEMAP] {summary['problem']}")
        return summary

    previous = {r[0]: (_as_datetime(r[1]), _as_datetime(r[2])) for r in db.execute_query(
        "SELECT url, lastmod, gone_at FROM sitemap_urls", fetch=True) or []}
    changes = diff(previous, current)
    live_before = sum(1 for _, gone in previous.values() if gone is None)
    last = _load(db) or {}
    # A much smaller sitemap marks nothing gone, unless the last read saw
    # the same smaller size: then Yotpo really did remove those articles
    shrunk = too_small(live_before, len(current)) and not (
        last.get('shrunk') and last.get('urls') == len(current))
    first_read = not previous

    # Only what changed is written: new rows, newer dates, returns
    for url in changes['new']:
        db.execute_query("INSERT INTO sitemap_urls (url, lastmod) VALUES (%s, %s) "
                         "ON CONFLICT (url) DO NOTHING", (url, current[url]))
    for url in changes['changed'] + changes['back']:
        # a date that can't be read keeps the one stored
        db.execute_query("UPDATE sitemap_urls SET lastmod = COALESCE(%s, lastmod), gone_at = NULL "
                         "WHERE url = %s", (current[url], url))
    seen = sorted(set(current) - set(changes['new']))
    for i in range(0, len(seen), 200):
        batch = seen[i:i + 200]
        db.execute_query(f"UPDATE sitemap_urls SET last_seen_at = CURRENT_TIMESTAMP "
                         f"WHERE url IN ({', '.join(['%s'] * len(batch))})", tuple(batch))
    if not shrunk:
        for url in changes['vanished']:
            db.execute_query("UPDATE sitemap_urls SET gone_at = CURRENT_TIMESTAMP "
                             "WHERE url = %s AND gone_at IS NULL", (url,))

    # The first read only records the sitemap: queueing every guide Yotpo
    # changed since its last crawl would re-crawl many at once, which is
    # Leo's call (roadmap C1.3 note). Later reads queue what changed since.
    queued, skipped = queue_changed(db, current, use_queue and not first_read)

    index = fetch(INDEX_URL)
    children = child_sitemaps(index.text) if index and index.status == 200 else None
    known_children = last.get('children') or []
    summary.update({
        'ok': True, 'urls': len(current), 'new': len(changes['new']),
        'changed': len(changes['changed']), 'back': len(changes['back']),
        'vanished': 0 if shrunk else len(changes['vanished']),
        'shrunk': shrunk, 'queued': queued, 'not_queued': skipped, 'first_read': first_read,
        'children': children if children is not None else known_children,
        'new_children': sorted(set(children or []) - set(known_children)) if known_children else [],
        'finished_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    })
    if shrunk:
        summary['problem'] = (f'the sitemap lists {len(current)} articles, fewer than '
                              f'{int(SHRINK_LIMIT * 100)}% of the {live_before} last time: none marked gone')
    _save(db, summary)
    log(f"[SITEMAP] {len(current)} articles; {summary['new']} new, {summary['changed']} changed, "
        f"{summary['vanished']} gone; {queued} re-crawls queued")
    return summary


def queue_changed(db, current: Dict[str, Optional[datetime]], use_queue: bool) -> Tuple[int, int]:
    """Record each held guide's sitemap date, and queue a re-crawl of the
    ones changed since their last crawl. (queued, due but not queued:
    no crawl queue on this server, the first read, or no product label)."""
    rows = db.execute_query("""
        SELECT d.id, d.esp_id, d.url, d.last_crawled_at, d.product, e.status, d.sitemap_lastmod
        FROM esp_documents d JOIN esps e ON e.id = d.esp_id
        WHERE d.retired_at IS NULL AND d.url LIKE %s
    """, (f'https://{HOST}/%',), fetch=True) or []
    queued = skipped = 0
    for doc_id, esp_id, url, last_crawled, product, status, stored in rows:
        lastmod = current.get(url)
        if lastmod is None:
            continue
        if _as_datetime(stored) != lastmod:
            db.execute_query("UPDATE esp_documents SET sitemap_lastmod = %s WHERE id = %s", (lastmod, doc_id))
        if not due(lastmod, _as_datetime(last_crawled)):
            continue
        if not use_queue or status == 'archived' or product not in ('loyalty', 'reviews', 'shared'):
            skipped += 1
            continue
        from workers.crawl_queue import enqueue_crawl_job
        _, created = enqueue_crawl_job(db, esp_id, doc_id, url, priority=PRIORITY)
        queued += 1 if created else 0
    return queued, skipped


def changes_since(db, since: datetime) -> Dict:
    """For the admin: articles new, changed or gone since `since`, each with
    the integration that holds it as a document, if any, or its open
    suggestion. Unassigned: nothing is matched by name here."""
    def rows(sql, params):
        return db.execute_query(sql, params, fetch=True) or []
    held = {r[0]: {'esp': r[1], 'display_name': r[2] or r[1], 'retired': bool(r[3])} for r in rows("""
        SELECT d.url, e.name, e.display_name, d.retired_at
        FROM esp_documents d JOIN esps e ON e.id = d.esp_id WHERE d.url LIKE %s
    """, (f'https://{HOST}/%',))}
    proposed = {r[0]: {'esp': r[1], 'display_name': r[2] or r[1], 'state': r[3]} for r in rows("""
        SELECT p.url, e.name, e.display_name, p.state
        FROM document_proposals p LEFT JOIN esps e ON e.id = p.esp_id WHERE p.url LIKE %s
    """, (f'https://{HOST}/%',))}

    def entry(url, when):
        return {'url': url, 'when': when.isoformat() if hasattr(when, 'isoformat') else when,
                'document': held.get(url), 'proposal': proposed.get(url)}
    # The very first read finds every article "new": that is not news, so
    # what it found is left out
    first = rows("SELECT MIN(first_seen_at) FROM sitemap_urls", ())
    first_read = _as_datetime(first[0][0]) if first else None
    after_first = max(since, first_read + timedelta(hours=1)) if first_read else since
    out = {
        'new': [entry(r[0], r[1]) for r in rows(
            "SELECT url, first_seen_at FROM sitemap_urls WHERE first_seen_at >= %s AND gone_at IS NULL "
            "ORDER BY first_seen_at DESC, url", (after_first,))],
        'changed': [entry(r[0], r[1]) for r in rows(
            "SELECT url, lastmod FROM sitemap_urls WHERE lastmod >= %s AND first_seen_at < %s "
            "AND gone_at IS NULL ORDER BY lastmod DESC, url", (since, after_first))],
        'vanished': [entry(r[0], r[1]) for r in rows(
            "SELECT url, gone_at FROM sitemap_urls WHERE gone_at >= %s ORDER BY gone_at DESC, url", (since,))],
    }
    out['first_read_at'] = first_read.isoformat() if first_read else None
    out['last_run'] = _load(db)
    return out


def _load(db) -> Optional[Dict]:
    rows = db.execute_query("SELECT value FROM app_settings WHERE key = %s", (LAST_RUN_KEY,), fetch=True)
    try:
        return json.loads(rows[0][0]) if rows and rows[0][0] else None
    except ValueError:
        return None


def _save(db, summary: Dict) -> None:
    db.execute_query("INSERT INTO app_settings (key, value) VALUES (%s, %s) "
                     "ON CONFLICT (key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                     (LAST_RUN_KEY, json.dumps(summary)))
