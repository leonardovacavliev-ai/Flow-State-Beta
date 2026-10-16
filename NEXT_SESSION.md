# Next session: agenda for the next agent

Written 2026-10-16 at the end of the fifth v2 build session (C1.10 Find links and the Add
integration dialog, then C1.3 refresh pipeline, both merged and deployed). Read this first, then
[ALL_INTEGRATIONS_ROADMAP.md](ALL_INTEGRATIONS_ROADMAP.md) §0–§2. Replace this file at the end of
your session with the agenda for the one after.

## 1. Where things stand

**Live in production (merged to `main`, deployed, smoke-checked).** Details of each are in the
roadmap's checkpoint sections, under Deviations.

| PR / commit | checkpoint | what it did |
|---|---|---|
| #1 | C0.2 | Dependencies pinned to production's own freeze (`requirements.txt`, `constraints.txt`, Dockerfile) |
| #2 | C0.1 | CI workflow. **Deleted 2026-10-16** (`dc79c2a`) at GitHub's request (§5); the tests run locally |
| #3 | C1.1 | Integration schema, `platform_type`, `document_proposals`, key validation in chat, URL normalisation, `vector_count` |
| #4 | C0.4 | `docs/integrations/messaging_sources.md`: help links for the 13 missing email/SMS platforms (docs only) |
| #5 | C1.2 | Yotpo guide header parser; `scripts/import_catalog.py` (dry run; `--apply` is C1.9); partner mechanics (below) |
| #6–#9 | C1.4 | Admin **Integrations** and **Suggested Links** tabs, owner/editor roles, plain wording, "i" popups, two states (In chat / Not in chat), products from documents, crawl box |
| #10 (`55124c7`) | C1.7 | A system prompt per platform type (four drafts in `backend/prompts/`), facts block, editor with preview. Messaging unchanged |
| `4030b87` | I10 | No integration without its category |
| `fecd270` | C1.10 | **Find links** per integration (`backend/link_finder.py`, shared with the yotpo.com import; `backend/find_links_job.py`, a background run; the Find links card) and the **Add integration** dialog (name, kind, optional website; adding starts Find links at once). Find links fetches only public addresses |
| `dbf63cb` | C1.3 | **Refresh pipeline** (`backend/refresh.py`, `refresh_routes.py`, `sitemap_refresh.py`): unchanged text isn't re-indexed; Yotpo guides read with their own rule; title/plans/platforms stored on crawl; support.yotpo.com's sitemap read **monthly** (the 1st, 03:17 UTC, and at boot when overdue; Leo); pages missing 3 times offer Retire / Replace; retired documents left out everywhere they would count |

Last live smoke check (2026-10-16 16:27, after `dbf63cb`): health 200, Klaviyo loyalty chat
answered with 15 sources, unknown integration 400, `/api/admin/sitemap-changes` and
`/api/admin/integrations/<name>/find-links` 403 without sign-in.

**The first sitemap read** runs by itself about ten minutes after that deploy (no read on record
yet). It only *records* the ~700 articles: it re-crawls nothing (Leo's call, below). The Suggested
Links tab, section "New on support.yotpo.com", shows it and counts our guides that Yotpo changed
since their last crawl.

**Partner mechanics (C1.2, Leo's design; keep it).** Per integration, a model (Gemini Flash, the
app's `GEMINI_API_KEY`) lists the partner functions the integration touches from the integration's
own documents, code searches the partner's help centre, and the model accepts only articles whose
text explains a function; blocked help centres go to a person; a person approves the final list.
Leo rejected two earlier versions (general "Welcome" articles; hand-made topic lists): don't bring
them back. Last catalog dry run: `docs/integrations/catalog_dry_run.md` (2026-10-14/15).

**Open, waiting for Leo** (tell him in plain words when it's relevant; none blocks the next work):
1. **C0.4**: he adds the 13 email/SMS platforms (Integrations tab → **+ Add integration**, kind
   Email & SMS, the names `catalog_import.KNOWN_MATCHES` expects, e.g. "Salesforce Marketing
   Cloud"). Find links suggests each one's links; he approves them in Suggested Links, adds what
   `messaging_sources.md` lists and Find links missed, and crawls or pastes them. Then you do C0.4's
   per-platform retrieval check.
2. **C1.7 drafts**: he reads the four non-messaging prompt drafts once (General Settings → Kind of
   platform). Final wording comes per wave.
3. **Yotpo guides re-crawled with the new rule**: only those Yotpo changes are re-crawled, from the
   second monthly read on. Re-crawling all of them at once, sooner, is his call (then run
   `eval/retrieval_recall.py`).
4. **Glued words on other sites**: every non-Yotpo page still loses the spaces around its links
   ("go toRecharge Marketplaceand"). Fixing the general rule changes every page on its next crawl:
   his decision.
5. **Before the first non-messaging wave**: should a chat whose integration type can't be read be
   refused instead of answered with the messaging prompt? (roadmap C1.7 Deviations)
6. **Not built, offered**: a daily cap on Find links runs (he asked why one is needed; none built);
   integration delete (owner-only; a catalog one would come back on the next import).
7. **Never run**: Find links with the real model (spends the chat's Gemini credit; tests use a fake
   one), and every Postgres test since CI was removed (no `TEST_DATABASE_URL`). Ask him how he wants
   database code tested when it matters.
8. **Pre-existing, from C1.4**: chat's integration check lets a message through when the database
   check fails, and the public Reviews-coverage list includes listed integrations' names. Both
   matter once listed integrations have indexed documents (after C1.9).

## 2. How to work with Leo (he asked for these)

- **Plain language, no jargon.** Each message: what was done and why it matters in a sentence or
  two, then whether anything is needed from him, as short numbered steps with exact clicks or
  commands.
- **Review every change before committing and before pushing.** Read the whole diff, and before a
  merge run an independent reviewer agent on the branch. This session's reviews found real bugs
  both times (an SSRF hole in Find links; retired documents that could come back into chat).
- **You merge and deploy, without asking** (Leo, 2026-10-15: "do the pulls and deploys, just go").
  Merge only when the local suite is green and the diff is reviewed; smoke-check after each deploy
  (§4); if it fails, revert the merge commit and tell him.
- **Data-changing scripts on production stay his** (`--apply`, `--write`, rebuilds). Give him the
  exact command, then verify it with the read-only checks. Read-only checks against production
  (roadmap §1.1 list: golden check, recall, label audit, seeding a local copy) are yours to run.
- **Ask before anything that spends Gemini credit at volume** (the key is the live chat's prepaid
  one; dry runs once emptied it).
- **The safety filter** once blocked a schema-changing merge (#3). Don't work around a block:
  explain it to Leo and ask.
- ⛔ **Never use the GitHub API from Leo's account** (Leo, 2026-10-16): no `curl` to
  `api.github.com`, no PRs opened or merged by API, no polling of Actions or deploy statuses, no
  `gh`. GitHub restricted his account twice after sessions that did. Plain `git` only, a handful of
  times per checkpoint. ⛔ No GitHub Actions workflow without his explicit OK.
- **Don't ask Leo to replace or rotate keys.**
- Leo does these himself: sign in to the admin (Google), run production data scripts.

## 3. Next work, in order

1. **C1.5 Chat: integration picker, `/api/integrations`, copy by type.** The design prototype is
   `design/integrations-redesign.html` (Chat screen; untracked: **don't commit it**, Leo). Products
   follow the documents (`admin_integrations_routes.effective_products`): use the same rule.
   `TYPES_IN_CHAT` stays messaging-only: each type joins chat in its wave, Leo decides. The Usage
   Analytics additions in that design (plan §4.9) come with or after C1.5.
2. **C1.6 Reviews readiness.**
3. **C1.8 Portability seams, Sentry, no local disk** (unblocked now C1.3 is done). It also moves
   the in-memory "one run at a time" checks of Find links and the sitemap into the database if the
   app is ever to run more than one web process (§5).
4. **Small follow-ups** (each a short branch, any time): Find links reads C1.3's `sitemap_urls`
   instead of fetching the sitemap; `test_crawl_pacing.py postgres` gains the C1.3 worker paths
   once there is a test database.
5. **C0.4**, once Leo has added the platforms (§1 item 1).
6. **C1.9** (Leo's production import) waits for C1.2–C1.8 deployed. From then on, **R1**: the
   catalog import re-run by hand every 1–2 months (roadmap §7). A dry run from an empty cache takes
   well over an hour and ~250 model calls: ask Leo first.

## 4. Procedures that worked

**Work in a worktree under the scratchpad**, never in the main checkout:
`git worktree add -b v2/<id>-<slug> <scratch>/wt origin/main`. The main checkout stays on `main`
with only `design/` and `production-freeze.txt` untracked; fast-forward it (`git merge --ff-only
origin/main`) after each merge so Leo's files match git.

**The local suite, network blocked.** Put a `sitecustomize.py` in a scratch folder that makes
`socket.connect` and `getaddrinfo` raise for anything but localhost; run with
`PYTHONPATH=<that folder> HF_HUB_OFFLINE=1 VECTOR_DB_PROVIDER=chromadb DATABASE_PROVIDER=sqlite
SESSION_PROVIDER=memory`:
```
backend/test_prompt_template.py  backend/test_product_write_paths.py  backend/test_conversation_seed.py
backend/test_crawl_pacing.py  "backend/test_analytics_providers.py sqlite"  eval/test_product_scorer.py
backend/test_integrations_schema.py  backend/test_doc_header.py  backend/test_catalog_import.py
backend/test_admin_integrations.py  backend/test_prompts_by_type.py  backend/test_find_links.py
backend/test_refresh_pipeline.py
```
plus the import smoke test (roadmap §1.1). `test_admin_integrations.py` prints a harmless
"disk I/O error" from the analytics flush; look for its "9/9 passed".

**Merge and deploy** (from a scratch worktree):
```bash
git fetch origin
git worktree add --detach <scratch>/mainwt origin/main
cd <scratch>/mainwt
git merge --no-ff origin/<branch> -F <scratch>/mergemsg.txt   # -F - (stdin) does not work here
git push origin HEAD:main
```
The merge message carries what a PR description would (what changed, checks, review). **Other
sessions push to `main` too** (2026-10-16: two styling commits landed while C1.3 merged). If the
push is refused, `git fetch`, `git reset --hard origin/main` in the scratch worktree, merge again,
and resolve conflicts; so far they were only the `?v=` cache-busters in `index.html`: give the file
you changed a fresh value and keep the other side's for the files you didn't. Run the suite on the
merged tree before pushing.

**Is GitHub reachable?** `git ls-remote origin refs/heads/main` (plain git). Don't `curl` the API:
auto mode refuses it, and Leo's rule forbids it anyway.

**After a deploy** (~12 minutes; don't poll GitHub): check the live site
(`https://flow-state-beta-production.up.railway.app`) serves the new `?v=` in `index.html`, then:
- `GET /api/health` → 200;
- `POST /api/session/init`, then `POST /api/chat` with `esp: klaviyo`, `product: loyalty` and a
  real question → an answer and ~15–16 sources;
- an unknown `esp` → 400 "Unknown integration. Reload the page.";
- new admin routes without sign-in → 403.

**Golden context check (I3)**, read-only against the live index (SQLite for the database, the model
stubbed). Capture on `origin/main`, check on the branch, back to back:
```bash
git worktree add --detach <scratch>/golden-base origin/main
ln -s "<main checkout>/.env" <scratch>/golden-base/.env
ln -s "<main checkout>/.env" <scratch>/wt/.env
(cd <scratch>/golden-base && python3 eval/check_context_unchanged.py capture <scratch>/golden.json)
(cd <scratch>/wt && python3 eval/check_context_unchanged.py check <scratch>/golden.json)
rm <scratch>/golden-base/.env <scratch>/wt/.env
```
Confirm the cases are status 200 with model input ("identical" also holds when both sides fail).

**Try the admin locally** (how C1.10 and C1.3 were checked): add a temporary entry to the main
checkout's `.claude/launch.json` that starts `app.py` from your worktree with every provider set by
hand (`DATABASE_PROVIDER=sqlite`, `SQLITE_DB_PATH=<scratch>/local.db`, `SESSION_PROVIDER=memory`,
`USE_ASYNC_CRAWL=false`, `VECTOR_DB_PROVIDER=chromadb`, `CHROMA_PERSIST_DIR=<scratch>/chroma`,
`GEMINI_API_KEY=` and the other keys and `DATABASE_URL=` empty, `ADMIN_PASSWORD_FALLBACK=true`,
`ADMIN_PASSWORD=local-only`), with no `.env` in the worktree; restore the file afterwards. In the
browser set `window.Auth.headers` to send `X-Admin-Password: local-only` and
`isSignedIn`/`isAdmin` to true, then `openAdminPanel()`. Override `window.confirm`/`prompt` to test
their flows. Local crawls write `docs/<name>/` and `docs/crawl_metadata.json` in the worktree:
restore them before committing. `eval/seed_local_db.py` copies production's knowledge base
read-only into a local file when you need real rows. Screenshots in the browser pane can lag; read
the page text to confirm.

**Testing the crawl worker without Postgres**: its job claiming is Postgres-only, but
`_process_job` runs on SQLite through a wrapper that rewrites `NOW()` to `CURRENT_TIMESTAMP`, with
the queue's extra columns added to the test database (`backend/test_refresh_pipeline.py`).

## 5. Watch out for

- **`.env` is production** (Postgres and Pinecone). Never start the app with it plain; tests set
  their own environment before importing.
- **Two in-memory guards assume one web process** (`--workers 1` in Procfile and Dockerfile):
  Find links' "one run per integration, two at once", and the sitemap's "one read at a time". If
  the app ever runs more web processes (C1.8, CX.2), move them into the database.
- **Find links fetches only public web addresses** (`link_finder.public_address_problem`, every
  request and redirect hop). Keep it that way for anything that fetches an address an admin typed or
  a page linked.
- **Retired documents** keep their rows (`crawl_status = 'retired'`, `retired_at`); a hand crawl
  brings one back; a retired URL is still refused as a duplicate when re-added. Any new query that
  counts, crawls or indexes documents must leave them out (roadmap C1.3 lists the ones that do).
- **The unchanged skip** trusts `content_hash`, `vector_count` and the saved filename. A change of
  chunking or embedding is applied by Rebuild Vectors, not by re-crawls.
- **Yotpo guides change text when re-crawled** (C1.3 rule). A golden check made across such a
  re-crawl differs for that reason alone.
- **Listed integrations are found by name** (`get_esp_by_name`, `find_documents_by_url` see
  `active` and `listed`); chat (`is_active_integration`) and the sidebar (`list_esps`) see `active`
  only. Keep it that way (I4).
- **No integration without its category** (I10): any new way of adding one must require it.
- **The catalog dry run and Find links spend the live chat's Gemini credit.** Ask first.
- **GitHub restricted Leo's account twice** (2026-10-15/16) after API-driven PR work and status
  polling; its notice named Actions. Hence §2's ⛔ rules.
- **Temporary folders are wiped overnight.** Push branches as you go.
- **Untracked, leave them**: `production-freeze.txt` (Leo's raw `pip freeze`; `constraints.txt` is
  its content), `design/` (the prototype, and `uncommitted-plan-notes-2026-10-13.patch`: a design
  session's notes set aside, also in `git stash@{0}`; they predate C1.4 and partly contradict later
  decisions, so bring one into the plan only when its checkpoint needs it).
- **Local Python is 3.9, production 3.11.** The pins don't install on 3.9, but the installed
  packages run the suite. Write code that runs on both (e.g. `sitemap_refresh.parse_lastmod` pads
  fractions of a second for 3.9). No Docker locally.
- **Chat validates the integration key** against active rows (60 s cache): a tool driving
  `/api/chat` on an empty database must create the integration first.
- **First deploy after a dependency change is slow** (the CUDA stack reinstalls); CX.3 is the fix
  if it starts to hurt.
