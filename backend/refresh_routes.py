"""
Admin routes for keeping documents current (roadmap C1.3): retire and
replace a document, and support.yotpo.com's sitemap changes.

    POST /api/admin/esp/<name>/retire   {urls}
    POST /api/admin/esp/<name>/replace  {old_url, new_url}
    GET  /api/admin/sitemap-changes?since=YYYY-MM-DD   (default: 30 days)
    POST /api/admin/sitemap-refresh     owner: read the sitemap now

Every route needs an admin. Retire and replace work on documents like the
other link actions (any admin); reading the sitemap now queues re-crawls
for everyone's documents, so it is an owner's, like Refresh All.
"""

import threading
from datetime import datetime, timedelta

from flask import jsonify, request

import refresh
import sitemap_refresh
from esp_manager import get_esp_manager, DuplicateURLError
from mechanics_cache import clear_mechanics_cache
from urls import normalize_url

MAX_URLS = 200
_sitemap_lock = threading.Lock()


def run_sitemap_refresh(use_queue: bool):
    """One sitemap run, unless one is going already (the daily schedule and
    an owner's button can meet). Returns the summary, or None if skipped."""
    if not _sitemap_lock.acquire(blocking=False):
        print('[SITEMAP] a run is going already; skipped')
        return None
    try:
        from adapters.database.db_manager import get_database_adapter
        import link_finder
        return sitemap_refresh.run(get_database_adapter(), link_finder.Fetcher(log=print), use_queue)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'[SITEMAP] the run failed: {e}')
        return None
    finally:
        _sitemap_lock.release()


def register_refresh_routes(app, vectorizer, use_async_crawl: bool):
    from adapters.database.db_manager import get_database_adapter
    from auth import admin_request_ok, owner_request_ok, OWNER_ONLY_ERROR

    def denied():
        if not admin_request_ok():
            return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403
        return None

    def body():
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}

    @app.route('/api/admin/esp/<esp_name>/retire', methods=['POST'])
    def retire_documents(esp_name):
        """Body: {"urls": [...]}. Their search entries are removed and they
        are no longer crawled; the rows stay, marked retired."""
        stop = denied()
        if stop:
            return stop
        urls = body().get('urls')
        if not isinstance(urls, list) or not urls or not all(isinstance(u, str) for u in urls):
            return jsonify({'error': 'Send {"urls": [...]}'}), 400
        if len(urls) > MAX_URLS:
            return jsonify({'error': f'Retire at most {MAX_URLS} at a time'}), 400
        if not get_esp_manager().get_esp_by_name(esp_name):
            return jsonify({'error': 'No such integration'}), 404
        result = refresh.retire(get_database_adapter(), vectorizer, esp_name, urls)
        if result['retired']:
            clear_mechanics_cache()
        return jsonify({'success': True, **result})

    @app.route('/api/admin/esp/<esp_name>/replace', methods=['POST'])
    def replace_document(esp_name):
        """Body: {"old_url", "new_url"}. The new link becomes a document with
        the old one's label and is crawled; the old one is retired once the
        new one is indexed, so the integration is never without it."""
        stop = denied()
        if stop:
            return stop
        data = body()
        old_url, new_url = data.get('old_url'), data.get('new_url')
        if not isinstance(old_url, str) or not isinstance(new_url, str) or not new_url.strip():
            return jsonify({'error': 'Send {"old_url": ..., "new_url": ...}'}), 400
        old_url, new_url = normalize_url(old_url), normalize_url(new_url)
        if not new_url.startswith(('http://', 'https://')):
            return jsonify({'error': 'The new link must be a web address (https://…)'}), 400
        if old_url == new_url:
            return jsonify({'error': 'The new link is the same as the old one'}), 400
        mgr, db = get_esp_manager(), get_database_adapter()
        esp = mgr.get_esp_by_name(esp_name)
        if not esp:
            return jsonify({'error': 'No such integration'}), 404
        old = mgr.get_document_by_url(esp['id'], old_url)
        if not old:
            return jsonify({'error': 'The old link is not a document of this integration'}), 404
        rows = db.execute_query("SELECT retired_at FROM esp_documents WHERE id = %s", (old['id'],), fetch=True)
        if rows and rows[0][0]:
            return jsonify({'error': 'The old link is retired already: add the new one as a link'}), 409
        if not old.get('product'):
            return jsonify({'error': 'The old link has no product label: pick one first, so the new '
                                     'link gets the same'}), 400
        try:
            new = mgr.add_document(esp_name, new_url, product=old['product'])
        except DuplicateURLError as e:
            return jsonify({'error': str(e), 'duplicate': True, 'matches': e.owners}), 409
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        db.execute_query("UPDATE esp_documents SET replaced_by = %s WHERE id = %s", (new['id'], old['id']))
        result = {'success': True, 'new_url': new['url'], 'product': old['product'], 'queued': False}
        if use_async_crawl and app.config.get('CRAWL_WORKER_RUNNING'):
            from workers.crawl_queue import enqueue_crawl_job
            try:
                job_id, _ = enqueue_crawl_job(db, esp['id'], new['id'], new['url'])
                result.update(queued=True, job_id=job_id)
            except Exception as e:
                result['warning'] = (f'Added, but its crawl was not queued ({e}). Tick it and use '
                                     f'Crawl Selected.')
        return jsonify(result)

    @app.route('/api/admin/sitemap-changes', methods=['GET'])
    def sitemap_changes():
        """GET ?since=YYYY-MM-DD: support.yotpo.com articles new, changed or
        gone since then (default 30 days), and the last run."""
        stop = denied()
        if stop:
            return stop
        since = (request.args.get('since') or '').strip()
        if since:
            try:
                start = datetime.strptime(since, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'since must be a date: YYYY-MM-DD'}), 400
        else:
            start = datetime.utcnow() - timedelta(days=30)
        out = sitemap_refresh.changes_since(get_database_adapter(), start)
        out['since'] = start.strftime('%Y-%m-%d')
        out['scheduled'] = bool(use_async_crawl)
        return jsonify(out)

    @app.route('/api/admin/sitemap-refresh', methods=['POST'])
    def sitemap_refresh_now():
        """Read the sitemap now, in the background (owner)."""
        stop = denied()
        if stop:
            return stop
        if not owner_request_ok():
            return jsonify({'error': OWNER_ONLY_ERROR}), 403
        if _sitemap_lock.locked():
            return jsonify({'error': 'The sitemap is being read already. Look again in a minute.'}), 409
        use_queue = bool(use_async_crawl and app.config.get('CRAWL_WORKER_RUNNING'))
        threading.Thread(target=run_sitemap_refresh, args=(use_queue,), daemon=True,
                         name='sitemap-refresh').start()
        return jsonify({'success': True, 'started': True}), 202
