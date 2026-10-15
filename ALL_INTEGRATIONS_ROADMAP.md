# Flow State v2: build map

**What this file is.** The step-by-step map from **v1** (today's app: 9 email/SMS platforms, commit
`feb29e5`) to the **finalised v2**: every Yotpo Loyalty and Reviews integration in
yotpo.com/integrations is either **live in chat**, answered by the prompt for its platform type, or
**listed** with the reason it isn't.

- **Why** each decision was made lives in [ALL_INTEGRATIONS_UPDATE.md](ALL_INTEGRATIONS_UPDATE.md)
  (plan v3, accepted 2026-10-13). This file is the **how and in what order**.
- **Written for Claude Code.** Each checkpoint lists what to read first, the exact tasks,
  deliverables, tests, acceptance checks, rollback, and where to stop for Leo.
- **Line numbers are hints** as of `feb29e5`. Find code by the function names given.

---

## 0. How to work from this file

1. **Each session:** read [NEXT_SESSION.md](NEXT_SESSION.md) (the last session's hand-off), then §1
   (rules), then §2 (status board), then the checkpoint you are on.
2. **Pick the next checkpoint:** the first `todo` row in §2 whose dependencies are all `done`.
   - 🛑 rows belong to Leo.
   - Claude Code only prepares their inputs, where the checkpoint says so.
3. **Branching:**
   - Use one branch per checkpoint: `v2/<id>-<slug>` (e.g. `v2/c1-1-schema`).
   - Use conventional commits and **open the PR yourself** (Leo, 2026-10-15: never ask him to).
     `gh` is not installed: use the GitHub REST API with the token `git credential fill` gives
     (never print it). NEXT_SESSION.md §4 has the commands.
   - **Claude Code merges and deploys** (Leo's decision, 2026-10-13). Railway deploys every push
     to `main`, so a merge is a deploy.
     - Merge only when the check suite is green, the whole diff has been reviewed, and every 🛑
       step the checkpoint puts before the merge is done. **GitHub Actions has never run on this
       repository** (0 workflow runs as of 2026-10-15, workflow active), so run §1.4 locally and
       say so in the PR. Don't stop to ask Leo between PR, merge and deploy: go, then report.
     - One PR at a time, in dependency order: `git merge --no-ff` into `main`, then push.
     - After each deploy, smoke-check the live site: `/api/health` answers and one Klaviyo chat
       answers. The admin panel needs Leo's Google sign-in, so ask him to open it.
     - If the smoke check fails, revert the merge commit on `main`, push at once, and tell Leo.
     - Data-changing scripts on production (§1.1) stay Leo's.
4. **Finishing a checkpoint:**
   - Every task box is ticked.
   - Every acceptance check passes, and its output summary is pasted into the PR.
   - The §2 row is updated (status, PR, date).
   - A line is added to §10 (change log).
5. **When reality disagrees with this file:**
   - Write it under the checkpoint's **Deviations** heading (add one if missing).
   - If a decision in ALL_INTEGRATIONS_UPDATE.md changes, update that file too.
   - Anything that changes what users see, or how the email/SMS platforms answer, needs Leo first.
6. **Stop and ask Leo when:**
   - a 🛑 step comes up;
   - an acceptance check fails for a reason outside the checkpoint;
   - a dependency needs adding;
   - a task would touch production data;
   - a task would change behaviour for the existing email/SMS platforms beyond what the checkpoint
     says.

Status values: `todo` · `doing` · `done` · `blocked (reason)`.

---

## 1. Ground rules (every checkpoint)

### 1.1 Production safety: production is one `.env` away

The local `.env` points at **production**:
- `DATABASE_PROVIDER=postgres` with the Railway `DATABASE_URL`;
- `VECTOR_DB_PROVIDER=pinecone`, index `esp-loyalty-docs1`.

So:

- **Never start the app with the plain `.env`.** `python3 backend/app.py` or `import app` with it
  runs boot DDL against production Postgres (`postgres_adapter.initialize`). Any crawl, paste,
  label edit or rebuild then writes production vectors.
- **To run the app locally,** use the `backend-local` launch configuration (`.claude/launch.json`:
  SQLite `local_dev.db`, memory sessions, sync crawl).
  - Also set **`VECTOR_DB_PROVIDER=chromadb`** before exercising any write path.
  - `eval/seed_local_db.py` copies the knowledge-base rows from production into `local_dev.db`
    (read-only on production).
- **Run the import smoke test like this** (env vars win over `.env`; `load_dotenv` does not
  override):
  ```bash
  cd backend && DATABASE_PROVIDER=sqlite SQLITE_DB_PATH=/tmp/smoke.db SESSION_PROVIDER=memory USE_ASYNC_CRAWL=false VECTOR_DB_PROVIDER=chromadb python3 -c "import app; print('ok')"
  ```
- **Postgres tests** run against `TEST_DATABASE_URL` (a local Docker Postgres, or the CI service),
  in a throwaway schema.
  - This follows the pattern in `test_crawl_pacing.py` / `test_analytics_providers.py`: schema
    `*_ci_test`, set through `search_path`.
  - Falling back to `.env`'s `DATABASE_URL` is allowed only with that schema isolation, as today.
- **Read-only against production is allowed** for the eval scripts that say so:
  - `retrieval_recall.py`
  - `check_context_unchanged.py` (vector reads; analytics go to temp SQLite)
  - `audit_product_labels.py` (no args)
  - `product_split_probe.py`
  - `seed_local_db.py`
- **Production writes are Leo's** (🛑): any `--apply` or `--write` flag, `rebuild-vectors`,
  `backfill --write`, `import_catalog.py --apply`, `activate_integrations.py --apply`, SQL fixes.
  Claude Code prepares them and shows the dry run.
- **Secrets:**
  - Never print, log or commit `.env` values. Redact them in any output pasted into a PR.
  - Never ask Leo to paste keys into chat.

### 1.2 Invariants that must hold after every checkpoint

| # | invariant | how it is checked |
|---|---|---|
| I1 | Every `esp_documents` row and every vector has a product label (`loyalty` · `reviews` · `shared`) | `add_document(…, *, product)` and the adapters refuse otherwise; `test_product_write_paths.py`; `eval/audit_product_labels.py` |
| I2 | The email/SMS platforms (`platform_type = 'messaging'`) get today's system prompt, byte for byte | after C1.7: `test_prompts_by_type.py` |
| I3 | Code-only changes leave the chat context byte-identical | `eval/check_context_unchanged.py capture` before, `check` after, back to back |
| I4 | Rows with `status != 'active'` never reach chat; older code never lists them | `esp_manager.list_esps` lists `status = 'active'` only; the admin sets `active` or `listed` (`archived` exists only on old rows, C1.4) |
| I5 | Schema changes are additive, idempotent and made at boot: `_add_missing_columns` / `CREATE … IF NOT EXISTS` in **both** `postgres_adapter.initialize` and `sqlite_adapter.initialize` | booting twice is a no-op; CI boots both |
| I6 | One integration key: `esps.name` (lowercase, underscores) everywhere — vectors, analytics, conversations, API, caches, deep links | `/api/chat` validation (C1.1) |
| I7 | Every string that reaches HTML from the database or the catalog is escaped (`escapeHtml` / `escapeAttr`, `app.js:12-19`) | code review checklist in each UI PR |
| I8 | Nothing new depends on Railway, and nothing new stores state on local disk | review; C1.8 removes what exists |
| I9 | Only Yotpo Loyalty & Referrals and Yotpo Reviews (incl. UGC) are in scope | catalog import ignores other products; header parser ignores SMS & Email and Subscriptions |

### 1.3 Conventions

- **Commits:** conventional, imperative, sentence case, as in `git log`. Examples:
  `feat: Validate the integration key on every chat request`;
  `fix: …`, `refactor: …`, `test: …`, `docs: …`, `chore: …`, `style: …`.
- **Python:** 3.11 (`runtime.txt`). The pinned dependencies need it: 77 pins require ≥ 3.10, so a local install on the Mac's 3.9 fails. Comments say *why*, at the density of `rag_context.py` and
  `crawl_queue.py`.
- **Tests:** plain scripts that run with `python3 path/to/test.py` **and** under pytest.
  - Follow `backend/test_product_write_paths.py` (env overrides before imports, temp SQLite, fake
    vectorizer) or `backend/test_crawl_pacing.py` (a `check()` harness, an optional `postgres`
    argument).
  - Fixtures go in `backend/fixtures/<topic>/`.
- **Frontend:** vanilla JS, no build.
  - New files are classic `<script>` tags in `index.html` with a `?v=` cache-buster bumped on every
    change.
  - No inline `onclick` in new code.
  - Escape per I7.
- **Dependencies:** none added without Leo's OK. Exception: the ones a checkpoint names (pinned).
- **New environment variables:** added to `.env.example` with a comment in the same PR.
- **Scripts that change data:** dry run by default; `--apply` to write; they print what they would
  change.

### 1.4 The check suite

Run what applies to the checkpoint, and always the first block.

```bash
# Pure and SQLite tests (no network, no production)
python3 backend/test_prompt_template.py
python3 backend/test_product_write_paths.py
python3 backend/test_conversation_seed.py
python3 backend/test_crawl_pacing.py              # pure part
python3 backend/test_analytics_providers.py sqlite
python3 eval/test_product_scorer.py
python3 backend/test_integrations_schema.py
# Import smoke test: §1.1 command

# Postgres-backed (TEST_DATABASE_URL, throwaway schema)
python3 backend/test_crawl_pacing.py postgres
python3 backend/test_analytics_providers.py postgres
python3 backend/test_integrations_schema.py postgres  # TEST_DATABASE_URL only

# Read-only against the live index (allowed)
python3 eval/check_context_unchanged.py capture /tmp/golden.json   # before the change
python3 eval/check_context_unchanged.py check   /tmp/golden.json   # after, back to back
python3 eval/retrieval_recall.py
python3 eval/audit_product_labels.py
```

Not part of the suite:
- `backend/test_async_crawl.py` hits a running server with an obsolete password.
- `backend/test_pinecone.py` and `backend/test_postgres.py` are live connectivity smoke tests.

---

## 2. Status board

| ID | checkpoint | depends on | owner | size | status | PR / notes |
|---|---|---|---|---|---|---|
| C0.1 | CI baseline | — | dev | 1–2 d | done | PR #2, merged and deployed 2026-10-13 |
| C0.2 | Pin dependencies | 🛑 production `pip freeze` | dev + 🛑 | ½ d | done | PR #1, deployed 2026-10-13; health, Klaviyo chat, admin panel and a crawl OK |
| C0.3 | Chat hardening: rate limit, daily cap, retrieval errors | C0.1 | dev | 2 d | todo | |
| C0.4 | 13 missing email/SMS platforms (content) | — | 🛑 Leo (dev prepares sources) | 13–20 h | doing | sources approved by Leo and merged 2026-10-15 (PR #4, `docs/integrations/messaging_sources.md`); next: Leo creates the platforms |
| C1.1 | Schema, canonical key, URL normalisation | C0.1 | dev | 3–4 d | done | PR #3, deployed 2026-10-13; URL fix and key rename applied by Leo |
| C1.2 | Document360 header parser + catalog import (dry run) | C1.1 | dev | 4–5 d | done | PR #5, merged and deployed 2026-10-15; adds partner mechanics (Leo's design); report `docs/integrations/catalog_dry_run.md`, read by Leo |
| C1.3 | Refresh pipeline: hash skip, Document360 extraction, sitemap job, retirement | C1.1, C1.2 | dev | 3–4 d | todo | |
| C1.4 | Admin: integrations, proposals inbox, crawl summary, roles | C1.1, C1.2 | dev | 5–6 d | done | PRs #6–#9, merged and deployed 2026-10-15; follow-ups from Leo's review (wording, popups, no tier, two states, products from documents, crawl box) in Deviations; live checks OK |
| C1.5 | Chat: integration picker, `/api/integrations`, copy by type | C1.1 | dev | 5–6 d | todo | |
| C1.6 | Reviews readiness | C1.1 | dev + 🛑 | 2–3 d + 4–6 h | todo | |
| C1.7 | System prompt per platform type + facts block | C1.1 | dev + 🛑 read drafts | 4–5 d | doing | branch `v2/c1-7-prompts-by-type`; built, tested, golden check 26/26 identical; next: PR, merge, deploy; then Leo reads the four drafts (Admin → General Settings → Kind of platform) |
| C1.8 | Portability seams, Sentry, no local disk | C1.3 | dev + 🛑 | 3–4 d | todo | |
| C1.9 | Production import, approvals, labelling | C1.2–C1.8 deployed | 🛑 Leo | 4–6 h | todo | |
| C1.10 | "Find links" for one integration | C1.3, C1.4 | dev + 🛑 model budget | 2–3 d | todo | Leo, 2026-10-15: needed for a complete product |
| R1 | Routine: re-run the catalog import | C1.9 | 🛑 Leo (dev prepares) | ~1 h each | from C1.9, every 1–2 months | Leo, 2026-10-15; §7 Routines |
| — | **Stage 1 exit gate** (§5 end) | C1.1–C1.9 | dev + 🛑 | — | todo | |
| C2.0 | Trap-question eval tool | C1.7 | dev | 1–2 d | todo | |
| C2.1 | Wave: `storefront` | C2.0, Stage 1 gate | dev + 🛑 | 3–4 d + 9–15 h | todo | |
| C2.2 | Wave: `service` | C2.1 | dev + 🛑 | 3–4 d + 9–15 h | todo | |
| C2.3 | Wave: `content` | C2.2, C1.6 | dev + 🛑 | 3–4 d + 9–15 h | todo | |
| C2.4 | Wave: `data` (+ Yotpo API & Webhooks moves to `data`) | C2.3 | dev + 🛑 | 3–4 d + 9–15 h | todo | |
| C2.5 | Deep links + per-answer thumbs | C2.1 | dev | 2 d | todo | |
| C2.6 | Gate `GET /api/admin/esps` | C1.5 in production ≥ 1 release | dev | ½ d | todo | |
| C2.7 | Messaging context upgrade (facts block, source headers) — optional | C1.7 | dev + 🛑 | 1–2 d | todo | |
| C2.8 | Finalisation: docs, cleanup, archive | C2.4 | dev | 1–2 d | todo | |
| CX.1 | Embedding bake-off and index rebuild — triggered only | C1.6 | dev + 🛑 | 1–2 w | not scheduled | |
| CX.2 | Separate worker process before the move — triggered only | C1.8 | dev + 🛑 | ½ d | not scheduled | |
| CX.3 | CPU-only torch: drop the unused CUDA stack — triggered only | C0.2 | dev + 🛑 | ½ d | not scheduled | |

---

## 3. Dependency map

```
Stage 0   C0.1 CI ──┬─────────────────────────────────────────────┐
          C0.2 pin  │   C0.3 hardening ◄─ C0.1                    │
          C0.4 🛑 content (independent; can start today)          │
                    ▼                                             │
Stage 1   C1.1 schema/keys ─┬─► C1.2 header+import ─┬─► C1.3 refresh ──► C1.8 portability
                            │                       │      └─────────┬─► C1.10 find links
                            │                       └─► C1.4 admin ──┘
                            ├─► C1.5 chat picker
                            ├─► C1.6 Reviews readiness
                            └─► C1.7 prompts by type ──► C2.0 trap eval
          C1.2–C1.8 deployed ─► C1.9 🛑 import + approvals ─► Stage 1 exit gate
Stage 2   C2.1 storefront ─► C2.2 service ─► C2.3 content (needs C1.6) ─► C2.4 data ─► C2.8 final
          C2.5 deep links + thumbs (after C2.1) · C2.6 gate old route · C2.7 messaging context (optional)
```

Order inside Stage 1:
- C1.4, C1.5, C1.6 and C1.7 can run in parallel branches once C1.1 is merged.
- C1.4 needs C1.2's proposals table.
- C1.8 waits for C1.3, because both touch the crawl path.
- C1.10 waits for C1.3 (its sitemap table finds Yotpo guides for integrations the catalog doesn't
  list) and C1.4 (results land in its inbox). C1.9 does not wait for C1.10.

---

## 4. Stage 0 — quick wins

### C0.1 CI baseline

**Goal:** every later checkpoint is a refactor of a codebase with no CI; add it first.

**Read first:** the check suite (§1.4); headers of `backend/test_crawl_pacing.py` and
`backend/test_analytics_providers.py` (how they find `DATABASE_URL`).

**Tasks**
- [x] `.github/workflows/ci.yml`, on pull requests and pushes to `main`:
  - [x] **job `unit`:** Python 3.11; pip cache; `pip install -r backend/requirements.txt` (with
    `-c backend/constraints.txt` once C0.2 lands); run the pure and SQLite block of §1.4 plus the
    import smoke test.
    - Set `VECTOR_DB_PROVIDER=chromadb`, `DATABASE_PROVIDER=sqlite`, `SESSION_PROVIDER=memory` for
      the whole job.
    - Cache the sentence-transformers model directory.
  - [x] **job `postgres`:** service container `postgres:16`; `TEST_DATABASE_URL` pointing at it;
    run the two Postgres-backed tests.
- [x] Both Postgres tests read `TEST_DATABASE_URL` first, then fall back to today's `.env` lookup.
  This is a small change at the top of each file.
- [x] Make sure no test needs network access: Pinecone, Google, ipapi.co. Stub any that does, as
  `test_product_write_paths.py` stubs the vectorizer.

**Deliverables:** `.github/workflows/ci.yml`; the two test files updated.

**Acceptance**
- A PR with these changes shows both jobs green.
- A deliberately broken assertion on a scratch branch turns `unit` red. Delete the branch afterwards.

**Rollback:** delete the workflow file.

**Deviations (2026-10-13)**
- **Stacked on C0.2.** CI installs with `-c backend/constraints.txt` from the start, so the branch
  is cut from `v2/c0-2-pin-dependencies`. On `main`'s unpinned `requirements.txt`, CI would test
  whatever PyPI serves that day. Merge C0.2 first.
- **One stale assertion fixed.** `test_analytics_providers.py` expected the last sparkline date
  to be today. Since `f0c5e92` the sparkline has weekly buckets labelled by their first day, so the
  last one starts six days ago. The test changed; `analytics.py` did not.
- **Network, found by running the suite with outbound sockets blocked:**
  - `test_analytics_providers.py` called ipapi.co through `create_session`. It is stubbed now.
  - The embedding model (`all-MiniLM-L6-v2`) is checked against huggingface.co on every load.
    CI downloads it once into an `actions/cache` entry and runs every test with
    `HF_HUB_OFFLINE=1`.
  - Nothing else connects. The `postgres` job needs no model.
- **Verified locally:**
  - The `unit` job passes from a clean checkout, with no `.env`, network blocked and the model
    offline. This ran on Python 3.9 with the packages already installed, not the 3.11 pins.
  - The Postgres tests did not run. There is no local Docker, and the `.env` fallback creates a
    schema on production. They run first in CI.
- **CI cost:** the pinned `torch` pulls the CUDA stack (several GB) into both jobs. The pip cache
  absorbs most of it after the first run. If CI time becomes a problem, that is a CX.3 trigger.

### C0.2 Pin dependencies

**Goal:** freeze what production runs today, so every later change upgrades nothing by accident.
`requirements.txt` is unpinned (PRODUCT_LINE_SPLIT_SCOPE.md: `pinecone` 10.x is a rewrite;
production may run an older one from the cached Docker layer).

**🛑 Leo:** get `pip freeze` from the running production container (Railway shell), or the resolved
versions from the last successful build log. Hand it over as a file. It contains no secrets.

**Tasks**
- [x] `backend/requirements.txt`: same package set, each pinned `==` to the production version.
- [x] `backend/constraints.txt`: the full freeze, transitive packages included.
- [x] `Dockerfile`: `pip install --no-cache-dir -r backend/requirements.txt -c backend/constraints.txt`.
- [x] CI uses the same flags (C0.1's workflow).

**Do not:** upgrade, add or remove any package here.

**Acceptance**
- CI is green.
- A local `docker build .` succeeds.
- After the deploy: `/api/health` responds, one Klaviyo chat answers, the admin panel loads,
  and one crawl completes.

**Rollback:** revert the PR. The cached layer stays valid.

**Findings (2026-10-13)**
- The production freeze has 158 packages. It contains all 17 direct dependencies.
- Several versions date from September 2026, so the install layer was rebuilt after `requirements.txt` last changed (2026-08-13).
- **Production already runs `pinecone==10.0.0`,** the rewrite PRODUCT_LINE_SPLIT_SCOPE.md worried about. The current code works on it.
- **Production installs the full NVIDIA/CUDA stack** (`nvidia-*`, `cuda-*`, `triton`). That is several GB, pulled in by `torch` from PyPI on Linux. Flow State never uses a GPU. See CX.3.
- **77 of the 158 pins need Python ≥ 3.10.**
  - Production and CI run 3.11. Leo's Mac runs 3.9.6.
  - A local `pip install` of the pinned files needs Python 3.11 (`runtime.txt`).
  - Packages already installed locally keep working.
- **Verified without Docker** (no Docker locally): every pin exists on PyPI, none is yanked, and each has a file installable on Linux with Python 3.11.
- **Still to verify:** the `docker build` (CI or Railway) and the post-deploy smoke check.

### C0.3 Chat hardening

**Goal:** close two gaps open since CODE_AUDIT_REPORT (2026-07-21) before the expansion attracts
traffic: no rate limit, and a raw 500 when retrieval fails.

**Read first:**
- `app.py:chat()` (229-367): `build_rag_context` sits outside the `try`, at 315-323.
- `adapters/session/redis_adapter.py`, for how Redis is reached.
- `frontend/app.js:sendMessage()` error branches (783-816).

**Tasks**
- [ ] `backend/rate_limit.py`:
  - Token bucket keyed by user id when signed in, otherwise by client IP (`request.remote_addr`,
    which is correct behind `ProxyFix`).
  - Redis when `REDIS_URL` is set; in-process dict otherwise.
  - Limits from env: `CHAT_RATE_PER_MINUTE` (default 10), `CHAT_RATE_PER_DAY` (default 200).
- [ ] Global daily cap:
  - `CHAT_DAILY_CAP` counts chat requests per UTC day in the same store (default unset, meaning no
    cap).
  - A `[SPEND]` warning is logged at 80% and at 100%.
  - `CHAT_DAILY_CAP_MODE=warn|block` (default `warn`). In `block` mode, over-cap requests get a 503
    with a plain message.
- [ ] `chat()`:
  - Check limits before any work. Over the limit → 429
    `{"error": "Too many questions in a short time. Try again in a minute."}`.
  - Wrap `build_rag_context` in its own `try`. On failure: log the traceback and return 503
    `{"error": "Search is unavailable right now. Try again in a minute."}`.
  - On failure, track no assistant message and append nothing to session history.
- [ ] Frontend `sendMessage()`: for 429 and 503, show the server's `error` text instead of the
  generic "Server error (…)".
- [ ] `.env.example`: the four new variables, with comments.
- [ ] `backend/test_chat_hardening.py` (SQLite, fake vectorizer, Flask test client, as in
  `test_product_write_paths.py`). It checks:
  - a burst over the limit gets 429;
  - a retrieval exception gets 503, and no assistant message is in the history or in the analytics
    queue;
  - the daily cap blocks only in `block` mode.

**Acceptance**
- Tests and CI are green.
- The golden check is unchanged. The context is unaffected, but `chat()` changed, so capture
  before and check after.

**Rollback:** revert. The new env variables are optional.

### C0.4 🛑 The 13 missing email and SMS platforms (content)

**Goal:** finish the `messaging` type. Today's prompt already fits it. The work is content, done in
the **existing admin**: Create ESP → Add link (with product) → Crawl Selected / Paste.

**Claude Code prepares** `docs/integrations/messaging_sources.md`. Per platform it lists:
- the Yotpo guide links from the table below;
- 1–3 candidate links to the platform's **own** documentation on journey/flow mechanics: trigger
  types, re-entry, delays, and which filters are re-evaluated at send time. Find them by browsing
  the official help centres; mark each `candidate` for Leo to approve.

| platform | catalog card(s) | products (catalog) | Yotpo / partner integration guide |
|---|---|---|---|
| Braze | `braze` | loyalty, reviews | `support.yotpo.com/docs/braze-integration-guide` |
| Cordial | `cordial` | loyalty | `…/integrating-yotpo-loyalty-referrals-with-cordial` |
| Drip | `drip` | reviews | `…/drip-integration-guide` |
| HubSpot | `hubspot` | reviews (catalog) | `…/hubspot-integration-guide-for-reviews` · `…/integrating-yotpo-loyalty-referrals-with-hubspot` |
| Insider | `insider` | loyalty, reviews | partner: `academy.useinsider.com/docs/external-platform-integrations-yotpo` · `…/sending-yotpo-data-to-insider` |
| Mailchimp | `mailchimp`, `mailchimp-loyalty` | loyalty, reviews | `…/mailchimp-integration-guide-for-reviews` · `…/mailchimp-integration-yotpo-loyalty-referrals` |
| Optimizely (Zaius) | `optimizely`, `optimizely-loyalty` | loyalty, reviews | partner: `apps.zaius.com/yotpo-swel` (thin; find better) |
| Optimove | `optimove` | loyalty | `…/optimove-integration-guide-for-yotpo-loyalty-referrals` (the catalog's link is dead; this is the renamed article) |
| Remarkety | `remarkety` | reviews | `…/remarkety-integration-guide` |
| Retention Science | `retention-science` | loyalty | `…/integrating-yotpo-loyalty-referrals-with-retention-science` |
| Rule | `rule` | loyalty | partner: `en.docs.rule.se/article/449-integrera-yotpo-loyalty-rewards-med-rule` (**in Swedish**; flag to Leo) |
| Sailthru | `sailthru` | loyalty | `…/integrating-yotpo-loyalty-referrals-with-sailthru` |
| Salesforce Marketing Cloud | `salesforce-marketing-cloud` | loyalty | `…/integrating-yotpo-loyalty-referrals-with-salesforce-marketing-cloud` |

**Leo:** creates the 13 ESPs, adds and labels each link (header pre-fill where shown), crawls them,
and pastes any that are blocked.

**Then Claude Code:**
- [ ] For each new platform, run one representative question with `RETRIEVAL_DEBUG=1` on
  `backend-local` (read-only vectors).
- [ ] Check that Query B (mechanics) returns the platform's mechanics docs.
  - Where it returns nothing usable, propose a per-platform query in
    `rag_context.MECHANICS_QUERY_BY_ESP` (today empty), worded in that platform's vocabulary
    ("Canvas", "Journey Builder", "workflow").
  - That is a code change: its own small PR, with recall before and after.

**Acceptance**
- `audit_product_labels.py` is OK.
- `retrieval_recall.py` still passes the existing Klaviyo cases.
- Every new platform has ≥ 1 integration guide and ≥ 1 mechanics document, both indexed.

---

## 5. Stage 1 — the foundation for every platform type

### C1.1 Schema, canonical key, URL normalisation

**Goal:**
- the data model for integrations, platform types, catalog facts and proposals;
- one validated integration key;
- one URL identity.

**Read first:**
- `postgres_adapter.initialize` (85-390): `_add_missing_columns` at 402, `_index_exists` at 396.
- `sqlite_adapter.initialize` and its `_add_missing_columns` (≈291).
- `esp_manager.py`: `create_esp`, `list_esps`, `add_document`, `find_documents_by_url`,
  `get_document_by_url`.
- `app.py`: `chat()`, `select_esp()` (217), `submit_feedback()` (369).
- `conversations.py:363,377` (key normalisation).
- `crawler.vectorize_single_document`.
- `add_document` in both vector adapters (it returns `None` today).

**Tasks**
- [x] **Columns, Postgres and SQLite.** Lists are JSONB in Postgres and TEXT holding JSON in SQLite,
  like `vector_ids`.
  - `esps`: `catalog_slugs`, `categories`, `products` (JSONB), `platform_type VARCHAR(20)`,
    `catalog_description TEXT`.
  - `esp_documents`: `title TEXT`, `source_kind VARCHAR(20)`, `supported_plans JSONB`,
    `supported_platforms JSONB`, `vector_count INTEGER`, `sitemap_lastmod TIMESTAMP`,
    `consecutive_misses INTEGER NOT NULL DEFAULT 0`, `retired_at TIMESTAMP`.
- [x] **Table `document_proposals`:**
  - columns: `id UUID PK`, `esp_id UUID REFERENCES esps(id) ON DELETE CASCADE`,
    `url TEXT NOT NULL UNIQUE`, `source VARCHAR(20)` (`catalog`|`sitemap`|`manual`),
    `suggested_label VARCHAR(20)`, `state VARCHAR(20) DEFAULT 'open'`, `note TEXT`, `created_at`,
    `decided_by TEXT`, `decided_at`;
  - index on `(state, esp_id)`;
  - SQLite mirror.
- [x] **Index** `idx_messages_timestamp_esp ON messages(timestamp, esp)`, created only when missing
  (`_index_exists`).
- [x] **`backend/integration_types.py`** (pure):
  - `PLATFORM_TYPES = ('messaging','storefront','service','data','content')`.
  - `CATEGORY_DEFAULT_TYPE`: catalog category slug → type.
    - messaging: `email-marketing`, `sms-marketing`, `whatsapp-social-dms`.
    - storefront: `ecommerce-platform`, `in-store-pos`, `mobile-app-builder`,
      `mobile-wallet-pass`, `page-builder-pwa`, `payment-checkout`,
      `subscription-recurring-billing`, `on-site-engagement`, `search`,
      `personalization-and-product-recs`, `quiz-and-gamification`.
    - service: `help-desk-crm`, `onsite-chatbots`.
    - content: `reviews-and-visual-ugc`, `retailers-and-review-syndication`, `product-sampling`,
      `influencer-marketing`, `consumer-platform`.
    - data: `data-automation`, `bi-analytics`, `ads`, `privacy-and-data-subject-requests`,
      `other`, `gift-cards`, `sustainability-and-donations`, `shipping-returns`,
      `loyalty-referrals`.
  - `default_type(categories)`: first match in the priority order messaging → service →
    storefront → content → data. An admin overrides conflicts.
- [x] **Boot seed, idempotent:**
  - `platform_type = 'messaging'` for every existing ESP row where it is NULL. This includes
    **`other_webhook`**: it is live on the email prompt today and moves to `data` only in C2.4.
  - `global` keeps NULL.
- [x] **`backend/urls.py`:** `normalize_url(url)`. It strips whitespace, drops the `#fragment`,
  lowercases scheme and host, drops default ports, and strips the trailing slash except on the
  root. The query string is kept. Pure, with tests.
- [x] **`eval/check_url_normalisation.py`** (read-only): lists `esp_documents` rows whose `url !=
  normalize_url(url)`.
  - 🛑 Run it against production. Expected: 0.
  - If not 0, Leo decides per row **before** the next task merges. Vectors are keyed on
    `(esp, source_url)`, so normalising lookups would orphan those rows.
- [x] **Use `normalize_url`:**
  - in `ESPManager.add_document`, `find_documents_by_url`, `get_document_by_url`;
  - in the `check-link` route;
  - in proposals.
- [x] **Vector chunk counts:**
  - Vector adapters' `add_document` returns the number of chunks written.
  - `vectorize_single_document` returns it.
  - Every caller stores it in `vector_count`: the crawl worker's `_finish_completed`, paste,
    rebuild.
- [x] **Key validation:**
  - `ESPManager.is_active_integration(name)`, with a 60 s in-process cache.
  - `chat()`: when `esp` is present and not an active row → 400
    `{"error": "Unknown integration. Reload the page."}`.
  - When `esp` is missing, the `klaviyo` default stays, for old tabs.
  - `select_esp()`, `submit_feedback()` and conversation create normalise `/` → `_` server-side.
- [x] **`scripts/normalize_esp_keys.py`** (dry run / `--apply`):
  - `UPDATE … SET esp = 'other_webhook' WHERE esp = 'other/webhook'` on `esp_selections`,
    `feedback`, `messages`, `conversations`.
  - Then bump `analytics._AGGREGATE_DEFINITION_VERSION` to `'4'`.
  - 🛑 Leo runs `--apply` on production after deploy.
- [x] **`ESPManager.list_integrations(statuses=('active',), …)`** returns the new fields.
  `list_esps` is unchanged, so older callers and older code still see only `active` rows (I4).
- [x] **`backend/test_integrations_schema.py`:**
  - booting twice on SQLite is a no-op; the columns exist;
  - `listed` rows are invisible to `list_esps`;
  - `normalize_url` cases;
  - unknown key → 400;
  - `vector_count` is stored;
  - `default_type` cases, including Klaviyo → messaging, Gorgias → service, Google → content.
  - Postgres variant in the CI `postgres` job.

**Acceptance**
- Check suite green.
- Golden check byte-identical.
- `audit_product_labels.py` OK.
- `check_url_normalisation.py` reports 0 on production, or Leo's decisions are recorded.

**Rollback:** older code ignores the new columns and table. Revert is safe. Leave the columns.

**Deviations (2026-10-13)**
- **Production URL check: 3 rows, not 0.** Two Attentive guides and the Klaviyo guide were stored
  with a `#section`. No page is stored twice. Leo chose to tidy them:
  `scripts/fix_url_spellings.py` re-points each one's vectors (`source_url`), then its row. The dry
  run shows 48 vectors (5, 3, 40). 🛑 **Leo runs `--apply` before PR #3 merges.** The current code
  works with the tidy URLs; C1.1's code would not find the old spellings. After the fix, the
  golden context differs only where these documents are cited, since their URL is shown to the
  model.
- **`normalize_url` rewrites only http(s).** `local://Yotpo`, the name of pasted global text, is a
  name and keeps its case. The legacy CSV has one such link.
- **Links are normalised at each route's entry** (add, paste, check, crawl-selected, global
  add/crawl/paste), not only in `ESPManager`. Each route carries its `url` into the crawl and the
  vectors, so normalising only the row would split one document across two spellings.
  `enqueue_urls` also uses the row's URL. Delete and set-product still match stored URLs exactly.
- **The boot seed runs once**, recorded in `app_settings` (`seed:platform_type_messaging`), not on
  every boot. Otherwise a catalog row imported in C1.2 with no type would become `messaging` at the
  next boot.
- **`create_esp` defaults `platform_type` to `messaging`.** Today's admin only creates email/SMS
  platforms (C0.4's 13 included). The hidden `global` row is created with `None`.
- **`vector_count` is recorded inside `vectorize_single_document`**, not by each caller. Every
  indexing path goes through it, so none can skip it. A failure to record the count is logged; it
  does not fail the crawl.
- **Chat lets a message through if the key check itself fails** (database error), and logs it. A
  validation step should not take chat down.
- **`check_context_unchanged.py` creates its cases' integrations** in its throwaway database. Chat
  now refuses unknown keys, and that database starts empty.
- **Key rename dry run:** 16 `esp_selections` rows hold `other/webhook`; feedback, messages and
  conversations hold none. `--apply` also clears the stored aggregate version, so the dashboard
  recomputes after the rename, whatever the deploy order.
- **Production steps done (2026-10-13, Leo):** `fix_url_spellings.py --apply` (then
  `check_url_normalisation.py` reports 0 and the label audit is OK: 577 vectors, 95 rows), and
  `normalize_esp_keys.py --apply` (16 rows). After the deploy: all 11 integrations read
  `messaging`, `global` NULL; `document_proposals` exists; live chat answers Klaviyo and
  Other/Webhook, and refuses an unknown key with 400.
- **Checks (2026-10-13):** the suite passes offline with the network blocked;
  `test_integrations_schema.py` 14/14; golden check 26/26 identical (all 200, captured on
  `v2/c0-1-ci`, checked on this branch back to back); `audit_product_labels.py` OK.

### C1.2 Document360 header parser + catalog import (dry run)

**Goal:** turn yotpo.com/integrations into integrations (`listed`) and proposals, with a diff a
human reads before anything is written.

**Read first:**
- `product_labels.header_label` (≈241): today it returns the *first* product it finds.
- `crawler._extract_text`.
- ALL_INTEGRATIONS_UPDATE.md §1 and §4.3.
- Appendix B of the plan (measurement method).

**Tasks**
- [x] **Fixtures** (`backend/fixtures/document360/`): save the raw HTML of these Yotpo guides:
  - `recharge-integration-guide-for-yotpo-loyalty-referrals`
  - `gorgias-integration-guide-for-reviews-and-loyalty-referrals` (has "Change this text for …"
    leftovers)
  - `tapcart-yotpo-integration-guide` (three products)
  - `zendesk-integration-guide-for-reviews` (product line missing from the text)
  - `integrating-loyalty-and-referrals-with-shopify-point-of-sale-pos`
  - `google-seller-ratings`

  Generate the expected text with the crawler's own `_extract_text`, not by hand.
- [x] **`backend/doc_header.py`:** `parse_header(text) → {products: set, plans: list,
  platforms: list}`, read from the first ~1,500 characters of stored content.
  - "Loyalty" and "Loyalty & Referrals" → `loyalty`.
  - "Reviews" and "Visual UGC" → `reviews`.
  - "SMS & Email" and "Subscriptions" → ignored (I9).
  - "Change this text for …" lines → ignored.
  - A plans line must never be read as a product.
- [x] **`doc_header.suggested_label(text)`** → `loyalty` | `reviews` | `None`. It returns `None`
  when both products appear (8 of 94 guides) or none.
  - `product_labels.header_label` delegates to it.
  - The admin picker keeps working, and now shows no pre-fill for both-product headers.
- [x] **Catalog fixtures** (`backend/fixtures/catalog/`):
  - a trimmed copy of the catalog page: ~15 cards covering pairs (`gorgias`/`gorgias-loyalty`),
    multi-category cards, `dixa` (product tag `reviews`, not `reviews-ugc`), and Shopify;
  - 4 detail pages: one with a Yotpo guide, one partner-only, one with nothing, one with a
    trailing-space href;
  - a 30-URL slice of `sitemap-en.xml`.
- [x] **`scripts/import_catalog.py`:**
  - [x] **Fetch:** `https://www.yotpo.com/integrations/`, or `--html <file>`. Parse each
    `div.integration-card`: `data-products`, `data-categories`, `href`, `h3` title, description.
    Normalise product tags: `reviews-ugc` and `reviews` → `reviews`; `loyalty` → `loyalty`.
  - [x] **Guard:**
    - Compare against the snapshot in `app_settings` key `catalog_last_import` (card count and
      slugs).
    - Fewer than 90% of the previous cards, or zero categories → abort, write nothing, exit 2.
  - [x] **Group** cards into integrations:
    - by slug base (strip `-loyalty`);
    - by explicit `KNOWN_MATCHES`, which maps existing `esps.name` values to catalog slugs
      (klaviyo, attentive, dotdigital, emarsys, listrak, ometria, omnisend, postscript, plus C0.4's
      13);
    - new integrations get `name = slug_base.replace('-', '_')`;
    - unresolvable name clashes are listed for Leo.
  - [x] **Detail pages:**
    - Fetch each at 1 request/s, with the crawler's headers.
    - Extract `support.yotpo.com/docs/*` and `develop.yotpo.com/*` links; otherwise
      documentation-like partner links.
    - Normalise every href (`normalize_url`; the trailing space is a real case).
  - [x] **Dead links:**
    - Check each Yotpo link.
    - On 404, look in the sitemap for a slug sharing the first two stem words.
    - A match → proposal with note `renamed from <old>`. No match → listed as gone.
  - [x] **Report** (markdown, stdout and `--report <path>`):
    - integrations to create, grouped by default type;
    - type conflicts (expect ~25);
    - proposals by source;
    - renamed, gone, and pages with nothing;
    - removed cards;
    - existing integrations whose catalog fields would change.
  - [x] **`--apply`:**
    - Insert new integrations as `status='listed'` with `catalog_slugs`, `categories`, `products`,
      `catalog_description` and the default `platform_type`.
    - Update catalog fields on existing ones, but never `status`, `name`, `display_name`, or an
      already-set `platform_type`.
    - Insert proposals, skipping URLs that are already documents or already proposals in any state
      (rejections are remembered).
    - Store the snapshot.
    - Never delete anything.
- [x] **Partner mechanics** (added 2026-10-14, Leo's design; plan §4.3, decision log):
  - `backend/app_mechanics.py`: find the partner's help centre (override file, catalog link, guide
    link, the partner homepage's help link, then `help.`/`support.`/`docs.`/`knowledge.` probes;
    the host must carry the app's name); read the partner's own Yotpo articles; search for each
    function (Zendesk API, or the model's pick from the centre's titles); read every candidate.
  - `backend/mechanics_ai.py`: the model lists the partner functions from the Yotpo guides and
    partner Yotpo pages, shortlists titles where there is no search API, and accepts only articles
    whose text explains a function. Numbers only, checked; a failure adds nothing.
  - Blocked centres (bot check, 401/403/429/503, no text without a browser) are listed for a
    person; Zendesk centres are read through their API.
  - `crawler._extract_text` falls back to JSON-LD article text when a page's visible text is an
    empty shell (under 200 characters).
  - Proposals with source `mechanics`, label pre-filled `shared`, note = function and reason; a
    person approves each integration's final list (C1.4).
  - `scripts/help_centres.json`: admin overrides. `--no-mechanics`, `--ai-model` on the script.
- [x] **`backend/test_catalog_import.py`:**
  - parsing the fixtures;
  - grouping;
  - the guard aborts on a shrunken page;
  - href normalisation;
  - renamed-slug lookup;
  - `--apply` on SQLite is idempotent (a second run creates nothing).
- [x] **`backend/test_doc_header.py`:** every fixture, including Zendesk returning `None` and
  Tapcart's products resolving to both.

**Deliverables:** `doc_header.py`, `scripts/import_catalog.py`, fixtures, tests, and a dry-run
report from the live catalog (read-only) attached to the PR.

**Acceptance**
- Tests and CI green.
- Live dry run is close to the plan's §1 figures, give or take catalog drift since 2026-10-13:
  - ~154 integrations;
  - ~101 Yotpo-guide proposals (95 live + 6 renamed);
  - ~58 partner proposals;
  - 1 gone;
  - 14 pages with nothing.
- 🛑 Leo reads the report. **No `--apply` here**: that is C1.9.

**Rollback:** nothing is written in this checkpoint.

**Deviations (2026-10-14)**
- **Partner mechanics added** (Leo, this session), in three versions: general "Welcome to the
  app" articles (rejected by Leo); topic lists with word matching (off target where words
  overlap); then Leo's design above, where the model reads the integration's own documents, lists
  the functions and confirms each article by reading it, blocked centres go to a person, and a
  person approves each final list. Final dry run: the model listed functions for
  111 integrations and accepted 272 articles for 65 of them (268 proposals after duplicates);
  39 help centres could not be read automatically (bot check, login, moved, or built in the
  browser) and go to a person; for 13 the model read the candidates and accepted none; 37 have
  no help centre found. 256 model calls, ~980k input tokens, no failures after the retry.
- **Live dry run** (`docs/integrations/catalog_dry_run.md`), against the live catalog and partner
  sites, with the knowledge-base rows read from a read-only copy of production
  (`eval/seed_local_db.py`), never production itself. Against the plan's figures:
  154 integrations (154); Yotpo guides 88 proposed + 15 already in the knowledge base (~101);
  renamed 6 (6); gone 1, Yieldify (1); pages with nothing documentary 13 (14); partner pages 135
  (~58–83: this also counts partner pages on detail pages that have a Yotpo guide, and partner pages
  whose address names Yotpo); type conflicts 18 among the integrations to create (~25 in all).
- **`--apply` writes a saved plan** (`--plan`), never a fresh fetch, so what Leo reads is what is
  written. A plan made with `--only` is refused.
- **The Zendesk guide now names "Reviews"** in its header; the plan expected no product line. The
  "no product" case is tested on a short synthetic header instead.
- **Renamed guides need the partner's name.** Two leading stem words alone matched 13 guides for
  `integrating-yotpo-loyalty-referrals-with-optimove`. The lookup keeps matches whose slug carries
  the partner's name, then falls back to a slug with the name and "integration"/"guide"
  (`builder-integration-guide` → `builderio-integration-guide`).
- **`KNOWN_MATCHES`** adds `bloomreach` (no catalog card today) and `brevo_pushowl`, and C0.4's
  13 under the names C0.4 plans. If C1.9 runs before C0.4's platforms are created, the import
  creates them as `listed`; C0.4 then activates those rows instead of creating new ones.
- **Import links:** `utm_*` parameters are dropped, and Yotpo's own guides are always `https`
  (Bold Commerce links one over `http`). `reamaze-2` is named `reamaze`.
- **Fixtures are trimmed:** scripts, styles, SVG and `data-*` attributes removed (1.4 MB → 50 KB a
  guide). `test_doc_header.py` checks that the crawler's text is unchanged by the trim.
- **A link proposed for two integrations** stays with the first (the URL is unique in
  `document_proposals`); the report lists the 7 cases (e.g. Shopify's intro articles for
  `shopify_flow`, `shopify_plus`).

### C1.3 Refresh pipeline

**Goal:** documents stay current without re-indexing unchanged text. Dead or renamed guides stop
serving stale answers.

**Read first:**
- `workers/crawl_worker.py`: `_process_job`, `_finish_completed`, `_finish_failed`,
  `_handle_failure`.
- `workers/crawl_queue.py`: `enqueue_crawl_job`, `describe_link`, `DOCUMENT_STATE_QUERY`.
- `crawler.py`: `fetch_main_content`, `_extract_text`.
- `app.py` scheduler setup (1371-1425).

**Tasks**
- [ ] **Hash short-circuit.**
  - After a successful fetch, compare `sha256(saved_text)` with the row's `content_hash`.
  - If equal and `vector_count > 0`: skip `vectorize_single_document`, set `last_crawled_at` and
    `crawl_status='completed'`, and record the job detail "unchanged; not re-indexed".
  - Do the same in the synchronous crawl path until C1.8 removes it.
- [ ] **Document360 extraction rule** (host `support.yotpo.com`), in `_extract_text`:
  - Choose the article container from the fixtures. **Inspect them; do not guess selectors.**
  - Drop the table of contents, the "Was this article helpful" block, related articles and
    "Change this text for …" lines.
  - Keep the header (Products / plans / platforms) at the top of the stored text.
- [ ] **Header fields on crawl.** For `support.yotpo.com` documents, write `title`,
  `supported_plans` and `supported_platforms` from `doc_header.parse_header`. They are never a
  label (I1 stays human).
- [ ] **Sitemap job.**
  - `backend/sitemap_refresh.py` plus table `sitemap_urls` (`url PK`, `lastmod`, `first_seen_at`,
    `last_seen_at`, `gone_at`), Postgres and SQLite.
  - Daily job: fetch `https://support.yotpo.com/sitemap-en.xml` (and `sitemap_index.xml` for new
    child sitemaps).
  - Upsert the URLs. For each non-retired `esp_documents` row on that host whose `lastmod` is newer
    than `last_crawled_at`: `enqueue_crawl_job(priority=0)`.
  - Mark vanished URLs `gone_at`.
  - Scheduled in the existing crawl scheduler (`USE_ASYNC_CRAWL`); C1.8 moves it.
  - `GET /api/admin/sitemap-changes?since=` returns new, vanished and changed URLs, unassigned.
- [ ] **Retirement.**
  - In `_finish_failed`, for `PERMANENT` with status 404 or 410: `consecutive_misses += 1`.
    Reset to 0 on success.
  - `describe_link` shows "missing 3 times — retire or replace" at ≥ 3.
  - `POST /api/admin/esp/<name>/retire {urls}`: `delete_by_url` vectors, set `retired_at` and
    `crawl_status='retired'`.
  - `POST /api/admin/esp/<name>/replace {old_url, new_url}`: `add_document(new_url,
    product=<old product>)`, enqueue it, retire the old one after the new one indexes.
- [ ] **Exclude retired rows** everywhere they would count:
  - `list_documents` default;
  - `get_documents_with_content` (rebuild);
  - Refresh All (`app.py:refresh_all`);
  - `reviews_documents` (coverage);
  - `DOCUMENT_STATE_QUERY` default;
  - the label audit.

  List every query you change in the PR.
- [ ] **Tests**, extending `test_crawl_pacing.py` (pure plus Postgres) or adding
  `test_refresh_pipeline.py`:
  - unchanged content does not call the vectorizer;
  - the Document360 rule on fixtures keeps the header and body and drops the boilerplate;
  - sitemap diff logic on the fixture slice;
  - the miss counter and retire flow, with a fake vectorizer and `delete_by_url` called.

**Acceptance**
- Tests green.
- Golden check byte-identical (no content changes).
- Locally on `backend-local` with `VECTOR_DB_PROVIDER=chromadb`: crawling the same URL twice
  re-indexes only once.

**Note:** existing Yotpo documents pick up the new extraction only when re-crawled (their `lastmod`
moves, or an admin re-crawls them). 🛑 An optional full re-crawl of Yotpo documents is Leo's call,
followed by `retrieval_recall.py`.

**Rollback:** revert. The new columns and table stay unused.

### C1.4 Admin: integrations, proposals inbox, crawl summary, roles

**Goal:** an admin that works with ~160 integrations and ~300 documents. It replaces ESP
Management, whose N+1 fetch-and-render cannot scale.

**Read first:**
- `frontend/app.js`: `loadESPManagement` (1835-1940), `productPickerHTML`/`saveProductLabel`
  (1725-1826), `addLink` (2513), `crawlAllSelected*` (2016-2356), `deleteAllSelected` (2358).
- `frontend/crawl-progress-tracker.js`.
- `frontend/paste-content-modal.js`.
- `app_admin_esp_routes_async.py`.
- `auth.py`: `admin_request_ok`, `current_user_is_admin`.

**Backend tasks**
- [x] `backend/admin_integrations_routes.py`, registered in `app.py` after the ESP routes. Every
  route requires admin.
  - [x] `GET /api/admin/integrations?q=&category=&type=&status=&tier=&flag=&page=&per_page=50`:
    - **one** summary SQL: per integration, document counts by product, failed, flagged misses,
      open proposals, and tier;
    - tier per plan §4.1:
      - `messaging` Basic = ≥ 1 completed loyalty/reviews document with `vector_count > 0` **and**
        ≥ 1 completed `shared` document;
      - other types Basic = ≥ 1 completed loyalty/reviews document;
      - otherwise Listed.
  - [x] `GET /api/admin/integrations/<name>`: facts and merged catalog cards.
  - [x] `PATCH /api/admin/integrations/<name>`: `platform_type`, `display_name`, `categories`,
    `products`. Changing `status` is **owner-only**.
  - [x] `GET /api/admin/integrations/<name>/documents?page=`: paginated
    `crawl_queue.list_document_states`.
  - [x] `GET /api/admin/proposals?esp=&source=&state=open&page=`. Sources are `catalog`,
    `sitemap`, `manual` and `mechanics` (the partner's own articles on the functions the
    integration touches, C1.2). `mechanics` proposals are shown per integration as one list, with
    the functions the model found and each article's function and reason; an admin approves the
    final list in one click or per article. Integrations whose help centre blocked automated
    reading are listed for an admin to pick articles by hand.
  - [x] `POST /api/admin/proposals/approve {items: [{id, product}]}`:
    - a product is required per item;
    - `add_document(…, product=…)` then `enqueue_crawl_job`;
    - state `approved`.
  - [x] `POST /api/admin/proposals/reject {ids, note}`: state `rejected` (remembered).
  - [x] `GET /api/admin/crawl-summary`: counts by state and host, plus active jobs (≤ 50).
- [x] **Roles:**
  - `ADMIN_OWNER_EMAILS` (comma-separated). `auth.current_admin_role()` → `owner` | `editor` |
    `None`.
  - **Unset means every admin is an owner,** which is today's behaviour.
  - Owner-only: `settings/*` (model, API key, system prompt, restore, audit log), `refresh`,
    `rebuild-vectors`, `debug/*`, integration `status`.
  - The break-glass password counts as owner.

**Frontend tasks**
- [x] `frontend/admin-integrations.js`:
  - integrations table with search, filters and pagination;
  - detail panel: documents table (paginated; reuse `productPickerHTML`/`saveProductLabel`), add
    link with product, paste (existing modal), crawl selected, delete, retire/replace;
  - catalog facts; `platform_type` select.
- [x] Proposals tab:
  - grouped list with select-all;
  - **a required product picker per row** (header suggestion pre-filled; no default otherwise);
  - approve and reject.
- [x] Crawl tracker polls `crawl-summary` instead of posting every job id every 2 s.
- [x] `index.html`:
  - the "ESP Management" tab becomes "Integrations"; add a "Proposals" tab;
  - new script tags;
  - user-facing "ESP" strings renamed (inventory in plan §2).
- [x] Remove `loadESPManagement` rendering and its runtime monkey-patch (`app.js:3263-3270`) once
  the new tab has parity. Global Knowledge stays as it is.

**Tests:** `backend/test_admin_integrations.py` (SQLite, Flask test client):
- pagination and filters;
- tier computation on synthetic rows;
- approve without a product → 400;
- a rejected URL is not re-proposed by a second import;
- role enforcement with `ADMIN_OWNER_EMAILS` set and unset.

**Acceptance**
- Tests green.
- On `backend-local`, with the catalog import `--apply`-ed into the **local SQLite** (fixtures or
  the live dry run):
  - the Integrations tab opens with ≤ 3 API requests;
  - it renders 160 integrations in under 1 s;
  - every old ESP Management action works (add link with product, crawl, paste, set-product,
    delete).
- Screenshots at 1280 px in the PR.

**Deviations** (2026-10-15)
- **Listed integrations can be documented.** `esp_manager.get_esp_by_name` and
  `find_documents_by_url` now see `listed` rows as well as `active` ones. Without it every document
  action (approve, add link, label, crawl, paste) failed with "not found" on the ~145 imported
  integrations, which made C1.9 step 4 impossible. Every caller is an admin or document path; chat
  checks `is_active_integration` and the sidebar lists through `list_esps`, both `active` only (I4).
  The duplicate-URL check now covers listed integrations too.
- **New columns** (additive, both adapters): `document_proposals.title`, `partner_function`,
  `reason` (a mechanics article's, shown in the inbox), `decision_note` (the admin's note on a
  rejection; `note` keeps the import's), and `esps.platform_type_set_by` (who chose the type, so a
  settled type conflict leaves the "Type to check" filter).
- **The import stores what the inbox shows.** `import_catalog.py --apply` also writes each
  mechanics proposal's title, function and reason (from the plan's `mechanics.accepted`, so plans
  saved before this change still apply), the per-integration notes (`app_settings`
  `catalog_mechanics`: functions found, help centre, why nothing was found) and the report
  (`catalog_last_report`). The plan format is unchanged.
- **Tier** (superseded the same day: the tier was removed, see "No coverage tier" below). "Indexed" is `crawl_status = 'completed'` and `vector_count` NULL or > 0: NULL is a
  document indexed before C1.1 recorded counts. It applies to the guide and to messaging's shared
  document alike, and the guide must be for a product the catalog lists (any product when the
  catalog lists none), as plan §4.1 says.
- **Only messaging integrations can be active** until C1.7 gives the other types their prompts
  (`admin_integrations_routes.TYPES_IN_CHAT`): a PATCH that would make a non-messaging integration
  active, or move an active one off messaging, gets 409. C1.7 and each wave extend the tuple.
- **Crawl tracker.** Batches up to 50 jobs keep today's per-job tracker; a larger one (Refresh All)
  is followed in the Crawls strip, which polls `crawl-summary` every 5 s while jobs are active.
- **Not built here:** the sitemap's new and vanished articles and the retire/replace buttons wait
  for C1.3 (a document missing ≥ 3 times already says "retire or replace it"); the hand-set
  "evaluated" flag (plan §4.1); the design's Usage Analytics additions (plan §4.9), which need the
  C1.5 picks and a source count per chat message; user-facing "ESP" strings outside the admin
  (sidebar, feedback modal), which C1.5 rewrites.
- **Create New Integration is owner-only**: it creates an `active` messaging integration, in chat
  at once, and putting an integration into chat is an owner's call like its status.
- **Refresh All and Rebuild Vectors "all" include listed integrations**, so a listed one's
  documents are current and indexed on the day it goes active.
- **Approving a link that is already this integration's document** (added by hand, or an approve
  that stopped half way) marks the proposal approved and keeps the document's label. A link that
  belongs to another integration stays open, with the reason.
- **Partner articles are pre-filled Shared** in the inbox, from the import's label (C1.2, Leo's
  design); the label is dashed until a person changes or approves it.
- **Roles change nothing until `ADMIN_OWNER_EMAILS` is set**: unset, every admin is an owner.
- **Plain words on screen** (Leo, 2026-10-15: the first version was "very confusing"). The code and
  this map keep their terms; the admin shows these instead. Use the same words in later UI work.

  | in code and this map | on screen |
  |---|---|
  | status `active` / `listed` | In chat? — **In chat** / **Not in chat** (`archived` is no longer offered, below) |
  | `platform_type` messaging / storefront / service / data / content | Kind of platform — **Email & SMS** / **Store & checkout** / **Customer service** / **Data & automation** / **Reviews & content** |
  | `products` | Yotpo products it works with (tick boxes in the list too; ticked automatically from documents, below) |
  | catalog cards | Its pages on yotpo.com/integrations |
  | proposals (sources catalog / sitemap / manual / mechanics) | **Suggested Links** (From yotpo.com / New Yotpo article / Added by hand / Platform help article) |
  | mechanics functions | the platform's features its Yotpo guide uses |
  | owner / editor | Owner access / Editor access |

  Every empty field says why it is empty and what fills it. Explanations open from a small "i"
  (hover, focus or click; the browser's own title tooltip proved unreliable).
- **No coverage tier** (Leo, 2026-10-15: "completely unreliable… root it out"). The Basic / Listed
  tier of plan §4.1 ("Ready / Missing documents" on screen) is gone from the admin and the API:
  no column, filter, checklist or to-do. What decides that an integration goes into chat is Leo's
  judgement, helped by its documents list and Suggested Links.
- **Two states** (Leo, 2026-10-15): an integration is in chat (front and back end) or not in chat
  (admin only); it is never hidden from the admin. The admin can't set `archived` any more; a row
  archived by older code (none in production on 2026-10-15) shows as "Not in chat", read-only until
  set to it. Removing for good is deleting.
- **Products follow the documents** (Leo, 2026-10-15): Loyalty / Reviews count as ticked whenever
  the integration has a document with that label (Shared doesn't count). Computed on read
  (`admin_integrations_routes.effective_products`), never stored, so every existing integration is
  pre-filled with no backfill; those boxes are locked in the admin. C1.5's `/api/integrations` uses
  the same rule.
- **The crawl box shows only when there is something to see** (Leo, 2026-10-15): documents
  waiting, crawling, failed or never crawled, or crawled since the Integrations tab was opened
  (`crawl-summary?since=` with the database's own clock, so time zones can't skew it).
- **Nothing is ticked in advance any more** (Integrations and Global Knowledge). Failed and
  never-crawled links used to be pre-ticked, which showed "5 selected · Delete Selected" before the
  admin had chosen anything. The admin ticks what to crawl.
- **"In chat" is disabled** on the page for kinds other than Email & SMS (the server already refused
  it, C1.4), and an integration with no kind is listed under "Kind of platform to set or confirm".

**Rollback:** revert. The old tab returns. Routes are additive.

### C1.5 Chat: integration picker, `/api/integrations`, copy by type

**Goal:** users choose among ~160 integrations. Listed ones are visible but greyed. The `/`↔`_`
hack and the hardcoded Klaviyo assumptions go away. Messaging users see no difference.

**Read first:** `frontend/app.js`:
- `selectedESP` (30), `CHAT_PRODUCTS` (34), the `conversationHistories` seed (152-157);
- `renderIntro` (290-340), `INPUT_PLACEHOLDERS` (388), `updateProductPicker` (376), `setProduct`
  (393);
- `initializeESPButtons` (444), `reloadSidebar` (490-565), `sendMessage` (710);
- `showHistory` (2671), `openConversation` (2748), `espDisplayName` (2637), feedback modal (1153);
- `index.html:249-320` (sidebar and welcome card).

**Tasks**
- [ ] **`GET /api/integrations`** (public):
  - `active` and `listed` integrations: `name`, `display_name`, `platform_type`, `categories`,
    `products` (the effective rule: `admin_integrations_routes.effective_products`), `status`,
    `catalog_url` (no tier: C1.4 Deviations);
  - in-process cache (60 s) with an `ETag`.
- [ ] **`frontend/integration-picker.js`:**
  - a searchable combobox (type-ahead over display names), grouped by category;
  - "Recently used" (localStorage `flowStateRecentIntegrations`);
  - `listed` items greyed under "Not covered yet", linking to the catalog page, not selectable;
  - keyboard: ↑ ↓ Enter Esc;
  - works at **375 px**: below 768 px the picker opens as a full-width sheet.
- [ ] **Replace `initializeESPButtons`/`reloadSidebar`'s list** with the picker.
  - Default selection: most recent, else `klaviyo` if active, else the first active.
  - Remove the `selectedESP = 'klaviyo'` literal as the source of truth.
- [ ] **Remove the slug hack** at every site: `app.js:96, 295, 507, 517, 522, 557, 738, 2702`.
  Keys are `esps.name`, URL-encoded (`encodeURIComponent`) wherever they reach a path.
  - Migration: on load, rewrite sessionStorage `espConversationHistories` keys containing `/` to
    `_`.
- [ ] **Product picker:**
  - offers only `integration.products`; a single product is locked;
  - if the current product is unsupported, switch to a supported one through `setProduct` (which
    ends the conversation, as today).
- [ ] **Welcome copy and placeholder by `platform_type`:**
  - `WELCOME_COPY` and `INPUT_PLACEHOLDERS[type][product]`;
  - **messaging keeps today's strings byte-for-byte**;
  - the other four use the plan's §4.7 drafts, marked `// DRAFT copy: Leo finalises in the wave`;
  - the `other_webhook` special case stays until C2.4;
  - remove the static Klaviyo card from `index.html`, so the first render comes from JS.
- [ ] **Feedback modal** shows the display name. **History** becomes one list with an integration
  filter; the sidebar clock buttons are removed.
- [ ] **Escape** every catalog-sourced string (I7). The sidebar's unescaped `display_name`
  (536-541) goes away with the old list.

**Acceptance**
- On `backend-local`, with local data including `listed` rows:
  - Klaviyo is selected by default;
  - chat works;
  - the `/api/chat` payload for Klaviyo is unchanged except for removed hack artefacts;
  - `other_webhook` sends `other_webhook`;
  - `listed` integrations can't be selected;
  - no console errors.
- Screenshots at 1280 px and 375 px.
- Golden check byte-identical (the backend is unaffected).

**Rollback:** revert the frontend. `/api/integrations` stays harmlessly. The old sidebar still uses
`GET /api/admin/esps`, which stays public until C2.6.

### C1.6 Reviews readiness

**Goal:** Reviews retrieval is measured and decided before the Reviews-heavy waves. Today Reviews
has 0 retrieval cases, unfiltered chats, and Loyalty-only global knowledge.

**Read first:**
- `rag_context.py` `CHAT_SEARCH_PRODUCTS` (≈350-365) and `chat_search_products`;
- `eval/retrieval_cases.json`;
- `eval/check_context_unchanged.py` `CASES`;
- `eval/product_eval.py`, `eval/product_scorer.py`;
- PRODUCT_LINE_SPLIT_SCOPE.md §5 steps 7–8.

**Tasks**
- [ ] **Draft ≥ 10 Reviews retrieval cases.**
  - Spread them over ≥ 4 integrations with Reviews documents (Klaviyo, Attentive, Dotdigital,
    Omnisend, plus C0.4's Braze, Drip, HubSpot, Mailchimp, Remarkety).
  - Read the stored content, read-only. Each case gets `must_contain` facts quoted from the stored
    documents.
  - 🛑 Leo validates the facts.
- [ ] **`check_context_unchanged.py`:** `CASES` gains an optional product. Add ≥ 4 Reviews cases.
  Capture a new golden file and record the date in the PR.
- [ ] **`eval/REVIEWS_FILTER_DECISION.md`**, pre-registered **before running**:
  - arms: unfiltered (today) vs `('reviews','shared')`;
  - metrics: Reviews cases recall; wrong-product rate from `product_scorer` on the Reviews questions
    in `questions.json`;
  - rule: ship the filter if recall is not lower **and** the wrong-product rate is not higher.
  - Then run the arms, record the results, and if the rule passes set
    `CHAT_SEARCH_PRODUCTS['reviews'] = ('reviews', 'shared')`.
- [ ] **🛑 Reviews global knowledge:**
  - Leo picks 2–5 Yotpo Reviews documents (e.g. site vs product reviews, review request settings);
  - add them to Global Knowledge labelled `reviews`;
  - re-run the Reviews cases.

**Acceptance**
- Cases committed.
- Decision document with results.
- The filter shipped or explicitly not, with the reason.
- The existing Loyalty cases still pass.

**Rollback:** the filter is one dict entry; remove it.

### C1.7 System prompt per platform type + integration facts block

**Goal:** the plumbing for five prompts, with `messaging` provably unchanged (I2) and the four new
types fed their shipped drafts. **No user sees a non-messaging prompt until its wave**, because
those integrations are `listed`.

**Read first:**
- ALL_INTEGRATIONS_UPDATE.md §4.6 and Appendix C.
- `config_manager.py`:
  - `_ensure_files_exist` (85-140), `get_config`, `update_config` (165-205);
  - `update_config` only updates keys that already exist;
  - `restore_from_backup` (238-275), `get_system_prompt`, `update_system_prompt`.
- `ai_client.py`: `__init__`, `generate_response` (155-196; renders per call).
- `prompt_template.py`.
- `app.py`: the settings routes (540-750) and `chat()`.
- `rag_context.build_rag_context`: the context-assembly part (526-590).
- `frontend/app.js`: `loadSystemPrompt` (2926), `loadAuditLog` (2942), `restoreFromBackup` (3121).

**Tasks**
- [x] **Shipped defaults**, `backend/prompts/system_prompt_{storefront,service,data,content}.txt`.
  - These live under `backend/` because the Dockerfile does not copy `eval/`.
  - Build each from Appendix C with the **common rules** and **closing** blocks expanded inline.
  - The first line of each file is a comment block the loader strips:
    `# DRAFT — Leo rewrites this in the <type> wave`.
- [x] **`backend/prompt_blocks.py`:** the common-rules text as one constant. A test checks that it
  appears verbatim in every shipped default.
- [x] **`config_manager`:**
  - Seed `system_prompts: {}` into the stored config when missing; `update_config` needs the key
    to exist.
  - `get_system_prompt(platform_type='messaging')`:
    - `messaging` → `config['system_prompt']`, unchanged;
    - other types → `config['system_prompts'].get(type)`, or the shipped default;
    - **never** the messaging prompt as a fallback;
    - unknown type → `ValueError`.
  - `update_system_prompt(prompt, user_email, platform_type='messaging')`:
    - the audit entry gains `platform_type`;
    - its backup gains the full `system_prompts`.
  - `restore_from_backup`:
    - an entry **with** `platform_type` restores only that type (`ai_model` untouched unless the
      entry changed it);
    - an entry **without** one (all existing entries) restores `ai_model` + `system_prompt` as
      today and leaves `system_prompts` untouched.
- [x] **`ai_client.AIClient`:**
  - holds a `prompts` mapping, all five, loaded through `config_manager`;
  - `generate_response(…, product, platform_type='messaging')` renders that type's prompt per
    call;
  - every place in `app.py` that rebuilds `ai_client` after a settings change reloads all five.
- [x] **`chat()`:**
  - read the integration's `platform_type` from the cached row (C1.1), default `messaging`;
  - pass it to `generate_response`;
  - pass the facts block and source style to `build_rag_context` **only** when the type is not
    `messaging`.
- [x] **`rag_context.build_rag_context`** gains `integration_facts: Optional[str] = None` and
  `source_style: str = 'esp'`. Defaults leave the context byte-identical (I3). With
  `source_style='integration'`:
  - source headers read `Integration:` and `Source: Yotpo guide | partner documentation`, from
    `source_kind`;
  - the no-sources fallback says the documentation does not cover this and points to the guide;
  - the limited-documentation warning is phrased per type (plan §4.6.6).
- [x] **`backend/integration_facts.py`:** `facts_block(esp_row, documents)`, in the format of plan
  §4.6.5. Lines with no data are omitted.
- [x] **Routes:**
  - `GET` and `POST /api/admin/settings/system-prompt?platform_type=` (default `messaging`, so the
    old frontend still works);
  - `POST /api/admin/settings/prompt-preview {esp, product}` → rendered prompt plus facts block.
    Owner-only.
- [x] **Editor UI:**
  - platform-type selector above the prompt textarea;
  - "Preview for…": pick an integration and a product;
  - the audit log shows the type;
  - warning when the common rules are missing from a non-messaging prompt;
  - warning when a type has `active` integrations but no stored prompt.
- [x] **`backend/test_prompts_by_type.py`:**
  1. Messaging rendered for `None`, `loyalty` and `reviews` equals `render(stored_template, p)`.
     The stored template is today's, from `eval/prompts/system_prompt_template.txt` and the
     `config_manager` default.
  2. Every shipped default validates and contains the common rules verbatim.
  3. A storefront type with nothing stored gets its default, not messaging.
  4. Restoring an old-style audit entry leaves `system_prompts` intact.
  5. Per-type restore restores only that type.
  6. `build_rag_context` with default arguments is unchanged on a fixture (with the fake
     vectorizer).
  7. The facts block appears only when passed.

**Acceptance**
- Tests green.
- Golden check byte-identical.
- Chat for every messaging platform unchanged.
- The preview shows a storefront prompt for a `listed` storefront integration.
- 🛑 Leo reads the four drafts once (2–3 h). Final wording happens in each wave.

**Deviations** (2026-10-15)
- **No type joins chat here.** `admin_integrations_routes.TYPES_IN_CHAT` stays `('messaging',)`.
  NEXT_SESSION.md suggested C1.7 extend it, but this checkpoint's goal and plan §4.6.8 put each
  type into chat in its wave, after Leo rewrites the draft and the trap eval passes. Extending it
  is Leo's call; the chat path already works for every type (tested with an active storefront row).
- **`build_rag_context` also takes `platform_type`**, to pick the per-type limited-documentation
  note (`rag_context.LIMITED_DOCS_BY_TYPE`). With `source_style='integration'` the task section is
  headed "## Integration Documentation:" instead of "## ESP-Specific Knowledge:". The four notes
  and the no-sources text are drafts for Leo, like the prompts.
- **`source_kind` is read from the address** while nothing writes the column
  (`integration_facts.source_kind`): `support.yotpo.com` → Yotpo guide, other `yotpo.com` hosts →
  Yotpo developer documentation, `local://` → text pasted by a Yotpo admin, anything else → partner
  documentation. A stored value wins.
- **Plans and store platforms** come from `supported_plans` / `supported_platforms` when the crawl
  has written them (C1.3), otherwise from the guide's header text (`doc_header.parse_header`).
  Only indexed documents count (completed, not retired, `vector_count` NULL or > 0). "Works with"
  uses C1.4's rule: the catalog's products plus any a document is labelled with.
- **The facts block also lists the Yotpo guides' links** ("Yotpo guide: <url>", up to 3), so the
  no-sources note can point the user to one.
- **`system_prompts` is seeded in memory** by `get_config`, and stored with the first save. Nothing
  is written to production at boot.
- **Saving the Email & SMS prompt also records its type** (`platform_type: messaging`). Undoing such a
  save now puts back that prompt only; before, it also put back the model from that moment, which
  could revert a later model change. Entries saved before this change (no type) restore as before.
- **The golden tool's stub refuses a non-messaging prompt**, so a messaging case answered with
  another prompt shows as a DIFF.
- **Test 6 compares against contexts captured from the old code**:
  `backend/fixtures/prompts/rag_context_default.json` was written by
  `test_prompts_by_type.py --write-rag-fixture` run on `origin/main` (7b81ac8), with a fake index.
- **Not here:** "Untrusted context" (plan §4.6.7: excerpts introduced as documentation, hidden text,
  outside links) is not in this checkpoint's tasks; it belongs with the first wave.

**Rollback:**
- Code older than this gives every integration the messaging prompt.
- **Before rolling back below this checkpoint, run `scripts/activate_integrations.py --deactivate
  --type storefront,service,content,data --apply`** (C2.1 creates it). Until then, no
  non-messaging integration is active, so a revert is safe.

### C1.8 Portability seams, Sentry, no local disk

**Goal:** a move off Railway becomes a configuration change (plan §3.2).

**Read first:**
- `app.py`: scheduler blocks (1343-1425), `_global_csv_links` and the global CSV writes
  (754-1021), `submit_feedback`, which writes `feedback.csv` to disk (388-405).
- `crawler.py`: `crawl_single_url_result`, `find_saved_copy`, `save_filename_for`.
- `crawl_worker.py`: `_try_saved_copy`, `_update_metadata_atomic` (fcntl).
- `app_admin_esp_routes.py` (sync paths).
- `Dockerfile`, `Procfile`, `.env.example`, `mechanics_cache.py`, `product_labels.clear_coverage_cache`.

**Tasks**
- [ ] **One scheduler builder**, `backend/workers/schedule.py`. Jobs:
  - stale-job cleanup (5 min);
  - sitemap refresh (daily);
  - conversation purge (24 h);
  - idle sweep (15 min).

  Each run takes `pg_try_advisory_lock(<job key>)` and skips if the lock is held. On SQLite it
  runs without locks.
- [ ] **`backend/workers/main.py`:** the standalone entrypoint. Crawl worker plus scheduler; clean
  SIGTERM.
- [ ] **`app.py`:** when `RUN_WORKER_IN_PROCESS` is true (default `true`, today's behaviour on
  Railway), start the same worker and scheduler in-process. Remove the duplicate schedulers.
- [ ] **Boot DDL:** `postgres_adapter.initialize` holds `pg_advisory_lock(hashtext('flowstate_schema'))`
  for the whole DDL. CI starts two app processes at once and both succeed.
- [ ] **`kb_version`:**
  - `app_settings` key, bumped by `bump_kb_version()` wherever caches are cleared today
    (`clear_mechanics_cache`, `clear_coverage_cache`, label edits, integration edits);
  - web checks it at most every 10 s at the top of `chat()` and `/api/integrations`; on change it
    clears the mechanics, coverage, integrations and active-key caches.
- [ ] **No local disk.**
  - 🛑 **Precondition:** a read-only production check that every non-retired `esp_documents` row
    has `content`. Write `eval/check_backfill.py`; expected 0 missing.
  - Then:
    - crawls write no files;
    - drop `find_saved_copy`, `save_filename_for` and `_update_metadata_atomic`;
    - global links come from the database only (remove the CSV reads and writes);
    - `submit_feedback` stops writing `feedback.csv` (the `feedback` table already holds it);
    - the synchronous crawl routes call the worker's job processing inline (one code path, still
      usable on SQLite);
    - the frontend's `crawlAllSelectedSync` duplicate goes;
    - `Dockerfile` stops copying `docs/` and `esp_support_links.csv`.
  - `config_manager`'s JSON file mirrors stay as best-effort mirrors. Verify that they are never
    read while the database answers.
- [ ] **Sentry** (`sentry-sdk[flask]`, pinned; in constraints):
  - initialise only when `SENTRY_DSN` is set;
  - `before_send` drops request bodies (chat text is user content);
  - worker errors included;
  - the `[SPEND]` warnings from C0.3 become Sentry messages.
- [ ] **`.env.example`:** every variable the code reads, each with a comment. Grep `os.environ`
  and `os.getenv` to find them.
- [ ] **🛑 Backups:** Leo confirms Railway Postgres backups are on and restores one to a scratch
  database. Claude Code runs `audit_product_labels.py` read-only against the scratch database.

**Acceptance**
- CI (Postgres) checks:
  - concurrent boot passes;
  - two scheduler instances run a job once;
  - a `kb_version` bump clears another process's cache (a two-process test).
- Crawl tests assert no files are written under `docs/`.
- `docker build` succeeds without `docs/`.
- Golden check byte-identical.
- `workers/main.py` runs locally against the test Postgres.

**Rollback:** revert. Before deleting `docs/` from the repo, keep the commit that removes it
separate from the code changes.

### C1.10 "Find links" for one integration

**Goal:** an admin can ask the app to look for one integration's documentation at any time: after
creating it by hand, or when its links have gone stale. What it finds lands in Suggested Links, for a
person to approve, exactly like the catalog import's suggestions (Leo, 2026-10-15: "both are needed
to have a complete product").

**Read first:** `scripts/import_catalog.py` `build_plan` (the per-integration body),
`backend/app_mechanics.py` `discover`, `backend/mechanics_ai.py`, `backend/catalog_import.py`
`detail_links` / `find_renamed`, `backend/admin_integrations_routes.py`, and the memory note that
the Gemini key is the live chat's prepaid key.

**Tasks**
- [ ] **One finder, two callers.** Move the per-integration body of `build_plan` (its yotpo.com
  detail pages → Yotpo guides and partner pages; renamed guides via the sitemap; partner help
  articles via `app_mechanics.discover`) into a backend module, e.g. `backend/link_finder.py`,
  `find_links(integration, fetch, chooser, sitemap) -> {proposals, mechanics_note}`.
  `import_catalog.py` calls it per integration; the plan file, the report and the dry run are
  unchanged (`test_catalog_import.py` stays green unchanged).
- [ ] **Integrations not on yotpo.com** (created by hand): no detail page, so look for Yotpo guides
  in C1.3's `sitemap_urls` by the integration's name tokens (`app_mechanics.name_tokens`), the same
  way renamed guides are found. Name collisions (Rule, Target, Drip) are fine here: a person
  approves every suggestion. Help centre: the `scripts/help_centres.json` override, else the usual
  discovery.
- [ ] **`POST /api/admin/integrations/<name>/find-links`**: queues one background job (the crawl
  worker's queue or a job of its own; never in the request: it takes about a minute). Returns at
  once. `GET` on the same path returns the last run (when, by whom, state, what was suggested,
  and the help-site note). One run per integration at a time.
- [ ] **Writes only suggestions**: rows in `document_proposals` (sources `catalog` and `mechanics`),
  skipping URLs that are already documents or were ever suggested (rejections are remembered),
  plus that integration's entry in `app_settings` `catalog_mechanics`. Never creates documents,
  integrations or labels.
- [ ] **Model budget**: the partner-article step calls Gemini. Leo, 2026-10-15: **use the app's
  same `GEMINI_API_KEY` for now** (the live chat's prepaid key). A daily cap on runs was proposed
  as a guard against a runaway draining that credit; Leo asked why it is needed. Unless he asks for
  a cap: one run per integration at a time, and the button says a run uses Gemini credit. Without
  a key, it still finds the yotpo.com and Yotpo-guide links and says the help-article step was
  skipped.
- [ ] **Admin:** a "Find links" button on the integration's page, its last run beside it ("Found 3
  links: review them in Suggested Links"), and "Find links" offered in the empty state of an
  integration with no documents and no suggestions.
- [ ] **Tests** (fake fetch, fake model, SQLite and Postgres): the import's output is unchanged;
  find-links on a catalog integration proposes what the import would; on a hand-made one it finds a
  sitemap guide by name; rejected and existing URLs are skipped; the cap; editor/owner rules as Leo
  decides.

**Acceptance**
- On `backend-local` (local SQLite, no production key): "Find links" on a hand-made integration and
  on a catalog one adds the expected suggestions; a second run adds nothing.
- The catalog dry run's report is byte-identical before and after the refactor, on the cached pages.

**Rollback:** revert; suggestions it already made stay in the inbox.

### C1.9 🛑 Production import, approvals, labelling (Leo)

After C1.1–C1.8 are deployed, in this order:

1. [ ] Run `scripts/normalize_esp_keys.py --apply` (C1.1).
2. [ ] Run `scripts/import_catalog.py --plan <file> --report <file>` as a dry run, read the
   report (add missing help centres to `scripts/help_centres.json` and re-run), then
   `--apply --plan <file>`. If C0.4's platforms do not exist yet, the import creates them as
   `listed` under the same names: activate those rows instead of creating them again.
3. [ ] Resolve the ~25 platform-type conflicts in the Integrations tab.
4. [ ] In the Proposals inbox, approve and label documents per document; reject homepages; paste
   blocked pages.
5. [ ] Let the queue crawl them.

**Claude Code then runs read-only and reports:**
- `audit_product_labels.py` (OK);
- `retrieval_recall.py` (no regression);
- per type, how many integrations are in chat and not, and which have no Loyalty or Reviews
  document yet, from `/api/admin/integrations`.

### Stage 1 exit gate

- [ ] The check suite is green on `main`.
- [ ] Golden check byte-identical against the last capture made before C1.9 content changes.
  After C1.9, a new capture becomes the baseline.
- [ ] `audit_product_labels.py` is OK on production.
- [ ] Every messaging platform answers as before. Leo spot-checks 5 questions, including the
  duplicate-send case.
- [ ] All non-messaging integrations are `listed`.
- [ ] Sentry receives errors from web and worker.

---

## 6. Stage 2 — waves

### C2.0 Trap-question eval tool

**Goal:** the measuring stick each wave ships against (plan §4.6.8).

**Tasks**
- [ ] **`eval/trap_cases.json` schema:** `{id, platform_type, esp, product, question,
  must_contain: [...], expected: "what a correct answer contains", fails_if: ["claims that make
  it wrong"]}`. Seed it with the plan's §4.6.8 examples, re-checked against stored content.
- [ ] **`eval/trap_eval.py`:**
  - [ ] `run --type <t>`:
    - for each case, `build_rag_context` with the type's arguments, plus the `must_contain` check
      (as in `retrieval_recall.py`);
    - then `ai_client.generate_response` at `AI_TEMPERATURE=0` with the type's prompt;
    - it calls internals directly, so `listed` integrations work;
    - saves prompt hash, context and answer to `eval/results/<date>-traps-<type>/`.
  - [ ] `sheet`: writes `scores.md`, a row per case with the answer and boxes for *trap handled*
    and *describes an undocumented screen*.
  - [ ] `summary`: reads the filled sheet and prints pass/fail for the rule: **≥ 8/10 handled and
    0 undocumented-screen answers**.
- [ ] Tests: schema validation; `summary` parsing on a sample sheet.

**Acceptance:** a dry run on 2 seed cases produces the folder and the sheet.

### Wave template (C2.1–C2.4)

Every wave runs these steps for its platform type.

| step | who | work |
|---|---|---|
| W1 | 🛑 Leo | Final prompt text: save it through the editor (stored), and update `backend/prompts/system_prompt_<type>.txt` so the default matches. Final welcome copy and placeholders (replace the `DRAFT` strings). |
| W2 | dev → 🛑 | Claude drafts 10 trap cases from the type's documents (stored content, read-only), each built on a documented limitation where the obvious answer is wrong. Leo validates `expected` and `fails_if`. |
| W3 | dev | `trap_eval.py run`. First make every `must_contain` pass: fix content or retrieval, not the prompt. Then `sheet`. |
| W4 | 🛑 Leo | Score the sheet. If the rule fails, revise the prompt (W1) and re-run, up to 3 rounds; then stop and decide together. If a type keeps failing, try the other configured providers on the same 10 questions before rewriting more. |
| W5 | 🛑 Leo | Content for the type: proposals approved and labelled (incl. the partner mechanics articles, source `mechanics`), blocked pages pasted, platform types confirmed. |
| W6 | dev → 🛑 | `scripts/activate_integrations.py --type <t>` (dry run lists the integrations Leo chose to activate, each with its labelled documents, and the ones staying `listed` with the reason). Leo runs `--apply`. Created in C2.1; it also supports `--deactivate`. |
| W7 | dev | One week later: errors (Sentry), thin answers per integration, thumbs (after C2.5). Write findings in this file; fix list as follow-up PRs. Update §2 and §10. |

**Watch in W3:** the partner mechanics articles share Query A's 10 chunks with the Yotpo guide
(Query B, today's mechanics query, is off for the new types). If a trap case fails because they
pushed the guide out, turn Query B on for that type or cap them (a measured change, recorded
here), rather than dropping them.

**Gate to activate:**
- the W4 rule passes and is recorded;
- `retrieval_recall.py` and `audit_product_labels.py` are OK;
- the messaging prompt test passes.

### C2.1 Wave: `storefront`

Scope:
- Shopify family: merge `shopify`, `shopify-plus`, `shopify-loyalty`, `shopify-plus-loyalty`,
  `shopify-point-of-sale(-loyalty)`, `shopify-flow(-loyalty)` per Leo.
  - The main `shopify` card links nothing; seed it by hand.
  - Keep the scope boundary (plan §4.1): integration documents only, not general Yotpo-on-Shopify
    setup.
- BigCommerce, Adobe Commerce, Salesforce Commerce Cloud, WooCommerce, Volusion.
- POS: Shopify POS, Square POS by Defsys, Heartland, Teamwork, Fobi, Subtotal, Swapt, Novel.
- Subscriptions: Recharge, Loop, Ordergroove.
- Mobile apps: Tapcart, Fuego, MageNative, Plobal, Vajro, Appbrew, Reactiv, poq.
- Page builders, checkout, on-site, search and personalization tools.

Trap seeds:
- POS free-product reward;
- Recharge renewals;
- Recharge cart minimum on existing subscriptions;
- Recharge on BigCommerce;
- Tapcart with Recharge discounts.

Extra deliverable: `scripts/activate_integrations.py`.

### C2.2 Wave: `service`

Scope: Gorgias, Zendesk, Gladly, Re:amaze, Dixa, HubSpot (CRM side, if typed `service`), Siena,
Rep AI.

Trap seeds:
- Gorgias data freshness;
- Zendesk's retroactive 15-day review requests;
- adjusting points through a custom button;
- Zendesk with several Yotpo stores without Multibrand.

### C2.3 Wave: `content`

**Requires C1.6 to be done.**

Scope: Google (Seller Ratings, Shopping), Meta (Facebook, Instagram), TikTok Shop, Target,
Bazaarvoice, PowerReviews, SoPost, Social Nature, Try & Review, Cohley, ExpertVoice, Skeepers,
Later, Trend, Beautytap, Stellar Reviews, Akeneo.

Trap seeds:
- seller-rating eligibility;
- excluding bad reviews from Google;
- TikTok UK;
- TikTok GTIN immutability;
- SoPost custom questions.

### C2.4 Wave: `data`

Scope: Data & automation (Alloy, MESA, Tray.io, Shopify Flow if typed `data`, Order Desk,
ProductsUp, Fueled), BI (Triple Whale, Glew, Daasity, Stitch, Lexer, Syncly, DaitaFix), privacy
(DataGrail, PieEye), ads (AdRoll, Adscale), gift cards (BHN Rewards/Rybbon, Rise.ai), donations,
shipping.

Plus the **Yotpo API & Webhooks** (`other_webhook`):
- switch its `platform_type` to `data`;
- remove its special-case welcome copy (`app.js:291, 300-314`);
- run its traps with this wave.

Trap seeds:
- the Shopify Flow action name;
- Klaviyo "Forward to Shopify";
- Alloy authentication by product;
- PieEye DSR forwarding.

### C2.5 Deep links + per-answer thumbs

- [ ] `?integration=<name>&product=<p>`:
  - validated against `/api/integrations`;
  - `listed` or unknown → ignore with a toast;
  - never put user data in the URL.
- [ ] Thumbs up/down under each assistant answer.
  - Table `answer_feedback` (`session_id`, `conversation_id`, `esp`, `platform_type`, `product`,
    `rating ±1`, `created_at`); no message text.
  - The admin analytics show the rate per platform type.
- [ ] Tests for the endpoint. Screenshots.

### C2.6 Gate `GET /api/admin/esps`

Only after `/api/integrations` has been in production for ≥ 1 release.
- [ ] Require admin on `GET /api/admin/esps`.
- [ ] Note in ACCOUNT_SYSTEM_PLAN.md that its "intentionally public" decision is superseded.

### C2.7 Messaging context upgrade (optional)

Facts block and integration-style source headers for `messaging` too.
- [ ] Before and after, both at temperature 0:
  - `product_eval.py` cells;
  - `retrieval_recall.py`;
  - the duplicate-send case run 5×.
- [ ] Ship only with no regression. 🛑 Leo decides.

### C2.8 Finalisation

- [ ] **CLAUDE.md:** replace the "Target Architecture", "Data Flow", "System Prompt", "RAG Context
  Retrieval" and "API Endpoints" sections with what was built:
  - platform types;
  - per-type prompts;
  - the catalog import;
  - proposals;
  - portability;
  - remove Pinecone-namespace-per-ESP, FastAPI, S3 and multi-tenancy as targets.
- [ ] **README / START_HERE:** how to run locally safely (§1.1).
- [ ] **Remove:** `backend/vectorize.py` (deprecated), `backend/reranker.py` and
  `backend/property_validator.py` (imported nowhere). Move root one-off scripts (`check_*`,
  `test_*` at the root, `fix_*`, `inspect_*`, `show_*`, `verify_*`, `recrawl_*`, `vectorize_*`) to
  `scripts/archive/`.
- [ ] **ALL_INTEGRATIONS_UPDATE.md:** status "built", with links to the wave results.

---

## 7. Routines and optional work

### R1 🛑 Re-run the catalog import (routine, from C1.9)

Leo, 2026-10-15. The import is how new and changed integrations reach the admin. It is re-run by
hand, not on a schedule (plan §4.3): **every 1–2 months, or when Yotpo announces integrations.**
1. Claude Code runs the dry run, read-only, against a local copy (NEXT_SESSION.md: "Re-running the
   catalog dry run"), with Leo's OK for the model calls, and gives Leo the report in plain words:
   new integrations, new links, renamed or dead guides, cards that disappeared.
2. Leo applies it (`--apply --plan`), then reviews Suggested Links.
3. Claude Code checks the result read-only (`audit_product_labels.py`, the Integrations tab's
   counts).
A re-run only adds: anything approved, rejected or already a document is never suggested again.

### CX.1 Embedding bake-off and index rebuild

**Trigger:** a recurring retrieval miss that the content can't fix, or the memory pressure from the
in-process model.

Follow plan §4.4 exactly:
- dependencies already pinned;
- ≥ 40 cases;
- the pre-registered rule (switch only if the candidate passes ≥ 5 more cases and breaks no
  existing Klaviyo case);
- the model × chunk-header grid;
- the floor re-set from score distributions;
- a side-by-side index built from `esp_documents.content`;
- env-var cutover; the old index kept 2 weeks;
- ids `doc_<uuid>#<i>` computed from `vector_count`, with `rag_context.next_chunk_id` updated.

🛑 Leo approves the vendor, since it receives user questions.

### CX.3 CPU-only torch

**Trigger:** build time, image size or memory on Railway, or the move.

- Install `torch` from PyTorch's CPU wheel index, so the CUDA stack (several GB) is not installed.
  - In the Dockerfile, install `torch` first with `--index-url https://download.pytorch.org/whl/cpu`.
  - Drop the `nvidia-*`, `cuda-*` and `triton` lines from `constraints.txt`.
- This is a dependency change, so it needs Leo's OK.
- Verify: chat retrieval is unchanged (golden check), and an embedding computed before and after is identical.
- Moot if CX.1 moves embeddings to a hosted API.

### CX.2 Separate worker process

**Trigger:** the move off Railway, or web memory pressure.

- Set `RUN_WORKER_IN_PROCESS=false` on web.
- Run a second service from the same image with `python -m workers.main`.

C1.8 already did the work, so this is configuration only.

---

## 8. Definition of done: v2 is finalised when

- [ ] Every catalog integration (Loyalty or Reviews) is either in chat, or not in chat with a
  recorded reason (no guide, gone, or content blocked).
- [ ] All five platform types are live, each with Leo's final prompt and welcome copy.
- [ ] Every non-messaging type passed its trap rule; results are in `eval/results/`.
- [ ] The messaging prompt is byte-identical to v1's (test), unless C2.7 deliberately changed the
  context and was approved.
- [ ] `retrieval_recall.py` passes every case (Loyalty, Reviews, traps); `audit_product_labels.py`
  is OK.
- [ ] Nothing is stored on local disk. The worker can run as its own process. The move off Railway
  is the §3.2 checklist in the plan.
- [ ] Rate limits, Sentry and backups are verified.
- [ ] An admin can find links for any one integration from its page (C1.10), and the catalog import
  has been re-run at least once after C1.9 (R1).
- [ ] CLAUDE.md describes v2, not v1.

---

## 9. Decision log

Decided; don't relitigate. Source: ALL_INTEGRATIONS_UPDATE.md v3 and Leo, 2026-10-13.

| decision | consequence for the build |
|---|---|
| Major update in this repo, not a spinoff | everything lands here |
| We build all integrations; no demand gate | waves are gated on quality only (trap questions) |
| Only Loyalty & Referrals and Reviews (incl. UGC) | the header parser ignores SMS & Email and Subscriptions; Visual UGC counts as Reviews (the catalog groups them as "Reviews & UGC") |
| Railway now, moved later | portability seams in C1.8; nothing Railway-specific |
| Partner pages as today: crawl, or paste if blocked | no robots/User-Agent work |
| No table rename; key is `esps.name` | Python and UI say "integration"; SQL says `esps` |
| Visibility is `status` (`active` / `listed` / `archived`) | older code never lists imported integrations |
| Labels: header pre-fill, human decides per document | no automatic labels from catalog tags or hosts |
| One stored prompt per platform type; messaging stays in today's key | template grammar unchanged; rollback-safe |
| Prompt wording comes per wave from Leo; Appendix C is a draft | `backend/prompts/*.txt` carry a DRAFT header until their wave |
| `other_webhook` stays `messaging` until C2.4 | its current prompt and copy are untouched until then |
| Wave order: storefront → service → content → data | §2 order |
| Lists stored as JSONB (TEXT JSON in SQLite) | refines plan §4.2's `TEXT[]` |
| No multi-integration chat, no alias matcher, no category-scoped knowledge, no automated link-following | out of scope for v2 |
| No coverage tier; two states (in chat / not in chat); products follow the documents (Leo, 2026-10-15) | C1.4 Deviations; plan §4.1's tier is dropped |
| New links keep coming after the first import: the import is re-run by hand every 1–2 months (R1), and any integration can be searched on demand with "Find links" (Leo, 2026-10-15) | C1.10 and R1; still no scheduled discovery: everything found is a suggestion a person approves |
| Partner mechanics are found by a model and approved by a person (Leo, 2026-10-14) | a bounded exception to "no automated link-following": the model lists the partner functions from the integration's own documents and confirms each article by reading it; blocked help centres go to a person; a person approves each integration's final list; source `mechanics`, label pre-filled `shared` (C1.2; plan §4.3) |

---

## 10. Change log

| date | checkpoint | change | by |
|---|---|---|---|
| 2026-10-13 | — | Map created from plan v3 | Claude Code |
| 2026-10-13 | — | CLAUDE.md points to this map, with the production `.env` warning | Claude Code |
| 2026-10-13 | C0.2 | `requirements.txt` pinned and `constraints.txt` added from the production freeze; Dockerfile uses both; CX.3 added | Claude Code |
| 2026-10-13 | C0.2 | Committed on `v2/c0-2-pin-dependencies`, with the plan, the map and the CLAUDE.md pointer | Claude Code |
| 2026-10-13 | C0.1 | `.github/workflows/ci.yml` (jobs `unit`, `postgres`); Postgres tests read `TEST_DATABASE_URL`; ipapi.co stubbed; sparkline assertion fixed | Claude Code |
| 2026-10-13 | C0.1 | PRs #1 and #2 opened; both CI jobs green. The red-run check used the local run where a real failing assertion exited 1 (CI runs only on PRs, so a scratch branch would need another PR) | Claude Code |
| 2026-10-13 | C0.4 | Sources prepared (PR #4): 13 platforms, links checked, 9 flags for Leo | Claude Code |
| 2026-10-13 | C0.2, C0.1 | #1 and #2 merged and deployed by Claude Code; live health and Klaviyo chat checked after each | Claude Code |
| 2026-10-13 | C0.2 | Leo confirmed the admin panel and a crawl after the deploy: done | Leo |
| 2026-10-13 | C1.1 | Schema, key validation, URL identity, chunk counts, both scripts, tests (PR #3); production URL check found 3 rows, fix script prepared | Claude Code |
| 2026-10-13 | C1.1 | Merged and deployed (#3); Leo applied the URL fix and the key rename; live checks OK: done | Claude Code |
| 2026-10-13 | — | NEXT_SESSION.md: hand-off agenda for the next session | Claude Code |
| 2026-10-14 | C1.2 | Header parser, catalog import (dry run by default, `--apply` from a saved plan), partner mechanics articles (Leo's request), fixtures, tests, live dry-run report | Claude Code |
| 2026-10-15 | C1.2 | Partner mechanics rebuilt to Leo's design (model lists functions from the integration's own documents, confirms articles by reading them; blocked centres to a person; person approves each list); crawler reads JSON-LD article text; PR #5 merged and deployed | Claude Code |
| 2026-10-15 | — | Found that GitHub Actions has never run on this repo; PRs are now opened by Claude Code through the API | Claude Code |
| 2026-10-15 | C0.4 | Leo approved the sources; PR #4 merged | Claude Code |
| 2026-10-15 | C1.4 | Integrations and Proposals tabs, crawl summary, owner/editor roles, listed integrations documentable; independent review, findings fixed; practice import into a local SQLite copy (no model calls) | Claude Code |
| 2026-10-15 | C1.4 | Crawl box hidden unless something is waiting, failed or crawled during the visit (Leo) | Claude Code |
| 2026-10-15 | C1.4 | Leo: the "i" popups work on hover, focus and click; coverage tier removed; Hidden merged into Not in chat; products ticked from documents | Claude Code |
| 2026-10-15 | C1.10, R1 | Leo: re-run the import by hand every 1–2 months (R1) and add "Find links" per integration (C1.10); both added | Claude Code |
| 2026-10-15 | C1.4 | PR #6: CI green (both jobs, incl. the new Postgres test); merged and deployed; live smoke check OK | Claude Code |
| 2026-10-15 | C1.7 | Prompts by platform type: four shipped drafts, per-type storage, audit and undo, facts block, integration source headers, editor with preview; `test_prompts_by_type.py` (16 checks); golden check 26/26 identical | Claude Code |
