"""
Google account authentication.

Flow: the browser gets a Google ID token from Google Identity Services and
POSTs it to /api/auth/google. We verify it against Google's public keys, upsert
the user, and hand back *our own* session token.

We mint our own token rather than passing Google's ID token through on every
request because Google's expires after one hour -- a user would silently lose
their session mid-conversation. Ours lasts SESSION_TOKEN_DAYS and is signed
with SECRET_KEY.

Identity is keyed on Google's `sub` claim, never on email: `sub` is permanent,
email addresses are not.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, Optional

import jwt
from flask import g, jsonify, request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from adapters.database.db_manager import get_database_adapter

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
SECRET_KEY = os.environ.get('SECRET_KEY', '')
ADMIN_EMAIL_DOMAIN = os.environ.get('ADMIN_EMAIL_DOMAIN', 'yotpo.com').lower()
SESSION_TOKEN_DAYS = int(os.environ.get('SESSION_TOKEN_DAYS', '7'))

# Break-glass admin access. If Google auth is misconfigured in production,
# domain gating would lock everyone out of the panel needed to fix it. Off by
# default; every use is logged loudly so it can't quietly become the norm.
ADMIN_PASSWORD_FALLBACK = os.environ.get('ADMIN_PASSWORD_FALLBACK', 'false').lower() == 'true'

# Google's token lifetime is checked against our clock; allow for small drift.
_CLOCK_SKEW_SECONDS = 10

AUTH_CONFIGURED = bool(GOOGLE_CLIENT_ID and SECRET_KEY)
if not AUTH_CONFIGURED:
    missing = [n for n, v in (('GOOGLE_CLIENT_ID', GOOGLE_CLIENT_ID),
                              ('SECRET_KEY', SECRET_KEY)) if not v]
    print(f"[WARNING] Account system disabled - missing {', '.join(missing)}. "
          "Sign-in will be unavailable and admin will fall back to password auth.")


def _iso(value):
    """Format a timestamp that may be a datetime (Postgres) or a string (SQLite)."""
    if value is None:
        return None
    return value.isoformat() if hasattr(value, 'isoformat') else str(value)


# ==================== Authorization rules ====================

def is_admin_email(email: Optional[str], email_verified: bool) -> bool:
    """Admin == a Google-verified address in the configured domain.

    `email_verified` is not optional paranoia: without it, an account whose
    email Google never confirmed could claim any address it liked.

    rsplit rather than endswith so that 'evil@notyotpo.com' and
    'user@sub.yotpo.com' are both rejected -- we want the exact domain.
    """
    if not email or not email_verified:
        return False
    return email.strip().lower().rsplit('@', 1)[-1] == ADMIN_EMAIL_DOMAIN


# ==================== Google token verification ====================

def verify_google_credential(credential: str) -> Dict:
    """Verify a Google ID token and return its claims.

    google-auth checks the signature against Google's rotating public keys and
    validates issuer, audience and expiry. Raises ValueError if any of that
    fails.
    """
    if not GOOGLE_CLIENT_ID:
        raise ValueError('GOOGLE_CLIENT_ID is not configured')

    claims = google_id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=_CLOCK_SKEW_SECONDS,
    )

    # verify_oauth2_token accepts both issuer spellings; be explicit anyway.
    if claims.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        raise ValueError('Unexpected token issuer')
    if not claims.get('sub'):
        raise ValueError('Token has no subject')
    return claims


# ==================== User storage ====================

def upsert_user(claims: Dict) -> Dict:
    """Create or refresh the user row for a verified Google identity."""
    db = get_database_adapter()
    google_sub = claims['sub']
    email = (claims.get('email') or '').strip()
    name = claims.get('name')
    picture = claims.get('picture')
    hd = claims.get('hd')
    now = datetime.now(timezone.utc)

    existing = db.execute_query(
        "SELECT id, email FROM users WHERE google_sub = %s",
        (google_sub,), fetch=True
    )

    if existing:
        user_id = str(existing[0][0])
        try:
            db.execute_query(
                """UPDATE users
                      SET email = %s, name = %s, picture_url = %s, hd = %s, last_login_at = %s
                    WHERE id = %s""",
                (email, name, picture, hd, now, user_id)
            )
        except Exception as exc:
            # LOWER(email) is unique. If this person's Google address changed
            # to one another row already holds, keep the stored email rather
            # than failing the login outright.
            print(f"[AUTH] Could not update email for user {user_id} ({exc}); "
                  "keeping the previously stored address")
            db.execute_query(
                "UPDATE users SET name = %s, picture_url = %s, hd = %s, last_login_at = %s WHERE id = %s",
                (name, picture, hd, now, user_id)
            )
            email = existing[0][1]
    else:
        # ids are generated here, not by the database: SQLite has no
        # gen_random_uuid(), so relying on the Postgres default would work in
        # production and fail locally.
        user_id = str(uuid.uuid4())
        try:
            db.execute_query(
                """INSERT INTO users (id, google_sub, email, name, picture_url, hd, last_login_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, google_sub, email, name, picture, hd, now)
            )
        except Exception:
            # Two tabs signing in at once both miss the SELECT above; the
            # loser of the race re-reads the winner's row.
            again = db.execute_query(
                "SELECT id, email FROM users WHERE google_sub = %s", (google_sub,), fetch=True
            )
            if not again:
                raise
            user_id, email = str(again[0][0]), again[0][1]

    return {'id': user_id, 'email': email, 'name': name, 'picture': picture, 'hd': hd}


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Load a user row. Returns None if the account no longer exists."""
    rows = get_database_adapter().execute_query(
        "SELECT id, google_sub, email, name, picture_url, hd, created_at, last_login_at "
        "FROM users WHERE id = %s",
        (user_id,), fetch=True
    )
    if not rows:
        return None
    r = rows[0]
    return {
        'id': str(r[0]), 'google_sub': r[1], 'email': r[2], 'name': r[3],
        'picture': r[4], 'hd': r[5],
        'created_at': _iso(r[6]), 'last_login_at': _iso(r[7]),
    }


# ==================== Session tokens ====================

def mint_session_token(user: Dict, email_verified: bool) -> str:
    """Issue our own signed session token for a freshly authenticated user."""
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user['id'],
        'email': user.get('email'),
        'ev': bool(email_verified),   # carried so admin checks can require it
        'iat': now,
        'exp': now + timedelta(days=SESSION_TOKEN_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_session_token(token: str) -> Optional[Dict]:
    """Return the token payload, or None if it is invalid or expired."""
    if not (token and SECRET_KEY):
        return None
    try:
        # algorithms is pinned: without it a caller could present an
        # unsigned ("alg": "none") token.
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.PyJWTError:
        return None


def _bearer_token() -> Optional[str]:
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header[7:].strip() or None
    return None


def current_token_payload() -> Optional[Dict]:
    """Decoded session token for this request, cached on `g`."""
    if not hasattr(g, '_auth_payload'):
        g._auth_payload = decode_session_token(_bearer_token())
    return g._auth_payload


def current_user_id() -> Optional[str]:
    payload = current_token_payload()
    return payload.get('sub') if payload else None


def current_user() -> Optional[Dict]:
    """The signed-in user for this request, or None. Cached on `g`.

    Reads the database rather than trusting the token's copy of the profile,
    so a renamed or deleted account is reflected immediately.
    """
    if not hasattr(g, '_auth_user'):
        user_id = current_user_id()
        g._auth_user = get_user_by_id(user_id) if user_id else None
    return g._auth_user


def current_user_is_admin() -> bool:
    """Admin status, recomputed per request from the *current* stored email.

    Deliberately not read from the token: if someone leaves the domain, we do
    not want their unexpired token to keep admin for another week.
    """
    payload = current_token_payload()
    if not payload:
        return False
    user = current_user()
    return bool(user) and is_admin_email(user.get('email'), payload.get('ev', False))


# ==================== Decorators ====================

def require_auth(fn):
    """401 unless a valid session token is presented."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({'error': 'Sign in required'}), 401
        return fn(*args, **kwargs)
    return wrapper


def _password_fallback_ok() -> bool:
    """Emergency password path, only when explicitly switched on."""
    if not ADMIN_PASSWORD_FALLBACK:
        return False
    supplied = (
        request.headers.get('X-Admin-Password', '')
        or request.args.get('password', '')
    )
    if not supplied and request.is_json:
        supplied = (request.get_json(silent=True) or {}).get('password', '')
    if not supplied:
        return False
    if supplied == os.environ.get('ADMIN_PASSWORD', 'RICHCSM'):
        print(f"[ADMIN FALLBACK] password auth used on {request.method} {request.path} "
              f"from {request.remote_addr} - Google auth should be fixed")
        return True
    return False


def require_admin(fn):
    """403 unless the caller is a verified @<ADMIN_EMAIL_DOMAIN> account.

    Hiding the Admin button in the UI is cosmetic; this is the access control.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user_is_admin() or _password_fallback_ok():
            return fn(*args, **kwargs)
        if current_user():
            return jsonify({'error': f'Admin access is limited to @{ADMIN_EMAIL_DOMAIN} accounts'}), 403
        return jsonify({'error': 'Sign in with a Yotpo account to access admin'}), 401
    return wrapper


# ==================== Routes ====================

def _public_user(user: Dict, is_admin: bool) -> Dict:
    return {
        'id': user['id'],
        'email': user.get('email'),
        'name': user.get('name'),
        'picture': user.get('picture'),
        'is_admin': is_admin,
    }


def register_auth_routes(app):
    """Register /api/auth/* endpoints."""

    @app.route('/api/auth/config', methods=['GET'])
    def auth_config():
        """Lets the frontend render sign-in without hardcoding the client id.

        The client id is public by design -- it identifies the app to Google
        and is visible in every sign-in request.
        """
        return jsonify({'enabled': AUTH_CONFIGURED, 'google_client_id': GOOGLE_CLIENT_ID})

    @app.route('/api/auth/google', methods=['POST'])
    def auth_google():
        """Exchange a Google ID token for one of our session tokens."""
        if not AUTH_CONFIGURED:
            return jsonify({'error': 'Sign-in is not configured on this server'}), 503

        credential = (request.get_json(silent=True) or {}).get('credential', '')
        if not credential:
            return jsonify({'error': 'No credential provided'}), 400

        try:
            claims = verify_google_credential(credential)
        except ValueError as exc:
            # Don't echo the reason back: it tells an attacker which part of
            # the token to adjust next.
            print(f"[AUTH] Rejected Google credential: {exc}")
            return jsonify({'error': 'Could not verify your Google account'}), 401

        try:
            user = upsert_user(claims)
        except Exception as exc:
            print(f"[AUTH] Failed to save user: {exc}")
            return jsonify({'error': 'Could not complete sign-in'}), 500

        email_verified = bool(claims.get('email_verified'))
        token = mint_session_token(user, email_verified)
        is_admin = is_admin_email(user.get('email'), email_verified)
        print(f"[AUTH] Signed in {user.get('email')} (admin={is_admin})")

        return jsonify({'token': token, 'user': _public_user(user, is_admin)})

    @app.route('/api/auth/me', methods=['GET'])
    def auth_me():
        """Who is this token? Used on page load to restore the session."""
        user = current_user()
        if not user:
            return jsonify({'authenticated': False}), 200
        return jsonify({
            'authenticated': True,
            'user': _public_user(user, current_user_is_admin()),
        })

    @app.route('/api/auth/logout', methods=['POST'])
    def auth_logout():
        """Sign-out is client-side: the browser discards the token.

        There is no server-side revocation list. A stolen token stays valid
        until it expires -- worth revisiting if this ever holds more than
        conversation history.
        """
        return jsonify({'success': True})

    print("[DEBUG] Auth routes registered "
          f"(configured={AUTH_CONFIGURED}, admin domain=@{ADMIN_EMAIL_DOMAIN}, "
          f"password fallback={'ON' if ADMIN_PASSWORD_FALLBACK else 'off'})")
