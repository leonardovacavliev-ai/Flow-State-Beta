"""
Admin ESP Routes - Database-backed version

These routes replace the filesystem-based ESP management in app.py
Import these routes into app.py to enable database-backed ESP management.

IMPORTANT: Uses lazy initialization to avoid database connection at import time.
"""

from flask import jsonify, request
from esp_manager import get_esp_manager
from crawler import crawl_single_url, vectorize_single_document, filename_from_url
import os
import json


def check_admin_password():
    """Check admin password from header, query param, or JSON body."""
    admin_password = os.environ.get('ADMIN_PASSWORD', 'RICHCSM')
    password = (
        request.headers.get('X-Admin-Password', '')
        or request.args.get('password', '')
    )
    if not password and request.is_json:
        data = request.get_json(silent=True) or {}
        password = data.get('password', '')
    return password == admin_password


def delete_document_artifacts(esp_name, urls, vectorizer, base_path):
    """
    Remove a document's vectors, saved file, and metadata entry, so a deleted
    link actually stops being served as RAG context.
    """
    docs_path = os.path.join(base_path, 'docs')
    metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
    esp_key = esp_name.lower()

    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, OSError):
            metadata = {}

    for url in urls:
        # Delete vector chunks for this URL
        try:
            if hasattr(vectorizer, 'delete_by_url'):
                vectorizer.delete_by_url(url, esp_key)
        except Exception as e:
            print(f"[DELETE] Vector cleanup failed for {url}: {e}")

        # Delete the saved file referenced by metadata
        for doc in metadata.get(esp_key, []):
            if doc.get('url') == url:
                filepath = doc.get('filepath')
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except OSError as e:
                        print(f"[DELETE] Could not remove {filepath}: {e}")

    # Drop metadata entries so a later refresh doesn't resurrect the docs
    if esp_key in metadata:
        metadata[esp_key] = [d for d in metadata[esp_key] if d.get('url') not in urls]
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except OSError as e:
            print(f"[DELETE] Could not update metadata: {e}")


def rebuild_esp_vectors(esp_name, vectorizer, base_path):
    """
    Rebuild an ESP's local doc files and vectors from content stored in the
    database.

    On ephemeral hosting (Railway) the docs/ folder and crawl_metadata.json
    are wiped on every redeploy; the database keeps the crawled text, so this
    re-materializes the files, repairs the metadata, and re-vectorizes each
    document per-URL.

    Returns (rebuilt_urls, skipped_urls) — skipped means no stored content.
    """
    esp_mgr = get_esp_manager()
    docs = esp_mgr.get_documents_with_content(esp_name)

    esp_key = esp_name.lower()
    esp_folder = os.path.join(base_path, 'docs', esp_key)
    docs_path = os.path.join(base_path, 'docs')
    metadata_path = os.path.join(docs_path, 'crawl_metadata.json')

    rebuilt, skipped = [], []

    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, OSError):
            metadata = {}
    metadata.setdefault(esp_key, [])

    for doc in docs:
        if not doc.get('content'):
            skipped.append(doc['url'])
            continue

        url = doc['url']
        filename = doc.get('filename') or ''
        if not filename.endswith('.txt'):
            filename = filename_from_url(url)

        os.makedirs(esp_folder, exist_ok=True)
        filepath = os.path.join(esp_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(doc['content'])

        metadata[esp_key] = [d for d in metadata[esp_key] if d.get('url') != url]
        metadata[esp_key].append({
            'url': url,
            'filename': filename,
            'filepath': filepath
        })

        try:
            vectorize_single_document(vectorizer, esp_key, url, filepath, filename)
            rebuilt.append(url)
        except Exception as e:
            print(f"[REBUILD] Vectorization failed for {url}: {e}")
            skipped.append(url)

    os.makedirs(docs_path, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return rebuilt, skipped


def register_esp_admin_routes(app, BASE_PATH, vectorizer):
    """Register all ESP admin routes with the Flask app."""

    # Lazy initialization - only connect to database when route is actually called
    def get_mgr():
        """Get ESP manager instance (lazy initialization)."""
        return get_esp_manager()

    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        """Get list of ESPs from database."""
        try:
            esp_mgr = get_mgr()
            # 'global' is an internal row holding global-knowledge docs,
            # not a selectable ESP
            esps = [e for e in esp_mgr.list_esps() if e['name'] != 'global']
            return jsonify({'esps': esps})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/<esp_name>/links', methods=['GET'])
    def get_esp_links(esp_name):
        """Get links for a specific ESP from database."""
        try:
            esp_mgr = get_mgr()
            docs = esp_mgr.list_documents(esp_name)

            # Convert to frontend format
            # Map database crawl_status to frontend status field
            links = [{
                'url': doc['url'],
                'filename': doc['filename'],
                'status': 'crawled' if doc['crawl_status'] == 'completed' else 'pending',  # Frontend expects 'status'
                'crawl_status': doc['crawl_status'],  # Keep for backward compat
                'last_crawled_at': doc['last_crawled_at'],
                'error_message': doc.get('error_message'),
                'crawled': doc['crawl_status'] == 'completed'
            } for doc in docs]

            return jsonify({'links': links})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/<esp_name>/add-link', methods=['POST'])
    def add_esp_link(esp_name):
        """Add a new link to an ESP."""
        if not check_admin_password():
            return jsonify({'error': 'Invalid password'}), 403
        try:
            esp_mgr = get_mgr()
            data = request.json
            url = data.get('url', '').strip()

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            # Add to database
            doc = esp_mgr.add_document(esp_name, url)

            return jsonify({
                'success': True,
                'message': f'Link added successfully',
                'doc_id': doc['id']
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/create', methods=['POST'])
    def create_esp():
        """Create a new ESP."""
        if not check_admin_password():
            return jsonify({'error': 'Invalid password'}), 403
        try:
            esp_mgr = get_mgr()
            data = request.json
            name = data.get('name', '').strip()
            display_name = data.get('display_name', '').strip()
            description = data.get('description', '').strip()

            if not name:
                return jsonify({'error': 'ESP name is required'}), 400

            if not display_name:
                display_name = name.title()

            # Create in database
            esp = esp_mgr.create_esp(name, display_name, description)

            # Create filesystem folder for backward compatibility (crawler still saves to files)
            docs_path = os.path.join(BASE_PATH, 'docs', esp['name'])
            os.makedirs(docs_path, exist_ok=True)

            return jsonify({
                'success': True,
                'message': f"ESP '{display_name}' created successfully",
                'esp': esp
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/<esp_name>/crawl-selected', methods=['POST'])
    def crawl_esp_selected(esp_name):
        """Crawl selected URLs for an ESP and update database."""
        if not check_admin_password():
            return jsonify({'error': 'Invalid password'}), 403
        try:
            esp_mgr = get_mgr()
            data = request.json
            urls = data.get('urls', [])

            if not urls:
                return jsonify({'error': 'No URLs provided'}), 400

            results = {
                'success': [],
                'failed': []
            }

            base_docs_path = os.path.join(BASE_PATH, 'docs')
            esp_docs_path = os.path.join(base_docs_path, esp_name)
            os.makedirs(esp_docs_path, exist_ok=True)

            for url in urls:
                doc = None  # reset so the except block can't act on the previous URL's doc
                try:
                    # Get document from database
                    esp = esp_mgr.get_esp_by_name(esp_name)
                    if not esp:
                        results['failed'].append({
                            'url': url,
                            'error': f"ESP '{esp_name}' not found"
                        })
                        continue

                    doc = esp_mgr.get_document_by_url(esp['id'], url)

                    if not doc:
                        # Add if doesn't exist
                        doc = esp_mgr.add_document(esp_name, url)

                    # Crawl the URL
                    filename = crawl_single_url(url, esp_name, BASE_PATH)

                    if filename:
                        # Read content to calculate hash
                        file_path = os.path.join(esp_docs_path, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        content_hash = esp_mgr.calculate_content_hash(content)

                        # Update crawl_metadata.json for vectorizer compatibility
                        import json
                        metadata_path = os.path.join(base_docs_path, 'crawl_metadata.json')
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                        except FileNotFoundError:
                            metadata = {}

                        if esp_name not in metadata:
                            metadata[esp_name] = []

                        # Add/update document in metadata
                        doc_metadata = {
                            'url': url,
                            'filename': filename,
                            'filepath': file_path
                        }

                        # Remove old entry if exists (by URL)
                        metadata[esp_name] = [d for d in metadata[esp_name] if d.get('url') != url]
                        metadata[esp_name].append(doc_metadata)

                        with open(metadata_path, 'w') as f:
                            json.dump(metadata, f, indent=2)

                        # Vectorize just this document — refresh_esp() would
                        # delete the whole namespace and re-add only local
                        # files, wiping prod knowledge on ephemeral storage.
                        try:
                            vectorize_single_document(vectorizer, esp_name, url, file_path, filename)
                            print(f"[VECTORIZE] Successfully vectorized {filename}")
                        except Exception as ve:
                            print(f"[VECTORIZE ERROR] {esp_name}/{filename}: {ve}")
                            import traceback
                            traceback.print_exc()

                        # Update database — store the content itself so the
                        # knowledge base survives redeploys of the ephemeral
                        # container filesystem
                        esp_mgr.update_document_crawl_status(
                            doc['id'],
                            status='completed',
                            content_hash=content_hash,
                            content=content,
                            filename=filename
                        )

                        results['success'].append({
                            'url': url,
                            'filename': filename
                        })
                    else:
                        # Mark as failed
                        esp_mgr.update_document_crawl_status(
                            doc['id'],
                            status='failed',
                            error_message='Crawl returned empty content'
                        )
                        results['failed'].append({
                            'url': url,
                            'error': 'Crawl returned empty content'
                        })

                except Exception as e:
                    # Mark as failed if doc exists
                    if doc:
                        esp_mgr.update_document_crawl_status(
                            doc['id'],
                            status='failed',
                            error_message=str(e)
                        )

                    results['failed'].append({
                        'url': url,
                        'error': str(e)
                    })

            return jsonify({
                'success': True,
                'results': results,
                'message': f"Crawled {len(results['success'])} URLs successfully, {len(results['failed'])} failed"
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/<esp_name>/paste-content', methods=['POST'])
    def paste_esp_content(esp_name):
        """Manually add content for a link that can't be crawled."""
        try:
            esp_mgr = get_mgr()
            data = request.json
            password = data.get('password', '')
            url = data.get('url', '')
            content = data.get('content', '')

            # Verify admin password
            ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'RICHCSM')
            if password != ADMIN_PASSWORD:
                return jsonify({'error': 'Invalid password'}), 403

            if not url or not content:
                return jsonify({'error': 'URL and content are required'}), 400

            # Get or create ESP
            esp = esp_mgr.get_esp_by_name(esp_name)
            if not esp:
                return jsonify({'error': f"ESP '{esp_name}' not found"}), 404

            # Get or create document
            doc = esp_mgr.get_document_by_url(esp['id'], url)
            if not doc:
                doc = esp_mgr.add_document(esp_name, url)

            # Generate filename from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            filename = '_'.join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
            filename = filename.replace('.html', '').replace('.htm', '')
            if not filename:
                filename = 'index'
            filename = f"{filename}.txt"

            # Save content to file
            base_docs_path = os.path.join(BASE_PATH, 'docs')
            esp_docs_path = os.path.join(base_docs_path, esp_name)
            os.makedirs(esp_docs_path, exist_ok=True)
            file_path = os.path.join(esp_docs_path, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Source URL: {url}\n\n")
                f.write(content)

            # Calculate content hash
            content_hash = esp_mgr.calculate_content_hash(f"Source URL: {url}\n\n{content}")

            # Update crawl_metadata.json for vectorizer compatibility
            import json
            metadata_path = os.path.join(base_docs_path, 'crawl_metadata.json')
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except FileNotFoundError:
                metadata = {}

            if esp_name not in metadata:
                metadata[esp_name] = []

            # Add/update document in metadata
            doc_metadata = {
                'url': url,
                'filename': filename,
                'filepath': file_path
            }

            # Remove old entry if exists (by URL)
            metadata[esp_name] = [d for d in metadata[esp_name] if d.get('url') != url]
            metadata[esp_name].append(doc_metadata)

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Vectorize just this document (see crawl route for why not refresh_esp)
            try:
                vectorize_single_document(vectorizer, esp_name, url, file_path, filename)
                print(f"[VECTORIZE] Successfully vectorized pasted content for {filename}")
            except Exception as ve:
                print(f"[VECTORIZE ERROR] {esp_name}/{filename}: {ve}")
                import traceback
                traceback.print_exc()

            # Update database — persist the pasted content too (it can't be
            # re-crawled, so losing it on redeploy would be permanent)
            esp_mgr.update_document_crawl_status(
                doc['id'],
                status='completed',
                content_hash=content_hash,
                content=f"Source URL: {url}\n\n{content}",
                filename=filename
            )

            return jsonify({
                'success': True,
                'message': 'Content saved and vectorized successfully',
                'filename': filename
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/<esp_name>/delete-links', methods=['POST'])
    def delete_esp_links(esp_name):
        """Delete selected links from an ESP."""
        if not check_admin_password():
            return jsonify({'error': 'Invalid password'}), 403
        try:
            esp_mgr = get_mgr()
            data = request.json
            urls = data.get('urls', [])

            if not urls:
                return jsonify({'error': 'No URLs provided'}), 400

            # Delete from database
            deleted_count = esp_mgr.delete_documents_by_urls(esp_name, urls)

            # Also remove vectors, files, and metadata so the deleted docs
            # actually stop being served as RAG context
            delete_document_artifacts(esp_name, urls, vectorizer, BASE_PATH)

            return jsonify({
                'success': True,
                'message': f"Deleted {deleted_count} links",
                'deleted_count': deleted_count
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/<esp_name>/stats', methods=['GET'])
    def get_esp_stats(esp_name):
        """Get statistics for an ESP."""
        try:
            esp_mgr = get_mgr()
            stats = esp_mgr.get_esp_stats(esp_name)
            if not stats:
                return jsonify({'error': f"ESP '{esp_name}' not found"}), 404

            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/rebuild-vectors', methods=['POST'])
    def rebuild_vectors():
        """
        Rebuild doc files and vectors from database-stored content.

        Body: {"esp": "<name>"} for one ESP, or {} / {"esp": "all"} for all.
        Use after a redeploy to restore the knowledge base, or to re-embed.
        """
        if not check_admin_password():
            return jsonify({'error': 'Invalid password'}), 403
        try:
            esp_mgr = get_mgr()
            data = request.get_json(silent=True) or {}
            target = (data.get('esp') or 'all').lower()

            if target == 'all':
                esp_names = [esp['name'] for esp in esp_mgr.list_esps()]
            else:
                if not esp_mgr.get_esp_by_name(target):
                    return jsonify({'error': f"ESP '{target}' not found"}), 404
                esp_names = [target]

            summary = {}
            for name in esp_names:
                rebuilt, skipped = rebuild_esp_vectors(name, vectorizer, BASE_PATH)
                summary[name] = {
                    'rebuilt': len(rebuilt),
                    'skipped_no_content': skipped
                }

            return jsonify({'success': True, 'results': summary})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    print("[ESP Admin Routes] Database-backed ESP management routes registered")
