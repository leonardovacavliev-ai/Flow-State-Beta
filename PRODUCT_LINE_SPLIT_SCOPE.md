# Splitting the knowledge base by Yotpo product line

**Status:** scope, v6. Progress as of 2026-10-01:

| | what | where |
|---|---|---|
| ✅ done | `esp_documents.product` column, added on boot | `main` (`0d47b27`) |
| ✅ done | Loyalty / Reviews / Shared picker on every ESP and global-knowledge link, unlabelled counter per ESP, `POST /api/admin/esp/<esp>/set-product` | `main` (`0d47b27`, fixed width since) |
| ✅ done | All 84 documents labelled by Leo (table below) | production |
| ✅ done | The seam: retrieval and context assembly in `backend/rag_context.py::build_rag_context()`; `eval/check_context_unchanged.py` shows `chat()`'s context and sources are byte-identical to the previous `main` (26 cases) | `main` (`9f46db1`) |
| ✅ done | Chat product picker (Loyalty · Reviews): remembered per browser, ends the conversation on switch, stored on saved conversations and analytics messages | `main` (`9f46db1`) |
| ✅ done | Dynamic prompt (step 5): `[[product]]`, `[[if loyalty]]…[[end]]`, `[[if reviews]]…[[end]]` in the one stored prompt, filled per request, validated on save and restore (`backend/prompt_template.py`). Stored in production config at deploy; Leo edits it from the admin prompt editor | `main` (`9f46db1`), production |
| ✅ done | Coverage guard (step 6): a Reviews question on an ESP with no indexed Reviews document gets a note telling the model to say so; the chat intro says so too | `main` (`9f46db1`) |
| ✅ done | The experiment tooling (step 7): `eval/product_eval.py`, `eval/product_scorer.py` + 19 tests, starter `eval/questions.json`, local-only backend (`backend-local`, `eval/seed_local_db.py`) | `main` (`ae67d23`) |
| ✅ done | Required label on every write path (step 2): `add_document(…, *, product)` refuses a row without one; both "Add link" forms have a product picker with no default; crawl and paste of a URL with no row need `product`, and refuse an unlabelled row before crawling; global add-link creates the row (so it is also duplicate-checked); the global list shows rows missing from the CSV | this change |
| ✅ done | Labels on every vector (step 3): `vectorize_single_document` reads the row's label and refuses before deleting old vectors; the Pinecone and Chroma adapters (and the deprecated `vectorize.py`) refuse a write without one; synchronous `/api/admin/refresh` disabled (the queued one stays) | this change |
| ✅ done | Label edits update the vectors (step 4): `set-product` updates the row, then that URL's vectors, and says so if the index part fails; a label can't be cleared; the picker flags a Loyalty/Reviews label that contradicts the page's Yotpo header | this change |
| next | Backfill the 474 existing vectors (`eval/audit_product_labels.py backfill --write`), then the audit must read zero | after deploy |
| next | Tag the saved real questions (`product_eval.py export-questions`); run step 7 | Leo, then eval |
| waits on step 7 | The retrieval filter (step 8) | — |

Not done, deliberately: **pinning `pinecone`.** `backend/requirements.txt` pins nothing, and the
Docker build installs it in one cached layer. Editing that file rebuilds the layer and upgrades
every dependency at once (the newest `pinecone` is 10.0.0, a rewrite; production may be on an
older one from the cached layer). Pin all of them together, deliberately, in a change of its own.
The new code uses only calls whose keyword form exists in both 7.x and 10.x
(`index.query(...)`, `index.update(id=…, set_metadata=…)`).

Labels in production (`product_eval.py status`, 2026-10-01):

| esp | loyalty | reviews | shared | Reviews coverage |
|---|---:|---:|---:|---|
| attentive | 2 | 1 | 0 | yes |
| dotdigital | 1 | 2 | 5 | yes |
| emarsys | 2 | 0 | 3 | no |
| global | 5 | 0 | 0 | — |
| klaviyo | 2 | 1 | 2 | yes |
| listrak | 1 | 0 | 3 | no |
| ometria | 3 | 0 | 1 | no |
| omnisend | 2 | 1 | 0 | yes |
| other_webhook | 27 | 0 | 18 | no |
| postscript | 2 | 0 | 0 | no |

Labels that may deserve a second look against §4.1 (`shared` means correct for both products,
and is visible in both): Listrak `6909272-loyalty-automations-in-listrak-conductor` is labelled
`shared` but describes Loyalty only. (Postscript `13564274` and global `record-a-customer-action`
were relabelled `loyalty`.) Listrak `2283752-integration-guide-yotpo` is `shared` by decision
(2026-10-01): despite its title it is a general connection guide. So Listrak has no Reviews
coverage, and the guard tells Listrak users so.

**Rollback:** do not roll production back below `9f46db1` while the template prompt is stored —
older code sends `[[product]]` and both `[[if …]]` blocks to the model verbatim. Put a
placeholder-free prompt back first. Rolling back below this change is safe: older code ignores
the `product` metadata on vectors.

Retrieval does not read labels: every document is retrieved as before, whichever product is
picked, and vector metadata is not shown to the model. Chat reads them in one place, to decide
whether an ESP has Reviews coverage.

Line references in §5 predate commits `2b13674` and `d244ee3`, which moved code in `app.py` and
the crawl path; re-check them before editing.

**Goal (Leo):** split the knowledge base by product line — Loyalty vs Reviews — so Yotpo Reviews
integration documentation can be added over time and answered from, without the two product
lines contaminating each other.

Numbers are as of **2026-09-29** and come from `eval/product_split_probe.py` (read-only against
the live Pinecone index and Postgres); the subcommand is named beside each one. The corpus is
changing — documents were added while this was written — so re-run rather than trust the figures.

---

## 1. Summary

1. **Reviews documentation is already in the index, unlabelled** — at least 83 chunks (79 by
   URL plus Listrak's 4-chunk guide), including Yotpo's whole Reviews guide for Klaviyo. The split is not only groundwork for future docs; it
   fixes contamination that is live today.
2. **The split is a `product` label on every document and every vector, required from the moment
   a document is added.** That is the core deliverable (steps 1–4). Users see no change.
3. **How retrieval uses the labels is a separate decision**, made by an experiment (step 7):
   labels plus an instruction in the context, or a filter on a selected product. The filter is
   the expensive option and has not been shown to be needed.
4. **Two things must ship before Reviews answering is promoted:** a product-neutral system
   prompt (the live one is written for Loyalty) and a guard for ESPs with no Reviews
   documentation (step 6).

---

## 2. What is in the index

`audit`: 414 vectors, 44 documents, 10 `esp` values. No vector has a `product` field.

| esp           | docs | chunks | Loyalty | Reviews | URL-silent |
|---------------|-----:|-------:|--------:|--------:|-----------:|
| klaviyo       |    5 |    118 |      37 |  **40** |         41 |
| dotdigital    |    8 |     65 |       9 |  **15** |         41 |
| global        |    5 |     56 |      51 |       0 |          5 |
| attentive     |    3 |     42 |      27 |  **15** |          0 |
| omnisend      |    3 |     33 |      24 |   **9** |          0 |
| listrak       |    4 |     32 |      17 |    0 ¹  |         15 |
| postscript    |    2 |     26 |      19 |       0 |          7 |
| ometria       |    4 |     19 |      16 |       0 |          3 |
| emarsys       |    5 |     18 |       7 |       0 |         11 |
| other_webhook |    5 |      5 |       0 |       0 |          5 |

Columns are assigned from the source URL, the only label that exists, and **it is wrong for some
documents**:

- ¹ Listrak's `articles_2283752-integration-guide-yotpo` was counted here as a Yotpo Reviews
  integration guide whose URL names no product. It ranks first on every Reviews question on
  Listrak (`reviewq`). Leo labelled it `shared` (2026-10-01): it is a general connection guide.
  The guard therefore tells Listrak Reviews users there is no Reviews documentation while this
  guide is still retrieved for them — intended: it covers connecting, not Reviews content.
- `global`'s 5 URL-silent chunks are `setting-up-custom-action-earning-rules-on-shopify`, which
  its Yotpo header marks as Loyalty (`headers`). All of `global` is Loyalty.
- `other_webhook`'s 5 documents were added today: Yotpo developer API pages
  (`develop.yotpo.com/reference/*-app-subscription`), about neither Loyalty nor Reviews. 45 more
  `other_webhook` rows added the same day failed to crawl and have no content (`traffic`). They
  still need a label.

"URL-silent" means only that the URL has no product word.

The largest Reviews document is `docs_klaviyo-integration-guide.txt`, 40 chunks, a third of the
default ESP. It is in the index and the database but not in the local `docs/` tree. **Never
measure this corpus from `docs/`**; it is missing that guide, all of Emarsys, and other documents.

**Traffic** (`traffic`): 168 user messages in production, ever — Klaviyo 121, Attentive 37,
Dotdigital 7, three others 1 each. Of 48 saved questions with text, 2 use Reviews vocabulary and
24 use Loyalty vocabulary. The tool introduces itself as a loyalty tool, so this measures
positioning as much as demand.

---

## 3. Contamination today

Retrieval-side only: which chunks reach the model. None of this shows a wrong answer; step 7
measures that.

### 3.1 Loyalty questions pulling Reviews chunks (`contam`)

The probe mirrors `app.py chat()` for a first turn: property-keyword boost, Query B's chunks
removed from Query A, global Query C. 10 loyalty questions per ESP.

| measure | Reviews chunks |
|---|---|
| Query A, all ESPs | 60 / 555 (11%), 95% interval **6–16%** |
| Query A, the 4 ESPs holding Reviews docs | 60 / 323 (19%) |
| weighted by production traffic | **21%** |
| Query A, questions that name a product | 46 / 486 (9%) |
| full context (A + B + C) | 60 / 825 (7%) |
| Reviews chunk at rank 1 | 8 / 90 queries |

The interval is a bootstrap over the 10 questions, the independent unit.

It concentrates where the two products differ — setup paths and property names: *"enable the
integration from the Yotpo admin"* 14/69, *"customer properties for segmentation"* 11/55,
*"segment by loyalty activity"* 12/55. Points and expiration questions are nearly clean (1/48,
1/29). The first of those names no product; under a both-products goal a Reviews chunk is a
legitimate answer to it, which is why the "names a product" row exists.

The sharpest case (`console`) — Attentive, *"Where in the Yotpo admin do I start the
integration?"*:

| rank | score | chunk says |
|---|---|---|
| 1 | 0.778 | "you'll need access to both your **Yotpo Reviews admin** and your Attentive admin" |
| 2 | 0.522 | "In your Yotpo **Reviews admin**, go to Integrations." |
| 3 | 0.505 | "From your **Yotpo Loyalty admin**, go to **Integrations Center**." |

Every chunk names its product in the deciding sentence (`names`: 93% of product-specific chunks
do); the embedding model does not weight it — those two admin sentences have a cosine similarity
of 0.85 (`console`). On Klaviyo the same question ranks correctly.

### 3.2 Reviews questions (`reviewq`)

| ESPs | Query A retrieves | rank 1 |
|---|---|---|
| Klaviyo, Attentive, Dotdigital, Omnisend | 148 Reviews / 28 Loyalty / 6 silent | Reviews document on 23 of 24 |
| Listrak | 13 URL-silent, all its Reviews guide; 7 Loyalty | Reviews guide on 6 of 6 |
| **Ometria** | 19 Loyalty, 0 Reviews | Loyalty document, or nothing |
| **Postscript** | 11 Loyalty + 12 URL-silent, all Postscript's own Yotpo Loyalty guide; 0 Reviews | Loyalty document, or nothing |
| **Emarsys** | 12 Loyalty + 2 URL-silent Loyalty (`email-integrations-attributes-events`) + 1 Emarsys's own; 0 Reviews | Loyalty document on 4 of 6 |
| **other_webhook** | 8 Yotpo developer pages, 0 Reviews | nothing, or an app-subscription page |

Where a Reviews document exists, Reviews questions find it. **On Ometria, Postscript, Emarsys and
other_webhook there is none**, and a Reviews answer would be built from Loyalty docs or the
model's general knowledge. Nobody asks today, so it costs nothing; once Reviews answering is
promoted it becomes the dominant failure. Only documents and a guard (step 6) fix it.

**Query C adds Loyalty to every Reviews answer.** It searches `global` with no ESP filter and
returns 2 chunks; for Reviews questions all 8 are Loyalty documents — `reviewq` lists the four
files, and the one with a silent URL is Loyalty by its header (`headers`).

---

## 4. What "the split" means

### 4.1 Three labels

| label | means | test |
|---|---|---|
| `loyalty` | Yotpo Loyalty & Referrals | mentions a Loyalty console, points, tiers, rewards, referrals, or Loyalty events or properties |
| `reviews` | Yotpo Reviews | mentions the Reviews admin, ratings, reviews, or Reviews events or properties |
| `shared` | correct for both products | mentions **neither** product's console, events, keys or properties |

`shared` covers two kinds of document:
- the ESP's own documentation, e.g. Klaviyo's *"Getting started with flows"*
  (`articles_115002774932`), which never mentions Yotpo. Every chunk Query B returns today comes
  from documents like it (`queryb`).
- Yotpo platform documentation that belongs to neither product, e.g. the `develop.yotpo.com`
  app-subscription pages now in `other_webhook`.

The definition wins over the test: `shared` means **correct for both products**. Yotpo platform
docs used by either product's integrations — app subscriptions, `application_id` /
`access_token` — are `shared`; those credentials are the platform's, not a product's. A Yotpo doc
specific to one product is that product, even with no console name in it.

A document covering both products gets its **majority** product, not `shared`. `shared` is the
label visible in both modes if a filter ever ships, so a wrong `shared` label leaks both ways;
keep the test strict.

### 4.2 Labelling cannot be automated

- URL keywords miss: the Klaviyo Reviews guide's URL names the product only in a fragment;
  Listrak's and many ESP help-centre URLs are numeric or generic.
- Word counts misfire: "review" is an ordinary verb ("Review and send your campaign").
- The Yotpo product header (`Products / Loyalty & Referrals`, `YotpoProducts / Reviews`) is
  reliable where present: **15 of 44** documents with content (`headers`), never disagreeing with
  a URL that names a product. It lives in `esp_documents.content` only — the chunker drops
  sections under 20 words, so it never reaches a vector.

**Header pre-fills; a human decides the rest.** Never pre-fill from URL or word counts — a
confident wrong suggestion gets confirmed without being read.

### 4.3 One index, one field

Metadata, not Pinecone namespaces (no call site supports them; a both-products query would need
two queries and a merge), not a second index. Label lookups are keyed on **`(esp, source_url)`**,
the key `esp_documents` enforces (`UNIQUE(esp_id, url)`) and `delete_by_url` uses — not on
filename, which `rebuild_esp_vectors` can rewrite.

---

## 5. Work, in order

Each step ships on its own without breaking production. Code for steps 2 and 3 deploys **before**
the step 3 backfill runs, so anything written after deploy is already labelled and no crawl pause
is needed.

### Core — the split

**Step 1 — Labels as data.** `eval/product_labels.py`: `(esp, source_url) → loyalty | reviews |
shared` for **every** `esp_documents` row, including the 45 without content — a failed crawl still
has a URL and a product, and re-crawling it later takes the existing-row branch, which never
asks. `headers` pre-fills; decide the rest against §4.1. The loader in step 2 fails on any row
missing from the file, so documents added in the meantime cannot slip through.

**Step 2 — Labels in the database, required on every write path.**
- `esp_documents.product`, nullable in the schema. Postgres: `ADD COLUMN IF NOT EXISTS`. SQLite
  has no such syntax and the existing pattern is a bare `try/except`
  (`sqlite_adapter.py:177-179`); check `PRAGMA table_info(esp_documents)` first and re-raise
  anything else.
- Load step 1's labels.
- **`ESPManager.add_document(esp, url, *, product)`**: keyword-only, checked against the
  allow-list. Keyword-only matters: `migrate_esps_to_db.py:209` passes `filename` third, which
  would otherwise land in `product` and pass a not-None check. It is the single place rows are
  created (no raw INSERTs outside `esp_manager.py`), so this covers every path at once: sync and async add-link
  (`app_admin_esp_routes.py:247`, `_async.py:100`), sync and async crawl-selected (`app_admin_esp_routes.py:332`, `_async.py:241`), sync and async paste-content
  (`app_admin_esp_routes.py:480`, `_async.py:524`), `_persist_global_doc` (`app.py:1497`), and the
  scripts `restore_esps.py`, `migrate_esps_to_db.py` and `test_new_esp_flow.py`, which must be
  given labels or refuse to run.
- **The admin forms send a product.** Today both ESP add-link (`frontend/app.js:1912`) and global
  add-link (`frontend/app.js:2569`) post only the URL; add a Loyalty / Reviews / Shared select to
  both in the same change. The paste modal opens only on existing rows, which already carry a
  label — except a global link listed only in the CSV (as built: its picker creates the row).
  crawl-selected and paste — ESP and global — for a URL with no row require `product` in
  the request (as built: unlabelled links are reported and the rest of the batch runs).
- **Global knowledge.** Global add-link writes only to `esp_support_links.csv`
  (`app.py:1520-1566`) and the `esp_documents` row is created later by `_persist_global_doc`,
  after vectorization (vectorize at `app.py:1663` / `:1773`, persist at `:1671` / `:1776`). Create the row, with its product, at global
  add-link; give `_persist_global_doc` a `product` argument; and move it before the vectorize call in both the crawl
  (`app.py:1663`) and paste (`app.py:1773`) paths.
- A cached `(esp, source_url) → product` lookup for the context builder, invalidated on label
  edits.

**Step 3 — Labels on every vector.**
- **New writes carry `product`.** The metadata dict is built in `crawler.vectorize_single_document`
  (`crawler.py:206`); the adapters' `add_document` only merges what it is given. Resolve the label
  from `esp_documents` and **validate it before `delete_by_url` runs** (`crawler.py:203`) —
  otherwise a missing label deletes a document's vectors and writes nothing, and the sync callers
  swallow the error (`app_admin_esp_routes.py:389-395`, `:126-131`, `app.py:1662-1666`). Callers:
  `app.py:1663, 1773`, `app_admin_esp_routes.py:127, 390, 533`, `app_admin_esp_routes_async.py:575`,
  `workers/crawl_worker.py:353`. The worker swallows vectorization errors and marks the job
  completed (`crawl_worker.py:350-358`); a missing label must fail the job.
- **The adapters' `add_document` rejects metadata without a valid `product`** (Pinecone, Chroma
  and the deprecated `vectorize.py`). That is the single vector choke point, and it catches the
  writers that bypass `vectorize_single_document`: `reindex_all_esps.py:117`,
  `fix_omnisend.py:119`, `vectorize_listrak.py:82`, `backend/rebuild_chromadb.py:59` (via
  `refresh_esp`), `fix_pinecone_data.py:62` and `backend/migrate_to_pinecone.py:67` (via
  `vectorize_all_docs`). All write straight to the production index.
- **Disable `/api/admin/refresh`.** It rebuilds from the CSV and the baked-in `docs/` tree, which
  cannot see Emarsys, the Klaviyo Reviews guide, Omnisend's `articles_5967363` or today's
  `other_webhook` pages; it would strip labels from what it touches and, for three Ometria files
  stored under old names, write duplicates. `rebuild_esp_vectors` covers the legitimate use.
- **Backfill** with `index.update(id=…, set_metadata={"product": …})`. The server merges the key
  into existing metadata and does not touch the embedding — the installed client (pinecone 7.3.0)
  only forwards the call, so **verify on one vector first**: update, fetch, diff the metadata,
  confirm `text`, `esp` and `source_url` are unchanged. One id per call, so the backfill is a
  loop of ~400 calls. Add
  `update_metadata(ids, patch)` to `VectorAdapter` and both adapters, and check ChromaDB's
  `update` semantics the same way locally. ~~Pin `pinecone`~~ — deferred, see the status note
  at the top.
- **Orphans.** Vector ids are `{esp}_{filename}_{i}` and every vector carries `total_chunks`. An
  orphan is a vector whose `chunk_index ≥ total_chunks` of the same URL's chunk 0 (chunk 0 is
  rewritten on every write). There are none today. The rule cannot see a whole duplicate under a
  second filename — the Ometria risk above — so the audit also asserts one filename and one chunk 0
  per `(esp, source_url)`.
- `eval/audit_product_labels.py`: every vector has `product ∈ {loyalty, reviews, shared}`, it
  matches `esp_documents.product` for its `(esp, source_url)`, and there are no orphans. Exit 1
  otherwise. Keep it separate from `audit_index_drift.py`, which compares against local files and
  already fails on known drift.

**Step 4 — Admin UI.** A product column on the links table, editable; a flag where the Yotpo
header disagrees with the chosen label; an unlabelled counter. **An edit updates the row and that
URL's vectors** (`update_metadata`), or the audit fails and any filter serves the old label. Both links routes build their row
dict by hand and drop the `id` that `esp_manager.list_documents` already selects — move the
projection into `esp_manager.py` once and include `id` and `product`. (The two copies have already
drifted: `is_crawling` is always `False` on the async path.) The global knowledge screen lists
from the CSV (`app.py:1410`); join it to `esp_documents` by URL to show and edit labels.

### Required before promoting Reviews answers

**Step 5 — A product-neutral system prompt.** The live prompt (`app_settings`) is written for
Loyalty: "loyalty retention specialist… using loyalty data", a REFERRAL PROPERTIES block. Store it
as three parts — a neutral base, a Loyalty block, a Reviews block. This is more than a text edit,
because the prompt is one field inside the `app_config` JSON (`config_manager.py:21`):
- `update_config` silently drops any key the stored config does not already have
  (`config_manager.py:182`), and production's config lives in Postgres, so adding defaults to
  `_ensure_files_exist` (fresh installs only) is not enough. Allow-list the new field names in
  `update_config`, or write them into the stored config once when the change deploys;
- extend audit backup and restore, which hard-code `system_prompt` (`config_manager.py:175`,
  `:249`);
- two more textareas on the settings screen (`frontend/app.js:2284`, `:2449`), and the POST route
  that rebuilds `AIClient` from one string (`app.py:1340`).

Pass the assembled prompt into `generate_response` as an argument; never mutate `ai_client.system_prompt`,
a module-level singleton shared by 4 gthread threads. Also update the welcome text in
`frontend/app.js` and the page title in `index.html:6` ("Loyalty Emails Assistant").

**Step 6 — The coverage guard.** An ESP has Reviews coverage when it has at least one
`esp_documents` row labelled `reviews` **with content and at least one vector**. Failed rows do not
count, and neither do rows whose vectorization failed — the sync routes save content even then
(`app_admin_esp_routes.py:389-395`, `:533-538`). Cache the
per-ESP answer; invalidate on label edits. For ESPs without coverage, add to the context: *"Flow
State has no Yotpo Reviews documentation for {ESP}. If the user is asking about Yotpo Reviews, say
so and do not answer from Loyalty sources."* The model reads the question; step 7 measures whether
it complies. This avoids inferring the product from the question in code, which does not work
reliably ("review" is a verb; many real questions name neither product). Covers Ometria,
Postscript, Emarsys and other_webhook today, and shrinks as Reviews docs are added.

The guard does not stop Query C adding Loyalty global chunks to Reviews answers on ESPs that do
have coverage. Labels in the context (step 7, arm C2) or the filter (step 8) handle that.

### The decision on retrieval

**Step 7 — The experiment.** Decides whether retrieval must filter, or labels in the context are
enough. Needs steps 1 and 5; not steps 2–4 — in the eval, labels and the step 6 coverage check are
computed from step 1's file.

Prerequisites:
- Extract `build_rag_context(message, esp, history, *, labels=None, product=None, filter=False)`
  from `chat()` (retrieval and context assembly, ~125 lines), called by the route and the eval.
  Worth having regardless: it is the only way to test retrieval without a deploy.
- Run as a script, not on Railway: `AI_TEMPERATURE` is process-global. Run at temperature 0.
- Pin the model version (the stored `gemini-flash-latest` is an alias that moves) and use the
  provider stored in Postgres, not `backend/app_config.json`.
- The API key: `GEMINI_API_KEY` in `.env` works through the app's own client
  (`google.generativeai`, as `ai_client.py` uses it) against `gemini-flash-latest`, the provider and
  model production has stored. An earlier draft called it blocked; that came from a raw API call,
  not from the key. `google.generativeai` is end-of-life and prints a deprecation warning — not a
  blocker for the eval.

> **Re-baselined 2026-10-01.** The chat picker shipped (`9f46db1`), so production always knows
> the product: every arm is now filled for the picked product (a question naming none is asked
> with Loyalty, the picker's default), arm D — "told the product" — is what every arm is, and
> it is dropped. Arms as run: **A** (production) → **C1** (+ instruction) → **C2** (+ source
> labels) → **B** (+ filter). The rule below reads with D removed; choosing B means building
> the filter (step 8), not the selector. The table and rule are kept as pre-registered.

Arms — all on the step 5 base prompt, **all with the step 6 guard**:

| arm | adds | user-selected product? |
|---|---|---|
| A | nothing (today, plus the neutral prompt and guard) | no |
| C1 | instruction: name the product you describe; ask if the question doesn't say | no |
| C2 | C1 + `Yotpo product line: …` in every source header, from step 1's file | no |
| D | C2 + "the user is asking about {product}" | yes |
| B | D + retrieval filtered to `product IN (selected, shared)` | yes |

C2 vs A measures what labels add; D vs B isolates the filter. To emulate B before any vector is
labelled: for each of Queries A, B and C, fetch with `top_k` equal to that ESP's (or `global`'s)
current vector count under the ESP filter, drop chunks by step 1's file, then keep the normal top
10 / 5 / 2 at ≥ 0.35, and remove Query B's chunks from Query A after filtering.

Question set:
- Loyalty questions on the 4 ESPs holding Reviews docs; Reviews questions on all ESPs.
- The 48 saved real questions where they fit, with their conversation history replayed — the
  previous answer feeds the next retrieval (`app.py:509-517`) — topped up with written ones.
- Leo assigns each question its product when building the set. **Questions that name no product
  run only in A, C1 and C2**, scored correct if the answer asks which product or answers both
  correctly.
- Screen with retrieval only (no model): keep cells where the other product's chunk reaches the
  context, Query C included.

Scoring:
- One outcome per answer: correct · wrong product (console, menu path or property) · no answer ·
  hedged; plus a flag for a property name absent from the context.
- **On ESPs without Reviews coverage, a Reviews question is correct only if the answer says the
  documentation is missing** — that is the guard working, not a refusal.
- A mechanical scorer first — extract `Yotpo … admin`, menu paths and property names and compare
  with the question's product — then a CSM checks a shuffled, arm-blind sample of ~20 to validate
  it; report the agreement.

Decision — write these counts down before running. **Every comparison is over the same set: the
screened questions that name a product**, since D and B do not run the others.
- If A is wrong-product on at most 10% of that set (and at most 2), ship C2 labels in the context
  if C2 adds no more than 2 no-answer or hedged outcomes; otherwise keep A. Stop.
- Otherwise ship **the cheapest arm, in the order C1 → C2 → D → B, that at least halves A's
  wrong-product count without adding more than 2 no-answer or hedged outcomes**. Choosing D or B
  means building the selector (step 8).
- If no arm does, the result is inconclusive: ship C2, and put the mechanical scorer on live
  answers so traffic settles it.
- Report D vs B either way. If B only beats A where D also does, the failures came from the
  prompt, not retrieval.

**Step 8 — Only if D or B is chosen: the selector, and for B the filter.**
- For B only: `{"esp": …, "product": {"$in": [selected, "shared"]}}` on Queries A, B and C; `product` in the
  `_mechanics_cache` key; validated against an allow-list (`esp` itself is unvalidated,
  `app.py:440`).
- Consider the asymmetric form: filter Loyalty mode only, and leave Reviews mode unfiltered with
  labels. It matches the measured asymmetry — §3.1 is the direction that leaks — and depends less
  on `shared` being exact.
- **Hard cutover once the step 3 audit reads zero.** A vector with no `product` key matches
  neither `$in` nor `$eq` (`filters`: 0 of 118 on Klaviyo) but matches `$nin` and `$ne` (118 of
  118). Shipping `$in` early returns nothing; `$nin` is not a safe bridge, because it returns every
  not-yet-labelled Reviews chunk and changes behaviour with each label written.
- A Loyalty · Reviews selector beside the ESP list (D and B); changing it ends the conversation,
  like changing the ESP (`endActiveConversation()`, `frontend/app.js:74`, called at `:250`).
- ChromaDB rejects a two-key `where`; wrap it in `$and`, as its `delete_by_url` does. Local dev
  defaults to ChromaDB, so this breaks locally while passing in production.
- `product` on `messages`, `esp_selections` and `conversations`. The `2e13d1d` test pins
  `esp_breakdown` (`GROUP BY esp`, `analytics.py:718`) and allows one session to count toward
  several rows, so a product dimension is consistent with it.
- SQLite's `execute_query` replaces every `%s` in the SQL text (`sqlite_adapter.py:296`); keep
  `LIKE` patterns in parameters.

### Content

**Step 9 — Reviews documents** for Ometria, Postscript, Emarsys and other_webhook. Each one added
through step 2's form arrives labelled and shrinks step 6's list.

---

## 6. Risks

| risk | when | mitigation |
|---|---|---|
| Reviews questions answered from Loyalty docs on ESPs with no Reviews docs | as soon as Reviews answering is promoted | step 6 before promotion; step 9 |
| A loyalty-only prompt skews every Reviews answer | now | step 5 before promotion |
| A document is created without a label | any write after step 2 | `add_document` rejects it; loader fails on unlabelled rows |
| A re-crawl deletes a document's vectors and writes nothing | step 3 | label validated before `delete_by_url` |
| `/api/admin/refresh` strips labels and writes duplicates | any time after step 3 | disabled in step 3 |
| `index.update` behaves differently from the docstring | step 3 backfill | one-vector test and diff first; client pinned |
| A wrong `shared` label leaks into both products | if the filter ships | strict test (§4.1); majority rule for mixed docs |
| A vector without `product` vanishes under `$in` | filter cutover | cutover gated on the audit |
| Labelling becomes a chore | every new document | header pre-fill (about a third); required field; unlabelled counter |
| The experiment is too small to decide | step 7 | pre-registered counts; inconclusive ships C2 and measures live |

---

## 7. Answers

- **Is a split needed?** Yes — labels on every document and vector, now, because Reviews docs are
  already mixed in. Whether retrieval also *filters* on them is decided by step 7.
- **Loyalty vs Reviews?** Three labels: `loyalty`, `reviews`, and `shared` for anything that is
  correct for both.
- **Separate databases?** No. One index, one metadata field.
- **What else stands between you and good Reviews answers?** A loyalty-only system prompt, and
  four ESPs with no Reviews documentation.

---

## Appendix — corrections from earlier drafts

- v1 measured the local `docs/` tree, which is missing the Klaviyo Reviews guide and all of
  Emarsys; its per-ESP numbers were wrong. Klaviyo is 34% Reviews, not 0%; Omnisend 27%, not
  "over half".
- The product name appears in 93% of product-specific chunks; the problem is the embedding, not
  the chunker.
- A two-label split does not break Query B if platform docs go with Loyalty; the case for a third
  label is Reviews retrieval and Yotpo documents that belong to neither product.
- The router experiment claiming product cannot be inferred from a question was circular and is
  dropped; step 6 is designed so nothing depends on inferring it.
- The 0.35 threshold was never tuned (`RETRIEVAL_FIXES_IMPLEMENTED.md` §3).
- v1's migration shipped a filter before any vector had a label — a total retrieval outage. v2's
  destructive re-vectorization is replaced by `index.update`.
- v2's `$nin` bridge was unsafe; v3 missed Listrak's Reviews guide and the system prompt; v4 said
  "platform" meant "never mentions Yotpo", which today's Yotpo developer pages do not fit, and left
  new-document write paths able to create unlabelled rows. v5 missed `_persist_global_doc`, the
  global add-link form, the 45 unlabelled failed rows, vector writers outside
  `vectorize_single_document`, label edits not reaching vectors, and the real size of the prompt
  change.
