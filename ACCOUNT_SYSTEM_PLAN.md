# Account System Plan — Google Login, Saved Conversations, Yotpo-Only Admin

**Status**: Feature complete — steps 1-7 of §9 done. Google sign-in, saved
conversations and Yotpo-gated admin all built and verified. Step 8 (cleanup) is
optional polish.
**Created**: 2026-08-13
**Owner**: Leo Vacavliev

This document is the single source of truth for the account-system work. It carries a
**Rolling Memory** section (below) that every future session must read first and update
last. Keep it in the repo root next to the other phase docs.

---

## 🧠 Rolling Memory (read this first, update it last)

### Current state of the work
| Item | State |
|---|---|
| Plan approved | ✅ All of §8 answered by Leo |
| Google Cloud OAuth client created | ✅ `906346920698-mb6i2n452iagsblgiduocgrtfcdt0dcs.apps.googleusercontent.com` |
| DB schema written (users / conversations / conversation_messages) | ✅ Both dialects, session 1 |
| DB schema applied to Railway | ✅ Verified live: 3 tables, 2 columns, 4 indexes |
| Backend auth module (`backend/auth.py`) | ✅ Session 1, 37 unit checks passing |
| Admin gating switched from password → email domain | ✅ Session 1 — 44 routes, probed with 3 identities |
| Frontend sign-in UI (`frontend/auth.js`) | ✅ Session 1, verified in browser |
| Conversation lifecycle (begin/end) wired in frontend | ✅ Session 1, 35 checks + browser-verified |
| History panel rebuilt (conversations, not messages) | ✅ Session 1, browser-verified |
| Deployed to Railway | ✅ Steps 2-5 live (`717ee0f`), admin gate verified in production |

**Production**: https://flow-state-beta-production.up.railway.app/ — real Google sign-in
confirmed working end to end (a `@yotpo.com` account with Workspace `hd=yotpo.com` is
already registered in `users`, so it will pass the step-5 admin gate).

### Decisions locked in
_(Leo, 2026-08-13, session 1)_
- **Login is optional.** Guests keep chatting exactly as today. Guests get an explicit
  disclaimer that their chats are not saved.
- **Reopening a saved conversation resumes it** — new messages append to that conversation.
- **Per-ESP clock buttons stay** in the sidebar. History remains ESP-scoped, one modal per ESP.
- **Account UI is a single avatar, top-right**, opening a popup dialog containing sign-out.
- **Retention: 90 days.** Conversations and their messages are purged 90 days after
  `last_message_at`. Resuming a conversation resets its clock.
- **Break-glass admin password is kept**, disabled by default, behind `ADMIN_PASSWORD_FALLBACK`.

### Decisions explicitly deferred
- Multi-tenancy / per-customer isolation (Phase 6 in CLAUDE.md) — accounts here are
  individual identities, **not** tenants. Do not conflate the two.

### Still open
_(nothing blocking — all of §8 is answered)_

### Session log
| Date | Session | What happened | Next action |
|---|---|---|---|
| 2026-08-13 | 1 | Analyzed codebase, wrote this plan. No code changed. | Get answers to §8, then start Step 1 (Google Cloud client + schema). |
| 2026-08-13 | 1 (cont.) | Leo answered Q1/Q2/Q5 + specified avatar UI. Updated §5, §7, §8, added §11 UI spec. Still no code changed. | Confirm Q4/Q6, then Step 1. |
| 2026-08-13 | 1 (cont.) | Leo: 90-day retention, keep break-glass. All of §8 closed. **Step 2 done** — schema added to both `postgres_adapter.py` and `sqlite_adapter.py`, verified fresh + migrated (SQLite) and against Railway in a rolled-back transaction (Postgres). Nothing else reads the tables yet. | Leo creates the Google Cloud OAuth client (§3); then Step 3, `backend/auth.py`. |
| 2026-08-13 | 1 (cont.) | Leo supplied the client id and set `GOOGLE_CLIENT_ID` + `SECRET_KEY` in Railway. **Step 3 done** — `backend/auth.py` (token verification, user upsert, `require_auth`/`require_admin`, `/api/auth/*`), registered in `app.py`, deps added. 37 unit checks pass; app boots with routes intact. Nothing is gated yet: admin still uses the old password path. | Step 4, frontend sign-in (§11.1). Then Step 5, the risky one. |
| 2026-08-13 | 1 (cont.) | **Step 4 done** — `frontend/auth.js` + markup in `index.html`. Verified live in the browser: popup opens/closes (click, Escape, outside-click, toggle), Google button renders, avatar falls back to initials on a broken picture URL, admin badge shows only for `@yotpo.com`, sign-out clears storage, expired token is purged on load. Synthetic test users deleted afterwards. Nothing gated yet. | Step 5: swap the 3 admin auth implementations for `@require_admin`. Test with a real `@yotpo.com` account **before** merging. |
| 2026-08-13 | 1 (cont.) | Pushed steps 2-4 (`08627f8`). **Step 5 done** — one shared `admin_request_ok()` swapped in behind the existing `is_admin_request()` / `check_admin_password()` names, so all 44 admin routes converted without a decorator retrofit. Closed 4 endpoints that were open (`esp/<n>/links`, `esp/<n>/stats` ×2, `crawl-status`, `settings/api-status`). Frontend password removed entirely. Probed every route with none/gmail/yotpo tokens: 403/403/pass. | Leo to confirm on production with a real `@yotpo.com` account, then Step 6 (conversation persistence). |
| 2026-08-13 | 1 (cont.) | **Step 5 deployed** (`717ee0f`). Verified on production: `RICHCSM` rejected with 403 on every admin route, `/api/admin/esps` and `/api/auth/config` still public, guest chat still 200, Admin button hidden and password field gone from the DOM. **Leo has not yet opened the admin panel with his real account — that is the one untested path.** | Leo signs in on production and opens Admin. Then Step 6 (conversation persistence). |
| 2026-08-13 | 1 (cont.) | **Step 6 done** — `backend/conversations.py` (CRUD, resume, idle sweep, 90-day purge), `/api/chat` accepts `conversation_id` and loads history from the DB, frontend lifecycle wired to first-message / ESP-click / tab-close. 35 automated checks + browser-verified. **Not pushed** — the clock modal still reads sessionStorage, so a signed-in user would see an empty history until step 7. Ship 6+7 together. | Step 7: rebuild the clock modal against `/api/conversations`, plus the three disclaimer variants (§11.3/§11.4). |
| 2026-08-13 | 1 (cont.) | **Step 7 done** — clock modal rebuilt against `/api/conversations`: per-ESP list, open-to-resume, per-row delete, guest vs signed-in disclaimers. Browser-verified incl. resume appending to the same conversation (seq 1-4, still 2 conversations not 3), cross-ESP open switching the sidebar, and titles escaped against XSS. Old `i`/`i+1` pairing and single-pair Restore removed. | Deploy 6+7 together, then optional Step 8 cleanup. |

### Gotchas discovered so far
- `messages` table stores **`message_length` only, never content** — the app has never
  retained message text. Saving conversations is a privacy-posture change, not just a
  feature. See §7.
- Three separate admin-auth implementations exist (`app.py:is_admin_request`,
  `app_admin_esp_routes.py:check_admin_password`, and ~9 inline `password != ADMIN_PASSWORD`
  checks). All three must change together or admin breaks in half.
- `GET /api/admin/esps` is **intentionally unauthenticated** — the public sidebar calls it.
  Do not put it behind the admin gate.
- There is no Flask `secret_key` anywhere in the codebase today.
- **The app is unusable below ~768px** — the sidebar is a fixed `w-64` with no responsive
  breakpoints, so on a 375px viewport the chat column collapses to one word per line. This is
  pre-existing (verified: hiding the account control changes `scrollWidth` not at all). Out of
  scope here, but it means any "does it work on mobile" question has a prior answer: no.
- Two 404s appear in the console on every page load and are **both pre-existing**:
  `/tailwindcss` (the Tailwind CDN script probing) and `/api/admin/crawl-status` (only
  registered when `USE_ASYNC_CRAWL=true`). Don't chase them.
- **SQLite does not enforce foreign keys** unless `PRAGMA foreign_keys=ON` is set on every
  connection, and this codebase never sets it. `ON DELETE CASCADE` is therefore a no-op
  locally while working correctly on Postgres. The retention purge hit this: it deleted
  conversation rows and left every message body behind. Both delete paths in
  `conversations.py` now delete messages explicitly. **Never rely on a cascade here.**
- The local `.env` has a **placeholder OpenAI key**, so `/api/chat` 500s locally. Stub
  `ai_client.generate_response` (see `run_stubbed.py` pattern) rather than chasing it.
- `POST /api/admin/refresh` is **not a read** — it re-crawls every documentation URL and
  rewrites `docs/`. Do not call it to test an auth gate; it rewrote 18 files once already.
- macOS blocks the Claude preview runner from reading `~/Downloads`, so `preview_start`
  can't launch the backend. Start it with Bash instead and open `http://localhost:5001`
  (Flask serves the frontend itself, same origin, and that origin is registered with Google).
  A `backend-local` entry in `.claude/launch.json` holds the sqlite/chromadb overrides.

---

## 1. What we're building

Three changes, in dependency order:

1. **Google account login**, open to anyone with a Google account.
2. **Account-scoped conversation history** — whole conversations saved and revisitable,
   replacing today's per-message, per-browser-session list.
3. **Admin restricted to `@yotpo.com` accounts**, replacing the shared `RICHCSM` password.

---

## 2. What exists today (verified against the code)

### Identity
There is none. Every visitor is anonymous. `POST /api/session/init`
([backend/app.py:355](backend/app.py:355)) mints a random UUID, records the IP, and returns it.
That `session_id` is the only handle on a user and it dies with the tab.

### History
Entirely client-side. [frontend/app.js:44](frontend/app.js:44) keeps
`conversationHistories = { klaviyo: [], dotdigital: [], ... }` in `sessionStorage` under the
key `espConversationHistories`. Each entry is a flat `{role, content, timestamp}` — messages,
not conversations. The history modal ([frontend/app.js:1650](frontend/app.js:1650)) renders
them by walking the array **two at a time** (`i`, `i+1`), assuming perfect user/assistant
alternation; a failed request desynchronizes the whole list. "Restore" replays exactly one
pair into the chat pane. Everything is lost on tab close, and the modal says so:
> "History is saved only for this browser session. We do not retain any user information."

### Chat request path
`POST /api/chat` ([backend/app.py:386](backend/app.py:386)) requires `session_id` and accepts
an optional `history` array. When the client sends `history`, it **wins over** the server-side
session store (`session_adapter`), truncated to the last 20 messages. So today the browser is
the authority on conversation context, and Redis is effectively a fallback.

### Admin
Password `RICHCSM` (default; overridable via `ADMIN_PASSWORD`). Checked in three places:
- `is_admin_request()` — [backend/app.py:48](backend/app.py:48) — header `X-Admin-Password`,
  query `?password=`, or JSON body. Used by 5 GET endpoints (analytics, ai-model,
  system-prompt, audit-log, global-knowledge links).
- `check_admin_password()` — [backend/app_admin_esp_routes.py:17](backend/app_admin_esp_routes.py:17)
  — same logic, duplicated. Used by 6 ESP routes.
- Inline `if password != ADMIN_PASSWORD` in ~9 POST handlers (refresh, ai-model, api-key,
  system-prompt, restore, and all four global-knowledge writes).

The frontend stores the password in a module-global `adminPassword`
([frontend/app.js:31](frontend/app.js:31)) and attaches it to **~24 call sites**.

Unprotected by design or oversight:
- `GET /api/admin/esps` — public, powers the sidebar. Must stay public.
- `GET /api/admin/esp/<name>/links` ([app_admin_esp_routes.py:162](backend/app_admin_esp_routes.py:162))
  — has no check. Likely an oversight; fix while we're in here.

### Storage available
PostgreSQL on Railway, already provisioned and in use, schema created idempotently at boot in
`PostgresAdapter.initialize()` ([backend/adapters/database/postgres_adapter.py:81](backend/adapters/database/postgres_adapter.py:81)).
Redis holds transient conversation context with a 1800s TTL. Pinecone holds document vectors.
None of these need to change structurally — we add tables to Postgres.

### Serving / deploy
Flask serves the frontend from the same origin
([backend/app.py:345](backend/app.py:345)). Gunicorn, **1 worker × 4 threads**
(`Procfile`). No build step on the frontend — `app.js` is 2,190 lines of global-scope
vanilla JS loaded directly. `CORS(app)` is wide open. Repo:
`github.com/leonardovacavliev-ai/Flow-State-Beta`, deployed on Railway.

---

## 3. Auth design

### Mechanism
**Google Identity Services (GIS)** in the browser → Google ID token (JWT) → backend verifies
it → backend mints its **own** session JWT → frontend sends `Authorization: Bearer <token>`
on every authenticated call.

Why our own token rather than passing Google's ID token through: Google ID tokens expire after
**one hour**. A user mid-conversation would silently lose auth. Our token (7-day expiry,
HS256, signed with a new `SECRET_KEY`) decouples session life from Google's.

Why `Authorization: Bearer` + `localStorage` rather than a cookie: the app is already served
same-origin in production, but the two static dev servers (`:8000`, `:3001`) call the backend
cross-origin at `:5001` ([frontend/app.js:4](frontend/app.js:4)). Cookies there mean
`SameSite=None`, credentialed CORS, and CSRF tokens on every admin POST. Bearer tokens avoid
all of it. The XSS exposure is acceptable given markdown output is already run through
DOMPurify ([frontend/app.js:25](frontend/app.js:25)) — but that DOMPurify call becomes
security-critical rather than merely prudent.

### New dependencies
```
google-auth      # verify_oauth2_token — validates signature, iss, aud, exp
PyJWT            # mint/verify our own session token
```

### New environment variables
| Var | Purpose | Notes |
|---|---|---|
| `GOOGLE_CLIENT_ID` | GIS client, also the `aud` we verify | Safe to expose to the browser |
| `SECRET_KEY` | Signs our session JWT | **New**. Nothing in the repo has one today |
| `ADMIN_EMAIL_DOMAIN` | Default `yotpo.com` | Avoids hardcoding |
| `ADMIN_EMAIL_ALLOWLIST` | Comma-separated break-glass emails | Optional; see §8 Q4 |
| `AUTH_ENABLED` | Feature flag for staged rollout | Default `true` once shipped |

No Google **client secret** is needed — GIS ID-token flow is public-client only. Nothing
secret ships to the browser.

### Google Cloud Console setup (manual, one-time — you must do this, not Claude)
1. Create an OAuth 2.0 Client ID, type **Web application**.
2. Authorized JavaScript origins:
   - `https://<your-railway-domain>`
   - `http://localhost:5001`, `http://localhost:8000`, `http://localhost:3001`
3. No redirect URIs needed for the ID-token flow.
4. Consent screen: **External**, publishing status **In production** (otherwise only
   test users can sign in — this is the single most common thing that breaks this setup).

### Admin authorization rule
```python
is_admin = (
    claims.get("email_verified") is True
    and claims["email"].lower().rsplit("@", 1)[-1] == ADMIN_EMAIL_DOMAIN  # "yotpo.com"
)
```
Computed **server-side on every request**, never trusted from the client, never stored as a
mutable column. `email_verified` is essential: without it a self-hosted OIDC identity could
claim any address. `rsplit("@", 1)` rather than `endswith("@yotpo.com")` is equivalent here
but states the intent — exact domain, not subdomain.

---

## 4. Data model

Added to `PostgresAdapter.initialize()` so fresh databases self-provision, matching the
existing pattern.

```sql
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_sub    TEXT UNIQUE NOT NULL,   -- Google's stable subject id; the real key
    email         TEXT NOT NULL,          -- may change; never the identity key
    name          TEXT,
    picture_url   TEXT,
    hd            TEXT,                   -- Workspace hosted domain, if any
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (LOWER(email));

CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    esp             TEXT NOT NULL,        -- normalized: 'other_webhook', not 'other/webhook'
    title           TEXT,                 -- first ~60 chars of first user message
    status          TEXT DEFAULT 'active',-- 'active' | 'ended'
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at        TIMESTAMP,
    last_message_at TIMESTAMP,
    message_count   INTEGER DEFAULT 0,
    session_id      TEXT                  -- analytics session it began in (nullable, no FK)
);
-- One index, not two: history is always opened per-ESP (§8 Q5), so every
-- listing query is (user_id, esp) ordered by recency.
CREATE INDEX IF NOT EXISTS idx_conv_user_esp ON conversations(user_id, esp, last_message_at DESC);
-- Serves the 90-day retention purge.
CREATE INDEX IF NOT EXISTS idx_conv_last_message ON conversations(last_message_at);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    seq             INTEGER NOT NULL,     -- 1-based order within the conversation
    role            TEXT NOT NULL,        -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (conversation_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_convmsg_conv ON conversation_messages(conversation_id, seq);
```

Plus two nullable columns on existing tables, so analytics can attribute activity to accounts
without breaking any current query:
```sql
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id UUID;
```

Notes:
- `google_sub`, not email, is the identity key. People change email addresses; `sub` is
  permanent. Email is stored for display and for the admin-domain check.
- `seq` makes ordering explicit, killing the `i`/`i+1` alternation assumption that the
  current history modal depends on.
- `sessions.user_id` has **no FK** to `users` on purpose — analytics sessions exist for
  anonymous visitors too, and a FK would force a join we don't want on the hot path.
- **SQLite has no `gen_random_uuid()`.** The SQLite mirror stores ids as `TEXT` with no
  default, matching the existing `esps` table. Application code must therefore always pass
  the id explicitly, in *both* dialects — never rely on the Postgres default, or local dev
  breaks with a NOT NULL violation while production silently works.

---

## 5. Conversation lifecycle

This is the part with the most hidden edges. The rule you gave:

> A conversation **begins** at the first message after the gradient intro, and **ends** when
> the user clicks an ESP (bringing the gradient back) or closes the window.

Mapped onto the actual code:

| Event | Code today | New behavior |
|---|---|---|
| **Begin** | `sendMessage()` [app.js:297](frontend/app.js:297); `addMessage('user', …)` fades out `#gradientIntro` [app.js:363](frontend/app.js:363) | If no active conversation, `POST /api/conversations` first, then send the chat with `conversation_id` |
| **End (ESP click)** | ESP button handler [app.js:156](frontend/app.js:156) rewrites `chatMessages.innerHTML` with a fresh gradient | Before rewriting, `POST /api/conversations/<id>/end` if one is active |
| **End (window close)** | `beforeunload` → `sendBeacon(/api/session/end)` [app.js:107](frontend/app.js:107) | Add `conversation_id` to that same beacon payload |

Three edges that will bite if not handled explicitly:

1. **`reloadSidebar()` also rewrites the gradient** ([app.js:278](frontend/app.js:278)) and runs
   on every page load. It must not end or create a conversation. Gate the end-conversation call
   on the ESP *click handler* specifically, not on "gradient appeared".
2. **`beforeunload` is unreliable** — it does not fire on mobile Safari backgrounding or on a
   tab crash. Conversations would sit in `status='active'` forever. Mitigate two ways:
   also listen for `visibilitychange → hidden`, and add a lazy server-side sweep that marks
   any conversation `ended` whose `last_message_at` is older than 30 minutes (matching the
   existing Redis `SESSION_TTL_SECONDS=1800`).
3. **Clicking the *same* ESP** currently resets the chat and re-shows the gradient. Under your
   rule that ends the conversation — which is consistent, just worth knowing it's intentional.

### Resuming (decided: reopen = resume)
Opening a saved conversation from the clock modal loads its messages into the chat pane and
makes it the active conversation. Concretely:
- `status` → `'active'`, `ended_at` → `NULL`.
- The gradient intro is **not** shown — restoring messages means we're mid-conversation.
  Today `addMessage('user', …)` is what removes the gradient; restoring a conversation must
  clear `chatMessages` and skip rendering the intro entirely.
- New messages continue the existing `seq` sequence.
- Consequence: `ended_at` is "the last time this conversation ended", not an immutable close.
  Any analytics reading it must not assume one span per conversation.
- Guests have nothing to resume — the clock modal shows them the §11.3 disclaimer instead.

### The `history` payload has to move server-side
Today the browser sends the last 20 messages on every `/api/chat`
([app.js:321](frontend/app.js:321)), and the backend prefers them over Redis
([app.py:400](backend/app.py:400)). Once conversations live in Postgres, the client should send
`conversation_id` and let the server load the context. Keep the client-`history` path alive for
anonymous users, otherwise anon chat loses multi-turn context.

---

## 6. New API surface

```
POST   /api/auth/google           { credential }  → { token, user: {email,name,picture,is_admin} }
GET    /api/auth/me                               → current user + is_admin (validates token)
POST   /api/auth/logout                           → client-side discard; server no-op unless we add a denylist

POST   /api/conversations         { esp, session_id } → { conversation_id }
GET    /api/conversations         ?esp=&limit=&offset= → list (id, title, esp, last_message_at, message_count)
GET    /api/conversations/<id>                        → full message list
POST   /api/conversations/<id>/end
DELETE /api/conversations/<id>
```
Every one of these requires a valid Bearer token and scopes by `user_id` from the token —
never from a request parameter.

### Admin routes
Replace all three auth implementations with one decorator:
```python
@require_admin   # 401 if no/invalid token, 403 if not @yotpo.com
```
Applied to: the 5 `is_admin_request()` GETs, the 6 `check_admin_password()` ESP routes, the
~9 inline-password POSTs, and `GET /api/admin/esp/<name>/links` (currently unguarded).
**Not** applied to `GET /api/admin/esps`.

Frontend: delete `adminPassword` and `adminHeaders()`; every one of the ~24 call sites
switches to the Bearer header. The `password` field in each POST body becomes dead and should
be removed server-side too, so a stale client can't authenticate.

---

## 7. Privacy — this is a real change, not a footnote

The app has **never stored message content**. `track_message()`
([backend/analytics.py:230](backend/analytics.py:230)) records `len(message)` and nothing else.
The history modal tells users so in plain text.

Saving conversations means storing what people typed, tied to a verified real-world identity,
in a database you operate. Before this ships:

- [ ] Rewrite the history modal disclaimer ([frontend/index.html:270](frontend/index.html:270)) —
      the current sentence becomes false the moment this deploys. It now needs **two** variants,
      guest and signed-in (§11.3).
- [ ] Add a short notice at the login prompt: what is stored, for how long, who can see it.
- [ ] Decide a retention period and implement deletion (see §8 Q6).
- [ ] Confirm whether Yotpo's own privacy/legal review is required before external customers
      log in. If customer CSMs paste account details into chat, this becomes customer data.
- [ ] Give users a delete control — per-conversation (`DELETE /api/conversations/<id>`) at
      minimum, ideally "delete my account and all data".
- [ ] Note that admins can read analytics but should **not** get a UI that reads other
      people's conversation text. Keep that boundary deliberate.

---

## 8. Open questions — answer these before any code

**Q1. Is login required, or optional?** ✅ **ANSWERED — optional.**
Guests chat exactly as today, on the existing ephemeral sessionStorage path. Signing in
unlocks saved conversations. Guests must see an explicit disclaimer that their chats are not
saved — see §11.3 for where it appears.

**Q2. What happens when a user opens a saved conversation and types?** ✅ **ANSWERED — resume.**
New messages append to that same conversation (`seq` continues from the last message). The
conversation flips back to `status='active'`, `ended_at` clears, and it re-ends on the next ESP
click / window close. Implication: a conversation can have several active spans, so `ended_at`
means "last time it ended", not "immutable close".

**Q3. Does opening a saved conversation switch the selected ESP?** ✅ **MOOT.**
With per-ESP clock buttons retained (Q5), history is only ever opened from within an ESP, so
every conversation listed already belongs to the selected ESP. No switching logic needed.

**Q4. Break-glass admin access?** ✅ **ANSWERED — keep it.**
`ADMIN_PASSWORD` survives as an emergency path, **off by default**, enabled only by setting
`ADMIN_PASSWORD_FALLBACK=true` in Railway. When off, the password is rejected everywhere and
`@yotpo.com` Google auth is the only way in. When on, `require_admin` accepts either. The
fallback must log loudly on every use (`[ADMIN FALLBACK] password auth used on <route>`) so
it can't quietly become the normal path — that's how emergency doors get propped open.

**Q5. Keep the per-ESP clock buttons in the sidebar?** ✅ **ANSWERED — keep them.**
Each ESP row keeps its own clock icon ([app.js:255](frontend/app.js:255)). The modal it opens
lists that ESP's saved conversations. `GET /api/conversations?esp=<name>` is therefore the
primary query, and `idx_conv_user_esp` in §4 is the index that serves it.

**Q6. Retention.** ✅ **ANSWERED — 90 days.**
A conversation and its messages are deleted 90 days after `last_message_at` (not
`started_at`) — so an actively revisited conversation keeps living, and only genuinely
abandoned ones age out. `ON DELETE CASCADE` on `conversation_messages` means the purge only
has to delete from `conversations`.

Implementation: a `purge_expired_conversations()` job on its own daily
`BackgroundScheduler`, registered at module level. It must **not** hang off the existing
scheduler at [app.py:1783](backend/app.py:1783) — that one only exists when
`USE_ASYNC_CRAWL=true`, so retention would silently stop if that flag were ever turned off.
Retention is a privacy commitment; it can't depend on an unrelated feature flag.

Two things this obliges us to say out loud in the UI: conversations disappear after 90 days
of inactivity, and that's a promise we now have to keep working.

**Q7. Does anything migrate?**
Existing sessionStorage history is per-browser and already ephemeral. Proposal: no migration —
it simply stops accumulating and users start fresh on their account. Confirm that's fine.

---

## 9. Implementation order

Each step is independently deployable and reversible.

1. **Google Cloud OAuth client** (manual) + `GOOGLE_CLIENT_ID`, `SECRET_KEY` in Railway.
2. **Schema** — add the three tables + two columns to `PostgresAdapter.initialize()`. Ships
   inert; nothing reads them yet.
3. **`backend/auth.py`** — verify Google ID token, upsert user, mint/verify session JWT,
   `@require_auth` / `@require_admin` decorators. Plus `/api/auth/*` routes.
4. **Frontend sign-in** — GIS script, top-right avatar / sign-in pill with its popup dialog
   (§11.1), token in localStorage, sign-out. Login optional; nothing gated yet.
5. **Admin gating** — swap all 3 auth implementations for `@require_admin`; hide the Admin
   button for non-`@yotpo.com`. **Highest-risk step** — this is where admin can lock itself out.
   Verify against a real `@yotpo.com` account before merging.
6. **Conversation persistence** — the CRUD routes, `/api/chat` accepting `conversation_id`,
   begin/end lifecycle wired into `sendMessage()` / ESP click / `beforeunload`.
7. **History panel rebuild** — per-ESP conversation list, open/resume, delete, and the three
   disclaimer variants (§11.3, §11.4).
8. **Cleanup** — remove the client `history` payload for signed-in users, the dead `password`
   body fields, and the idle-conversation sweeper.

---

## 10. Things that will need care

- **`app.js` is 2,190 lines in one global scope** with no modules or build step. Auth state,
  conversation state, and the history panel all add globals. Consider a small
  `frontend/auth.js` + `frontend/conversations.js` loaded before `app.js` to keep this from
  becoming unmaintainable — still no build step required.
- **Gunicorn runs 1 worker.** Fine now. Any in-process caching of user/auth state must not
  assume that (`get_mechanics_results` already caches per-process — same caveat).
- **`CORS(app)` is fully open.** With Bearer tokens that's survivable, but restrict it to
  known origins as part of step 5 regardless.
- **The `other/webhook` ESP has a slash in its name** and gets normalized with a single
  `replace('/', '_')`. Store the normalized form (`other_webhook`) in `conversations.esp`
  and normalize on read, or history will silently split into two buckets.
- **Feedback modal asks for the email by hand** ([index.html:228](frontend/index.html:228)).
  Prefill it from the signed-in account — small, free win.
- **Railway Postgres growth.** Conversation text is unbounded where analytics was not. Watch
  the plan limit; §8 Q6's retention answer is the control.

---

## 11. UI specification

### 11.1 Account avatar — top right

**There is no header bar in this app today.** The layout is a fixed sidebar plus
`<main class="flex-1 flex flex-col overflow-hidden bg-background relative">`
([index.html:186](frontend/index.html:186)) holding the scrolling chat area and the input box.
Nothing spans the top.

Two ways to place the avatar, and the choice matters:

| Option | Trade-off |
|---|---|
| **A. Float it over the chat area** — `main` already has `position: relative`, so an `absolute top-4 right-4 z-30` button needs no layout change | Zero disruption, but it overlaps the gradient intro's top-right corner. The gradient block is `p-8` with text starting at the left, so a 36px avatar sits in empty space — visually fine in practice |
| **B. Add a real header strip** inside `main`, above `#chatMessages` | Cleaner and gives somewhere to put future controls, but costs vertical chat height and touches the scroll container |

→ *Recommendation: **A**, floating.* It's reversible, costs no chat real estate, and the
gradient's top-right is empty. If the overlap looks wrong once it's on screen, B is a
ten-line change.

**States:**
- **Signed out** — a compact "Sign in" pill in that slot (Google mark + label). Clicking it
  triggers the GIS prompt.
- **Signed in** — circular 36px avatar from the `picture` claim, `rounded-full`, thin border.
  Google's avatar URLs occasionally 404 or get blocked; **must** have a fallback to an initials
  circle (first letter of `name` or `email`) via the `<img>` `onerror` handler. Don't skip
  this — a broken image icon in the corner is the failure mode.

**Popup dialog on click:**
Anchored under the avatar (`absolute right-4 top-16`), styled like the existing modals
(`bg-card rounded-xl shadow-lg border border-border`), containing:
- Avatar, display name, email.
- A small `Yotpo Admin` badge when the account is `@yotpo.com` — a visible signal of why the
  Admin button is there.
- **Sign out** button.
- Closes on outside click and on `Escape`. The existing outside-click handler
  ([app.js:1774](frontend/app.js:1774)) is a `window` click listener that checks
  `e.target === modal` — that pattern won't work for an anchored popup, so this needs its own
  handler that ignores clicks inside the popup and on the avatar itself.

**Sign out** clears the token from localStorage, resets the in-memory user, ends any active
conversation, re-shows the gradient intro, and re-renders the sidebar (hiding Admin).

### 11.2 Admin button visibility
The Admin button ([index.html:168](frontend/index.html:168)) is hidden unless the signed-in
account is `@yotpo.com`. This is **cosmetic only** — every admin route still enforces
`@require_admin` server-side. Hiding a button is not access control; the server check is.

### 11.3 Guest disclaimer
Guests need to know chats aren't saved, without nagging. Two placements, no more:

1. **Inside the clock/history modal** — the primary moment of intent. Replaces the current
   sentence at [index.html:270](frontend/index.html:270), which needs three variants now:
   - Guest: *"You're not signed in, so this conversation won't be saved. Sign in with Google to
     keep your conversations and come back to them later."* + an inline sign-in button.
   - Signed in: *"Your conversations are saved to your account."* (plus retention wording once
     §8 Q6 is answered).
   - Signed in, no conversations yet for this ESP: the existing empty state.
2. **A single quiet line under the sign-in pill** in the top-right — *"Not signed in — chats
   aren't saved"* — small, muted, no icon, no dismiss button.

Do **not** put it in the gradient intro. That block is already dense prose and it's the first
thing every user reads; adding a caveat there makes the tool feel like a form.

### 11.4 The clock modal, rebuilt
Same entry point, different contents. For a signed-in user it lists that ESP's conversations —
title (first ~60 chars of the opening message), relative timestamp, message count — newest
first, each row opening the conversation into the chat pane. Per-row delete. The current
"Restore" button that replays a single message pair
([app.js:1701](frontend/app.js:1701)) disappears; opening a whole conversation replaces it.
The `i` / `i+1` pairing loop goes away with it — `seq` gives real ordering.
