# Next session: agenda for the next agent

Written 2026-10-13, at the end of the first v2 build session. Read this first, then
[ALL_INTEGRATIONS_ROADMAP.md](ALL_INTEGRATIONS_ROADMAP.md) §0–§2. Replace this file at the end of
your session with the agenda for the one after.

## 1. Where things stand

**Live in production (merged to `main`, deployed, smoke-checked):**

| PR | checkpoint | what it did |
|---|---|---|
| #1 | C0.2 | Dependencies pinned to production's own freeze (`requirements.txt`, `constraints.txt`, Dockerfile) |
| #2 | C0.1 | CI: `.github/workflows/ci.yml`, jobs `unit` (pure + SQLite) and `postgres` |
| #3 | C1.1 | Integration schema, `platform_type`, `document_proposals`, key validation in chat, URL normalisation, `vector_count` |

Production data steps Leo ran on 2026-10-13:
- `scripts/fix_url_spellings.py --apply`: the 3 links stored with a `#section` were tidied (row and
  vectors). `eval/check_url_normalisation.py` now reports 0, and `audit_product_labels.py` is OK
  (577 vectors, 95 rows).
- `scripts/normalize_esp_keys.py --apply`: 16 `esp_selections` rows renamed `other/webhook` →
  `other_webhook`. The dashboard recomputes its daily aggregates on its next load.

**Open:**
- **PR #4 (C0.4 sources)**: `docs/integrations/messaging_sources.md`, the help links for the 13
  missing email/SMS platforms. It waits for Leo to read the "Flags for Leo" and approve the links.
  After he approves, merge it. Then Leo creates the platforms in the admin panel, and you do the
  per-platform retrieval check that C0.4 describes.

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
- Leo has to do these himself: open the admin panel (Google sign-in), click "Create pull
  request" on GitHub (`gh` is not installed here), and run production data scripts.

## 3. Next work, in order

1. **C1.2: Document360 header parser + catalog import (dry run).** This is the next `todo`; its
   dependency C1.1 is done. Branch `v2/c1-2-catalog-import` from `main`. Notes:
   - Fixtures come from live pages (six support.yotpo.com guides, the catalog page, 4 detail
     pages, a sitemap slice). Fetching them is read-only. Save the raw HTML and generate the
     expected text with the crawler's own `_extract_text`.
   - **`KNOWN_MATCHES` in the roadmap misses two live integrations:** `bloomreach` and
     `brevo_pushowl` exist in production `esps` (12 rows incl. `global`). Map them to their catalog
     slugs too, or the import proposes duplicates. Record it as a deviation.
   - `normalize_url` changes only http(s) URLs (see `backend/urls.py`); `local://…` names are left
     alone.
   - Nothing is written in this checkpoint. The live dry-run report goes in the PR for Leo to read.
     `--apply` is C1.9.
2. **Then, in parallel** (each its own branch, once C1.2 is merged where needed): C1.3 refresh
   pipeline, C1.4 admin (needs C1.2's proposals), C1.5 chat picker, C1.6 Reviews readiness, C1.7
   prompts by type. C1.8 waits for C1.3. C1.4 and C1.5 now have a design prototype; see §5.
3. **C0.4**, whenever Leo approves PR #4 (see §1).

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

**Open a PR without `gh`:** push the branch and give Leo a
`…/compare/main...<branch>?expand=1&title=…&body=…` link (URL-encoded) to click.

## 5. Watch out for

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
