# Next session: agenda for the next agent

Written 2026-10-13 after the first v2 build session; updated 2026-10-15 after the second (C1.2),
the third (C0.4 merge, C1.4) and the fourth (C1.7, not yet merged: see "Open, waiting" below).
Read this first, then
[ALL_INTEGRATIONS_ROADMAP.md](ALL_INTEGRATIONS_ROADMAP.md) §0–§2. Replace this file at the end of
your session with the agenda for the one after.

## 1. Where things stand

**Live in production (merged to `main`, deployed, smoke-checked):**

| PR | checkpoint | what it did |
|---|---|---|
| #1 | C0.2 | Dependencies pinned to production's own freeze (`requirements.txt`, `constraints.txt`, Dockerfile) |
| #2 | C0.1 | CI: `.github/workflows/ci.yml`, jobs `unit` (pure + SQLite) and `postgres` |
| #3 | C1.1 | Integration schema, `platform_type`, `document_proposals`, key validation in chat, URL normalisation, `vector_count` |
| #4 | C0.4 | `docs/integrations/messaging_sources.md`: help links for the 13 missing email/SMS platforms, approved by Leo 2026-10-15 (docs only) |
| #6 | C1.4 | Admin **Integrations** tab (list, filters, an integration's page, crawl summary) and **Proposals** tab (the import's inbox); owner/editor roles (`ADMIN_OWNER_EMAILS`, unset = all owners); listed integrations can be documented before they go into chat; only messaging can be active; `--apply` stores the inbox's notes. Details: roadmap C1.4 Deviations |
| #7 | C1.4 | Plain wording in the admin (In chat / Not in chat, Kind of platform, Suggested Links, "the yotpo.com import"), explanations behind "i", product ticks in the list, nothing pre-ticked; plan: C1.10 "Find links" and R1 |
| #8 | C1.4 | Working "i" popups (hover, focus, click); coverage tier ("Ready / Missing documents") removed; Hidden merged into Not in chat (admin can't set `archived`); Loyalty/Reviews ticked automatically from labelled documents (computed, locked) |
| #9 | C1.4 | Crawls box shown only when something is waiting, failed, never crawled, or crawled since the tab was opened |
| #5 | C1.2 | Yotpo guide header parser; `scripts/import_catalog.py` (catalog → integrations and proposals; dry run, `--apply` from a saved plan); partner mechanics (below); crawler reads JSON-LD article text on empty-shell pages. Nothing imported yet: `--apply` is C1.9 |

Production data steps Leo ran on 2026-10-13:
- `scripts/fix_url_spellings.py --apply`: the 3 links stored with a `#section` were tidied (row and
  vectors). `eval/check_url_normalisation.py` now reports 0, and `audit_product_labels.py` is OK
  (577 vectors, 95 rows).
- `scripts/normalize_esp_keys.py --apply`: 16 `esp_selections` rows renamed `other/webhook` →
  `other_webhook`. The dashboard recomputes its daily aggregates on its next load.

**Partner mechanics (C1.2, Leo's design, 2026-10-14/15).** Besides the Yotpo guides, every
integration needs the partner's own articles on the functions the integration touches (Klaviyo flow
triggers, Recharge subscription discount codes). Per integration, `backend/app_mechanics.py` and
`backend/mechanics_ai.py` (Gemini Flash, the app's `GEMINI_API_KEY`):
1. read the Yotpo guides, the partner's Yotpo pages and the partner help centre's own Yotpo articles;
2. the model lists the partner functions the integration touches;
3. code searches the help centre (Zendesk API, or the model picks from the centre's titles);
4. code reads each candidate, the model accepts only articles whose text explains a function;
5. help centres that can't be read automatically (bot check, login, moved, browser-only) go to a
   person; **a person approves each integration's final list in the admin (C1.4)**.
Leo rejected two earlier versions (general "Welcome to the app" articles; hand-made topic lists).
Don't bring them back. Last dry run (2026-10-14/15): 272 articles for 65 integrations, 39 for a
person, 37 with no help centre found, 13 where the model accepted nothing. Report:
`docs/integrations/catalog_dry_run.md`.

**Open, ready to merge — blocked by GitHub, not by the code:**
- **PR #10, C1.7** (branch `v2/c1-7-prompts-by-type`, head `11d7320`): a system prompt per platform
  type, the four shipped drafts, the integration facts block, the editor's kind picker and preview.
  Email & SMS unchanged: golden check 26/26 identical (run twice, before and after the review
  fixes), all local suites green, independent review done and its findings fixed (roadmap C1.7
  Deviations). **Not merged** because on 2026-10-15 ~17:40 the account was restricted again:
  `https://api.github.com/users/leonardovacavliev-ai` returned 404, the first CI run was
  cancelled by the fix push and no run started for `11d7320` (Actions lists 0 runs). Next session:
  check that URL; once it returns 200, check CI runs on the PR (push an empty commit if none
  starts), then merge, deploy and smoke-check (§4). After the deploy, ask Leo to read the four
  drafts once (Admin → General Settings → Kind of platform), and set the C1.7 row to `done`.

**Open, waiting for Leo:**
- **C0.4:** Leo creates the 13 email/SMS platforms in the admin (Integrations tab → Create New
  Integration, owner only), adds and labels each link from `docs/integrations/messaging_sources.md`,
  and crawls or pastes them. Use the names the import expects (`catalog_import.KNOWN_MATCHES`), e.g.
  "Salesforce Marketing Cloud" → `salesforce_marketing_cloud`. Then you do the per-platform
  retrieval check C0.4 describes.
- **C1.4:** done (#6–#9); Leo confirmed the "i" popups work. Suggested Links is empty until
  C1.9's import. Optionally he sets `ADMIN_OWNER_EMAILS` on Railway. The screen vocabulary and
  Leo's later decisions (no coverage tier, two states, products from documents, crawl box) are in
  the roadmap's C1.4 Deviations: follow them in C1.5 and later UI work.
- **Integration delete:** offered to Leo (not built). If he wants it: owner-only, deletes vectors
  and rows; a catalog integration comes back on the next import unless that is handled.
- **A suggested task** (chip in the session that built C1.4): chat's integration check lets a
  message through when the database check fails, and the public Reviews-coverage list includes
  listed integrations' names. Both are pre-existing; they matter once listed integrations have
  indexed documents (after C1.9).

## 2. How to work with Leo (he asked for these)

- **Plain language, no jargon.** Every message says what was done and why it matters in a
  sentence or two, then whether anything is needed from him, as short numbered steps with exact
  commands or clicks. He said he could not follow a jargon-heavy summary.
- **Review every change before committing and before pushing.** Read the whole diff. This
  session's review caught a real bug: the hidden `global` row would have been typed `messaging`.
- **You merge and deploy** (his decision, roadmap §0.3). Railway deploys every push to `main`.
  Merge only when CI is green, the diff is reviewed, and the checkpoint's pre-merge 🛑 steps are
  done. Smoke-check after each deploy (§4). If it fails, revert the merge commit and tell him.
- **Data-changing scripts on production stay his** (`--apply`, `--write`, rebuilds). Give him the
  exact command, then verify it afterwards with the read-only checks.
- **Read-only checks against production** may be run by you: he approved this session's (the URL
  check and the key-rename dry run). The roadmap §1.1 list applies otherwise.
- **The safety filter blocked one merge** (#3, the first one that changes the live database
  schema). Don't work around it. Explain it to Leo and ask. He then said "merge 3", and it went
  through.
- **Open PRs, merge and deploy yourself, without asking** (Leo, 2026-10-15, firmly: "do the
  pulls and deploys, just go"). Report when done. See §4 for the API commands.
- Leo still does these himself: open the admin panel (Google sign-in) and run production data
  scripts.

## 3. Next work, in order

1. **Next** (each its own branch; C1.1, C1.2 and C1.4 are done, C1.7 waits only for the merge):
   C1.3 refresh pipeline, C1.5 chat picker, C1.6 Reviews readiness. C1.8 waits for C1.3.
   Suggested order: finish **C1.7** (above; `TYPES_IN_CHAT` deliberately stays messaging-only,
   each type joins chat in its wave — Leo decides), then **C1.3** (the Suggested Links tab's
   sitemap section and the retire/replace buttons wait for it), then **C1.10 "Find links"** (Leo,
   2026-10-15: needed for a complete product; same Gemini key as the app, by Leo's choice; ask
   him whether he wants a daily cap before shipping it), then C1.5, C1.6.
   - From C1.9 on, **R1**: the catalog import is re-run by hand every 1–2 months (roadmap §7).
   - C1.5 has a design prototype (`design/integrations-redesign.html`, Chat screen; untracked,
     **don't commit it**: Leo, 2026-10-15). Use it as the baseline.
   - The Usage Analytics additions in that design (plan §4.9) need C1.5's picks of listed
     integrations and a source count per chat message; build them with or after C1.5.
2. **C0.4**, once Leo has created the platforms (see §1).
3. **Re-running the catalog dry run** (e.g. after help centres are added to
   `scripts/help_centres.json`), read-only, against a local copy of the knowledge base:
   ```bash
   python3 eval/seed_local_db.py /private/tmp/<scratch>/seed.db
   DATABASE_PROVIDER=sqlite SQLITE_DB_PATH=/private/tmp/<scratch>/seed.db python3 scripts/import_catalog.py --cache /private/tmp/<scratch>/cache --plan /private/tmp/<scratch>/plan.json --report /private/tmp/<scratch>/report.md
   ```
   From an empty cache this takes **well over an hour** (1 request/s per host, ~1,500 pages) and
   ~250 model calls (~1M tokens). **Ask Leo first** (§5: it spends the live chat's Gemini
   credit). Run it in the background. Then copy the report
   to `docs/integrations/catalog_dry_run.md`.

## 4. Procedures that worked

**Merge and deploy** (from a scratch worktree, so the main checkout is never switched):
```bash
git fetch origin
git worktree add --detach /private/tmp/<scratch>/mainwt origin/main
cd /private/tmp/<scratch>/mainwt
git merge --no-ff origin/<branch> -m "Merge pull request #N from leonardovacavliev-ai/<branch>"
git push origin HEAD:main
```
Railway reports each deploy to GitHub. Poll
`https://api.github.com/repos/leonardovacavliev-ai/Flow-State-Beta/deployments?per_page=1` for the
merge commit's sha, then its `statuses_url` until `success`. A deploy took about 12 minutes.

**Smoke check** (live: `https://flow-state-beta-production.up.railway.app`):
- `GET /api/health`;
- `POST /api/session/init`, then `POST /api/chat` with `esp: klaviyo`, `product: loyalty` and a
  real question. Expect an answer and ~16 sources;
- since C1.1: an unknown `esp` gets 400 "Unknown integration. Reload the page.";
- ask Leo to open the admin panel and crawl one link.

**Golden context check (I3)**, read-only against the live index. Capture on the base code, then
check on the branch, back to back:
```bash
git worktree add /private/tmp/<scratch>/golden-base origin/main
cp eval/check_context_unchanged.py /private/tmp/<scratch>/golden-base/eval/   # if the tool changed
ln -s "$PWD/.env" /private/tmp/<scratch>/golden-base/.env
(cd /private/tmp/<scratch>/golden-base && python3 eval/check_context_unchanged.py capture /private/tmp/<scratch>/golden.json)
python3 eval/check_context_unchanged.py check /private/tmp/<scratch>/golden.json
```
Also confirm the captured cases are status 200 with model input. "Identical" also holds if both
sides failed.

**Prove a test needs no network:** put a `sitecustomize.py` in a scratch folder that makes
`socket.connect` and `getaddrinfo` raise for anything but localhost, then run the suite with
`PYTHONPATH=<that folder> HF_HUB_OFFLINE=1`. This session found two network calls that way
(ipapi.co in the analytics test, huggingface.co on model load).

**Open, check and merge a PR without `gh`** (do it yourself; never send Leo a link to click). The
token comes from the macOS keychain via git; never print it:
```bash
TOKEN=$(printf "protocol=https\nhost=github.com\n\n" | git credential fill | sed -n 's/^password=//p')
API=https://api.github.com/repos/leonardovacavliev-ai/Flow-State-Beta
# open
curl -s -X POST -H "Authorization: Bearer $TOKEN" $API/pulls -d '{"title":"…","head":"<branch>","base":"main","body":"…"}'
# merge (merge commit, like the earlier PRs)
curl -s -X PUT -H "Authorization: Bearer $TOKEN" $API/pulls/<N>/merge -d '{"merge_method":"merge","commit_title":"Merge pull request #<N> from leonardovacavliev-ai/<branch>"}'
# deploy: Railway posts a commit status on the merge sha
curl -s -H "Authorization: Bearer $TOKEN" $API/commits/<sha>/status
```
**CI may not run on GitHub**: on 2026-10-15 Actions showed 0 runs ever while the account was
restricted (see §5); check whether runs appear again once it is lifted. Run the §1.4 suite locally (network blocked, see above) before merging and say so in the
PR. The Postgres jobs need `TEST_DATABASE_URL`, which isn't available locally. Tell Leo if a change
touches the database code; fixing Actions (billing or settings) is his.

**Try the admin in the built-in browser, on local data only** (how C1.4 was checked):
- Seed a scratch SQLite: `python3 eval/seed_local_db.py <scratch>/local.db` (reads production
  read-only; needs `.env`, so link it in for this one command and remove the link after).
- Optional: `DATABASE_PROVIDER=sqlite SQLITE_DB_PATH=<scratch>/local.db GEMINI_API_KEY= python3
  scripts/import_catalog.py --no-mechanics --cache <scratch>/cache --plan <scratch>/plan.json`
  (about 10 minutes, no model calls), then `--apply --plan` into the **same local file**.
- Add a temporary entry to the main checkout's `.claude/launch.json` that starts `app.py` from your
  worktree with every provider set by hand (`DATABASE_PROVIDER=sqlite`, `SQLITE_DB_PATH`,
  `SESSION_PROVIDER=memory`, `USE_ASYNC_CRAWL=false`, `VECTOR_DB_PROVIDER=chromadb`,
  `GEMINI_API_KEY=` and the other keys empty, `ADMIN_PASSWORD_FALLBACK=true`,
  `ADMIN_PASSWORD=local-only`), with no `.env` in the worktree. Restore the file afterwards.
- The page has no password sign-in: in the browser, set `window.Auth.headers` to send
  `X-Admin-Password`, `isSignedIn`/`isAdmin` to true, then call `openAdminPanel()`.
- Crawls and pastes write `docs/` and `docs/crawl_metadata.json` in the worktree: remove or restore
  them before committing.

**The app's PR panel can't follow PRs here** (`bind_pr` needs `gh`). Read CI from the Actions API
for the branch's sha, at most once a minute.

## 5. Watch out for

- **Listed integrations are found by name** (C1.4): `get_esp_by_name` and `find_documents_by_url`
  see `active` and `listed` rows, so their documents can be approved, crawled and indexed before
  they go into chat. Chat (`is_active_integration`) and the sidebar (`list_esps`) still see
  `active` only; `test_admin_integrations.py` checks it. Keep it that way.

- **Another session is working on a design** (`design/integrations-redesign.html`, untracked).
  It edited `ALL_INTEGRATIONS_ROADMAP.md` (C1.4/C1.5 design notes, an analytics deviation) and
  `ALL_INTEGRATIONS_UPDATE.md` (§4.7–4.9) in the main checkout **without committing**. Don't
  commit or discard those edits as your own. Ask Leo whether to commit them. Until then, record
  your progress from a worktree, or stage only your own lines. This session did it like this:
  write the edited file from `git show HEAD:<file>`, then
  `git update-index --cacheinfo 100644,$(git hash-object -w <file>),<path>`.
  The main checkout is on `main`. The other session's edits were carried over with `git stash`;
  the stash entry is kept, and a backup sits in
  `/private/tmp/claude-502/other-session-backup/`. Uncommitted edits to a file make `git switch`
  refuse when the branches differ there, so work in worktrees.
- **The catalog dry run spends the live chat's Gemini credit.** `.env`'s `GEMINI_API_KEY` is
  production's, on a prepaid balance. The 2026-10-14/15 dry runs (~2.3M tokens) emptied it and
  live chat failed with 429 "prepayment credits are depleted" until Leo topped it up. Don't run
  the mechanics dry run (or anything else that calls Gemini at volume) without Leo's OK, and ask
  him for a separate development key first.
- **GitHub restricted the account once (found 2026-10-15).** Railway failed with "couldn't find
  the repo", Actions showed 0 runs ever, and `https://api.github.com/users/leonardovacavliev-ai`
  returned 404 to everyone else. Leo had it lifted the same day. If a deploy fails at "Snapshot
  code" or Actions history vanishes, check that URL first (200 = fine), and stop merging until it
  is. Poll GitHub at most once a minute (the 20-second polling that day ran into the API limit).
- **Temporary folders are wiped overnight.** The scratchpad and worktrees under `/private/tmp`
  disappeared between 2026-10-14 and 10-15, with the dry-run page cache. Push branches as you go;
  keep nothing only there.
- **Partner mechanics: Leo's design, keep it.** No hand-made topic lists and no human picking,
  except where a help centre blocks automated reading. The model lists the functions from the
  integration's own documents and confirms articles by reading them; a person approves the final
  list. A dry run needs `GEMINI_API_KEY`; tests use a fake model. Two runs can differ slightly.
- **`production-freeze.txt`** (untracked) is Leo's raw `pip freeze`. Its content is
  `backend/constraints.txt`. Leave it, or ask before deleting.
- **Local Python is 3.9; production and CI are 3.11.** The pins don't install on 3.9, but the
  already-installed packages run the suite. There is no Docker locally.
- **`.env` is production.** Never start the app with it plain. Tests set their own environment
  before importing. The Postgres tests need `TEST_DATABASE_URL` (CI provides one).
  `test_integrations_schema.py postgres` never falls back to `.env`.
- **Chat now validates the integration key** against active `esps` rows, with a 60 s cache
  (`ESPManager.is_active_integration`). Any test or tool driving `/api/chat` on an empty database
  must create the integration first. `check_context_unchanged.py` does.
- **The `platform_type` boot seed ran once** and is recorded in `app_settings`
  (`seed:platform_type_messaging`). New integrations get their type from `create_esp`, which
  defaults to `messaging`; C1.2's import sets its own.
- **First deploy after a dependency change is slow**: the full CUDA stack reinstalls (several
  GB). If build time or image size starts to hurt, that is CX.3's trigger.
