from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from adapters.vector.vector_manager import get_vector_adapter
from adapters.session.session_manager import get_session_adapter
from crawler import vectorize_single_document
from analytics import (
    create_session, track_message, track_esp_selection,
    track_feedback, get_analytics, end_session, attach_user_to_session
)
from config_manager import ConfigManager
from ai_client import AIClient
from mechanics_cache import clear_mechanics_cache
# Retrieval lives in rag_context so the eval can run the same code without
# importing this module. filter_by_relevance and MECHANICS_QUERY are re-exported
# here for callers that still import them from app.
from rag_context import (  # noqa: F401
    build_rag_context, chat_search_products, filter_by_relevance, MECHANICS_QUERY)
from dotenv import load_dotenv
import os
import csv
from datetime import datetime
import uuid

# Load environment variables from .env file (if it exists)
# This must happen before any code that reads os.environ
load_dotenv()

app = Flask(__name__)
CORS(app)

# Behind Railway/other proxies the client IP arrives via X-Forwarded-For;
# without this every session records the load balancer's IP.
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Initialize vectorizer with adapter pattern
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_PATH, "backend/chroma_db")

# Use factory to get vector adapter based on environment
vectorizer = get_vector_adapter(persist_directory=DB_PATH)

# Use factory to get session adapter based on environment
session_adapter = get_session_adapter()

# Admin password - from environment variable for security
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'RICHCSM')
if 'ADMIN_PASSWORD' not in os.environ:
    print("[WARNING] ADMIN_PASSWORD not set - using the default password. "
          "Set ADMIN_PASSWORD in the environment for production.")

def is_admin_request():
    """True when the caller is a verified @yotpo.com Google account.

    Was a shared-password check. The password now only works as the
    break-glass path (ADMIN_PASSWORD_FALLBACK=true), handled inside
    admin_request_ok().
    """
    from auth import admin_request_ok
    return admin_request_ok()

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

# Register Google account authentication routes.
# Nothing is gated behind these yet -- admin still uses the password path
# below, and chat is unchanged. Signing in is currently a no-op for the user.
#
# Deliberately non-fatal: auth depends on two packages added late (google-auth,
# PyJWT). If either fails to install on a deploy, the app should lose sign-in,
# not fall over and take the chat down with it. The frontend hides the sign-in
# control when /api/auth/config is unavailable.
AUTH_AVAILABLE = False
try:
    from auth import register_auth_routes
    register_auth_routes(app)
    AUTH_AVAILABLE = True
except Exception as e:
    print(f"[ERROR] Auth routes unavailable: {e}")
    import traceback
    traceback.print_exc()

# Saved conversations. Requires auth, so it is only registered when auth
# loaded -- and is non-fatal for the same reason: losing saved history should
# not take chat down.
CONVERSATIONS_AVAILABLE = False
if AUTH_AVAILABLE:
    try:
        from conversations import register_conversation_routes
        register_conversation_routes(app)
        CONVERSATIONS_AVAILABLE = True
    except Exception as e:
        print(f"[ERROR] Conversation routes unavailable: {e}")
        import traceback
        traceback.print_exc()

# Register database-backed ESP admin routes (Phase 4).
# The filesystem-based routes this replaced have been deleted, so setting
# this to False now leaves the ESP admin endpoints unregistered.
USE_DATABASE_ESP_ROUTES = True

# Feature flag: Async crawl with background jobs (Phase 5)
USE_ASYNC_CRAWL = os.environ.get('USE_ASYNC_CRAWL', 'false').lower() == 'true'

if USE_DATABASE_ESP_ROUTES:
    if USE_ASYNC_CRAWL:
        from app_admin_esp_routes_async import register_esp_admin_routes_async
        register_esp_admin_routes_async(app, BASE_PATH, vectorizer)
        print("[DEBUG] ESP database routes (ASYNC) registered successfully")
    else:
        from app_admin_esp_routes import register_esp_admin_routes
        register_esp_admin_routes(app, BASE_PATH, vectorizer)
        print("[DEBUG] ESP database routes (SYNC) registered successfully")

    # Product-line labels on documents; same for both route modules
    from product_labels import register_product_label_routes
    register_product_label_routes(app, vectorizer)

# Health check endpoint for Railway
@app.route('/api/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# Debug endpoint to test ESP routes
@app.route('/api/debug/esps', methods=['GET'])
def debug_esps():
    """Debug endpoint to verify ESP database connection"""
    try:
        from esp_manager import get_esp_manager
        esp_mgr = get_esp_manager()
        esps = esp_mgr.list_esps()
        return jsonify({
            'status': 'success',
            'esp_count': len(esps),
            'esps': [esp['name'] for esp in esps],
            'database_provider': os.environ.get('DATABASE_PROVIDER', 'not set'),
            'use_database_routes': USE_DATABASE_ESP_ROUTES
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'database_provider': os.environ.get('DATABASE_PROVIDER', 'not set'),
            'use_database_routes': USE_DATABASE_ESP_ROUTES
        }), 500

# Vector DB provider determines how to interpret the 'distances' field:
# - ChromaDB returns L2 distances (lower = more similar)
# - Pinecone returns cosine similarity scores (higher = more similar)
VECTOR_PROVIDER = os.environ.get('VECTOR_DB_PROVIDER', 'chromadb').lower()

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

def _signed_in_user_id():
    """The signed-in account for this request, or None. Never raises.

    Auth is registered defensively (see AUTH_AVAILABLE) and analytics must not
    be the thing that takes chat down, so a broken auth import degrades this
    visitor to a guest rather than failing the request.

    Only meaningful on requests the frontend sends a token with -- /api/chat
    does, /api/session/init does not.
    """
    if not AUTH_AVAILABLE:
        return None
    try:
        from auth import current_user_id
        return current_user_id()
    except Exception:
        return None

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
    # sendBeacon payloads may arrive as text/plain; parse leniently so the
    # session end isn't rejected with a 415.
    data = request.get_json(silent=True, force=True) or {}
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
    session_id = data.get('session_id')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400

    # A signed-in user with a conversation_id gets their history from the
    # database, which is authoritative. get_history_for_ai scopes by user_id,
    # so a forged id cannot pull someone else's chat into this prompt.
    #
    # Guests have no conversation, so they keep the original path: the browser
    # sends its own history and the server trusts it for the length of the tab.
    conversation_id = data.get('conversation_id')
    conversation_user_id = None
    if conversation_id and CONVERSATIONS_AVAILABLE:
        from auth import current_user_id
        conversation_user_id = current_user_id()
        if not conversation_user_id:
            conversation_id = None

    if conversation_id and conversation_user_id:
        from conversations import get_history_for_ai
        conversation_history = get_history_for_ai(conversation_id, conversation_user_id)
    else:
        conversation_history = None

    # Prefer the client's per-ESP history (it isolates conversations per ESP
    # and honors "Clear History"); fall back to the server-side session store.
    client_history = data.get('history')
    if conversation_history is not None:
        pass  # already loaded from the database
    elif isinstance(client_history, list):
        conversation_history = [
            {'role': m['role'], 'content': m['content']}
            for m in client_history[-20:]
            if isinstance(m, dict)
            and m.get('role') in ('user', 'assistant')
            and isinstance(m.get('content'), str)
        ]
    else:
        conversation_history = session_adapter.get_conversation_history(session_id)

    # The Yotpo product picked in chat. A saved conversation keeps the product
    # it was started with, whatever the page sends; otherwise the request's
    # value, and Loyalty -- today's behaviour -- for anything unrecognised.
    from product_labels import chat_product, esp_display_name, has_reviews_coverage
    product = None
    if conversation_id and conversation_user_id:
        from conversations import get_conversation_product
        product = get_conversation_product(conversation_id, conversation_user_id)
    product = product or chat_product(data.get('product'))

    # Sign-in almost always happens after the session row was created, so the
    # account is stamped here too -- without this, analytics would count every
    # signed-in visitor as a guest IP.
    signed_in_user_id = conversation_user_id or _signed_in_user_id()
    if signed_in_user_id:
        attach_user_to_session(session_id, signed_in_user_id)

    # Track user message in analytics
    track_message(session_id, 'user', message, esp, product)

    # Add user message to session history
    session_adapter.add_message(session_id, 'user', message)

    # The saved conversation is written only after the AI answers -- see the
    # success path below. Saving the user's message here instead would leave a
    # dangling user turn in the transcript whenever generation fails, so a
    # reopened conversation would show questions with no answers and feed the
    # model two user turns in a row. The old client-side history recorded on
    # success only; this matches it.

    # Retrieve (Queries A, B and C) and assemble the context. See rag_context
    # for the reasoning behind each query and the order sources appear in.
    # A Reviews question on an ESP with no Reviews documentation gets a note
    # saying so, instead of an answer built from the Loyalty docs that are
    # all retrieval can find there. Loyalty requests search only Loyalty and
    # shared documents (rag_context.CHAT_SEARCH_PRODUCTS).
    esp_key = esp.lower().replace('/', '_') if esp else 'klaviyo'
    uncovered = product == 'reviews' and not has_reviews_coverage(esp_key)
    rag = build_rag_context(vectorizer, message, esp, conversation_history,
                            product=product,
                            reviews_coverage=False if uncovered else None,
                            esp_display=esp_display_name(esp_key) if uncovered else None,
                            search_products=chat_search_products(product))
    context = rag.context
    search_results = {'metadatas': [rag.metadatas] if rag.metadatas else []}

    try:
        # Generate response using configured AI client
        assistant_message = ai_client.generate_response(
            message=message,
            context=context,
            conversation_history=conversation_history,
            product=product
        )

        # Add assistant message to session history
        session_adapter.add_message(session_id, 'assistant', assistant_message)

        # Track assistant message in analytics
        track_message(session_id, 'assistant', assistant_message, esp, product)

        # Persist the exchange as a pair, now that it actually is one.
        # Failing to save history must not cost the user their answer, so this
        # never raises out of the request.
        if conversation_id and conversation_user_id:
            from conversations import append_message
            try:
                if append_message(conversation_id, conversation_user_id, 'user', message) is not None:
                    append_message(conversation_id, conversation_user_id, 'assistant', assistant_message)
            except Exception as e:
                print(f"[CONVERSATION] Could not save exchange: {e}")

        return jsonify({
            'response': assistant_message,
            # The product this answer was generated for. A saved conversation
            # keeps its own, so it can differ from what the page sent.
            'product': product,
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
    comments = data.get('comments', '')
    session_id = data.get('session_id')

    # Validate rating BEFORE writing anywhere, so a bad rating can't leave
    # the CSV and analytics out of sync.
    try:
        rating = int(data.get('rating'))
    except (TypeError, ValueError):
        return jsonify({'error': 'A numeric rating is required'}), 400

    if not 1 <= rating <= 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400

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
    track_feedback(session_id, email, esp, rating, comments)

    return jsonify({'success': True})

@app.route('/api/admin/verify', methods=['POST'])
def verify_admin():
    """Report whether the caller may use the admin panel.

    Used to gate the UI only. Every admin route enforces access itself, so a
    forged 'valid': true here buys nothing.
    """
    return jsonify({'valid': is_admin_request()})

@app.route('/api/admin/debug/pinecone-sample', methods=['GET'])
def debug_pinecone_sample():
    """Debug endpoint to see what's actually in Pinecone (admin only)"""
    password = request.args.get('password', '') or request.headers.get('X-Admin-Password', '')
    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    if VECTOR_PROVIDER != 'pinecone':
        return jsonify({'error': f'Not using Pinecone (provider: {VECTOR_PROVIDER})'}), 400

    try:
        # Reuse the adapter's lazily-loaded embedding model instead of
        # instantiating a fresh 250MB SentenceTransformer per request.
        query_vector = vectorizer.embedding_model.encode("sample query").tolist()

        results = vectorizer.index.query(
            vector=query_vector,
            top_k=10,
            include_metadata=True
        )

        samples = []
        for match in results.get('matches', []):
            metadata = match.get('metadata', {})
            samples.append({
                'id': match['id'],
                'esp': metadata.get('esp', 'N/A'),
                'filename': metadata.get('filename', 'N/A'),
                'source_url': metadata.get('source_url', 'N/A'),
                'score': match.get('score', 0)
            })

        return jsonify({
            'provider': VECTOR_PROVIDER,
            'total_vectors': vectorizer.get_collection_count(),
            'sample_count': len(samples),
            'sample_vectors': samples
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/refresh', methods=['POST'])
def refresh_all():
    """Re-crawl all links and update vector database"""
    data = request.json

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    if USE_ASYNC_CRAWL and not app.config.get('CRAWL_WORKER_RUNNING'):
        return jsonify({'error': 'The background crawl worker is not running, so nothing '
                                 'would process this refresh. Check the server logs.'}), 503

    if USE_ASYNC_CRAWL:
        # Through the paced queue like every other crawl. The synchronous
        # version below fires the whole CSV at 1 req/s with no rate-limit
        # handling (the burst that caused the develop.yotpo.com 429s), then
        # rebuilds vectors from local files, which on Railway's ephemeral
        # disk are only whatever was crawled since the last deploy.
        try:
            from esp_manager import get_esp_manager
            from adapters.database.db_manager import get_database_adapter
            from workers.crawl_queue import enqueue_crawl_job, queued_response
            db = get_database_adapter()
            esp_mgr = get_esp_manager()
            _ensure_global_esp(esp_mgr)
            job_ids, skipped, not_queued = [], [], []
            no_label = {'error': 'No product label: pick Loyalty, Reviews or Shared beside it, '
                                 'then crawl it'}
            for esp in esp_mgr.list_esps():
                labels = esp_mgr.get_product_labels(esp['name'])
                for doc in esp_mgr.list_documents(esp['name']):
                    if (labels.get(doc['url']) or {}).get('product') is None:
                        not_queued.append({'url': doc['url'], **no_label})   # would only fail in the worker
                        continue
                    job_id, created = enqueue_crawl_job(db, esp['id'], doc['id'], doc['url'])
                    job_ids.append(job_id)
                    if not created:
                        skipped.append(doc['url'])
            # ESP links live in the database; global-knowledge links are
            # still listed from the CSV, and may not have a row yet. A
            # CSV-only link has no row, so no product label: left out too.
            known = {doc['url'] for doc in esp_mgr.list_documents('global')}
            not_queued += [{'url': url, **no_label} for url in _global_csv_links() if url not in known]
            body = queued_response(job_ids, skipped, not_queued)
            # Chat caches are cleared by the worker as each doc is re-indexed
            return jsonify(body)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Could not queue the refresh: {e}'}), 500

    # The synchronous version is disabled. It re-crawled from the CSV and
    # the baked-in docs/ tree and re-indexed with vectorize_all_docs, which
    # cannot see documents added since (Emarsys, most of other_webhook),
    # writes vectors without product labels (the adapters now refuse them),
    # and duplicates files stored under old names. Rebuild Vectors restores
    # the index from the database, labels included (POST
    # /api/admin/rebuild-vectors; there is no button for it).
    return jsonify({'error': 'Refresh All is off on this server: it needs the background crawl '
                             'queue. To re-crawl links, select them and use Crawl Selected.'}), 409

@app.route('/api/admin/analytics', methods=['GET'])
def get_analytics_data():
    """Get analytics data for dashboard (admin only)"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    time_range = request.args.get('time_range', 'all_time')

    if time_range not in ['all_time', 'last_90_days', 'last_30_days', 'last_7_days', 'last_24_hours']:
        return jsonify({'error': 'Invalid time range'}), 400

    try:
        analytics_data = get_analytics(time_range)
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== GENERAL SETTINGS ENDPOINTS ==========

@app.route('/api/admin/settings/ai-model', methods=['GET'])
def get_ai_model_config():
    """Get current AI model configuration (admin only)"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403
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
    provider = data.get('provider', '')
    model_name = data.get('model_name', '')
    user_email = data.get('user_email', '')

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

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
    provider = data.get('provider', '')
    api_key = data.get('api_key', '')
    user_email = data.get('user_email', '')

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

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
    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403
    try:
        status = ai_client.check_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/system-prompt', methods=['GET'])
def get_system_prompt():
    """Get current system prompt (admin only)"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403
    try:
        prompt = config_manager.get_system_prompt()
        return jsonify({'system_prompt': prompt})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/system-prompt', methods=['POST'])
def update_system_prompt():
    """Update system prompt"""
    data = request.json
    new_prompt = data.get('system_prompt', '')
    user_email = data.get('user_email', '')

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    if not user_email:
        return jsonify({'error': 'User email is required for audit trail'}), 400

    if not new_prompt:
        return jsonify({'error': 'System prompt cannot be empty'}), 400

    # [[product]] and [[if ...]] placeholders are filled per request
    # (prompt_template.py); a typo would otherwise reach the model verbatim.
    from prompt_template import validate as validate_prompt
    prompt_errors = validate_prompt(new_prompt)
    if prompt_errors:
        return jsonify({'error': 'The prompt has placeholder problems: ' + ' '.join(prompt_errors),
                        'placeholder_errors': prompt_errors}), 400

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

        from prompt_template import product_warning
        body = {'success': True, 'system_prompt': updated_prompt}
        warning = product_warning(updated_prompt)
        if warning:
            body['warning'] = warning
        return jsonify(body)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings/audit-log', methods=['GET'])
def get_audit_log():
    """Get configuration change audit log (admin only)"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403
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
    audit_index = data.get('audit_index', -1)
    user_email = data.get('user_email', '')

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

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

        from prompt_template import product_warning
        body = {'success': True, 'restored_config': restored_config,
                'status': ai_client.check_status()}
        warning = product_warning(system_prompt)
        if warning:
            body['warning'] = warning
        return jsonify(body)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== GLOBAL KNOWLEDGE ENDPOINTS ==========

def _global_csv_links():
    """Global-knowledge URLs listed in esp_support_links.csv, in order."""
    csv_path = os.path.join(BASE_PATH, 'esp_support_links.csv')
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
    return csv_links


@app.route('/api/admin/global-knowledge/links', methods=['GET'])
def get_global_knowledge_links():
    """Get links for global knowledge base (admin only)"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    csv_links = _global_csv_links()
    # Plus links that have a database row but are missing from the CSV: the
    # CSV sits on the container's disk, so a link added since the last
    # deploy is gone from it while its row (and label) survives. Without
    # this it would be invisible here, yet refused as a duplicate on re-add.
    try:
        from esp_manager import get_esp_manager
        listed = set(csv_links)
        csv_links += [doc['url'] for doc in reversed(get_esp_manager().list_documents('global'))
                      if doc['url'] not in listed]
    except Exception as e:
        print(f"[GLOBAL] Could not read global documents from the database: {e}")

    # URLs whose content is backed up in the database (used for the
    # needs_backfill flag below). If the DB has no 'global' docs yet,
    # every crawled link correctly shows as needing backfill.
    backed_up_urls = set()
    try:
        from esp_manager import get_esp_manager
        backed_up_urls = {
            doc['url'] for doc in get_esp_manager().list_documents('global')
            if doc.get('has_content')
        }
    except Exception as e:
        print(f"[GLOBAL PERSIST] Could not check backed-up docs: {e}")

    # Crawl state from the queue (failed / queued / retrying / ...). The
    # vector check below only knows "indexed or not", so a failed crawl
    # used to show up as 'pending', as if it had never been tried.
    queue_states = {}
    if USE_ASYNC_CRAWL:
        try:
            from esp_manager import get_esp_manager
            from adapters.database.db_manager import get_database_adapter
            from workers.crawl_queue import list_document_states
            global_esp = get_esp_manager().get_esp_by_name('global')
            if global_esp:
                queue_states = {
                    doc['url']: doc
                    for doc in list_document_states(get_database_adapter(), global_esp['id'])
                }
        except Exception as e:
            print(f"[GLOBAL] Could not read crawl states: {e}")

    # Check actual vectorization status from vector DB
    links_with_status = []
    seen = set()
    for url in csv_links:
        if url not in seen:
            seen.add(url)

            # Check if URL actually exists in vector database
            try:
                url_vectorized = vectorizer.url_exists(url, 'global')
                status = 'crawled' if url_vectorized else 'pending'
            except Exception as e:
                print(f"Error checking URL {url}: {e}")
                status = 'checking'  # Unknown state

            detail = None
            queued = queue_states.get(url)
            if queued and queued['state'] not in ('pending', 'crawled'):
                status, detail = queued['state'], queued['detail']
            elif queued and queued['state'] == 'crawled' and status == 'crawled':
                detail = queued['detail']  # e.g. "re-indexed from the saved copy"

            links_with_status.append({
                'url': url,
                'status': status,
                'detail': detail,
                'needs_backfill': status == 'crawled' and url not in backed_up_urls,
                # local:// entries are pasted content — they can't be fetched,
                # only backed up from the saved copy or re-pasted
                'can_crawl': not url.startswith('local://')
            })

    # Product labels. Only URLs with a database row can be labelled.
    try:
        from esp_manager import get_esp_manager
        from product_labels import merge_labels
        merge_labels(links_with_status, get_esp_manager().get_product_labels('global'))
    except Exception as e:
        print(f"[GLOBAL] Could not read product labels: {e}")

    return jsonify({'links': links_with_status})

def _ensure_global_esp(esp_mgr):
    """
    The hidden 'global' ESP row that holds global-knowledge docs, created or
    reactivated as needed.
    """
    # Look up including archived rows: esps.name is UNIQUE, so an
    # archived 'global' row (hidden from the UI the old way, by
    # archiving) made this lookup miss and the create below fail with a
    # duplicate-key error on every crawl — the docs were never backed up.
    esp = esp_mgr.get_esp_by_name('global', include_archived=True)
    if not esp:
        esp = esp_mgr.create_esp('global', 'Global Knowledge',
                                 'Internal: global knowledge base (not a selectable ESP)')
    elif esp.get('status') != 'active':
        # Reactivate: it's filtered out of the selectable ESP list by
        # name, and add_document/list_documents only see active ESPs
        esp_mgr.restore_esp(esp['id'])
    return esp


def _persist_global_doc(url, filename, filepath, file_content):
    """
    Mirror a global-knowledge doc into the database (under a hidden 'global'
    ESP row) so its content survives container redeploys and can be rebuilt
    via /api/admin/rebuild-vectors. Non-fatal for the file-based flow, but the
    outcome must be surfaced: a silent failure here leaves the doc permanently
    flagged NO BACKUP with no way for the admin to know why.

    Returns None on success, or an error message.
    """
    try:
        from esp_manager import get_esp_manager
        esp_mgr = get_esp_manager()
        esp = _ensure_global_esp(esp_mgr)
        doc = esp_mgr.get_document_by_url(esp['id'], url)
        if not doc:
            # Rows are created, with their product label, when the link is
            # added or before it is crawled (_ensure_global_rows)
            return "the link has no database row; add it again with a product"
        esp_mgr.update_document_crawl_status(
            doc['id'],
            status='completed',
            content_hash=esp_mgr.calculate_content_hash(file_content),
            content=file_content,
            filename=filename
        )
        return None
    except Exception as e:
        print(f"[GLOBAL PERSIST] Could not persist {url} to database: {e}")
        return str(e)


def _ensure_global_rows(urls, product):
    """Sort a global crawl or paste by label, creating rows for new URLs.

    Returns (ok_urls, refused, error):
      ok_urls  will be labelled (rows now exist), so vectorize_single_document
               finds each label;
      refused  [{'url', 'error'}], unlabelled: reported, not crawled;
      error    (message, HTTP status) when a new URL already belongs to an
               ESP -- then nothing is created.
    Everything is checked before the first row is created.
    """
    from esp_manager import get_esp_manager, DuplicateURLError
    from product_labels import split_by_label
    esp_mgr = get_esp_manager()
    esp = _ensure_global_esp(esp_mgr)
    ok, refused = split_by_label(esp_mgr, 'global', urls, product)
    new = [url for url in ok if not esp_mgr.get_document_by_url(esp['id'], url)]
    for url in new:
        owners = esp_mgr.find_documents_by_url(url)   # owned by another ESP
        if owners:
            return [], refused, (str(DuplicateURLError(url, owners)), 409)
    for url in new:
        esp_mgr.add_document('global', url, product=product)
    return ok, refused, None


def _delete_global_docs(urls):
    """Remove global-knowledge doc rows from the database (best-effort)."""
    try:
        from esp_manager import get_esp_manager
        get_esp_manager().delete_documents_by_urls('global', urls)
    except Exception as e:
        print(f"[GLOBAL PERSIST] Could not delete from database: {e}")


@app.route('/api/admin/global-knowledge/add-link', methods=['POST'])
def add_global_knowledge_link():
    """Add a new link to global knowledge"""
    data = request.json
    url = (data.get('url') or '').strip()

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    if 'product' not in data:
        from product_labels import OUTDATED_PAGE
        return jsonify({'error': OUTDATED_PAGE}), 400

    # The database row comes first, with its product label: it is what the
    # crawl reads the label from, and it refuses a URL that already exists.
    try:
        from esp_manager import get_esp_manager, DuplicateURLError
        esp_mgr = get_esp_manager()
        _ensure_global_esp(esp_mgr)
        esp_mgr.add_document('global', url, product=data.get('product'))
    except DuplicateURLError as e:
        return jsonify({'error': str(e), 'duplicate': True, 'matches': e.owners}), 409
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Could not add the link: {e}'}), 500

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

        # Already listed: a CSV-only link being labelled from its picker
        if url not in _global_csv_links():
            lines.insert(insert_index, url)
            with open(csv_path, 'w') as f:
                f.write('\n'.join(lines))

    except Exception as e:
        # The row is saved, and the list shows database rows too
        print(f"[GLOBAL] Added {url} to the database but not the CSV: {e}")

    return jsonify({'success': True})

def _find_local_global_copy(url, global_folder):
    """
    Locate the saved .txt file for a global-knowledge URL, if one exists.

    Used as a fallback when a URL can't be (re-)crawled — pasted local://
    docs, or sites that started blocking the crawler — so its content can
    still be backed up to the database from the copy on disk.
    """
    # Only a file that provably belongs to this URL (see find_saved_copy):
    # filenames collide, e.g. every local:// URL maps to index.txt
    from crawler import find_saved_copy
    filename, _content = find_saved_copy(BASE_PATH, 'global', url)
    if not filename:
        return None, None
    return filename, os.path.join(global_folder, filename)


@app.route('/api/admin/global-knowledge/crawl-selected', methods=['POST'])
def crawl_global_knowledge_links():
    """
    Crawl selected global knowledge links.

    Reports the outcome per URL instead of a bare count: a URL that fails to
    crawl (blocked site, timeout, pasted local:// doc) used to be silently
    skipped while the response still claimed success, leaving admins unable
    to trust which docs were actually captured. If a URL can't be crawled but
    its saved file still exists on disk, its content is backed up to the
    database from that copy ('backfilled') so the NO BACKUP flag can clear.
    """
    data = request.json
    urls = data.get('urls', [])

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    if USE_ASYNC_CRAWL and not app.config.get('CRAWL_WORKER_RUNNING'):
        return jsonify({'error': 'The background crawl worker is not running, so nothing '
                                 'would process this crawl. Check the server logs.'}), 503

    # Every URL needs a labelled row before it is crawled; unlabelled ones
    # are reported and the rest go ahead
    try:
        urls, refused, problem = _ensure_global_rows(urls, data.get('product'))
    except Exception as e:
        return jsonify({'error': f'Could not prepare the crawl: {e}'}), 500
    if problem:
        return jsonify({'error': problem[0]}), problem[1]
    if not urls:
        return jsonify({'error': f"{refused[0]['url']}: {refused[0]['error']}"}), 400

    if USE_ASYNC_CRAWL:
        # Same paced background queue as ESP docs: a burst of global URLs on
        # one site must not trip its rate limit either. The worker crawls
        # into docs/global/, indexes under 'global', and backs the content
        # up to the database (falling back to the saved copy for pasted
        # local:// docs), which is everything the synchronous path did.
        try:
            from esp_manager import get_esp_manager
            from adapters.database.db_manager import get_database_adapter
            from workers.crawl_queue import enqueue_urls, queued_response
            esp_mgr = get_esp_manager()
            esp = _ensure_global_esp(esp_mgr)
            job_ids, skipped = enqueue_urls(get_database_adapter(), esp_mgr, esp, 'global', urls)
            return jsonify(queued_response(job_ids, skipped, refused))
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Could not queue global knowledge crawl: {e}'}), 500

    try:
        from crawler import extract_main_content_detailed
        import json
        import time

        docs_path = os.path.join(BASE_PATH, 'docs')
        global_folder = os.path.join(docs_path, 'global')
        os.makedirs(global_folder, exist_ok=True)

        metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: could not read crawl metadata, starting fresh: {e}")
        metadata.setdefault('global', [])

        succeeded = []
        failed = list(refused)

        for url in urls:
            print(f"Crawling {url}...")
            content, crawl_error = extract_main_content_detailed(url)
            backfilled = False

            if content is not None:
                from crawler import save_filename_for
                filename = save_filename_for(BASE_PATH, 'global', url)
                filepath = os.path.join(global_folder, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Source URL: {url}\n\n")
                    f.write(content)
                print(f"  Saved to {filepath}")
                time.sleep(1)
            else:
                # Crawl failed — fall back to the saved copy on disk so the
                # content can still be backed up to the database.
                filename, filepath = _find_local_global_copy(url, global_folder)
                if not filepath:
                    failed.append({'url': url, 'error': crawl_error})
                    continue
                backfilled = True
                print(f"  Crawl failed ({crawl_error}); backing up from local copy {filepath}")

            warnings = []

            # Vectorize just this document — refresh_esp() would wipe the
            # global namespace and re-add only local files
            try:
                vectorize_single_document(vectorizer, 'global', url, filepath, filename)
            except Exception as ve:
                print(f"[VECTORIZE ERROR] global/{filename}: {ve}")
                warnings.append(f"vectorization failed: {ve}")

            # Back up the content in the database (clears the NO BACKUP flag)
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            persist_error = _persist_global_doc(url, filename, filepath, file_content)
            if persist_error:
                warnings.append(f"database backup failed: {persist_error}")

            # Upsert this URL's metadata entry. Only touched on success — a
            # failed re-crawl must not drop the entry for a good older crawl.
            metadata['global'] = [d for d in metadata['global'] if d.get('url') != url]
            metadata['global'].append({'url': url, 'filename': filename, 'filepath': filepath})

            entry = {
                'url': url,
                'filename': filename,
                'backfilled': backfilled,
                'backed_up': persist_error is None
            }
            if backfilled:
                entry['note'] = f"could not crawl ({crawl_error}); backed up from saved local copy"
            if warnings:
                entry['warnings'] = warnings
            succeeded.append(entry)

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Global chunks feed the same answers as ESP chunks, so memoized
        # Query B results are stale now.
        clear_mechanics_cache()

        crawled_count = sum(1 for r in succeeded if not r['backfilled'])
        backfilled_count = len(succeeded) - crawled_count
        parts = [f"Crawled {crawled_count} link(s)"]
        if backfilled_count:
            parts.append(f"backed up {backfilled_count} from saved local copies")
        if failed:
            parts.append(f"{len(failed)} failed")

        return jsonify({
            'success': True,
            'message': ', '.join(parts),
            'count': len(succeeded),  # backward compat with older frontend
            'results': {'success': succeeded, 'failed': failed}
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/global-knowledge/paste-content', methods=['POST'])
def paste_global_content():
    """Manually add content for a global knowledge link that can't be crawled"""
    data = request.json
    url = data.get('url', '')
    content = data.get('content', '')

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

    if not url or not content or not content.strip():
        return jsonify({'error': 'URL and content are required'}), 400

    try:
        _ok, refused, problem = _ensure_global_rows([url], data.get('product'))
    except Exception as e:
        return jsonify({'error': f'Could not save the content: {e}'}), 500
    if problem:
        return jsonify({'error': problem[0]}), problem[1]
    if refused:
        return jsonify({'error': refused[0]['error']}), 400

    try:
        from urllib.parse import urlparse
        import json

        docs_path = os.path.join(BASE_PATH, 'docs')
        global_folder = os.path.join(docs_path, 'global')
        os.makedirs(global_folder, exist_ok=True)

        # A name no other URL's saved copy uses (see save_filename_for)
        from crawler import save_filename_for
        filename = save_filename_for(BASE_PATH, 'global', url)

        # Save content to file
        filepath = os.path.join(global_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n\n")
            f.write(content)

        # Update metadata
        metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        if 'global' not in metadata:
            metadata['global'] = []

        # Remove old entry for this URL if exists
        metadata['global'] = [doc for doc in metadata['global'] if doc['url'] != url]

        # Add new entry
        metadata['global'].append({
            'url': url,
            'filename': filename,
            'filepath': filepath
        })

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Vectorize only this document (see crawl route for why not refresh_esp)
        vectorize_single_document(vectorizer, 'global', url, filepath, filename)
        clear_mechanics_cache()

        # Pasted content can't be re-crawled — persist it in the database
        persist_error = _persist_global_doc(url, filename, filepath, f"Source URL: {url}\n\n{content}")

        message = 'Content saved and vectorized successfully'
        if persist_error:
            message += (f" — WARNING: database backup failed ({persist_error}); "
                        "the content will be lost on the next redeploy")

        return jsonify({
            'success': True,
            'message': message,
            'backed_up': persist_error is None,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/global-knowledge/delete-links', methods=['POST'])
def delete_global_knowledge_links():
    """Delete selected global knowledge links"""
    data = request.json
    urls = data.get('urls', [])

    if not is_admin_request():
        return jsonify({'error': 'Admin access requires a Yotpo Google account'}), 403

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

        # Delete just these URLs' vectors — a full refresh would rebuild the
        # namespace from the (possibly incomplete) local filesystem
        if hasattr(vectorizer, 'delete_by_url'):
            for url in urls:
                vectorizer.delete_by_url(url, 'global')

        # Remove the persisted copies from the database as well
        _delete_global_docs(urls)

        clear_mechanics_cache()

        return jsonify({'success': True, 'message': f'Deleted {len(urls)} links'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== CONVERSATION MAINTENANCE ====================
# Retention (90 days) and the idle-conversation sweep run on their own
# scheduler, deliberately NOT the one below. That one only exists when
# USE_ASYNC_CRAWL is true, and a retention promise made to users in the UI
# cannot quietly stop being kept because an unrelated crawl flag was turned off.

if CONVERSATIONS_AVAILABLE:
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from conversations import purge_expired_conversations, sweep_idle_conversations

        conversation_scheduler = BackgroundScheduler()
        conversation_scheduler.add_job(
            func=purge_expired_conversations,
            trigger='interval', hours=24, id='purge_expired_conversations',
        )
        conversation_scheduler.add_job(
            func=sweep_idle_conversations,
            trigger='interval', minutes=15, id='sweep_idle_conversations',
        )
        conversation_scheduler.start()
        print("[CONVERSATIONS] Retention + idle sweep scheduler started")

        import atexit
        atexit.register(lambda: conversation_scheduler.shutdown(wait=False))
    except Exception as e:
        print(f"[ERROR] Could not start conversation maintenance scheduler: {e}")

# ==================== ASYNC CRAWL WORKER SETUP ====================
# Start background worker threads if async crawl is enabled

crawl_worker = None

if USE_ASYNC_CRAWL:
    try:
        from workers.crawl_worker import start_worker_in_background, CrawlWorker
        from adapters.database.db_manager import get_database_adapter
        from apscheduler.schedulers.background import BackgroundScheduler

        # Start worker threads
        max_workers = int(os.environ.get('CRAWL_WORKER_THREADS', '3'))
        crawl_worker = start_worker_in_background(
            worker_id=f"flask-{os.getpid()}",
            max_workers=max_workers,
            base_path=BASE_PATH
        )
        # Read by the queueing endpoints: with no worker, a queued job would
        # sit in QUEUED forever, so they refuse instead
        app.config['CRAWL_WORKER_RUNNING'] = True
        print(f"[ASYNC CRAWL] Worker started with {max_workers} threads")

        # Start stale job cleanup scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=lambda: CrawlWorker.cleanup_stale_jobs(
                get_database_adapter(),
                timeout_minutes=10
            ),
            trigger='interval',
            minutes=5,
            id='cleanup_stale_jobs'
        )
        scheduler.start()
        print("[ASYNC CRAWL] Stale job cleanup scheduler started (every 5 minutes)")

        # Graceful shutdown on exit
        import atexit
        def shutdown_worker():
            if crawl_worker:
                crawl_worker.stop()
            if scheduler:
                scheduler.shutdown()
        atexit.register(shutdown_worker)

    except ImportError as e:
        print(f"[WARNING] Could not start async crawl worker: {e}")
        print("[WARNING] Falling back to synchronous crawl")
        USE_ASYNC_CRAWL = False
    except Exception as e:
        print(f"[ERROR] Failed to start async crawl worker: {e}")
        import traceback
        traceback.print_exc()
        USE_ASYNC_CRAWL = False

if __name__ == '__main__':
    # Support cloud deployment platforms (Heroku, Railway, etc.)
    port = int(os.getenv('PORT', 5001))
    # Debug mode must be opt-in: the Werkzeug debugger allows remote code
    # execution and this binds to 0.0.0.0.
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', debug=debug, port=port)
