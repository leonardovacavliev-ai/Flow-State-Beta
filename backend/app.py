from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from adapters.vector.vector_manager import get_vector_adapter
from crawler import crawl_and_save
from analytics import (
    create_session, track_message, track_esp_selection,
    track_feedback, get_analytics, end_session
)
from config_manager import ConfigManager
from ai_client import AIClient
import os
import csv
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# Initialize vectorizer with adapter pattern
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_PATH, "backend/chroma_db")

# Use factory to get vector adapter based on environment
vectorizer = get_vector_adapter(persist_directory=DB_PATH)

# Admin password - from environment variable for security
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'RICHCSM')

# Initialize configuration manager
config_manager = ConfigManager(BASE_PATH)

# Initialize AI client based on config
config = config_manager.get_config()
ai_model_config = config.get('ai_model', {})
system_prompt = config.get('system_prompt', '')

ai_client = AIClient(
    provider=ai_model_config.get('provider', 'gemini'),
    model_name=ai_model_config.get('model_name', 'gemini-flash-latest'),
    system_prompt=system_prompt
)

# Serve frontend
FRONTEND_PATH = os.path.join(BASE_PATH, 'frontend')

@app.route('/')
def serve_frontend():
    """Serve the main frontend HTML"""
    return send_from_directory(FRONTEND_PATH, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images)"""
    return send_from_directory(FRONTEND_PATH, path)

@app.route('/api/session/init', methods=['POST'])
def init_session():
    """Initialize a new analytics session"""
    session_id = str(uuid.uuid4())
    ip_address = request.remote_addr
    create_session(session_id, ip_address)
    return jsonify({'session_id': session_id})

@app.route('/api/session/end', methods=['POST'])
def end_session_endpoint():
    """Mark a session as ended"""
    data = request.json
    session_id = data.get('session_id')
    if session_id:
        end_session(session_id)
    return jsonify({'success': True})

@app.route('/api/esp/select', methods=['POST'])
def select_esp():
    """Track ESP selection"""
    data = request.json
    session_id = data.get('session_id')
    esp = data.get('esp')

    if session_id and esp:
        track_esp_selection(session_id, esp)

    return jsonify({'success': True})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with RAG"""
    data = request.json
    message = data.get('message', '')
    esp = data.get('esp', 'klaviyo')
    conversation_history = data.get('history', [])
    session_id = data.get('session_id')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Track user message
    if session_id:
        track_message(session_id, 'user', message, esp)

    # Search vector database for relevant context
    # Normalize ESP name for database lookup
    esp_normalized = esp.lower().replace('/', '_') if esp else 'klaviyo'

    # Search ESP-specific docs (3 results)
    esp_results = vectorizer.search(message, esp_filter=esp_normalized, n_results=3)

    # Search global knowledge (2 results)
    global_results = vectorizer.search(message, esp_filter='global', n_results=2)

    # Build context from search results
    context = "# Relevant Documentation:\n\n"

    # Add ESP-specific results
    source_index = 1
    if esp_results['documents'] and esp_results['documents'][0]:
        context += "## ESP-Specific Knowledge:\n"
        for doc, metadata in zip(esp_results['documents'][0], esp_results['metadatas'][0]):
            context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
            context += f"ESP: {metadata.get('esp', 'Unknown')}\n"
            context += f"URL: {metadata.get('source_url', 'N/A')}\n"
            context += f"{doc}\n\n"
            source_index += 1

    # Add global knowledge results
    if global_results['documents'] and global_results['documents'][0]:
        context += "## Global Knowledge:\n"
        for doc, metadata in zip(global_results['documents'][0], global_results['metadatas'][0]):
            context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
            context += f"Type: Global Knowledge Base\n"
            context += f"URL: {metadata.get('source_url', 'N/A')}\n"
            context += f"{doc}\n\n"
            source_index += 1

    if source_index == 1:
        context += "No specific documentation found. Provide general guidance based on ESP best practices.\n\n"

    # Combine results for source display
    all_metadatas = []
    if esp_results['metadatas'] and esp_results['metadatas'][0]:
        all_metadatas.extend(esp_results['metadatas'][0])
    if global_results['metadatas'] and global_results['metadatas'][0]:
        all_metadatas.extend(global_results['metadatas'][0])

    search_results = {'metadatas': [all_metadatas] if all_metadatas else []}

    try:
        # Generate response using configured AI client
        assistant_message = ai_client.generate_response(
            message=message,
            context=context,
            conversation_history=conversation_history
        )

        # Track assistant message
        if session_id:
            track_message(session_id, 'assistant', assistant_message, esp)

        return jsonify({
            'response': assistant_message,
            'sources': [
                {
                    'filename': meta.get('filename'),
                    'esp': meta.get('esp'),
                    'url': meta.get('source_url')
                }
                for meta in (search_results['metadatas'][0] if search_results['metadatas'] else [])
            ]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Save feedback to CSV and track in analytics"""
    data = request.json
    email = data.get('email', '')
    esp = data.get('esp', '')
    rating = data.get('rating', '')
    comments = data.get('comments', '')
    session_id = data.get('session_id')

    feedback_path = os.path.join(BASE_PATH, 'feedback.csv')

    # Create file with headers if it doesn't exist
    file_exists = os.path.exists(feedback_path)

    with open(feedback_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(['Date', 'Email', 'Selected ESP', 'Rating', 'Comments'])

        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            email,
            esp,
            rating,
            comments
        ])

    # Track in analytics
    track_feedback(session_id, email, esp, int(rating), comments)

    return jsonify({'success': True})

@app.route('/api/admin/verify', methods=['POST'])
def verify_admin():
    """Verify admin password"""
    data = request.json
    password = data.get('password', '')

    return jsonify({'valid': password == ADMIN_PASSWORD})

@app.route('/api/admin/esps', methods=['GET'])
def get_esps():
    """Get list of ESPs"""
    docs_path = os.path.join(BASE_PATH, 'docs')
    esps = []

    # Mapping for display names
    display_names = {
        'other_webhook': 'Other/Webhook',
        'klaviyo': 'Klaviyo',
        'dotdigital': 'DotDigital',
        'attentive': 'Attentive'
    }

    if os.path.exists(docs_path):
        for item in os.listdir(docs_path):
            item_path = os.path.join(docs_path, item)
            # Exclude 'global' directory as it has its own dedicated section
            if os.path.isdir(item_path) and not item.startswith('.') and item != 'global':
                # Count documents
                doc_count = len([f for f in os.listdir(item_path) if f.endswith('.txt')])
                esps.append({
                    'name': item,
                    'display_name': display_names.get(item, item.title()),
                    'doc_count': doc_count
                })

    return jsonify({'esps': esps})

@app.route('/api/admin/esp/<esp_name>/links', methods=['GET'])
def get_esp_links(esp_name):
    """Get links for a specific ESP with crawl status"""
    csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')
    metadata_path = os.path.join(BASE_PATH, 'docs/crawl_metadata.json')

    # Get all links from CSV
    csv_links = []
    try:
        with open(csv_path, 'r') as f:
            lines = f.readlines()

        esp_normalized = esp_name.lower().replace('_', ' ')
        in_section = False

        for line in lines:
            line = line.strip()
            if 'integration urls' in line.lower() and esp_normalized in line.lower():
                in_section = True
                continue
            elif in_section and line.lower().endswith('urls'):
                # Stop when we hit any section header (ends with "URLs")
                break
            elif in_section and line.startswith('http'):
                csv_links.append(line)
    except Exception as e:
        print(f"Error reading CSV: {e}")

    # Get crawled links from metadata
    crawled_urls = set()
    try:
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            if esp_name.lower() in metadata:
                crawled_urls = set(doc['url'] for doc in metadata[esp_name.lower()])
    except Exception as e:
        print(f"Error reading metadata: {e}")

    # Combine and mark status
    links_with_status = []
    seen = set()
    for url in csv_links:
        if url not in seen:
            seen.add(url)
            links_with_status.append({
                'url': url,
                'status': 'crawled' if url in crawled_urls else 'pending'
            })

    return jsonify({'links': links_with_status})

@app.route('/api/admin/esp/<esp_name>/add-link', methods=['POST'])
def add_esp_link(esp_name):
    """Add a new link to an ESP"""
    data = request.json
    password = data.get('password', '')
    url = data.get('url', '')

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Read CSV
        csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')

        with open(csv_path, 'r') as f:
            content = f.read()

        # Find the ESP section and add the URL
        lines = content.split('\n')
        esp_section_found = False
        insert_index = -1

        # Normalize esp_name for matching
        esp_normalized = esp_name.lower().replace('_', ' ')

        for i, line in enumerate(lines):
            if 'integration urls' in line.lower() and esp_normalized in line.lower():
                esp_section_found = True
                # Find the next empty line or next section
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == '' or 'integration urls' in lines[j].lower():
                        insert_index = j
                        break
                if insert_index == -1:
                    insert_index = len(lines)
                break

        if esp_section_found:
            lines.insert(insert_index, url)

            # Write back to CSV
            with open(csv_path, 'w') as f:
                f.write('\n'.join(lines))

            return jsonify({'success': True})
        else:
            return jsonify({'error': 'ESP section not found in CSV'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/esp/create', methods=['POST'])
def create_esp():
    """Create a new ESP directory"""
    data = request.json
    password = data.get('password', '')
    esp_name = data.get('name', '').lower()

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not esp_name:
        return jsonify({'error': 'No ESP name provided'}), 400

    # Create directory
    esp_path = os.path.join(BASE_PATH, 'docs', esp_name)
    os.makedirs(esp_path, exist_ok=True)

    # Update CSV
    csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')

    with open(csv_path, 'a', newline='') as f:
        f.write(f'\n\n{esp_name.title()} Integration URLs\n')

    return jsonify({'success': True})

@app.route('/api/admin/esp/<esp_name>/crawl-selected', methods=['POST'])
def crawl_selected_links(esp_name):
    """Crawl selected links for a specific ESP"""
    data = request.json
    password = data.get('password', '')
    urls = data.get('urls', [])

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    try:
        from crawler import extract_main_content
        from urllib.parse import urlparse
        import json
        import time

        docs_path = os.path.join(BASE_PATH, 'docs')
        esp_folder = os.path.join(docs_path, esp_name.lower())
        os.makedirs(esp_folder, exist_ok=True)

        results = []
        for url in urls:
            print(f"Crawling {url}...")
            content = extract_main_content(url)

            if content:
                # Generate filename from URL
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                filename = '_'.join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
                filename = filename.replace('.html', '').replace('.htm', '')
                if not filename:
                    filename = 'index'
                filename = f"{filename}.txt"

                # Save to folder
                filepath = os.path.join(esp_folder, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Source URL: {url}\n\n")
                    f.write(content)

                results.append({
                    'url': url,
                    'filename': filename,
                    'filepath': filepath
                })

                print(f"  Saved to {filepath}")

            time.sleep(1)

        # Update metadata
        metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        if esp_name.lower() not in metadata:
            metadata[esp_name.lower()] = []

        # Remove old entries for these URLs and add new ones
        existing_urls = {doc['url'] for doc in metadata[esp_name.lower()]}
        metadata[esp_name.lower()] = [doc for doc in metadata[esp_name.lower()] if doc['url'] not in urls]
        metadata[esp_name.lower()].extend(results)

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Re-vectorize this ESP
        vectorizer.refresh_esp(esp_name.lower(), docs_path)

        return jsonify({'success': True, 'message': f'Crawled {len(results)} links', 'count': len(results)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/esp/<esp_name>/delete-links', methods=['POST'])
def delete_esp_links(esp_name):
    """Delete selected links for a specific ESP"""
    data = request.json
    password = data.get('password', '')
    urls = data.get('urls', [])

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    try:
        import json

        # Remove from CSV
        csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')
        with open(csv_path, 'r') as f:
            lines = f.readlines()

        new_lines = [line for line in lines if line.strip() not in urls]

        with open(csv_path, 'w') as f:
            f.writelines(new_lines)

        # Remove from metadata
        metadata_path = os.path.join(BASE_PATH, 'docs/crawl_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            if esp_name.lower() in metadata:
                # Remove entries and delete files
                docs_to_remove = [doc for doc in metadata[esp_name.lower()] if doc['url'] in urls]
                for doc in docs_to_remove:
                    # Delete file if exists
                    if os.path.exists(doc['filepath']):
                        os.remove(doc['filepath'])

                # Update metadata
                metadata[esp_name.lower()] = [doc for doc in metadata[esp_name.lower()] if doc['url'] not in urls]

                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

        # Refresh vector database for this ESP
        docs_path = os.path.join(BASE_PATH, 'docs')
        vectorizer.refresh_esp(esp_name.lower(), docs_path)

        return jsonify({'success': True, 'message': f'Deleted {len(urls)} links'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/refresh', methods=['POST'])
def refresh_all():
    """Re-crawl all links and update vector database"""
    data = request.json
    password = data.get('password', '')

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    try:
        # Re-crawl
        csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')
        docs_path = os.path.join(BASE_PATH, 'docs')
        crawl_and_save(csv_path, docs_path)

        # Re-vectorize
        vectorizer.vectorize_all_docs(docs_path)

        return jsonify({'success': True, 'message': 'All documentation refreshed'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics', methods=['GET'])
def get_analytics_data():
    """Get analytics data for dashboard"""
    time_range = request.args.get('time_range', 'all_time')

    if time_range not in ['all_time', 'last_90_days', 'last_7_days']:
        return jsonify({'error': 'Invalid time range'}), 400

    try:
        analytics_data = get_analytics(time_range)
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== GENERAL SETTINGS ENDPOINTS ==========

@app.route('/api/admin/settings/ai-model', methods=['GET'])
def get_ai_model_config():
    """Get current AI model configuration"""
    try:
        config = config_manager.get_model_config()
        available_models = AIClient.get_available_models()

        return jsonify({
            'current': config,
            'available_models': available_models,
            'status': ai_client.check_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/ai-model', methods=['POST'])
def update_ai_model_config():
    """Update AI model configuration"""
    data = request.json
    password = data.get('password', '')
    provider = data.get('provider', '')
    model_name = data.get('model_name', '')
    user_email = data.get('user_email', '')

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not user_email:
        return jsonify({'error': 'User email is required for audit trail'}), 400

    if not provider or not model_name:
        return jsonify({'error': 'Provider and model name are required'}), 400

    try:
        # Update configuration
        updated_config = config_manager.update_model_config(provider, model_name, user_email)

        # Reinitialize AI client with new config
        global ai_client
        system_prompt = config_manager.get_system_prompt()
        ai_client = AIClient(provider, model_name, system_prompt)

        return jsonify({
            'success': True,
            'config': updated_config,
            'status': ai_client.check_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/api-key', methods=['POST'])
def update_api_key():
    """Update API key for a provider"""
    data = request.json
    password = data.get('password', '')
    provider = data.get('provider', '')
    api_key = data.get('api_key', '')
    user_email = data.get('user_email', '')

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not user_email:
        return jsonify({'error': 'User email is required for audit trail'}), 400

    if not provider or not api_key:
        return jsonify({'error': 'Provider and API key are required'}), 400

    try:
        success = config_manager.update_api_key(provider, api_key, user_email)

        if success:
            # Reinitialize AI client if it's the current provider
            global ai_client
            current_config = config_manager.get_model_config()
            if current_config.get('provider') == provider:
                system_prompt = config_manager.get_system_prompt()
                ai_client = AIClient(
                    provider,
                    current_config.get('model_name'),
                    system_prompt
                )

            return jsonify({
                'success': True,
                'status': ai_client.check_status()
            })
        else:
            return jsonify({'error': 'Invalid provider'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/api-status', methods=['GET'])
def check_api_status():
    """Check current API status"""
    try:
        status = ai_client.check_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/system-prompt', methods=['GET'])
def get_system_prompt():
    """Get current system prompt"""
    try:
        prompt = config_manager.get_system_prompt()
        return jsonify({'system_prompt': prompt})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/system-prompt', methods=['POST'])
def update_system_prompt():
    """Update system prompt"""
    data = request.json
    password = data.get('password', '')
    new_prompt = data.get('system_prompt', '')
    user_email = data.get('user_email', '')

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not user_email:
        return jsonify({'error': 'User email is required for audit trail'}), 400

    if not new_prompt:
        return jsonify({'error': 'System prompt cannot be empty'}), 400

    try:
        updated_prompt = config_manager.update_system_prompt(new_prompt, user_email)

        # Reinitialize AI client with new prompt
        global ai_client
        model_config = config_manager.get_model_config()
        ai_client = AIClient(
            model_config.get('provider'),
            model_config.get('model_name'),
            updated_prompt
        )

        return jsonify({
            'success': True,
            'system_prompt': updated_prompt
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/audit-log', methods=['GET'])
def get_audit_log():
    """Get configuration change audit log"""
    try:
        limit = request.args.get('limit', type=int, default=50)
        audit_log = config_manager.get_audit_log(limit=limit)

        return jsonify({'audit_log': audit_log})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/restore', methods=['POST'])
def restore_from_backup():
    """Restore configuration from backup"""
    data = request.json
    password = data.get('password', '')
    audit_index = data.get('audit_index', -1)
    user_email = data.get('user_email', '')

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not user_email:
        return jsonify({'error': 'User email is required for audit trail'}), 400

    try:
        restored_config = config_manager.restore_from_backup(audit_index, user_email)

        # Reinitialize AI client with restored config
        global ai_client
        model_config = restored_config.get('ai_model', {})
        system_prompt = restored_config.get('system_prompt', '')
        ai_client = AIClient(
            model_config.get('provider'),
            model_config.get('model_name'),
            system_prompt
        )

        return jsonify({
            'success': True,
            'restored_config': restored_config,
            'status': ai_client.check_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== GLOBAL KNOWLEDGE ENDPOINTS ==========

@app.route('/api/admin/global-knowledge/links', methods=['GET'])
def get_global_knowledge_links():
    """Get links for global knowledge base"""
    csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')
    metadata_path = os.path.join(BASE_PATH, 'docs/crawl_metadata.json')

    csv_links = []
    try:
        with open(csv_path, 'r') as f:
            lines = f.readlines()

        in_section = False
        for line in lines:
            line = line.strip()
            if 'global knowledge urls' in line.lower():
                in_section = True
                continue
            elif in_section and 'integration urls' in line.lower():
                break
            elif in_section and (line.startswith('http') or line.startswith('local://')):
                csv_links.append(line)
    except Exception as e:
        print(f"Error reading CSV: {e}")

    # Get crawled links from metadata
    crawled_urls = set()
    try:
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            if 'global' in metadata:
                crawled_urls = set(doc['url'] for doc in metadata['global'])
    except Exception as e:
        print(f"Error reading metadata: {e}")

    # Combine and mark status
    links_with_status = []
    seen = set()
    for url in csv_links:
        if url not in seen:
            seen.add(url)
            links_with_status.append({
                'url': url,
                'status': 'crawled' if url in crawled_urls else 'pending'
            })

    return jsonify({'links': links_with_status})

@app.route('/api/admin/global-knowledge/add-link', methods=['POST'])
def add_global_knowledge_link():
    """Add a new link to global knowledge"""
    data = request.json
    password = data.get('password', '')
    url = data.get('url', '')

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')

        with open(csv_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        section_found = False
        insert_index = -1

        for i, line in enumerate(lines):
            if 'global knowledge urls' in line.lower():
                section_found = True
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == '' or 'integration urls' in lines[j].lower():
                        insert_index = j
                        break
                if insert_index == -1:
                    insert_index = len(lines)
                break

        if not section_found:
            # Add section if it doesn't exist
            lines.append('\n\nGlobal Knowledge URLs\n')
            insert_index = len(lines)

        lines.insert(insert_index, url)

        with open(csv_path, 'w') as f:
            f.write('\n'.join(lines))

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/global-knowledge/crawl-selected', methods=['POST'])
def crawl_global_knowledge_links():
    """Crawl selected global knowledge links"""
    data = request.json
    password = data.get('password', '')
    urls = data.get('urls', [])

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    try:
        from crawler import extract_main_content
        from urllib.parse import urlparse
        import json
        import time

        docs_path = os.path.join(BASE_PATH, 'docs')
        global_folder = os.path.join(docs_path, 'global')
        os.makedirs(global_folder, exist_ok=True)

        results = []
        for url in urls:
            print(f"Crawling {url}...")
            content = extract_main_content(url)

            if content:
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                filename = '_'.join(path_parts[-2:]) if len(path_parts) > 1 else path_parts[-1]
                filename = filename.replace('.html', '').replace('.htm', '')
                if not filename:
                    filename = 'index'
                filename = f"{filename}.txt"

                filepath = os.path.join(global_folder, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Source URL: {url}\n\n")
                    f.write(content)

                results.append({
                    'url': url,
                    'filename': filename,
                    'filepath': filepath
                })

                print(f"  Saved to {filepath}")

            time.sleep(1)

        # Update metadata
        metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        if 'global' not in metadata:
            metadata['global'] = []

        metadata['global'] = [doc for doc in metadata['global'] if doc['url'] not in urls]
        metadata['global'].extend(results)

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Re-vectorize global knowledge
        vectorizer.refresh_esp('global', docs_path)

        return jsonify({'success': True, 'message': f'Crawled {len(results)} links', 'count': len(results)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/global-knowledge/delete-links', methods=['POST'])
def delete_global_knowledge_links():
    """Delete selected global knowledge links"""
    data = request.json
    password = data.get('password', '')
    urls = data.get('urls', [])

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Invalid password'}), 403

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    try:
        import json

        # Remove from CSV
        csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')
        with open(csv_path, 'r') as f:
            lines = f.readlines()

        new_lines = [line for line in lines if line.strip() not in urls]

        with open(csv_path, 'w') as f:
            f.writelines(new_lines)

        # Remove from metadata
        metadata_path = os.path.join(BASE_PATH, 'docs/crawl_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            if 'global' in metadata:
                docs_to_remove = [doc for doc in metadata['global'] if doc['url'] in urls]
                for doc in docs_to_remove:
                    if os.path.exists(doc['filepath']):
                        os.remove(doc['filepath'])

                metadata['global'] = [doc for doc in metadata['global'] if doc['url'] not in urls]

                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

        # Refresh vector database for global knowledge
        docs_path = os.path.join(BASE_PATH, 'docs')
        vectorizer.refresh_esp('global', docs_path)

        return jsonify({'success': True, 'message': f'Deleted {len(urls)} links'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Support cloud deployment platforms (Heroku, Railway, etc.)
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', debug=debug, port=port)
