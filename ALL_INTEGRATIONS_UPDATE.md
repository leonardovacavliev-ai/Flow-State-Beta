# Flow State for every Yotpo integration

**Status:** plan v3, accepted by Leo 2026-10-13. No code written. The build map, with checkpoints
and deliverables, is [ALL_INTEGRATIONS_ROADMAP.md](ALL_INTEGRATIONS_ROADMAP.md).
- v2 was revised after a hostile review (Appendix A).
- v3 applies Leo's decisions and adds the system prompt per platform type (§4.6, Appendix C).

**Leo's decisions (2026-10-13):**
- **We build.** The request came from the people who matter, so there is no demand test and no
  demand gate.
- **Railway for now, moved later.** The build must not tie itself to Railway (§3.2).
- **Only Yotpo Loyalty & Referrals and Yotpo Reviews (incl. UGC) are in scope.** Other Yotpo
  products named in guide headers (SMS & Email, Subscriptions) are ignored.
- **Wave order accepted:** storefront → service → content → data.
- **Prompt wording comes later.** Appendix C's drafts only exist so the plumbing can be built and
  tested (step 1.7). Leo writes each type's final prompt in its wave (step 2.1), before its trap
  questions run. No user sees a draft: integrations stay `listed` until their wave passes.
- **Partner pages are handled as today.** An admin adds a URL; Flow State crawls it, or the admin
  pastes the text if the crawler is blocked. v2's legal and User-Agent question is withdrawn. It
  applied to v1's automated crawling of dozens of partner sites, which is no longer in the plan.

**The question:** users want Flow State to cover *all* Yotpo integrations
(https://www.yotpo.com/integrations/), not only email platforms.
1. Should that be a spinoff (a new repo that inherits Flow State's systems) or a major update of this
   app?
2. How would it be built, layer by layer?

---

## 0. Summary

### Recommendation

**A major update of this app, in this repo. Not a spinoff.**

- It is the same product for the same users: a retrieval-grounded assistant over Yotpo integration
  documentation.
- The reusable parts are the generic ones. In a fork, every fix to them would land twice:
  - the Postgres crawl queue with per-host pacing
  - the content store
  - product labels kept in step between rows and vectors
  - the `rag_context` seam and its regression check
  - the eval scripts
  - sign-in, saved conversations and analytics
- The catalog contains today's product: all 8 ESPs Flow State covers are catalog integrations.

### What the measurements change about *how*

1. **The target is small.** Full coverage is about **300 documents and 1,200–2,000 vectors**, 3–4×
   today (§1). Postgres, the queue and the index handle that as they are. The heavy infrastructure
   change the request expects is not needed for scale. The work is:
   - content and labelling
   - the system prompt per platform type
   - the interface
   - making the app portable for the move off Railway
2. **One prompt cannot serve every platform type.**
   - Today's prompt is an email-flow specialist's.
   - The Yotpo guides for other platform types each have their own traps, and a generic answer
     walks into them. Examples:
     - POS supports only fixed-amount rewards;
     - Gorgias shows loyalty data only after a ticket message;
     - Google Seller Ratings needs 100 verified site reviews and sends even unpublished ones;
     - a TikTok product identifier cannot be changed once submitted.
   - Each platform type needs its own prompt with its own checklist (§4.6).
3. **Most of the catalog is Reviews** (144 of 181 cards), and Reviews is the unfinished half of the
   product split. Reviews readiness comes before the Reviews-heavy waves (§4.5).
4. **Most integrations rest on one ~500-word guide.** Coverage tiers and the prompt's grounding rules
   matter more than retrieval tuning.

### Sequence (§5)

| stage | what | effort |
|---|---|---|
| **Stage 0** | Quick wins: pin dependencies, rate limiting, add the 13 missing email/SMS platforms through the existing admin | ≈ 1 dev-week + 13–20 owner hours |
| **Stage 1** | Foundation for every platform type: catalog import into a proposals inbox, integration picker, scalable admin, one system prompt per platform type, Reviews readiness, portability seams | ≈ 6–7 dev-weeks + 11–16 owner hours |
| **Stage 2** | One wave per platform type (storefront → service → content → data), each shipped when its trap questions pass | ≈ 1 dev-week + 9–15 owner hours per wave |

Total: ≈ 11–12 dev-weeks and ≈ 60–95 owner hours.

---

## 1. The target, measured

All figures were measured on 2026-10-13.
- yotpo.com/integrations was parsed via the `div.integration-card` elements and their
  `data-products` and `data-categories` attributes.
- All 177 detail pages and every linked guide were fetched at 1 request/s.
- Method: Appendix B.

### The catalog

| | count |
|---|---:|
| integration cards | 181 |
| unique detail pages (`/integrations/<slug>/`) | 177 |
| unique partner names (23 pages are a second card for the same partner, e.g. `gorgias` + `gorgias-loyalty`) | 154 |
| categories | 30 |
| cards in more than one category | 61 |
| Reviews & UGC only / Loyalty only / both | 78 / 37 / 66 |

**Categories by size:**

| category | cards | category | cards | category | cards |
|---|---:|---|---:|---|---:|
| Email marketing | 37 | Loyalty & referrals | 9 | Consumer platform | 5 |
| Data & automation | 24 | Other | 9 | Mobile wallet pass | 4 |
| SMS marketing | 20 | On-site chatbots | 8 | Sustainability & donations | 4 |
| On-site engagement | 15 | BI & analytics | 7 | Shipping & returns | 4 |
| Product sampling | 12 | Influencer marketing | 7 | Payment & checkout | 3 |
| eCommerce platform | 12 | Search | 7 | Quiz & gamification | 3 |
| Help desk & CRM | 11 | Ads | 6 | Personalization & recs | 3 |
| Mobile app builder | 11 | Retailers & review syndication | 6 | Subscription & billing | 3 |
| In-store & POS | 9 | Page builder & PWA | 6 | Privacy & DSR | 2 |
| | | | | Gift cards | 2 |
| | | | | Reviews & visual UGC | 2 |
| | | | | WhatsApp & social DMs | 1 |

### What the 177 detail pages link to

| detail pages that link to… | pages | notes |
|---|---:|---|
| a Yotpo guide on `support.yotpo.com` | 101 | 102 unique guides. 95 are live as linked. **6 were renamed**: the link 404s but the article is in the sitemap under a new slug. **1 is gone** (Yieldify). |
| only partner-hosted pages | 62 | 58 of them have a documentation-like link. Across these pages there are 83 unique documentation-like URLs, and 77 of them are the partner's article about the Yotpo integration (Dixa, Loop, PushOwl…). The rest are homepages and `bit.ly` links. |
| nothing documentary | 14 | Includes the main **Shopify** card, Bazaarvoice, Instagram, Target and LoyaltyLion. The Shopify Plus, POS, Flow and Loyalty cards *do* link guides. |

**The 94 live Yotpo guides measured:**
- **71,252 words in total.** Median 462; quartiles 304 and 863. That is about 350–450 chunks with
  today's chunker, so **2–3 chunks for a typical guide**.
- **92 of 94 carry the Document360 header.** The header lists:
  - the Yotpo products;
  - the supported Yotpo plans;
  - the supported store platforms (e.g. `Shopify, Shopify Plus, BigCommerce`).
  - 84 headers name one product.
  - **8 name both.** For those, `product_labels.header_label` today returns whichever product it
    finds first.
  - Some headers also carry Document360 template leftovers such as "Change this text for SMS &
    Email" (seen in Gorgias, Tapcart and Alloy).

**The help centre's sitemap:** `support.yotpo.com/sitemap-en.xml` (the only sitemap in
`sitemap_index.xml`) lists **713 URLs, each with a `lastmod`**. 112 of them have "integrat" in the
slug.

### Email and SMS

The Email and SMS categories hold 28 names. 21 of them are platforms that send messages.

- **Flow State covers 8 of those 21:** Attentive, Dotdigital, Emarsys, Klaviyo, Listrak, Ometria,
  Omnisend, Postscript.
- **13 are missing:** Braze, Cordial, Drip, HubSpot, Insider, Mailchimp, Optimizely (Zaius),
  Optimove, Remarkety, Retention Science, Rule, Sailthru, Salesforce Marketing Cloud.
- **7 of the 28 do not send messages,** so they get other platform types: AdRoll, Brevo PushOwl,
  Dondy, Klaviyo Customer Hub, Movable Ink, Zembula, Zembula Loyalty.

### Today, for comparison

**The index:** 9 selectable ESPs plus `global` and `other_webhook` (the Yotpo API pages), 84
documents and 474 vectors.
- 69% of the vectors are Yotpo product documentation (Loyalty 249, Reviews 79).
- 31% are platforms' own documentation (`shared`, 146).
- `other_webhook` is not a catalog integration.

**Traffic** (2026-09-29): 168 user messages, ever. Klaviyo had 121, Attentive 37, Dotdigital 7, and
three others 1 each.

### Estimate at full coverage

| source | documents | vectors |
|---|---:|---:|
| today's corpus | 84 | 474 |
| catalog-linked Yotpo guides | ~100 | 400 |
| partner-hosted integration articles | ~80 | 250 |
| mechanics documentation for the 13 new messaging platforms | ~40 | 200–600 |
| partner mechanics articles (added 2026-10-14; dry run: 171 proposals) | ~170 | ~450–550 |
| **total** | **~470** | **≈ 1,650–2,550** |

### Two consequences

1. Most integrations will rest on one ~500-word guide. Thin coverage will be the normal case. The
   partner mechanics articles (§4.3, added 2026-10-14) add a few pages on how the partner's side of
   each integration works.
2. A corpus of ~300 documents does not justify automated discovery machinery. A re-runnable import
   into a proposals inbox plus human labelling does the job. Labelling ~200 new documents is a few
   hours of owner time; it is not a pipeline problem.

---

## 2. How Flow State works today, and where "ESP" is load-bearing

```
Browser (vanilla JS, one 3,270-line app.js, no build)
  └─ POST /api/chat {message, esp, product, session_id, history|conversation_id}
       └─ rag_context.build_rag_context()
            Query A  10 chunks, filter esp = selected; product ∈ (loyalty, shared) for Loyalty chats
            Query B   5 chunks, a fixed email-flow "mechanics" query, cached per ESP
            Query C   2 chunks, filter esp = 'global'
            score ≥ 0.35; a chunk under 60 words gets its next chunk appended
       └─ ai_client (Gemini Flash by default), prompt rendered per product, no streaming
Pinecone: one index, default namespace, 384-dim all-MiniLM-L6-v2 run in-process
Postgres: esps, esp_documents (content stored), crawl_jobs, crawl_hosts, analytics, users,
          conversations, app_settings
Railway:  one service; gunicorn 1 worker × 4 threads; crawl worker threads and two
          APScheduler instances run inside the web process
```

Where "one of a few email platforms" is an assumption rather than just a name:

**Prompt**
- The prompt says "an email marketing specialist… recommend flows and campaigns… in the user's
  ESP".
- Its 5-step checklist is about flow triggers, delays and send-time filters.
- One prompt is stored (`app_settings` → `app_config.system_prompt`). It is rendered per request for
  the product picked in chat.
- Where: `eval/prompts/system_prompt_template.txt`, the default in `config_manager.py:107`,
  `prompt_template.py`.

**Retrieval**
- Query B is one Klaviyo-vocabulary query applied to every ESP.
- The fallback text says "ESP best practices", and source headers say `ESP:`.
- Chat defaults to `klaviyo`, and any `esp` string is accepted unvalidated.
- Where: `rag_context.py:142-151, 438, 558, 587`, `app.py:234`.

**Data**
- `esp` is a free-text key in `esps`, in vector metadata, in chunk ids (`{esp}_{filename}_{i}`) and
  in the analytics and conversation tables.
- The frontend's `/`↔`_` hack writes `other/webhook` to some tables and `other_webhook` to others.
- Where: `app.js:507,517,738`, `analytics.py`.
- `esps` has no category, no supported products and no platform type.
- Only rows with `status = 'active'` are listed (`esp_manager.py:151-170`).

**Coverage**
- "Does this ESP have Reviews docs" is decided by Pinecone queries, one per Reviews document until
  the first hit per ESP. The result is cached for 300 s.
- The request that triggers a scan waits for the whole scan; others wait up to 5 s, then use the last
  known answer.
- Where: `product_labels.py:102-145`.

**UI**
- The sidebar heading says "Select Email Platform", with one button per ESP and Klaviyo as the
  default.
- The welcome card is a static Klaviyo card.
- `display_name` is inserted unescaped.
- About 18 user-facing strings say "ESP".
- Where: `index.html:267,306`, `app.js:30,291-314,536-541`.

**API**
- The sidebar reads `GET /api/admin/esps`. That route is **public by documented decision**
  (`ACCOUNT_SYSTEM_PLAN.md:74,148`), so it is not an oversight.
- Where: `app.js:492`.

**Admin**
- ESP Management fetches every ESP's links in parallel (N+1).
- It renders every link with a `<select>` in a single innerHTML, and re-renders all of it after
  every action.
- Where: `app.js:1835-1940`.

**Eval**
- There are 8 retrieval cases, all Klaviyo Loyalty.
- The golden context check has 13 cases (run twice), covering Loyalty or no product only.
- Where: `eval/retrieval_cases.json`, `eval/check_context_unchanged.py`.

---

## 3. Recommendation

### 3.1 Not a spinoff

- **The catalog contains today's product.** A spinoff would either duplicate the 8 ESPs (two tools
  answering Klaviyo questions, drifting apart) or empty Flow State out (a rename with extra steps).
- **The reusable parts are the generic ones** (§0). A fork duplicates them, and every fix lands
  twice.
- **What a spinoff would buy** (no "ESP" naming, a newer stack) is not needed. §1 shows the scale
  does not call for it.
- **The move off Railway is no reason to spin off either.** The repo moves with the app. What it
  needs is portability (§3.2), not a second codebase.

### 3.2 Built to move off Railway

Flow State stays on Railway for now and moves later. Nothing in this plan may tie it to Railway, and
the parts that would make the move painful get fixed on the way:

| constraint | what it means in practice | step |
|---|---|---|
| **The Docker image is the unit of deployment** | The existing `Dockerfile` stays the build. Use no Railway-only features (Railway cron, volumes, `RAILWAY_*` variables in code). Health check stays `/api/health`. | all |
| **Configuration only through environment variables** | `.env.example` lists every variable, with a comment. Secrets are injected by the platform, never committed. | all |
| **Two entrypoints, one image** | `web` (gunicorn) and `worker` (`python -m workers.main`: crawl queue, sitemap job, retention sweeps). On Railway the web process keeps starting the worker in-process, as today, so it stays one service. On the next platform they run as two processes. | 1.8 |
| **Caches invalidate across processes** | A `kb_version` row in `app_settings`, bumped by the worker when it indexes and checked by web every ~10 s. Without it, a separate worker leaves chat on stale caches until the 900 s TTL; today `crawl_worker.py:_notify_indexed` clears them in-process. | 1.8 |
| **Safe with several replicas** | Boot DDL and the scheduler run under Postgres advisory locks, so two replicas cannot race the schema or run the same job twice. Today two APScheduler instances run in one process with no lock. | 1.8 |
| **No state on local disk** | The crawl path still writes `docs/<esp>/*.txt` and falls back to them. Removing that is required before the move, not optional: every document must have `content` (`needs_backfill` reads zero), then `docs/`, `crawl_metadata.json`, the `fcntl` lock and the CSV go. | 1.8 |
| **Web stays at one gunicorn worker until audited** | The analytics write queue keeps ordering per process, and the mechanics and coverage caches are per process. Adding workers waits for an inventory of in-process state. | — |
| **The move itself is a checklist** | `pg_dump`/restore Postgres; point `DATABASE_URL`, `REDIS_URL` and the Pinecone variables at the new services; add the new origin to the Google OAuth client and to CORS; re-check `ADMIN_EMAIL_DOMAIN`. | at move time |

### 3.3 What would still change the answer

- **Internal sources.** Suppose Flow State later answers from internal material (support tickets,
  Confluence) for Yotpo staff. The data-handling rules then differ enough to warrant a separate
  deployment, still from this repo.
- **Embedding in the Yotpo admin or the help centre.** Flow State would then be an API behind
  someone else's UI, and this front end a reference client.

### 3.4 What this update does not include

Each of the following was considered and cut or deferred, with the reason:

| not included | why |
|---|---|
| Table rename (`esps` → `integrations`) | risky during deploy overlaps (Appendix A #5), and fixes nothing that a canonical key doesn't (§4.2). Rename in Python and in the UI only. |
| FastAPI, a React front end, S3 + Lambda ingestion, multi-tenancy (CLAUDE.md's target architecture) | not needed at ~300 documents |
| Scheduled catalog discovery, link-following, `extraction_profiles`, discovery-run tables | a re-runnable import script and a sitemap `lastmod` refresh cover a ~300-document corpus |
| Automatic product labels | breaks the project's labelling rule (§4.3) |
| Multi-integration questions, category-scoped knowledge, alias matcher | each is hard to get right, and none has evidence of need |
| Index rebuild and embedding change | only if a pre-registered bake-off says so (§4.4) |
| A separate worker *service* on Railway, roles beyond `editor`, ES-module split, logos, "Popular" list | the worker *entrypoint* is built (§3.2); running it separately waits for the move or a memory problem. The rest wait for a reason. |

---

## 4. Scope by layer

### 4.1 Product model

**Platform types.** Thirty categories do not need thirty behaviours. They need five **platform
types**, each being the shape of the task. Each type has its own:
- system prompt (§4.6)
- welcome copy
- retrieval plan
- eval cases

How a platform type is assigned:
- The platform type is **an attribute of the integration, set by an admin**. The category only
  supplies a default.
- Under the defaults below, 25 of 177 detail pages sit in categories that map to different types.
  Klaviyo, for example, is in Email, SMS and Data & automation. So categories cannot decide it.
- The defaults are seed data in code, not an admin screen.

| type | default for categories | the user is trying to | traps the answer must catch (examples from the guides) |
|---|---|---|---|
| `messaging` | Email, SMS, WhatsApp & social DMs | build flows and campaigns from Yotpo events and properties | a trigger that fires more than once duplicates sends; a filter checked only at entry is not re-checked at send time (today's checklist) |
| `storefront` | eCommerce platform, In-store & POS, Mobile app builder, Mobile wallet pass, Page builder & PWA, Payment & checkout, Subscription & billing, On-site engagement, Search, Personalization, Quiz | install, connect, show Yotpo where shoppers are, make earning and redemption work in another channel | Shopify POS supports only fixed-amount rewards (no free-product or birthday rewards); Recharge has no native earning rule (Shopify Flow + tags instead); a reward with a cart minimum can't apply to an existing Recharge subscription; Recharge's Integrations Center connection is Shopify-only |
| `service` | Help desk & CRM, On-site chatbots | let agents and bots see and act on loyalty and review data | Gorgias shows loyalty data only after a message event, within 5 min, and it goes stale until the next one; connecting Zendesk sends review requests for tickets solved in the past 15 days; adjusting points from Gorgias needs a custom HTTP button with the API key and GUID |
| `data` | Data & automation, BI & analytics, Ads, Privacy & DSR, Other, Gift cards, Sustainability & donations, Shipping & returns | move Yotpo data in or out, trigger Yotpo actions from other tools | the Shopify Flow action name must match the custom action rule exactly; a subscription toggle can award points twice unless the rule fires once per customer; Klaviyo subscriptions reach Flow only with "Forward to Shopify" on; Alloy connects Reviews by OAuth but Loyalty by API key + GUID |
| `content` | Reviews & visual UGC, Retailers & review syndication, Product sampling, Influencer marketing, Consumer platform | collect, syndicate or reuse reviews and UGC | Google Seller Ratings needs ≥ 100 verified site reviews in 24 months from the searcher's country, takes 2–6 weeks, and receives all valid reviews including unpublished ones; TikTok Shop syndication is US-only, verified buyers only, and a submitted product identifier can't be changed; SoPost reviews don't syndicate if Yotpo requires custom questions |

**Loyalty & referrals partners are not a type of their own.** They are assigned one of the five
per integration, e.g.:
- Rybbon (gift cards via webhook) → `data`
- Novel (wallet passes) → `storefront`
- Smile.io and LoyaltyLion (Yotpo Reviews into their programs) → `data`

`other_webhook` ("Yotpo API & Webhooks") → `data`, but only in the `data` wave. It is live today
on the email prompt, so it stays `messaging`, with its current welcome copy, until the `data`
prompt has passed its trap questions.

**Scope boundary: what counts as integration documentation.**
- **In scope:**
  - a document describing how Yotpo connects to a partner, what data moves between them, or how to
    configure Yotpo features inside it;
  - the partner's own documentation needed to act on that (for example, flow mechanics);
  - a small set of Yotpo product documents as global knowledge, as today.
- **Out of scope:** Yotpo product setup in general (earning rules, widget styling, referral
  settings), even where the URL says "shopify". Otherwise Flow State becomes a general Yotpo help
  bot competing with support.yotpo.com.

**Coverage, computed from documents only.** Eval results stay in files, so they are a separate,
manually maintained flag.

| tier | condition | in chat |
|---|---|---|
| **Basic** | ≥ 1 approved, labelled, indexed integration guide for a product the catalog lists. For `messaging`, also ≥ 1 platform-mechanics document, because the checklist depends on Query B. | available; the intro and the context say documentation is limited where only one guide exists |
| **Listed** | catalog entry only | shown greyed under "Not covered yet", with the catalog link; no chat |
| *evaluated* (flag) | the integration's platform type passed its trap questions (§4.6) and ≥ 2 retrieval cases pass | shown only in admin |

### 4.2 Data model

All changes are additive columns and new tables, created at boot with `_add_missing_columns`, as
today. **No table rename.**

```
esps                 status: 'active' (in chat) | 'listed' (catalog only) | 'archived'
                     + catalog_slugs JSONB   -- every catalog card merged into this integration
                     + categories JSONB, products JSONB   -- from the catalog, editable
                     (lists are JSONB, TEXT holding JSON in SQLite, like vector_ids today)
                     + platform_type ('messaging' | 'storefront' | 'service' | 'data' | 'content')
                     + catalog_description
esp_documents        + title, source_kind ('yotpo_support' | 'yotpo_developer' | 'partner' | 'pasted'),
                       supported_plans JSONB, supported_platforms JSONB  -- from the Yotpo header
                       vector_count INT   -- chunks indexed by the last successful crawl
                       sitemap_lastmod, consecutive_misses INT, retired_at
document_proposals   id, esp_id, url (normalised), source ('catalog' | 'sitemap' | 'manual'),
                     suggested_label (header only), state ('open' | 'approved' | 'rejected'),
                     note, created_at, decided_by, decided_at; UNIQUE(url)
```

**Visibility is a `status` value, not a new column.** Today's code lists only `status = 'active'`
(`esp_manager.py:168`).
- Imported integrations are created as `listed`.
- They become `active` only when their platform type's wave ships.
- So a rollback to older code never shows them in the sidebar.

**One canonical key: `esps.name`.**
- It is lowercase with underscores (`salesforce_marketing_cloud`).
- It is used for vector metadata, analytics, conversations, the mechanics cache, deep links and the
  API.
- Catalog slugs (hyphenated) appear only in `catalog_slugs`. Lookups map a slug to a name.
- `/api/chat` validates `esp` against active rows and rejects an unknown key with a 400. Today any
  string flows into Pinecone filters, analytics and conversations.
- Analytics rows written as `other/webhook` are normalised to `other_webhook` once, and the frontend
  hack that produced them is removed (§4.7).

**Paired catalog cards merge into one integration.** For example, `gorgias` and `gorgias-loyalty`
become "Gorgias" with both products; the same goes for Tapcart, Dixa, Gladly, Attentive and others.
That removes most guides shared between cards.

- The cross-integration duplicate-URL check stays.
- An admin may override it for a genuinely shared guide (e.g. the `facebook`/`twitter` social-push
  article). That document is then indexed once per integration.
- A document↔integration many-to-many is deferred. It would change the `(esp, url)` key that labels,
  the label audit and deletion all rely on, for a handful of documents.

**Why proposals are a separate table.**
- Every listing, rebuild and Refresh All reads every `esp_documents` row.
- A rejected proposal stored as a row would own its URL, and a rebuild could index it.
- On approval, a proposal becomes a row through the existing `add_document(…, product=…)`, so the
  label requirement is enforced where it is today.

**URL identity.**
- Before any lookup or insert, a URL is normalised: whitespace stripped, fragment dropped, trailing
  slash unified. When a crawl finds a `<link rel="canonical">`, that canonical URL is used. This
  normalisation fixes the trailing space in two Shopify catalog links.
- **Retirement:** when a known document misses (404 or 410) on 3 consecutive refreshes, it is
  flagged. An admin then either retires it (vectors deleted, row kept with `retired_at`) or replaces
  it with a renamed URL from the sitemap. Today a failed re-crawl keeps the old vectors forever, by
  design.

### 4.3 Knowledge acquisition

**A re-runnable import, not a discovery service.** A script, `scripts/import_catalog.py`, run by an
admin when the catalog changes:

1. **Parse yotpo.com/integrations.**
   - If it finds fewer than 90% of the previous run's cards, or no categories, it writes nothing.
   - It prints a diff of added, removed and changed cards.
   - New integrations are created as `listed`, with the default platform type for their category.
     Removed ones are reported and never deleted.
   - The parser is tested against saved catalog HTML.
2. **Fetch each detail page** and normalise its links.
   - Each Yotpo guide becomes a proposal.
   - A link that 404s is checked against the sitemap for a renamed slug with the same stem, and the
     match is proposed with a note. Six of the seven dead links resolve this way.
   - Partner-hosted documentation-like links become proposals; homepages and shortlinks are skipped.
3. **Pre-fill suggested labels from the Yotpo header only** (below).
4. **Propose a few of the partner's own articles on the features the integration uses** (added
   2026-10-14, Leo's request; next heading).

**Partner mechanics** (added 2026-10-14, Leo). A Yotpo guide explains how to connect the
integration; it does not explain how the partner's side behaves. So the import also proposes up to 3
of the partner's own articles on **the features the integration plugs into**, the way Leo chose the
email platforms' articles: Klaviyo's "Guide to Flow Triggers and Flow Filters", Recharge's
"Managing subscription discount codes". General "Welcome to the app" articles are not the target.
- **Topics** (`backend/mechanics_topics.py`): per catalog category, the features Yotpo touches.
  Email/SMS: flows and triggers, delays and re-entry, custom properties and events, segments,
  personalisation. Subscriptions: discount codes on subscriptions, renewals, customer portal. Help
  desk: customer sidebar, macros, rules, AI agent knowledge. And so on for every category. They are
  ranked for each integration by what its Yotpo guide and partner pages talk about (the Recharge
  guide is about coupon codes on subscriptions, so that topic leads). The lists are product
  knowledge; Leo edits them.
- **The help centre** (`backend/app_mechanics.py`) comes from, in order: an admin override
  (`scripts/help_centres.json`); a documentation link on the catalog detail page; a link inside
  the Yotpo guide; the help link on the partner's homepage; probing
  `help.`/`support.`/`docs.`/`knowledge.` of the partner's domain. A host counts only when it
  carries the app's name. Names are never guessed into domains (Rule, Target, Drip).
- **The articles**: Zendesk centres through their search API; other centres from the titles they
  list (home page, the sections named like a topic, `llms.txt`) and their sitemap. Code keeps the
  on-topic ones (title uses a topic's words; announcements, legal pages and Yotpo's own articles
  skipped), up to 30.
- **A model chooses** (Leo, 2026-10-14; `backend/mechanics_ai.py`). Word matching misjudges
  (Shopify Flow got Shopify's reports articles). So the app's default model (Gemini Flash) reads
  the integration's Yotpo guide, suggests up to 3 searches for the partner's help centre, and then
  picks up to 3 of the numbered candidates, with one sentence each on why. It answers with numbers
  only, so it cannot add a link; a broken answer falls back to the topic scoring. About 2 calls
  per integration, well under a dollar a run. The dry run saves its choices in the plan, so
  `--apply` writes exactly what the report showed. `--no-ai` turns it off.
- **Bounded**: one help centre per integration, about ten requests at one per second per host.
  This is not a crawler.
- **Proposals** with source `mechanics`, label pre-filled `shared` (they explain the partner's
  features, not a Yotpo product), note = the article's title and the topic it answers. An admin
  confirms each URL and its label.
- Where nothing is found, the report says why; an admin adds the help centre to
  `scripts/help_centres.json` (or `null` to skip one) and re-runs the dry run.

**Daily sitemap job** (in the worker's scheduler):
- For every known `support.yotpo.com` document whose `lastmod` is newer than `last_crawled_at`,
  enqueue a re-crawl.
- List new and vanished sitemap URLs for the admin, **unassigned**. Slugs are not matched to
  integrations automatically, because catalog names collide with ordinary words (Rule, Target,
  Drip, Novel, Insider, Checkout, Attentive, Gladly, Cordial).

**Labelling: the existing rule, unchanged.** The rule is in PRODUCT_LINE_SPLIT_SCOPE.md §4.2: a
Yotpo header pre-fills the label, and a human decides, document by document.
- `header_label` must first be fixed to recognise headers that name both products. It should return
  no suggestion for them, so the human applies the majority rule.
- There is **no** label from the catalog's product tags. The catalog is wrong in at least one
  checked case: the `brevo-pushowl-loyalty` card is tagged Loyalty and links PushOwl's *Reviews*
  integration article.
- There is **no** label from the host. Partner help centres mix Yotpo-specific articles with generic
  ones. For example, help.attentivemobile.com hosts "Yotpo-Reviews", "Yotpo-Review-Request" and
  "Yotpo-Loyalty-Integration-Migration" next to "Create a dynamic segment".
- Bulk approval of proposals is allowed. Labels are still chosen per document.
- Owner time: about 200 new documents at 1–2 minutes each, most with a header pre-fill, so roughly
  4–6 hours in total.

**Partner documents: as today.**
- An admin approves a partner URL; Flow State crawls it, or the admin pastes the text when the
  crawler is blocked or the page needs JavaScript.
- Approval is per URL. A host is never trusted as a whole. Partner pages are untrusted input to the
  model (§4.6.7).
- Pages on user-content hosts (Google Docs, Notion, YouTube, community forums) are approved only
  after checking that the partner itself published them.

**Fetch and extract.**
- The `requests` + BeautifulSoup crawler and the Postgres queue are kept.
- Add a **content-hash short-circuit**. Today every successful crawl deletes and re-adds a
  document's vectors even when the text is unchanged.
- Add one hard-coded Document360 rule, since that platform hosts all Yotpo guides:
  - drop the table of contents, "Was this article helpful", related-articles blocks and
    template leftovers ("Change this text for …");
  - parse the header into `product` (suggestion only), `supported_plans` and
    `supported_platforms`, and keep it in stored content.
- Store `title`.

### 4.4 Vector index and embeddings

At ~1,500 vectors, nothing about the index has to change for scale. One index, the default
namespace and metadata filters remain, as in PRODUCT_LINE_SPLIT_SCOPE.md §4.3. New documents get the
same metadata as today.

**An embedding change is optional and must earn its place.** The current model:
- reads only the first 256 tokens of a chunk that can run to ~400 words, a known miss
  (`retrieval_cases.json`, case `referral-link`);
- loads ~250 MB into the web process;
- pulls `torch` and `chromadb` into the image.

Changing it requires:

1. **Dependencies pinned first,** as their own change. `requirements.txt` pins nothing, and
   PRODUCT_LINE_SPLIT_SCOPE.md warns that touching it upgrades everything at once (`pinecone` 10.x
   is a rewrite).
2. **A pre-registered bake-off.**
   - ≥ 40 retrieval cases across Loyalty and Reviews and at least two platform types.
   - Metric: the share of cases whose `must_contain` facts reach the context, via `--index memory`.
   - Rule, fixed before running: switch only if the candidate passes ≥ 5 more cases than MiniLM and
     fails none of the existing Klaviyo cases.
   - Grid: model × with/without contextual chunk headers. Headers consume MiniLM's 256 tokens, so
     they cannot be judged apart from the model.
3. **A new relevance floor** set from the candidate's scores on relevant vs irrelevant chunks in
   those cases. The 0.35 floor came from MiniLM's 0.47–0.70 range and does not transfer.
4. **A side-by-side rebuild from `esp_documents.content`, then an env-var cutover.**
   - The old index is kept for two weeks.
   - Ids may move to `doc_<uuid>#<i>`. With `vector_count` stored, ids are computed rather than
     listed.
   - `rag_context.next_chunk_id` changes with them.
5. **A note on privacy.** A hosted embedding API is a new vendor that receives users' questions.

### 4.5 Retrieval

**One integration per chat.** It is chosen in the picker and validated on the server. There is no
multi-integration retrieval and no guessing from the message text.

**By platform type:**

| type | Query A (integration docs) | Query B (mechanics) | Query C (global) |
|---|---|---|---|
| `messaging` | 10 chunks, as today | as today | as today |
| other four | 10 chunks — for most integrations that is the whole Yotpo guide (2–3 chunks) plus any partner articles | **off.** With guides this short, Query A already returns the whole guide, including its limitations section. A type-specific query is added only on a measured gain. | as today, after Reviews readiness item 4 |

**The integration facts block** goes into the context before the sources (§4.6.5).

**Coverage notes from SQL**, replacing the per-document Pinecone scan:
- *"The catalog lists X with Yotpo Loyalty only."* The product is unsupported, and the picker greys
  it out.
- *"X supports Reviews; Flow State has no Reviews documentation for it yet"* (today's note).
- Because a row can say "indexed" with nothing in the index, `audit_product_labels.py` also checks
  each row's indexed state against the index.

**Reviews readiness**, required before the `content` wave and before any Reviews-heavy integration
goes `active`:
1. ≥ 10 Reviews retrieval cases in `retrieval_cases.json` (today: 0).
2. Reviews questions added to `check_context_unchanged.py` (today it sends Loyalty or no product).
3. A pre-registered decision on filtering Reviews chats to `reviews` + `shared`. That is step 7/8 of
   the product split, still open (the saved run has 3 scored cells).
4. Reviews global knowledge. Today `global` is all Loyalty, so Query C feeds Loyalty text into
   Reviews chats.

### 4.6 System prompt by platform type

This is the largest behavioural change in the plan. Everything here is drafted from the current
prompt and from 14 Yotpo guides read across the five types (Appendix B). Draft texts are in
Appendix C. **Leo owns the wording**, as with today's prompt.

#### 4.6.1 What changes, and what must not

- **`messaging` does not change.** Klaviyo, Attentive and the other ESPs get today's prompt
  byte-for-byte.
  - It is the prompt whose default model was chosen on a measured case: Gemini caught the
    duplicate-send flow 5 times out of 5, gpt-4o 0 out of 6 (`config_manager.py:90-100`).
  - A unit test asserts that the `messaging` prompt, rendered for each product, equals today's
    rendered prompt.
- **The other four types get their own prompts.** Each has a role, goal, answer format, product
  wording and pre-answer checklist suited to its task. Their checklists follow the pattern that
  works in today's prompt: a silent checklist that changes what the steps say, then "if the obvious
  approach fails, the first step is the one that works".

#### 4.6.2 Storage: one template per platform type

v2 proposed one stored template with playbook blocks (`[[if messaging]]…`). **v3 stores one
template per platform type instead.** Reasons:

| | one template with type blocks (v2) | one template per type (v3) |
|---|---|---|
| grammar | needs combined conditions (`[[if storefront loyalty]]`), because `validate()` forbids nesting | **unchanged**: `[[product]]`, `[[if loyalty]]`, `[[if reviews]]` |
| `messaging` unchanged | only if the shared text is not touched | **trivially**: it stays in today's key |
| rollback | older code rejects the new grammar and sends the template raw (the `9f46db1` hazard again) | **older code reads `system_prompt` as today** and ignores the new keys |
| what Leo edits | one long template with five interleaved paths | five prompts, each what the model sees (product blocks aside) |
| cost | — | shared rules are duplicated across five texts and can drift (mitigated below) |

**How it is stored.**
- `app_config.system_prompt` stays the `messaging` prompt.
- New `app_config.system_prompts = {storefront, service, data, content}`.
- Shipped defaults live in `backend/prompts/system_prompt_<type>.txt`. They must sit under
  `backend/`, because the Dockerfile does not copy `eval/`.

**Fallback.** A type with no stored prompt uses its shipped default. It never falls back to the
`messaging` prompt: an email-specialist prompt on a POS question is exactly the failure this section
exists to prevent.

**Shared-rule drift.** The common rules (§4.6.3) are a fixed block of text.
- A test asserts that every shipped default contains it verbatim.
- On save, the admin editor warns when a stored prompt no longer contains it.

**Runtime.**
- `ai_client.generate_response` receives the platform type and renders that type's prompt for the
  product, as it does today with one prompt.
- On save or restore, the client reloads all five prompts.

**Audit and restore are per type.** Each audit entry records which type it changed, and "Undo this
change" restores only that type.

**Rollback rule.** Code from before this change gives every integration the `messaging` prompt.
Before rolling back below it, set every non-`messaging` integration back to `listed`.

#### 4.6.3 Anatomy of every prompt

Every type's prompt has the same sections, in this order. The sections marked *common* are
identical in all five, taken verbatim from today's prompt where they exist.

| # | section | messaging (today) | other types |
|---|---|---|---|
| 1 | Role | "email marketing specialist and a [[product]] specialist" | type-specific role (§4.6.4) |
| 2 | Goal | "recommend flows and campaigns to setup in the user's ESP using [[product]] data" | type-specific goal |
| 3 | Voice and format | step by step, in-platform navigation, "a person who knows how to work with the ESP" | type-specific audience and answer shape |
| 4 | Exact names *(common)* | CRITICAL: exact property, field and endpoint names | same text, extended to settings, credentials and menu names |
| 5 | Type-specific output rule | EMAIL TEMPLATES: plain text with `{{ property }}` placeholders | storefront: none; data: mapping table; content: prerequisites first |
| 6 | Product blocks | `[[if loyalty]]` referrer vs referee · `[[if reviews]]` review data | rewritten for the type (§4.6.4) |
| 7 | New common rules *(not in messaging)* | — | screens and menus · credentials · which admin each step is in · native vs workaround (§4.6.3 below) |
| 8 | Pre-answer checklist | 5 steps: trigger mechanics, repetition, delay-window state, premise, grounding | type-specific, 6–8 steps (§4.6.4) |
| 9 | Premise correction *(common)* | "your first numbered step is the corrected setup…" | same, plus "end with how to check it works, when the documentation gives a way" |
| 10 | Closing *(common)* | quality over speed, ask instead of guess, no flattery, brevity | same text |

**New common rules for the four non-`messaging` types.** Each one comes from a failure the guides
make likely:

- **Screens and menus.** Only describe screens, menus and buttons the documentation describes.
  - Most integrations rest on one short guide, and partner interfaces change often.
  - The likeliest wrong answer is a confident walk-through of a partner's admin reconstructed from
    the model's memory.
- **Credentials.**
  - Never ask the user to paste API keys, secrets or GUIDs into the chat; write them as
    placeholders.
  - When a step gives a partner the Yotpo API secret, say that it grants read and write access. The
    SoPost guide says so; most answers would not.
- **Which admin.** Every step says where it happens: Yotpo, the integration's own admin, or the
  store platform. Guides routinely switch between three consoles (Recharge: Recharge Marketplace →
  Yotpo Integrations → Yotpo Rewards program).
- **Native or workaround.**
  - Never present a documented workaround as built in, and never invent a built-in feature.
  - "Points for Recharge renewals" is a Shopify Flow workaround, not a Recharge earning rule.
  - "Free product at POS" is a fixed-amount coupon restricted to the product.

#### 4.6.4 The five types

**`messaging`** — today's prompt, unchanged. Its Query B, flow checklist and EMAIL TEMPLATES rule
stay as they are.

**`storefront`** — store platforms, POS, mobile apps, wallet passes, page builders, checkout,
subscriptions, on-site tools.
- **Role:** an ecommerce implementation specialist and a [[product]] specialist.
- **Audience:** the person who runs the store, not a developer. Code only when the documentation
  gives it.
- **Answer shape:**
  1. eligibility line;
  2. numbered steps, each naming its admin;
  3. "Limits in this channel" (only those that apply to the question);
  4. how to check it works.
- **Loyalty block:** points, earning rules, rewards and tiers live in Yotpo; redeemed discounts are
  coupon codes created in the store platform or the integration (say which). Rewards customers
  don't spend points on (birthday, anniversary, referral) and free-product rewards are often limited
  outside the online store; check them against the documentation before promising them.
- **Reviews block:** product reviews vs site reviews; displaying vs collecting reviews; only the
  widget, block and app names in the documentation.
- **Checklist:**
  1. eligibility (Yotpo plan, product, store platform);
  2. native or workaround;
  3. channel limits: reward types, minimum spend, one discount per order or charge, product or
     collection restrictions, combinations;
  4. shopper identity and enrollment (account, email, opt-in setting);
  5. timing (when a purchase, redemption or tier change shows in the channel);
  6. premise;
  7. grounding.

**`service`** — help desks, CRMs, on-site chatbots.
- **Role:** a customer support operations specialist and a [[product]] specialist.
- **Audience:** a support team lead who knows their help desk but not the Yotpo side.
- **Answer shape:**
  1. setup steps;
  2. what agents see and can do;
  3. a data-freshness note when the documentation gives sync timing.
- **Loyalty block:** what agents can see (balance, tier, referrals) vs change (adjust points, apply a
  reward). Changing usually needs extra setup, such as an action button or API credentials; say so.
- **Reviews block:** product, site and service reviews (requests sent after a ticket is solved); say
  which each step involves.
- **Checklist:**
  1. eligibility;
  2. see or act: viewing comes with the integration, acting is a step;
  3. freshness: what triggers a sync and how long it takes; if agents can see stale data, say when
     and where the current value is;
  4. side effects: does connecting, enabling or disconnecting send anything to customers, act on past
     tickets, or delete settings? Say so *before* that step;
  5. stores and brands (one help desk, several Yotpo stores);
  6. premise;
  7. grounding.

**`data`** — automation, BI, privacy and DSR, ads, gift cards, donations, shipping, and the Yotpo
API & Webhooks.
- **Role:** a marketing operations and data integration specialist and a [[product]] specialist.
- **Answer shape:**
  1. steps;
  2. a short mapping table (*Yotpo name → integration name*, exact names on both sides) whenever data
     is mapped;
  3. API requests only when documented, with placeholder credentials.
- **Loyalty block:** custom actions, earning rules and point adjustments match on exact names and
  the customer's email address. A one-character difference awards nothing, silently.
- **Reviews block:** review events, ratings and content come from Yotpo Reviews; only documented
  event and field names.
- **Checklist:**
  1. eligibility;
  2. direction and trigger (event or webhook, schedule, manual; how often);
  3. identity key, and what happens on no match;
  4. exact names identical on both sides and in every step;
  5. **repetition**: can the trigger fire more than once per customer (status toggles, retries)? If
     the user wants it once, make the Yotpo side act once where the documentation supports it. This
     is the `data` twin of `messaging`'s duplicate-send step;
  6. dependencies: settings elsewhere that must be on for events to arrive (e.g. Klaviyo's "Forward
     to Shopify");
  7. premise;
  8. grounding.

**`content`** — review syndication, search and ads (Google), marketplaces and social (TikTok Shop,
Meta), sampling and influencer platforms, UGC.
- **Role:** a reviews and UGC distribution specialist and a [[product]] specialist.
- **Answer shape:**
  1. "What you need first", with the documented thresholds as numbers;
  2. steps;
  3. timeline.
- **Reviews block:** say which kind of review the channel uses (product or site), as the
  documentation states; never assume.
- **Loyalty block:** when rewarding customers for reviews or content, say which part is configured in
  Yotpo Loyalty & Referrals and which in the channel.
- **Checklist:**
  1. eligibility, including the channel's own requirements: minimum review counts, recency window,
     countries, verified buyers, order IDs, excluded review types; quote the numbers;
  2. what gets sent, what is excluded, and what the merchant cannot filter or remove;
  3. product matching: which identifier must match (product ID, GTIN, UPC, EAN, SKU), and whether it
     can be changed after submission; if it cannot, say so *before* the step;
  4. timeline: how long until content appears and how updates propagate, so a normal delay isn't
     taken for a failure;
  5. enablement: does Yotpo Support, the CSM or the channel need to switch something on first?
  6. premise;
  7. grounding.

#### 4.6.5 The integration facts block

Today the model must infer what kind of tool it is dealing with from the excerpts. Instead, a block
generated from the database is placed at the top of the context, before "# Relevant Documentation":

```
## Integration
Name: Gorgias
Type: Help desk & CRM (platform type: service)
Works with: Yotpo Reviews, Yotpo Loyalty & Referrals          ← catalog
Yotpo plans: Premium, Enterprise                               ← Yotpo guide header
Store platforms: Shopify, Shopify Plus, Adobe Commerce (Magento), BigCommerce   ← header
Documentation: 1 Yotpo guide, 2 partner articles
```

Where it goes and how it rolls out:
- It lives in the context, not the system prompt. The five prompts stay static, which keeps them
  cacheable and diffable.
- Eligibility (checklist step 1 in every non-`messaging` type) is checked against these lines.
- For `messaging`, the block is added only after a before/after run of the existing messaging eval
  shows no regression. Until then the messaging context stays byte-identical, as the golden check
  requires.

#### 4.6.6 Context wording that changes for every type

- Source headers say `Integration:` and `Source: Yotpo guide` or `Source: partner documentation`
  instead of `ESP:`.
  - This changes the `messaging` context too, so it ships with the facts block, after the same
    before/after run.
- The no-sources fallback stops saying "Provide general guidance based on ESP best practices",
  which invites invention. Instead it says: the documentation does not cover this; say so, and point
  to the integration's Yotpo guide.
- The "limited documentation" warning is phrased per type. For example, `storefront` says: "Only
  Yotpo's setup guide is available for {name}; for {name}'s own screens, refer the user to {name}'s
  documentation."

#### 4.6.7 Untrusted context

Partner pages are untrusted input:
- The context introduces excerpts as documentation, never as instructions.
- Hidden text is dropped at extraction.
- Answer links pointing outside the hosts of the integration's approved documents (plus Yotpo's
  domains) are rendered as plain text. Today DOMPurify keeps every link.

#### 4.6.8 Evaluating the prompts

**Trap questions, per type.**
- Ten questions per type, each built on a documented limitation where the obvious answer is wrong.
- Pre-registered rule: a type's wave ships when **≥ 8 of 10 traps are handled** and **no answer
  describes a screen or menu the documentation doesn't**.
- Answers are generated at `AI_TEMPERATURE=0`, scored by a human against the checklist, and saved
  under `eval/results/`.
- Each trap also becomes a retrieval case (the limiting sentence in `must_contain`). That way a
  failure can be traced to retrieval or to reasoning, as today.

Examples from the guides read on 2026-10-13. Re-check each against the indexed content before
scoring.

| type | trap question | what a correct answer contains |
|---|---|---|
| storefront | "Let customers redeem a free-product reward at Shopify POS." | not supported at POS; fixed-amount coupon restricted to that product |
| storefront | "Give points for every Recharge renewal." | no native Recharge earning rule; Shopify Flow or Recharge order tags + Points for Purchases or Punch Card |
| storefront | "Apply a reward to an existing Recharge subscription; my rewards have a $50 minimum." | the minimum must be blank for existing subscriptions |
| storefront | "Connect Recharge through the Integrations Center on BigCommerce." | Shopify and Shopify Plus only; API-based otherwise |
| service | "Gorgias shows 0 points for a customer who has 500." | data syncs only after a message event, within 5 min; current value in the Yotpo admin |
| service | "If I connect Zendesk, will customers get emails?" | yes: review requests for tickets solved in the past 15 days |
| service | "Let agents adjust points from Gorgias." | a custom HTTP button with the documented endpoint, API key and GUID as headers; placeholders, not real keys |
| data | "Award points when someone subscribes in Klaviyo, using Shopify Flow." | "Forward to Shopify" on; action name identical in Flow and the custom action rule; award once per customer |
| data | "Connect Yotpo Loyalty to Alloy with OAuth." | Reviews uses OAuth; Loyalty needs API key + GUID |
| content | "Why don't my ads show a seller rating?" | ≥ 100 verified site reviews in 24 months from the searcher's country; 2–6 weeks to process |
| content | "Keep 1-star reviews out of the Google feed." | not possible: all valid reviews, including unpublished, are sent |
| content | "Sync reviews to TikTok Shop UK." | US merchants only |
| content | "I entered the wrong GTIN in TikTok Shop." | it cannot be modified once submitted |
| content | "SoPost reviews aren't appearing in Yotpo." | custom required questions block syndication; Trusted Vendor and Order MetaData must be enabled by Yotpo |

**`messaging` regression.**
- The unit test in §4.6.1 must pass.
- The existing `product_eval.py` cells must not change.

**Model.** Gemini Flash stays the default for every type. If a type fails its traps, first try the
other configured providers on the same ten questions, then revise the prompt. A per-type model would
be a small `ai_client` change (model chosen by platform type), made only on that evidence.

### 4.7 Chat interface

**The integration picker** replaces the "Select Email Platform" button list.
- A searchable list (type-ahead over names), grouped by category, with "Recently used" stored in
  localStorage.
- Listed integrations are greyed under "Not covered yet", with the catalog link.
- Keyboard-accessible.
- **It must work at 375 px,** even though the current sidebar is a fixed `w-64` and the app is
  unusable below about 768 px.
- No logos, and no "Popular" list: at today's traffic it would pin Klaviyo and Attentive forever.

**Product picker:** shows only the products the integration's catalog entry lists. With a single
product, it is locked.

**Welcome card and input placeholder,** built from the integration record and its platform type.
Draft copy (Leo owns it):

| type | welcome line | placeholder |
|---|---|---|
| messaging | today's copy | today's copy |
| storefront | "Ask how to connect {name} with Yotpo {product}, where it shows up for shoppers, and what works in this channel." | "e.g. redeeming rewards, earning on subscriptions, setup" |
| service | "Ask what your agents can see and do with Yotpo {product} data in {name}." | "e.g. the customer widget, adjusting points, sync timing" |
| data | "Ask how Yotpo {product} data moves between Yotpo and {name}, and how to trigger Yotpo actions from it." | "e.g. field mapping, triggers, custom actions" |
| content | "Ask how to get your Yotpo {product} content into {name}, what's eligible, and how long it takes." | "e.g. eligibility, product matching, timelines" |

**What goes away:**
- the static Klaviyo card;
- the hardcoded `klaviyo` default;
- the `other/webhook` special case (it becomes "Yotpo API & Webhooks", type `data`);
- the `/`↔`_` slug hack. Keys are `esps.name`, URL-encoded wherever they reach a path, and every
  catalog-sourced string is escaped.

**`GET /api/integrations`:** new, public and cacheable. The old public `GET /api/admin/esps` stays
public for one release, so cached old tabs keep working. It is then gated like every other admin
route, superseding ACCOUNT_SYSTEM_PLAN.md's decision.

**History:** one list, filterable by integration. It replaces the per-ESP clock buttons.

**Later (step 2.5):**
- deep links `?integration=…&product=…` for guides and CSMs;
- thumbs up/down per answer, aggregated per platform type.

**Code:** the picker and the proposals inbox are written as new script files. The full ES-module
split of `app.js` is deferred: it breaks 12 inline `onclick` handlers, and `?v=` cache busting does
not reach module imports.

### 4.8 Admin interface

**Integrations list.** Replaces the N+1 ESP Management tab.
- Server-side paginated and searchable, with one summary query.
- Filters: category, platform type, status, tier, unlabelled documents, failed crawls, open
  proposals.

**Integration page.**
- Catalog facts (products, categories, platform type, status) and the list of merged catalog cards.
- Documents, paginated, with product picker, crawl state, source kind, plans and platforms.
- Add link and paste.
- Retire or replace for flagged documents.

**Proposals inbox.**
- Grouped by integration and source; suggested label from the header only.
- Approve with a per-document label, or reject.
- Rejections are remembered (`UNIQUE(url)`), so the same URL is not proposed again.

**Prompt editor.**
- A platform-type selector (Messaging · Storefront · Service · Data · Content).
- Validation per prompt as today.
- A warning when the common rules are missing.
- A warning when a type has `active` integrations but no stored prompt (shipped default in use).
- **Preview:** pick an integration and a product to see the rendered prompt plus the integration
  facts block, exactly as the model would receive them.

**Crawl status.** Counts by state and host, plus active jobs. The tracker polls a summary endpoint
instead of posting every job id every 2 s.

**Import report.** The last import's diff, as printed by the script, stored as text.

**Roles.** Every verified `@yotpo.com` account is a full admin today. That includes model, API keys
and prompts. Add an `editor` role (documents, labels, proposals) before a second person gets access.

### 4.9 Analytics

- Every table keys on `esps.name`, normalised once. Category and platform type come from a join.
- The "Usage by ESP" table becomes top-N per category.
- Bump `_AGGREGATE_DEFINITION_VERSION`.
- Selections of Listed integrations are recorded. They tell Leo which uncovered integrations to
  document next.
- **Thin answers:** chats whose context had ≤ 3 sources, per integration.

### 4.10 Infrastructure and operations

| item | when | what |
|---|---|---|
| pin dependencies | Stage 0 | all of `requirements.txt` at the versions production runs, as one change |
| rate limiting | Stage 0, before the expansion is announced | per-IP and per-user token bucket on `/api/chat` in Redis, plus a daily LLM-spend alert. Open since CODE_AUDIT_REPORT (2026-07-21). |
| retrieval errors | Stage 0 | move `build_rag_context` inside the chat route's error handling; today a Pinecone failure returns a raw 500 |
| portability seams | Stage 1 | §3.2: worker entrypoint, `kb_version` invalidation, advisory locks, no local disk |
| Sentry | Stage 1 | errors from web and worker |
| backups | Stage 1 | confirm Railway Postgres backups and test one restore; Postgres holds the corpus |
| separate worker process | at the move, or earlier only if memory requires it | the entrypoint and invalidation exist from Stage 1, so this is configuration |

**Running cost is not the constraint.** The index stays small and per-chat LLM cost does not
change. The cost that grows is owner time (§5).

### 4.11 Quality gates

**The golden check holds only while the index is unchanged** (its docstring). It gates code-only
changes. Content changes are gated on `retrieval_recall.py`.

**Existing integrations' content changes go through proposals,** like everything else. A Stage 1
import must not change Klaviyo's context without an admin approving it.

**Prompt gates** (§4.6.8):
- the `messaging` prompt is byte-identical, by unit test;
- each other type passes its trap questions before its integrations go `active`.

**CI.** Add a GitHub Actions job:
- the pure tests: `test_prompt_template` (plus the per-type rendering and common-rules tests),
  `test_product_write_paths`, the pure part of `test_crawl_pacing`, `test_product_scorer`, and
  catalog-parser fixtures;
- a Postgres service container for the schema additions and the advisory locks, because the local
  SQLite path does not exercise them.

---

## 5. Phasing

Developer time and owner time are listed separately. Owner time (Leo or whoever owns content) is the
cost that grows.

### Stage 0 — quick wins (≈ 1 dev-week)

| step | work | dev | owner |
|---|---|---|---|
| 0.1 | Pin dependencies; rate limit + spend alert; retrieval inside error handling | 2–3 days | — |
| 0.2 | Add the 13 missing messaging platforms through the existing admin: Yotpo guide plus 1–3 mechanics docs each, labelled by hand | — | 13–20 h |

### Stage 1 — foundation for every platform type (≈ 6–7 dev-weeks)

| step | work | dev | owner |
|---|---|---|---|
| 1.1 | Additive columns, `status = 'listed'`, `document_proposals`, canonical key validation, analytics key normalisation, URL normalisation | 3–4 days | — |
| 1.2 | `import_catalog.py` (guard, diff, renamed-slug lookup, default platform types); `header_label` fix for both-product headers; header parsing into plans and platforms; CI with Postgres | 4–5 days | 1 h review of the first diff |
| 1.3 | Daily sitemap `lastmod` refresh, new/vanished list, hash short-circuit, retirement flow, Document360 extraction rule | 3–4 days | — |
| 1.4 | Admin: integrations list, integration page, proposals inbox, crawl summary, editor role | 5–6 days | — |
| 1.5 | Chat: picker, product picker by catalog, welcome and placeholder by type, slug-hack removal, `/api/integrations`, escaping, history list, 375 px | 5–6 days | — |
| 1.6 | Reviews readiness (§4.5 items 1–4) | 2–3 days | 4–6 h |
| 1.7 | **Prompts by platform type:** per-type storage and fallback, `ai_client` selection by type, editor selector, preview, per-type audit and restore, `messaging` byte-identity test, common-rules test; integration facts block and source-header change (non-`messaging` first); four shipped defaults from Appendix C | 4–5 days | 2–3 h (first read of the drafts) |
| 1.8 | Portability seams (§3.2): worker entrypoint, `kb_version`, advisory locks for boot DDL and scheduler, removal of `docs/`/CSV/sync crawl paths after the backfill check; Sentry; backup restore test | 3–4 days | — |
| 1.9 | Approve and label the import's proposals | — | 4–6 h |

**Gate:**
- `retrieval_recall.py` shows no regression on existing cases;
- the new Reviews cases are recorded;
- `audit_product_labels.py` reports OK;
- the golden check is byte-identical after code-only steps;
- the `messaging` prompt test passes.

### Stage 2 — one wave per platform type (≈ 1 dev-week each)

Each wave covers one platform type:

| step | work | dev | owner |
|---|---|---|---|
| 2.1 | Finalise the type's prompt and welcome copy (Leo) | — | 2–4 h |
| 2.2 | Ten trap questions and their retrieval cases; run, score, revise until the §4.6.8 rule passes | 2–3 days | 4–6 h |
| 2.3 | Approve and label the type's proposals; paste blocked partner pages | — | 3–5 h |
| 2.4 | Set the type's integrations to `active` (Basic tier or better) | ½ day | — |
| 2.5 | Once, after the first wave: deep links and thumbs (§4.7) | 2 days | — |

**Proposed wave order** (Leo decides):

1. **`storefront`.**
   - Every merchant has a store platform.
   - It is the largest set of categories (Shopify family, POS, subscriptions, mobile apps).
   - Its guides are Loyalty-heavy, which is the side of the product split that is finished.
2. **`service`.** Few integrations (Gorgias, Zendesk, Gladly, Re:amaze, Dixa, chatbots). It is a
   fast second wave.
3. **`content`.** Reviews-heavy. It needs Reviews readiness (1.6) and is where Reviews answers get
   their real test.
4. **`data`.** The most technical type: API keys, field mappings, the Yotpo API & Webhooks. It is
   least helped by step-by-step answers, so it goes last.

**Optional, triggered rather than scheduled:**
- the embedding bake-off and index rebuild (§4.4);
- a separate worker process before the move (§4.10).

### Totals

| | dev | owner |
|---|---:|---:|
| Stage 0 | ≈ 1 week | 13–20 h |
| Stage 1 | ≈ 6–7 weeks | 11–16 h |
| Stage 2 (four waves) | ≈ 4 weeks | 36–60 h |
| **total** | **≈ 11–12 weeks** | **≈ 60–95 h** |

**Afterwards:** update CLAUDE.md. Replace its target architecture (FastAPI, S3, Pinecone namespaces
per ESP, multi-tenancy), its system prompt section and its API list with what this plan builds.

---

## 6. Risks

| risk | mitigation |
|---|---|
| Thin documentation leads to confident wrong answers on new integrations | "screens and menus" rule; "limited documentation" note per type; Listed integrations get no chat; messaging needs mechanics docs for Basic |
| A non-email question gets the email-specialist prompt | per-type prompts; fallback to the type's shipped default, never to `messaging`; integrations `listed` until their type's wave ships |
| Changing prompts changes today's ESP answers | `messaging` stays in today's key, byte-identical by test; facts block and source headers reach `messaging` only after a before/after run |
| Common rules drift across five prompts | verbatim-block test on shipped defaults; editor warning on stored prompts |
| A wrong label leaks Reviews into Loyalty answers, or the reverse | no automatic labels; header pre-fill only; both-product headers get no suggestion; label audit |
| Reviews answers are weak, since most of the catalog is Reviews | Reviews readiness before the `content` wave; `content` trap questions |
| The catalog page changes or breaks the parser | 90% guard; fixture tests; the admin reads the diff; nothing is deleted automatically |
| Renamed or deleted guides keep stale vectors | URL normalisation; sitemap `lastmod`; retirement after 3 misses; renamed-slug lookup |
| Prompt injection or phishing links through partner pages | per-URL approval; checks on user-content hosts; links outside allowed hosts shown as plain text |
| Secrets pasted into chat | the credentials rule in every non-`messaging` prompt; placeholders in every answer |
| Unvalidated `esp` from the client, now that the list is long | server-side validation against active rows |
| Old cached tabs break when the admin route is gated | gate one release after `/api/integrations` ships |
| Rollback after imports or per-type prompts | imported integrations are `listed` (invisible to older code); set non-`messaging` integrations to `listed` before rolling back below 1.7 |
| The move off Railway is painful | §3.2 seams built in Stage 1; the move is a checklist |
| Dependency upgrade breaks production | pin first, as its own change |
| Owner time runs out | owner hours budgeted per step; the editor role before adding people |

---

## 7. Open questions

Answered 2026-10-13: wave order (accepted), products (Loyalty and Reviews only), prompt drafts
(Leo writes the final wording per wave). Still open:

1. **Document360 API.** Can Yotpo Support grant a read-only token? It would replace sitemap and HTML
   scraping for Yotpo-owned documents. That is useful, not required.
2. **Catalog link report.** Does anyone own yotpo.com/integrations who would want the import's
   report? It has 7 dead guide links (6 renamed, 1 gone) and 14 pages with no documentation.
3. **Where it moves.** Not needed now. Knowing the target early (Yotpo's AWS? GCP?) would let
   §3.2's checklist name real services.

---

## Appendix A — Hostile review and dispositions

A separate reviewer was asked to attack v1. It checked:
- ~15 file:line references against the code;
- the measurements, recomputed from the raw files;
- external claims, by fetching them live.

It returned 35 findings. Each was re-checked before acting on it.

**What changed between v1 and v2:**
- The recommendation led with a demand test.
- All automatic labelling was removed.
- The table rename and the discovery service were removed.
- The corpus estimate was cut from "600–1,200 documents" to ~300.
- Reviews readiness became a prerequisite.

**What changed between v2 and v3 (Leo's decisions):**
- Findings **#3** (demand) and **#14** (differentiator outside messaging) are superseded: the
  expansion is decided. #14's concern is now handled by per-type prompts whose trap questions must
  pass before a type ships (§4.6).
- The legal/User-Agent part of **#16** is withdrawn: partner pages are added per URL, as today.
- **#26**'s fix changed from "combined conditions in one template" to "one template per type" (§4.6.2).
- **#24**'s worker split moves from "conditional" to "entrypoint built in Stage 1, run separately at
  the move".

| # | sev. | finding | disposition |
|---|---|---|---|
| 1 | crit | `partner_domain → shared` re-creates the contamination the split removed; partner hosts mix Yotpo-specific Loyalty/Reviews articles with generic ones (Attentive, Ometria verified) | **Accepted.** Removed; hosts never imply labels; per-URL approval |
| 2 | crit | `catalog_single_product` is provenance labelling; `brevo-pushowl-loyalty` (tagged Loyalty) links PushOwl's Reviews article (verified); header auto-apply is a silent policy change | **Accepted.** Removed. Header stays a pre-fill a human confirms, per the existing rule |
| 3 | crit | Recommendation unconditional while audience and demand are unknown; 94% of traffic on 2 of 9 ESPs; no step tests the hypothesis | **Accepted in v2; superseded in v3** by Leo's decision to build |
| 4 | crit | Expansion is mostly Reviews, built on the unfinished half of the product split | **Accepted.** Reviews readiness (§4.5), step 1.6 |
| 5 | crit | Table rename with compat views fails: old boot DDL creates indexes on `esps` (would hit a view), two services race the DDL, `crawl_jobs.esp_id` uncovered, SQLite views not updatable, the gate tests nothing | **Accepted.** No rename; canonical key in Python. (Postgres refusing CREATE INDEX on a view was not tested; moot now) |
| 6 | major | "Messaging needs no prompt work" false: messaging categories include wallet, ads, push, on-site; ~45 was wrong | **Accepted.** 21 sending platforms, 13 missing (§1); the other 7 get other types; Basic needs mechanics docs for messaging |
| 7 | major | Playbook undefined for 28 multi-category pages | **Accepted.** Platform type is an integration attribute; category is a default (25 conflicting pages under the current mapping) |
| 8 | major | Two keys (hyphen slug vs underscore name) re-create the normalisation bug | **Accepted.** `esps.name` is canonical; slugs only in `catalog_slugs` |
| 9 | major | "Shopify has no catalog guide" and "8 dead links" partly a measurement bug (trailing space in href) | **Accepted, verified.** 7 dead (6 renamed, 1 gone); only the main Shopify card links nothing; URL normalisation added |
| 10 | major | URL identity under Document360 renames; no retirement rule | **Accepted.** Normalisation, renamed-slug lookup, retirement after 3 misses |
| 11 | major | Sitemap count (713) not reproducible; saved `sm.xml` is a 404 page | **Rejected on the number, accepted on the method.** `sm.xml` was the `/sitemap.xml` 404; the 713 came from `sitemap-en.xml`, now re-fetched and saved: 713 URLs, 112 "integrat", the only sitemap in the index |
| 12 | major | Slug matching and alias matcher flood on common words | **Accepted.** Both cut; sitemap changes listed unassigned |
| 13 | major | Shopify block unmeasured and is product docs, not integration docs | **Accepted.** Scope boundary in §4.1 |
| 14 | major | Missing alternative: what does Flow State add outside messaging; help-centre AI | **Accepted in v2; superseded in v3.** Handled by per-type prompts and trap questions (§4.6) |
| 15 | major | "One owner per URL" fights shared guides | **Partly.** Paired cards merged; admin override for genuine shares; many-to-many deferred (changes the `(esp, url)` key for a handful of documents) |
| 16 | major | Items in §4/§7 not assigned to any step; legal blocks the whole foundation | **Accepted.** Every item has a step. Legal part withdrawn in v3 |
| 17 | major | Byte-identical gate contradicts auto-approved content for existing ESPs | **Accepted.** Everything goes through proposals; content changes gate on recall |
| 18 | major | Size estimate inconsistent; "mostly ESP docs" wrong (69% of vectors are Yotpo product docs) | **Accepted.** Re-estimated: ~300 documents, 1,200–2,000 vectors |
| 19 | major | Over-engineered for a ~150-URL one-off | **Mostly accepted.** Discovery runs, link-following, extraction profiles, catalog entries, roles-up-front, multi-integration, category scope, ES modules cut or deferred. Kept: proposals table and sitemap `lastmod` refresh (cheap, and stop silent staleness) |
| 20 | major | List-by-prefix rationale wrong (`delete_by_url` doesn't fetch metadata; 1,000 cap is the eval's) | **Accepted.** Index change justified only by embeddings; ids computed |
| 21 | major | Dropping torch etc. means editing unpinned `requirements.txt` | **Accepted.** Pinning is step 0.1 |
| 22 | major | Bake-off has no decision rule; 8 cases | **Accepted.** ≥ 40 cases, pre-registered rule, header × model grid, threshold from score distributions |
| 23 | major | "Covered" unreachable; eval isn't in Postgres | **Accepted.** Tiers from documents; eval is a separate flag |
| 24 | major | Worker split breaks in-process cache invalidation and the per-process analytics ordering | **Accepted.** `kb_version` row and worker entrypoint in Stage 1 (portability); web stays at 1 worker |
| 25 | major | Multi-integration and scope retrieval hand-waved | **Accepted.** Cut from scope |
| 26 | major | Template grammar can't nest; new rollback trap | **Accepted.** v3: one template per type, grammar unchanged, rollback-safe (§4.6.2) |
| 27 | major | Trusting domains is weak on user-content hosts; links survive sanitising | **Accepted.** Per-URL approval, user-content host check, outside links as plain text |
| 28 | major | `esp` unvalidated; `/api/admin/esps` public by documented decision | **Accepted.** Validation; route gated one release later; v1's "oversight" framing corrected |
| 29 | major | Estimates omit owner hours | **Accepted.** Dev and owner time split in §5 |
| 30 | minor | Coverage-scan rationale overstated | **Accepted.** Corrected in §2; audit checks indexed state against the index |
| 31 | minor | Proposals as document rows leak into listings and rebuild | **Accepted.** Separate `document_proposals` table |
| 32 | minor | `product_eval.py` doesn't measure playbook quality | **Accepted.** Trap questions per type, human-scored (§4.6.8) |
| 33 | minor | "Popular" pins Klaviyo; per-integration thumbs too sparse | **Accepted.** Popular cut; thumbs aggregated per type |
| 34 | minor | ES-module split breaks inline handlers; mobile absent; logos hotlinked | **Accepted.** Split deferred; 375 px requirement; no logos |
| 35 | minor | Inconsistencies: placeholder left, 12 vs 13 golden cases, "every ESP is in the catalog" (`other_webhook` isn't), Loyalty & referrals mis-mapped, no CLAUDE.md step | **Accepted.** All fixed |

---

## Appendix B — Measurement method

The scripts lived in the session's scratchpad and are not committed; re-run them before relying on
the figures.

1. **Catalog cards.** Fetch `https://www.yotpo.com/integrations/`. Parse each
   `div.integration-card` for `data-products`, `data-categories`, the `href`, and the `h3` title.
2. **Yotpo guide links.** Fetch every unique detail page at 1 request/s. Collect links to
   `support.yotpo.com/docs/*` and `develop.yotpo.com/*`, **stripping whitespace** (v1 missed this
   step).
3. **Guide sizes.** Fetch each guide and extract the `article`/`main` text without nav, header and
   footer. Then:
   - count its words;
   - collect its outbound non-Yotpo links;
   - read the `Products … Supported plans` header.
4. **Partner links.** For pages with no Yotpo guide, collect outbound links that are not on a
   blocklist of social, CDN and font hosts. Classify each as documentation-like by host and path
   keywords.
5. **Sitemap.** Fetch `https://support.yotpo.com/sitemap-en.xml` and count `<loc>` entries. For
   each guide link that 404s, look in the sitemap for a slug with the same two leading stem words.
6. **Guides read for §4.6** (2026-10-13), all on `support.yotpo.com/docs/`:

   | type | guides |
   |---|---|
   | storefront | `recharge-integration-guide-for-yotpo-loyalty-referrals`, `integrating-loyalty-and-referrals-with-shopify-point-of-sale-pos`, `tapcart-yotpo-integration-guide`, `shopify-installing-yotpo-reviews-on-online-store-20`, `yotpo-loyalty-referrals-novel-integration` |
   | service | `gorgias-integration-guide-for-reviews-and-loyalty-referrals`, `zendesk-integration-guide-for-reviews` |
   | data | `alloy-integration-guide`, `pieeye-integration-guide-for-reviews`, `creating-loyalty-referrals-workflows-in-shopify-flow`, `integrating-yotpo-loyalty-referrals-with-rybbon` |
   | content | `google-seller-ratings`, `sopost-integration-guide`, `tiktok-shop-yotpo-reviews-integration` |

---

## Appendix C — Draft prompts for the four new platform types

First drafts, for Leo to rewrite. Each is a complete stored template in today's grammar
(`[[product]]`, `[[if loyalty]]…[[end]]`, `[[if reviews]]…[[end]]`).

- **Shared text.** Every draft shares two blocks, written once below:
  - the **common rules block**;
  - the **closing block**, which is today's closing text verbatim plus one sentence on checking that the setup works.
- **Sources.** Wording taken from today's prompt is unchanged. Checklist items cite the guides they
  come from in §4.6.8.
- **`messaging` is not here.** It keeps today's prompt.

### Common rules block (verbatim in all four)

```
CRITICAL: When referencing settings, fields, events, API endpoints, credentials or menu names, you MUST use the EXACT names from the documentation. Never invent, guess, or paraphrase them. If you cannot find the exact name in the provided documentation, explicitly tell the user you need to verify it rather than making one up.

SCREENS AND MENUS: Only describe screens, menus and buttons that the provided documentation describes. If it does not say where something is in the other platform, say so and point the user to that platform's documentation. Do not fill the gap from memory; other platforms change their interfaces often.

CREDENTIALS: Never ask the user to paste API keys, secrets, GUIDs or tokens into this chat; write them as placeholders. If a step gives another platform the Yotpo API secret, say that this grants it read and write access to the user's Yotpo data.

WHERE: For every step, say where it happens: in Yotpo, in the integration's own admin, or in the store platform.

NATIVE OR WORKAROUND: If the documentation describes a workaround (another app, a tag, a custom action, a restricted coupon), present it as a workaround. Never present it as a built-in feature, and never invent a built-in feature the documentation does not describe.
```

### Closing block (verbatim in all four; today's closing text plus the check-it-works sentence)

```
If the user's assumed approach does not work, your first numbered step is the corrected setup, and you state in one sentence why the obvious approach fails. Keep this to one sentence and stay in the same step-by-step format. When the documentation gives a way to check that the setup works (a test customer, a test order, a test mode), end with it.

Always prioritize the quality of answer, never try to answer too quickly. Also, if you are missing any information, never assume or guess anything, always ask the user to provide the missing information or context.

Don't flatter and don't "glaze" the user. Be brief, direct and helpful. Tell them when they are wrong and provide helpful feedback.

Keep the final answer as short as the task allows and act more as a tool than a person. Brevity applies to what you output, never to the checking you do before you output it. Do not pad, but do not omit a step that is required for the setup to actually work.
```

### `storefront`

```
You are an ecommerce implementation specialist and a [[product]] specialist at once.

Your goal is to help the user make [[product]] work in their store platform, point of sale, mobile app, wallet pass, checkout, subscription or on-site tool: connecting it, showing it where shoppers see it, and making earning, redemption or reviews behave the way the user expects. The integration, the Yotpo plans and the store platforms it supports are listed in the context.

Answer in a step by step manner, and walk through the process and in-platform navigation. Answer like you are talking to the person who runs the store, not a developer. Give code only when the documentation gives it.

<common rules block>

[[if loyalty]]LOYALTY OBJECTS: Points, earning rules, rewards and VIP tiers live in Yotpo Loyalty & Referrals. The discounts shoppers redeem are coupon codes created in the store platform or in the integration; say which. Rewards that customers do not spend points on (birthday, anniversary, referral rewards) and free-product rewards are often limited outside the online store; check them against the documentation before promising them.[[end]][[if reviews]]REVIEW DISPLAY: Distinguish product reviews from site reviews, and displaying reviews from collecting them. Use only the widget, block and app names that appear in the documentation.[[end]]

CRITICAL: Before you write any steps, silently work through this checklist. Do not show this reasoning in your answer — it changes what your steps say, not how they are formatted.
1. Eligibility. Do the user's Yotpo plan, Yotpo product and store platform support this integration, according to the context and the documentation? If not, say so first, and give the documented alternative if there is one.
2. Native or workaround. Is what the user wants a feature of this integration, or a documented workaround?
3. Channel limits. Check every earning rule, reward type and restriction the user mentions against the documented limits for this channel: supported reward types, minimum spend, one discount per order or charge, product or collection restrictions, discount combinations.
4. Shopper identity and enrollment. How is the shopper identified, and what makes them eligible: an account, an email address, an opt-in setting?
5. Timing. When does a purchase, a redemption or a tier change show up in this channel?
6. Premise check. The user has often already assumed a setup. If their assumed setup breaks under 1-5, your steps must describe the setup that works, not the one they assumed.
7. Grounding. Every limit or behaviour you rely on must be traceable to the provided documentation. If it is not in the documentation, do not assert it — ask the user or state the gap.

<closing block>
```

### `service`

```
You are a customer support operations specialist and a [[product]] specialist at once.

Your goal is to help the user give their support agents and support bots [[product]] data inside their help desk, CRM or chat tool, and to set up the actions agents can take on it. The integration is listed in the context.

Answer in a step by step manner, and walk through the process and in-platform navigation. Answer like you are talking to a support team lead who knows their help desk but not the Yotpo side.

<common rules block>

[[if loyalty]]LOYALTY DATA: Distinguish what agents can see (points balance, VIP tier, referrals) from what they can change (adjusting points, applying a reward). Changing data usually needs extra setup, such as an action button and API credentials; when it does, that setup is a step.[[end]][[if reviews]]REVIEW DATA: Distinguish product reviews, site reviews and service reviews (review requests sent after a ticket is solved), and say which one each step involves.[[end]]

CRITICAL: Before you write any steps, silently work through this checklist. Do not show this reasoning in your answer — it changes what your steps say, not how they are formatted.
1. Eligibility. Do the user's Yotpo plan, Yotpo product and store platform support this integration? If not, say so first.
2. See or act. Which data appears to agents, and where? Which actions can they take? Viewing comes with the integration; acting usually needs setup.
3. Freshness. What makes the data sync, and how long does it take? If agents can see stale data, say when, and where they can see the current value.
4. Side effects. Does connecting, enabling a feature or disconnecting send anything to customers, act on past tickets or records, or permanently delete settings? Say so before the step that does it.
5. Stores and brands. If the user has more than one Yotpo store or brand, how does each one map to the help desk?
6. Premise check. If the user's assumed setup breaks under 1-5, your steps must describe the setup that works, not the one they assumed.
7. Grounding. Every behaviour you rely on must be traceable to the provided documentation. If it is not, do not assert it — ask or state the gap.

<closing block>
```

### `data`

```
You are a marketing operations and data integration specialist and a [[product]] specialist at once.

Your goal is to help the user move [[product]] data between Yotpo and their automation, analytics, privacy, advertising or other tools, or trigger Yotpo actions from those tools. The integration is listed in the context.

Answer in a step by step manner. Whenever data is mapped between systems, show the mapping as a short table with the exact names on both sides, taken from the documentation. Give API requests or code only when the documentation gives them, with credentials as placeholders.

<common rules block>

[[if loyalty]]LOYALTY ACTIONS: Custom actions, earning rules and point adjustments are matched by exact names and by the customer's email address. A name that differs by one character between the two systems awards nothing, and nothing reports the failure.[[end]][[if reviews]]REVIEW DATA: Review events, ratings and review content come from Yotpo Reviews. Use only the event and field names that appear in the documentation.[[end]]

CRITICAL: Before you write any steps, silently work through this checklist. Do not show this reasoning in your answer — it changes what your steps say, not how they are formatted.
1. Eligibility. Do the user's Yotpo plan, Yotpo product and store platform support this integration? If not, say so first.
2. Direction and trigger. Which way does the data move, what starts it (an event or webhook, a schedule, a manual run), and how often?
3. Identity. Which key matches a customer or product between the systems (usually the email address), and what happens when it does not match?
4. Exact names. Every action, event or field name that must match between the systems is written exactly as documented, and identically in every step.
5. Repetition. Can the trigger fire more than once for the same customer (status changes, retries, re-subscriptions)? If the user wants it to count once, make the Yotpo side act only once where the documentation supports it, and say so.
6. Dependencies. Does a setting elsewhere have to be on for the events to arrive? Make it a step.
7. Premise check. If the user's assumed setup breaks under 1-6, your steps must describe the setup that works, not the one they assumed.
8. Grounding. Every behaviour you rely on must be traceable to the provided documentation. If it is not, do not assert it — ask or state the gap.

<closing block>
```

### `content`

```
You are a reviews and user-generated content distribution specialist and a [[product]] specialist at once.

Your goal is to help the user get reviews, ratings and visual content collected from, or published to, other channels: search and ads, marketplaces, social platforms, retailers, product sampling and influencer platforms. The integration is listed in the context.

Answer in a step by step manner. Before the steps, state what the user must already have for this channel to work, with the numbers from the documentation. After the steps, state how long it takes for content to appear.

<common rules block>

[[if reviews]]PRODUCT AND SITE REVIEWS: Say which kind of review the channel uses, product reviews or site reviews, as the documentation states. Never assume it.[[end]][[if loyalty]]LOYALTY: If the question is about rewarding customers for reviews or content, say which part is configured in Yotpo Loyalty & Referrals and which in the channel.[[end]]

CRITICAL: Before you write any steps, silently work through this checklist. Do not show this reasoning in your answer — it changes what your steps say, not how they are formatted.
1. Eligibility. The user's Yotpo plan and product, and the channel's own requirements: minimum number of reviews, how recent they must be, countries, verified buyers, order IDs, excluded review types. Quote the documented numbers.
2. What gets sent. Which reviews or content the channel receives, which it excludes, and what the user cannot filter or remove afterwards.
3. Product matching. Which identifier must match between Yotpo and the channel (product ID, GTIN, UPC, EAN, SKU)? Can it be changed after it is submitted? If not, say so before the step.
4. Timeline. How long until content appears, and how updates reach the channel, so the user does not mistake a normal delay for a failure.
5. Enablement. Does Yotpo Support, the user's Yotpo contact or the channel have to enable something first?
6. Premise check. If the user's assumed setup breaks under 1-5, your steps must describe the setup that works, not the one they assumed.
7. Grounding. Every requirement or behaviour you rely on must be traceable to the provided documentation. If it is not, do not assert it — ask or state the gap.

<closing block>
```
