"""
Saved conversations.

A conversation begins with the first message after the gradient intro and ends
when the user picks an ESP again or closes the window. Reopening one resumes
it, so `ended_at` means "the last time this ended", not a permanent close, and
one conversation may span several sessions.

Only signed-in users get conversations. Guests keep the previous behaviour:
history lives in sessionStorage and disappears with the tab.

Every read and write is scoped by user_id taken from the session token, never
from a request parameter -- otherwise anyone could read anyone's chats by
guessing a UUID.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import jsonify, request

from adapters.database.db_manager import get_database_adapter
from auth import current_user_id, decode_session_token, require_auth

# Conversations are deleted this long after their last message. Resuming one
# resets the clock, so only genuinely abandoned chats age out.
RETENTION_DAYS = int(os.environ.get('CONVERSATION_RETENTION_DAYS', '90'))

# A conversation left active this long without a message is treated as ended.
# beforeunload is unreliable -- it does not fire on mobile backgrounding or a
# tab crash -- so without this sweep, conversations would sit 'active' forever.
IDLE_END_MINUTES = int(os.environ.get('CONVERSATION_IDLE_MINUTES', '30'))

TITLE_MAX_CHARS = 60


def _now() -> str:
    """Current UTC time in a format both dialects order correctly.

    Written explicitly on every insert rather than relying on
    DEFAULT CURRENT_TIMESTAMP: SQLite stores that as 'YYYY-MM-DD HH:MM:SS'
    while Python's isoformat() uses a 'T' separator, and mixing the two in one
    column breaks lexicographic ordering -- which is how SQLite sorts text
    timestamps. One format everywhere avoids that.
    """
    return datetime.utcnow().isoformat(sep=' ', timespec='microseconds')


def _sql(query: str) -> str:
    """Translate canonical `?` placeholders to the dialect's style."""
    if get_database_adapter().dialect == 'postgres':
        return query.replace('?', '%s')
    return query


def _iso(value):
    """Format a timestamp that may be a datetime (Postgres) or a str (SQLite)."""
    if value is None:
        return None
    return value.isoformat() if hasattr(value, 'isoformat') else str(value)


def _title_from(message: str) -> str:
    title = ' '.join((message or '').split())
    if len(title) > TITLE_MAX_CHARS:
        title = title[:TITLE_MAX_CHARS - 1].rstrip() + '…'
    return title or 'Untitled conversation'


# ==================== Writes ====================

def create_conversation(user_id: str, esp: str, session_id: Optional[str] = None) -> Dict:
    """Start a conversation. Returns its id."""
    conversation_id = str(uuid.uuid4())
    now = _now()
    db = get_database_adapter()
    db.execute_query(_sql("""
        INSERT INTO conversations (id, user_id, esp, status, started_at, last_message_at, session_id)
        VALUES (?, ?, ?, 'active', ?, ?, ?)
    """), (conversation_id, user_id, esp, now, now, session_id))
    return {'id': conversation_id, 'esp': esp, 'started_at': now}


def append_message(conversation_id: str, user_id: str, role: str, content: str) -> Optional[int]:
    """Append one message and update the conversation's counters.

    Returns the message's seq, or None if the conversation isn't this user's.

    Runs as a single transaction: the message insert and the counter update
    must not be able to diverge, or message_count stops matching reality.
    """
    db = get_database_adapter()
    now = _now()

    with db.connection() as conn:
        cur = conn.cursor()

        cur.execute(_sql("SELECT title, message_count FROM conversations WHERE id = ? AND user_id = ?"),
                    (conversation_id, user_id))
        row = cur.fetchone()
        if not row:
            return None
        title = row[0] if not isinstance(row, dict) else row['title']

        cur.execute(_sql("SELECT COALESCE(MAX(seq), 0) + 1 FROM conversation_messages WHERE conversation_id = ?"),
                    (conversation_id,))
        seq_row = cur.fetchone()
        seq = (seq_row[0] if not isinstance(seq_row, dict) else list(seq_row.values())[0]) or 1

        cur.execute(_sql("""
            INSERT INTO conversation_messages (conversation_id, seq, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """), (conversation_id, seq, role, content, now))

        # The first user message names the conversation.
        if not title and role == 'user':
            cur.execute(_sql("""
                UPDATE conversations
                   SET title = ?, message_count = message_count + 1,
                       last_message_at = ?, status = 'active', ended_at = NULL
                 WHERE id = ?
            """), (_title_from(content), now, conversation_id))
        else:
            cur.execute(_sql("""
                UPDATE conversations
                   SET message_count = message_count + 1,
                       last_message_at = ?, status = 'active', ended_at = NULL
                 WHERE id = ?
            """), (now, conversation_id))

        conn.commit()
        return seq


def end_conversation(conversation_id: str, user_id: str) -> bool:
    """Mark a conversation ended. Safe to call more than once."""
    db = get_database_adapter()
    db.execute_query(_sql("""
        UPDATE conversations SET status = 'ended', ended_at = ?
         WHERE id = ? AND user_id = ? AND status = 'active'
    """), (_now(), conversation_id, user_id))
    return True


def delete_conversation(conversation_id: str, user_id: str) -> bool:
    """Delete a conversation and its messages.

    Messages are deleted explicitly rather than left to ON DELETE CASCADE.
    SQLite ignores foreign keys unless PRAGMA foreign_keys=ON is set on every
    connection, which this codebase does not do -- so the cascade silently
    does nothing locally and the message text would survive the delete.
    Deleting both here behaves identically on both backends.
    """
    db = get_database_adapter()
    rows = db.execute_query(
        _sql("SELECT id FROM conversations WHERE id = ? AND user_id = ?"),
        (conversation_id, user_id), fetch=True)
    if not rows:
        return False

    with db.connection() as conn:
        cur = conn.cursor()
        cur.execute(_sql("DELETE FROM conversation_messages WHERE conversation_id = ?"),
                    (conversation_id,))
        cur.execute(_sql("DELETE FROM conversations WHERE id = ? AND user_id = ?"),
                    (conversation_id, user_id))
        conn.commit()
    return True


# ==================== Reads ====================

def list_conversations(user_id: str, esp: Optional[str] = None,
                       limit: int = 50, offset: int = 0) -> List[Dict]:
    """This user's conversations, newest activity first.

    Conversations with no messages are excluded: one is created the moment a
    user starts typing into a fresh chat, and an abandoned empty shell should
    not appear in the history list.
    """
    db = get_database_adapter()
    params = [user_id]
    where = "user_id = ? AND message_count > 0"
    if esp:
        where += " AND esp = ?"
        params.append(esp)
    params.extend([limit, offset])

    rows = db.execute_query(_sql(f"""
        SELECT id, esp, title, status, started_at, ended_at, last_message_at, message_count
          FROM conversations
         WHERE {where}
         ORDER BY last_message_at DESC
         LIMIT ? OFFSET ?
    """), tuple(params), fetch=True) or []

    return [{
        'id': str(r[0]),
        'esp': r[1],
        'title': r[2],
        'status': r[3],
        'started_at': _iso(r[4]),
        'ended_at': _iso(r[5]),
        'last_message_at': _iso(r[6]),
        'message_count': r[7],
    } for r in rows]


def get_conversation(conversation_id: str, user_id: str) -> Optional[Dict]:
    """One conversation with its full message list, or None if not this user's."""
    db = get_database_adapter()
    rows = db.execute_query(_sql("""
        SELECT id, esp, title, status, started_at, ended_at, last_message_at, message_count
          FROM conversations WHERE id = ? AND user_id = ?
    """), (conversation_id, user_id), fetch=True)
    if not rows:
        return None
    r = rows[0]

    msg_rows = db.execute_query(_sql("""
        SELECT seq, role, content, created_at
          FROM conversation_messages WHERE conversation_id = ? ORDER BY seq
    """), (conversation_id,), fetch=True) or []

    return {
        'id': str(r[0]), 'esp': r[1], 'title': r[2], 'status': r[3],
        'started_at': _iso(r[4]), 'ended_at': _iso(r[5]),
        'last_message_at': _iso(r[6]), 'message_count': r[7],
        'messages': [{'seq': m[0], 'role': m[1], 'content': m[2], 'created_at': _iso(m[3])}
                     for m in msg_rows],
    }


def get_history_for_ai(conversation_id: str, user_id: str, limit: int = 20) -> List[Dict]:
    """The last N messages as the AI client expects them.

    Scoped by user_id so a forged conversation_id can't pull someone else's
    chat into another user's prompt.
    """
    db = get_database_adapter()
    rows = db.execute_query(_sql("""
        SELECT role, content FROM conversation_messages
         WHERE conversation_id = (SELECT id FROM conversations WHERE id = ? AND user_id = ?)
         ORDER BY seq DESC LIMIT ?
    """), (conversation_id, user_id, limit), fetch=True) or []
    return [{'role': r[0], 'content': r[1]} for r in reversed(rows)]


# ==================== Maintenance ====================

def sweep_idle_conversations() -> int:
    """End conversations that went quiet without a proper end signal."""
    cutoff = (datetime.utcnow() - timedelta(minutes=IDLE_END_MINUTES)).isoformat(
        sep=' ', timespec='microseconds')
    db = get_database_adapter()
    db.execute_query(_sql("""
        UPDATE conversations SET status = 'ended', ended_at = ?
         WHERE status = 'active' AND last_message_at < ?
    """), (_now(), cutoff))
    return 0


def purge_expired_conversations() -> int:
    """Delete conversations untouched for RETENTION_DAYS.

    This enforces the retention promise made in the UI, so it must not depend
    on any feature flag.

    Messages are deleted explicitly, not left to ON DELETE CASCADE: SQLite
    does not enforce foreign keys unless PRAGMA foreign_keys=ON is set per
    connection, so relying on the cascade would delete the conversation row
    while leaving every message body in the database -- the retention promise
    would appear kept while the actual content survived.
    """
    cutoff = (datetime.utcnow() - timedelta(days=RETENTION_DAYS)).isoformat(
        sep=' ', timespec='microseconds')
    db = get_database_adapter()
    rows = db.execute_query(
        _sql("SELECT COUNT(*) FROM conversations WHERE last_message_at < ?"),
        (cutoff,), fetch=True)
    doomed = rows[0][0] if rows else 0
    if doomed:
        with db.connection() as conn:
            cur = conn.cursor()
            cur.execute(_sql("""
                DELETE FROM conversation_messages
                 WHERE conversation_id IN (
                       SELECT id FROM conversations WHERE last_message_at < ?)
            """), (cutoff,))
            cur.execute(_sql("DELETE FROM conversations WHERE last_message_at < ?"), (cutoff,))
            conn.commit()
        print(f"[RETENTION] Purged {doomed} conversation(s) inactive for "
              f"{RETENTION_DAYS}+ days", flush=True)
    return doomed


# ==================== Routes ====================

def register_conversation_routes(app):
    """Register /api/conversations endpoints. All require a signed-in user."""

    @app.route('/api/conversations', methods=['POST'])
    @require_auth
    def create_conversation_route():
        data = request.get_json(silent=True) or {}
        esp = (data.get('esp') or '').strip().lower().replace('/', '_')
        if not esp:
            return jsonify({'error': 'esp is required'}), 400
        conv = create_conversation(current_user_id(), esp, data.get('session_id'))
        return jsonify({'conversation_id': conv['id']})

    @app.route('/api/conversations', methods=['GET'])
    @require_auth
    def list_conversations_route():
        esp = request.args.get('esp')
        if esp:
            esp = esp.strip().lower().replace('/', '_')
        try:
            limit = min(int(request.args.get('limit', 50)), 100)
            offset = max(int(request.args.get('offset', 0)), 0)
        except ValueError:
            return jsonify({'error': 'limit and offset must be integers'}), 400
        return jsonify({'conversations': list_conversations(current_user_id(), esp, limit, offset)})

    @app.route('/api/conversations/<conversation_id>', methods=['GET'])
    @require_auth
    def get_conversation_route(conversation_id):
        conv = get_conversation(conversation_id, current_user_id())
        if not conv:
            return jsonify({'error': 'Conversation not found'}), 404
        return jsonify(conv)

    @app.route('/api/conversations/<conversation_id>/end', methods=['POST'])
    def end_conversation_route(conversation_id):
        """End a conversation.

        Deliberately not @require_auth: this is also called from
        navigator.sendBeacon on tab close, and sendBeacon cannot set an
        Authorization header. So the token may instead arrive in the body.

        It is the same signed token, verified the same way -- the only thing
        relaxed is where it is read from, and only on this one endpoint. The
        conversation is still scoped to the user the token names, so this
        cannot end anyone else's conversation.
        """
        user_id = current_user_id()

        if not user_id:
            body = request.get_json(silent=True, force=True) or {}
            payload = decode_session_token(body.get('token', ''))
            user_id = payload.get('sub') if payload else None

        if not user_id:
            return jsonify({'error': 'Sign in required'}), 401

        end_conversation(conversation_id, user_id)
        return jsonify({'success': True})

    @app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
    @require_auth
    def delete_conversation_route(conversation_id):
        if not delete_conversation(conversation_id, current_user_id()):
            return jsonify({'error': 'Conversation not found'}), 404
        return jsonify({'success': True})

    print("[DEBUG] Conversation routes registered "
          f"(retention {RETENTION_DAYS}d, idle end {IDLE_END_MINUTES}m)")
