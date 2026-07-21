"""
Admin ESP Routes - ASYNC VERSION with background job system

These routes provide async crawling with job queue and progress tracking.
Replaces synchronous crawl-selected endpoint with async version.

Usage:
    Set USE_ASYNC_CRAWL=true in environment to enable this version.
"""

from flask import jsonify, request
from esp_manager import get_esp_manager
import os
import uuid


def register_esp_admin_routes_async(app, BASE_PATH, vectorizer):
    """Register async ESP admin routes with the Flask app."""

    # Import database adapter
    from adapters.database.db_manager import get_database_adapter

    # Lazy initialization
    def get_mgr():
        """Get ESP manager instance (lazy initialization)."""
        return get_esp_manager()

    def get_db():
        """Get database adapter instance."""
        return get_database_adapter()

    # ==================== EXISTING ROUTES (unchanged) ====================
    # These routes work exactly the same way

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
            links = [{
                'url': doc['url'],
                'filename': doc['filename'],
                'status': 'crawled' if doc['crawl_status'] == 'completed' else 'pending',
                'crawl_status': doc['crawl_status'],
                'last_crawled_at': doc['last_crawled_at'],
                'error_message': doc.get('error_message'),
                'crawled': doc['crawl_status'] == 'completed',
                'is_crawling': doc.get('is_crawling', False)  # Show if currently being crawled
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

            # Create filesystem folder for backward compatibility
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

    # ==================== NEW ASYNC ROUTES ====================

    @app.route('/api/admin/esp/<esp_name>/crawl-selected', methods=['POST'])
    def crawl_esp_selected_async(esp_name):
        """
        Queue URLs for async crawling (ASYNC VERSION).

        Returns immediately with job IDs. Frontend polls /api/admin/crawl-status
        to track progress.

        Request body:
            {
                "urls": ["https://...", "https://..."]
            }

        Response:
            {
                "success": true,
                "job_ids": ["uuid1", "uuid2"],
                "total": 2,
                "message": "Queued 2 URLs for crawling"
            }
        """
        try:
            esp_mgr = get_mgr()
            db = get_db()
            data = request.json
            urls = data.get('urls', [])

            if not urls:
                return jsonify({'error': 'No URLs provided'}), 400

            # Get ESP
            esp = esp_mgr.get_esp_by_name(esp_name)
            if not esp:
                return jsonify({'error': f"ESP '{esp_name}' not found"}), 404

            # Ensure ESP folder exists
            esp_docs_path = os.path.join(BASE_PATH, 'docs', esp_name)
            os.makedirs(esp_docs_path, exist_ok=True)

            job_ids = []
            skipped = []

            for url in urls:
                # Get or create document
                doc = esp_mgr.get_document_by_url(esp['id'], url)
                if not doc:
                    doc = esp_mgr.add_document(esp_name, url)

                document_id = doc['id']

                # Check if job already exists for this document
                check_query = """
                    SELECT id FROM crawl_jobs
                    WHERE document_id = %s AND status IN ('pending', 'processing')
                """
                existing = db.execute_query(check_query, (document_id,), fetch=True)

                if existing:
                    # Job already queued or processing
                    job_ids.append(existing[0][0])
                    skipped.append(url)
                else:
                    # Create new job
                    job_id = str(uuid.uuid4())
                    create_query = """
                        INSERT INTO crawl_jobs (id, esp_id, document_id, priority)
                        VALUES (%s, %s, %s, 10)
                    """
                    db.execute_query(create_query, (job_id, esp['id'], document_id))

                    # Mark document as crawling
                    mark_query = """
                        UPDATE esp_documents
                        SET is_crawling = TRUE,
                            crawl_job_id = %s
                        WHERE id = %s
                    """
                    db.execute_query(mark_query, (job_id, document_id))

                    job_ids.append(job_id)

            message = f'Queued {len(job_ids)} URLs for crawling'
            if skipped:
                message += f' ({len(skipped)} already queued/processing)'

            return jsonify({
                'success': True,
                'job_ids': job_ids,
                'total': len(job_ids),
                'message': message,
                'skipped_count': len(skipped)
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/crawl-status', methods=['GET'])
    def get_crawl_status():
        """
        Get status of crawl jobs (polling endpoint).

        Query params:
            job_ids: Comma-separated list of job UUIDs

        Response:
            {
                "jobs": [
                    {
                        "id": "uuid",
                        "status": "completed",
                        "url": "https://...",
                        "filename": "file.txt",
                        "error_message": null,
                        "created_at": "2024-01-01T00:00:00",
                        "completed_at": "2024-01-01T00:00:30"
                    }
                ],
                "summary": {
                    "total": 5,
                    "completed": 3,
                    "failed": 1,
                    "processing": 1,
                    "pending": 0,
                    "is_complete": false
                }
            }
        """
        try:
            db = get_db()
            job_ids_str = request.args.get('job_ids', '')
            job_ids = [j.strip() for j in job_ids_str.split(',') if j.strip()]

            if not job_ids:
                return jsonify({'error': 'No job_ids provided'}), 400

            # Validate UUIDs (PostgreSQL UUID format check)
            import uuid
            valid_job_ids = []
            for job_id in job_ids:
                try:
                    uuid.UUID(job_id)  # Validates UUID format
                    valid_job_ids.append(job_id)
                except ValueError:
                    pass  # Skip invalid UUIDs silently

            if not valid_job_ids:
                return jsonify({
                    'jobs': [],
                    'summary': {
                        'total': 0,
                        'queued': 0,
                        'processing': 0,
                        'completed': 0,
                        'failed': 0
                    }
                }), 200

            job_ids = valid_job_ids

            # Build query with proper parameterization
            placeholders = ','.join(['%s'] * len(job_ids))
            query = f"""
                SELECT
                    j.id,
                    j.status,
                    j.attempts,
                    j.error_message,
                    j.created_at,
                    j.started_at,
                    j.completed_at,
                    d.url,
                    d.filename,
                    d.crawl_status as doc_status
                FROM crawl_jobs j
                JOIN esp_documents d ON j.document_id = d.id
                WHERE j.id IN ({placeholders})
                ORDER BY j.created_at ASC
            """

            result = db.execute_query(query, tuple(job_ids), fetch=True)

            # Convert to list of dicts
            jobs = []
            for row in result:
                jobs.append({
                    'id': row[0],
                    'status': row[1],
                    'attempts': row[2],
                    'error_message': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'started_at': row[5].isoformat() if row[5] else None,
                    'completed_at': row[6].isoformat() if row[6] else None,
                    'url': row[7],
                    'filename': row[8],
                    'doc_status': row[9]
                })

            # Calculate summary
            total = len(jobs)
            completed = sum(1 for j in jobs if j['status'] == 'completed')
            failed = sum(1 for j in jobs if j['status'] == 'failed')
            processing = sum(1 for j in jobs if j['status'] == 'processing')
            pending = sum(1 for j in jobs if j['status'] == 'pending')
            cancelled = sum(1 for j in jobs if j['status'] == 'cancelled')

            return jsonify({
                'jobs': jobs,
                'summary': {
                    'total': total,
                    'completed': completed,
                    'failed': failed,
                    'processing': processing,
                    'pending': pending,
                    'cancelled': cancelled,
                    'is_complete': (completed + failed + cancelled) == total
                }
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/crawl-cancel', methods=['POST'])
    def cancel_crawl_jobs():
        """
        Cancel pending/processing jobs.

        Request body:
            {
                "job_ids": ["uuid1", "uuid2"]
            }

        Response:
            {
                "success": true,
                "cancelled": 2
            }
        """
        try:
            db = get_db()
            data = request.json
            job_ids = data.get('job_ids', [])

            if not job_ids:
                return jsonify({'error': 'No job_ids provided'}), 400

            # Build query with proper parameterization
            placeholders = ','.join(['%s'] * len(job_ids))
            query = f"""
                UPDATE crawl_jobs
                SET status = 'cancelled',
                    completed_at = NOW()
                WHERE id IN ({placeholders})
                AND status IN ('pending', 'processing')
            """

            db.execute_query(query, tuple(job_ids))

            # Note: We can't easily get rowcount from execute_query
            # Just return success
            return jsonify({
                'success': True,
                'message': 'Jobs cancelled'
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # Paste content route (unchanged from sync version)
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

            # Update crawl_metadata.json
            import json
            metadata_path = os.path.join(base_docs_path, 'crawl_metadata.json')
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except FileNotFoundError:
                metadata = {}

            if esp_name not in metadata:
                metadata[esp_name] = []

            # Remove old entry if exists
            metadata[esp_name] = [d for d in metadata[esp_name] if d.get('url') != url]
            metadata[esp_name].append({
                'url': url,
                'filename': filename,
                'filepath': file_path
            })

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Vectorize
            try:
                vectorizer.refresh_esp(esp_name, base_docs_path)
            except Exception as ve:
                print(f"[VECTORIZE ERROR] {esp_name}/{filename}: {ve}")

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
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    print("[ESP Admin Routes] ASYNC version registered (job queue enabled)")
