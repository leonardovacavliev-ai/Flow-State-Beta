"""
Admin ESP Routes - Database-backed version

These routes replace the filesystem-based ESP management in app.py
Import these routes into app.py to enable database-backed ESP management.

IMPORTANT: Uses lazy initialization to avoid database connection at import time.
"""

from flask import jsonify, request
from esp_manager import get_esp_manager
from crawler import crawl_single_url
import os


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
            esps = esp_mgr.list_esps()
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

            docs_path = os.path.join(BASE_PATH, 'docs', esp_name)
            os.makedirs(docs_path, exist_ok=True)

            for url in urls:
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
                        file_path = os.path.join(docs_path, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        content_hash = esp_mgr.calculate_content_hash(content)

                        # Update crawl_metadata.json for vectorizer compatibility
                        import json
                        metadata_path = os.path.join(BASE_PATH, 'docs', 'crawl_metadata.json')
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

                        # Vectorize the content
                        try:
                            # Refresh ESP in vector DB (will pick up the new file)
                            vectorizer.refresh_esp(esp_name)
                            print(f"[VECTORIZE] Successfully vectorized {filename}")
                        except Exception as ve:
                            print(f"[VECTORIZE ERROR] {esp_name}/{filename}: {ve}")
                            import traceback
                            traceback.print_exc()

                        # Update database
                        esp_mgr.update_document_crawl_status(
                            doc['id'],
                            status='completed',
                            content_hash=content_hash,
                            vector_ids=None
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
            docs_path = os.path.join(BASE_PATH, 'docs', esp_name)
            os.makedirs(docs_path, exist_ok=True)
            file_path = os.path.join(docs_path, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Source URL: {url}\n\n")
                f.write(content)

            # Calculate content hash
            content_hash = esp_mgr.calculate_content_hash(f"Source URL: {url}\n\n{content}")

            # Vectorize the content
            try:
                vectorizer.refresh_esp(esp_name)
            except Exception as ve:
                print(f"Vectorization warning: {ve}")

            # Update database
            esp_mgr.update_document_crawl_status(
                doc['id'],
                status='completed',
                content_hash=content_hash,
                vector_ids=None
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
        try:
            esp_mgr = get_mgr()
            data = request.json
            urls = data.get('urls', [])

            if not urls:
                return jsonify({'error': 'No URLs provided'}), 400

            # Delete from database
            deleted_count = esp_mgr.delete_documents_by_urls(esp_name, urls)

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

    print("[ESP Admin Routes] Database-backed ESP management routes registered")
