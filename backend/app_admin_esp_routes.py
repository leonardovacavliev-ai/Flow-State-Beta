"""
Admin ESP Routes - Database-backed version

These routes replace the filesystem-based ESP management in app.py
Import these routes into app.py to enable database-backed ESP management.
"""

from flask import jsonify, request
from esp_manager import get_esp_manager
from crawler import crawl_and_save
from adapters.vector.vector_manager import get_vector_adapter
import os

# Get singleton instances
esp_mgr = get_esp_manager()


def register_esp_admin_routes(app, BASE_PATH, vectorizer):
    """Register all ESP admin routes with the Flask app."""

    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        """Get list of ESPs from database."""
        try:
            esps = esp_mgr.list_esps()
            return jsonify({'esps': esps})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/esp/<esp_name>/links', methods=['GET'])
    def get_esp_links(esp_name):
        """Get links for a specific ESP from database."""
        try:
            docs = esp_mgr.list_documents(esp_name)

            # Convert to frontend format
            links = [{
                'url': doc['url'],
                'filename': doc['filename'],
                'crawl_status': doc['crawl_status'],
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
                    doc = esp_mgr.get_document_by_url(esp['id'], url)

                    if not doc:
                        # Add if doesn't exist
                        doc = esp_mgr.add_document(esp_name, url)

                    # Crawl the URL
                    filename = crawl_and_save(url, esp_name, BASE_PATH)

                    if filename:
                        # Read content to calculate hash
                        file_path = os.path.join(docs_path, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        content_hash = esp_mgr.calculate_content_hash(content)

                        # Vectorize the content
                        vector_ids = []
                        try:
                            # Delete old vectors if they exist
                            if doc.get('vector_ids'):
                                # TODO: Implement vector deletion in vector adapter
                                pass

                            # Refresh ESP in vector DB (will pick up the new file)
                            vectorizer.refresh_esp(esp_name)

                            # Note: We don't have direct access to vector IDs from refresh_esp
                            # This is a limitation of the current vectorizer design
                            # For now, we'll mark as completed without storing vector IDs

                        except Exception as ve:
                            print(f"Vectorization warning: {ve}")

                        # Update database
                        esp_mgr.update_document_crawl_status(
                            doc['id'],
                            status='completed',
                            content_hash=content_hash,
                            vector_ids=None  # Will add in future when vectorizer returns IDs
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

    @app.route('/api/admin/esp/<esp_name>/delete-links', methods=['POST'])
    def delete_esp_links(esp_name):
        """Delete selected links from an ESP."""
        try:
            data = request.json
            urls = data.get('urls', [])

            if not urls:
                return jsonify({'error': 'No URLs provided'}), 400

            # Delete from database
            deleted_count = esp_mgr.delete_documents_by_urls(esp_name, urls)

            # Note: Files in docs/ folder are not deleted for safety
            # Vectorizer will handle them on next refresh

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
            stats = esp_mgr.get_esp_stats(esp_name)
            if not stats:
                return jsonify({'error': f"ESP '{esp_name}' not found"}), 404

            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    print("[ESP Admin Routes] Database-backed ESP management routes registered")
