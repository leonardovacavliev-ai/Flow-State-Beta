/**
 * Google sign-in.
 *
 * Loads before app.js and exposes `window.Auth` so the rest of the app can ask
 * who is signed in and get an Authorization header. Signing in is optional:
 * everything works signed out, you just don't get saved conversations.
 *
 * The top-right control is a pill when signed out and an avatar when signed
 * in; both open the same popup. Google's own rendered button lives inside that
 * popup rather than in the corner, because GIS requires its real button and we
 * want the corner to stay compact.
 */

const AUTH_API_URL = (() => {
    const isStaticDevServer =
        (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        && ['3001', '8000'].includes(window.location.port);
    return isStaticDevServer
        ? 'http://localhost:5001/api'
        : `${window.location.protocol}//${window.location.host}/api`;
})();

const TOKEN_STORAGE_KEY = 'flowStateAuthToken';

let authToken = null;
let currentUser = null;      // { id, email, name, picture, is_admin } or null
let googleClientId = '';
let googleReady = false;
const changeListeners = [];

// ---------- token storage ----------

function loadStoredToken() {
    try {
        return localStorage.getItem(TOKEN_STORAGE_KEY);
    } catch (error) {
        // Safari private mode throws on localStorage access; sign-in simply
        // won't persist, which is survivable.
        console.warn('Could not read stored session:', error);
        return null;
    }
}

function storeToken(token) {
    try {
        if (token) {
            localStorage.setItem(TOKEN_STORAGE_KEY, token);
        } else {
            localStorage.removeItem(TOKEN_STORAGE_KEY);
        }
    } catch (error) {
        console.warn('Could not persist session:', error);
    }
}

// ---------- public surface ----------

function notifyChange() {
    renderAccountControl();
    changeListeners.forEach(fn => {
        try {
            fn(currentUser);
        } catch (error) {
            console.error('Auth change listener failed:', error);
        }
    });
}

window.Auth = {
    getUser: () => currentUser,
    getToken: () => authToken,
    isSignedIn: () => !!currentUser,
    isAdmin: () => !!(currentUser && currentUser.is_admin),
    /** Headers for an authenticated request; empty when signed out. */
    headers: () => (authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    /** Register a callback fired whenever sign-in state changes. */
    onChange: (fn) => {
        changeListeners.push(fn);
        if (currentUser !== null) fn(currentUser);
    },
    signOut
};

// ---------- sign in / out ----------

async function handleCredentialResponse(response) {
    try {
        const res = await fetch(`${AUTH_API_URL}/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credential: response.credential })
        });
        const data = await res.json();

        if (!res.ok) {
            console.error('Sign-in rejected:', data.error);
            alert(data.error || 'Sign-in failed. Please try again.');
            return;
        }

        authToken = data.token;
        currentUser = data.user;
        storeToken(authToken);
        closeAccountPopup();
        notifyChange();
    } catch (error) {
        console.error('Sign-in request failed:', error);
        alert('Could not reach the server to sign you in. Please try again.');
    }
}

function signOut() {
    const wasSignedIn = !!currentUser;

    // Fired while the token is still valid, so listeners can make their last
    // authenticated call (ending the open conversation). Clearing the token
    // first would make that call 401.
    if (wasSignedIn) document.dispatchEvent(new CustomEvent('auth:signingout'));

    authToken = null;
    currentUser = null;
    storeToken(null);

    // Stops Google silently re-signing the user in on the next page load.
    if (googleReady && window.google?.accounts?.id) {
        try {
            google.accounts.id.disableAutoSelect();
        } catch (error) {
            console.warn('Could not clear Google auto-select:', error);
        }
    }

    fetch(`${AUTH_API_URL}/auth/logout`, { method: 'POST' }).catch(() => {});
    closeAccountPopup();
    notifyChange();
    if (wasSignedIn) document.dispatchEvent(new CustomEvent('auth:signedout'));
}

/** Validate a stored token against the server. Expired or revoked -> signed out. */
async function restoreSession() {
    authToken = loadStoredToken();
    if (!authToken) return;

    try {
        const res = await fetch(`${AUTH_API_URL}/auth/me`, { headers: window.Auth.headers() });
        const data = await res.json();
        if (data.authenticated) {
            currentUser = data.user;
        } else {
            // Token expired or the account is gone; drop it rather than
            // leaving a dead token in storage.
            authToken = null;
            storeToken(null);
        }
    } catch (error) {
        console.error('Could not restore session:', error);
        authToken = null;
    }
}

// ---------- UI ----------

function initials(user) {
    const source = (user.name || user.email || '?').trim();
    return source.charAt(0).toUpperCase();
}

function renderAccountControl() {
    const mount = document.getElementById('accountControl');
    if (!mount) return;

    if (currentUser) {
        const avatar = currentUser.picture
            // Google avatar URLs sometimes 404 or get blocked; fall back to
            // an initials circle rather than showing a broken image.
            ? `<img src="${escapeAttrSafe(currentUser.picture)}" alt=""
                    class="w-9 h-9 rounded-full object-cover"
                    referrerpolicy="no-referrer"
                    onerror="this.replaceWith(window.__authInitialsBadge('${escapeAttrSafe(initials(currentUser))}'))">`
            : `<span class="w-9 h-9 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">${escapeHtmlSafe(initials(currentUser))}</span>`;

        mount.innerHTML = `
            <button id="accountAvatarBtn" title="${escapeAttrSafe(currentUser.email || '')}"
                    class="block rounded-full ring-1 ring-border hover:ring-primary transition-all shadow-sm bg-card">
                ${avatar}
            </button>
        `;
    } else {
        mount.innerHTML = `
            <button id="accountAvatarBtn"
                    class="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-full text-sm font-medium text-foreground hover:bg-muted transition-colors shadow-sm">
                ${googleGlyph()}
                Sign in
            </button>
            <!-- The chip background is not decoration: this sits on top of the
                 gradient intro, where plain muted text is unreadable. -->
            <p class="mt-1.5 ml-auto w-fit px-2 py-0.5 rounded-full bg-card/85 backdrop-blur-sm border border-border text-[11px] text-muted-foreground leading-tight">
                Not signed in — chats aren't saved
            </p>
        `;
    }

    document.getElementById('accountAvatarBtn')
        ?.addEventListener('click', toggleAccountPopup);
}

/** Used by the avatar's onerror handler, hence the global. */
window.__authInitialsBadge = (letter) => {
    const span = document.createElement('span');
    span.className = 'w-9 h-9 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold';
    span.textContent = letter;
    return span;
};

function googleGlyph() {
    return `<svg width="14" height="14" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.6 2.4 30.2 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.2 17.7 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.1 24.6c0-1.6-.1-2.8-.4-4.1H24v7.4h12.7c-.3 2.1-1.6 5.2-4.7 7.3l7.2 5.6c4.3-4 6.9-9.9 6.9-16.2z"/>
        <path fill="#FBBC05" d="M10.5 28.7c-.5-1.5-.8-3-.8-4.7s.3-3.2.8-4.7l-7.9-6.1C1 16.3 0 20 0 24s1 7.7 2.6 10.8l7.9-6.1z"/>
        <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.2-5.6c-2 1.3-4.6 2.3-8.7 2.3-6.3 0-11.6-3.7-13.5-9.2l-7.9 6.1C6.5 42.6 14.6 48 24 48z"/>
    </svg>`;
}

// Local copies: auth.js loads before app.js, so its helpers aren't defined yet.
function escapeHtmlSafe(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}
function escapeAttrSafe(text) {
    return escapeHtmlSafe(text).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ---------- popup ----------

function popupEl() {
    return document.getElementById('accountPopup');
}

function toggleAccountPopup(event) {
    event?.stopPropagation();
    const popup = popupEl();
    if (!popup) return;
    if (popup.classList.contains('hidden')) {
        openAccountPopup();
    } else {
        closeAccountPopup();
    }
}

function openAccountPopup() {
    const popup = popupEl();
    if (!popup) return;

    if (currentUser) {
        const adminBadge = currentUser.is_admin
            ? `<span class="inline-block mt-2 px-2 py-0.5 bg-primary/10 text-primary rounded-full text-[11px] font-medium">Yotpo Admin</span>`
            : '';
        popup.innerHTML = `
            <div class="p-4">
                <div class="text-sm font-semibold text-card-foreground">${escapeHtmlSafe(currentUser.name || 'Signed in')}</div>
                <div class="text-xs text-muted-foreground break-all">${escapeHtmlSafe(currentUser.email || '')}</div>
                ${adminBadge}
            </div>
            <div class="border-t border-border p-3">
                <button id="signOutBtn" class="w-full px-3 py-2 text-sm font-medium text-foreground border border-input rounded-lg hover:bg-muted transition-colors">
                    Sign out
                </button>
            </div>
        `;
        popup.querySelector('#signOutBtn').addEventListener('click', signOut);
    } else {
        popup.innerHTML = `
            <div class="p-4">
                <div class="text-sm font-semibold text-card-foreground mb-1">Save your conversations</div>
                <p class="text-xs text-muted-foreground leading-relaxed mb-3">
                    Sign in with Google to keep your chats and come back to them later.
                    Without signing in, this conversation disappears when you close the tab.
                </p>
                <div id="googleButtonMount" class="flex justify-center min-h-[40px]"></div>
                <p id="googleButtonFallback" class="hidden text-xs text-destructive mt-2">
                    Google sign-in couldn't load. Check your connection and reload the page.
                </p>
            </div>
        `;
        renderGoogleButton();
    }

    popup.classList.remove('hidden');
    document.addEventListener('click', onDocumentClick);
    document.addEventListener('keydown', onEscape);
}

function closeAccountPopup() {
    const popup = popupEl();
    if (!popup) return;
    popup.classList.add('hidden');
    document.removeEventListener('click', onDocumentClick);
    document.removeEventListener('keydown', onEscape);
}

// The existing modals close via `e.target === modal` on the backdrop; an
// anchored popup has no backdrop, so it needs its own outside-click test.
function onDocumentClick(event) {
    const popup = popupEl();
    const trigger = document.getElementById('accountAvatarBtn');
    if (!popup || popup.contains(event.target) || trigger?.contains(event.target)) return;
    closeAccountPopup();
}

function onEscape(event) {
    if (event.key === 'Escape') closeAccountPopup();
}

function renderGoogleButton() {
    const mount = document.getElementById('googleButtonMount');
    if (!mount) return;

    if (!googleReady || !window.google?.accounts?.id) {
        document.getElementById('googleButtonFallback')?.classList.remove('hidden');
        return;
    }

    google.accounts.id.renderButton(mount, {
        theme: 'outline',
        size: 'large',
        shape: 'pill',
        text: 'signin_with',
        logo_alignment: 'center',
        // Pinned: GIS otherwise follows the browser's locale and renders the
        // button in a different language from the rest of this English-only UI.
        locale: 'en'
    });
}

// ---------- bootstrap ----------

/** Poll briefly for the async-loaded GIS script. */
function waitForGoogle(timeoutMs = 8000) {
    return new Promise((resolve) => {
        if (window.google?.accounts?.id) return resolve(true);
        const started = Date.now();
        const timer = setInterval(() => {
            if (window.google?.accounts?.id) {
                clearInterval(timer);
                resolve(true);
            } else if (Date.now() - started > timeoutMs) {
                clearInterval(timer);
                resolve(false);
            }
        }, 100);
    });
}

async function initAuth() {
    // Render the signed-out control immediately so the corner is never empty
    // while the config request is in flight.
    renderAccountControl();

    try {
        const res = await fetch(`${AUTH_API_URL}/auth/config`);
        const config = await res.json();
        if (!config.enabled || !config.google_client_id) {
            console.warn('Sign-in is not configured on this server.');
            document.getElementById('accountControl')?.classList.add('hidden');
            return;
        }
        googleClientId = config.google_client_id;
    } catch (error) {
        console.error('Could not load auth config:', error);
        document.getElementById('accountControl')?.classList.add('hidden');
        return;
    }

    await restoreSession();
    notifyChange();

    googleReady = await waitForGoogle();
    if (!googleReady) {
        console.warn('Google Identity Services did not load.');
        return;
    }

    google.accounts.id.initialize({
        client_id: googleClientId,
        callback: handleCredentialResponse,
        // No One Tap on load: an unprompted popup on first visit is intrusive
        // for a tool people open to ask one question.
        auto_select: false,
        cancel_on_tap_outside: true
    });

    // If the popup was already open waiting on the script, fill it in now.
    if (!popupEl()?.classList.contains('hidden') && !currentUser) renderGoogleButton();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuth);
} else {
    initAuth();
}
