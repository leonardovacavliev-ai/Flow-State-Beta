# Flow State Reasoning & Accuracy Optimization Plan

**Constraint**: The output format does not change. Flow State keeps its numbered, step-by-step, brief, tool-like voice. Every change below targets what the model *considers before writing*, and whether the correct facts are in front of it. The shape of the answer is held constant and enforced by a regression test (§5.3).

**Baseline commit**: `b1a95a5` (local `main` == `origin/main`, clean tree)

---

## 1. Diagnosis

### 1.1 The test case

User asked how to build 3 uniquely-worded emails off the Yotpo "Loyalty Expiration Reminder" event at 30/14/7 days. Flow State answered: use the event as the metric trigger, then insert 16-day and 7-day time delays between three emails.

That answer produces duplicate sends. The Yotpo event fires **three separate times** per customer, so each fire creates its own flow entry, and each entry runs the full delay chain.

### 1.2 The critical finding: this was not a knowledge gap

Every fact needed for the correct answer is already crawled, vectorized, and sitting in the `klaviyo` namespace:

| Fact required | Where it already lives |
|---|---|
| Event fires 3× (30/14/7 days before) | `docs_loyalty-emails-setup-guide-for-klaviyo.txt:833` |
| Date-property triggers exist as a trigger type | `articles_115002774932.txt:73` |
| Profile filters re-check before each component; **trigger filters are not checked again at send time** | `articles_115002774932.txt:84` |
| Duplicate-avoidance pattern for a repeating event | `docs_loyalty-emails-setup-guide-for-klaviyo.txt:825-827` (Redemption Created / trigger split) |
| `loyalty_next_points_expire_on` | same file, `:969` |
| `loyalty_next_points_expire_amount` | same file, `:970` |
| `swell_point_balance` | same file, `:972` |

Line 84 of the flow-mechanics article is, almost verbatim, the reasoning the better answer depends on. The model had access to it and did not use it.

So this is **not** a crawling or coverage problem. Do not respond to this by adding documents.

### 1.3 Root cause A — retrieval never surfaced the mechanics doc

The correct answer requires synthesis across **two documents in the same namespace**:

- `docs_loyalty-emails-setup-guide-for-klaviyo.txt` — 5,412 words ≈ 27 chunks — *what the Yotpo event is*
- `articles_115002774932.txt` — 3,375 words ≈ 16 chunks — *how Klaviyo triggers and filters behave*

Both compete for the same `n_results=10` slots (`app.py:288`). The user's query — "Loyalty Expiration Reminder", "points expire", "3 emails", "trigger delay" — is lexically and semantically saturated with the Yotpo doc's vocabulary. The flow-mechanics article never says "loyalty" or "expiration"; it says "trigger", "profile filter", "component".

Near-certain outcome: **all 10 ESP slots went to the Yotpo doc, and zero to the mechanics article.** The single most load-bearing sentence in the corpus was not in the context window.

This is a retrieval *composition* problem, not a `top_k` problem. Raising `n_results` to 15 would mostly buy more chunks of the same document.

### 1.4 Root cause B — the prompt forecloses validation

Two live instructions in `app_config.json` work against the desired behavior:

- `"Answer in a step by step manner, and walk through the process and in-platform navigation."` — commits the model to recipe mode before it has decided whether the user's implied approach is sound. Once in recipe mode, it fills in steps rather than questioning the premise.
- `"Aim to answer as short as possible."` — brevity pressure applied globally, including to the reasoning phase. The model skips the check that costs it tokens.

The prompt already contains a strong, well-written correctness clause — the `CRITICAL:` paragraph about never inventing property names. That clause works: Flow State's answer used a real property. The gap is that there is an equivalent guard for *nouns* but none for *mechanisms*.

### 1.5 Root cause C — secondary retrieval issues

- **Follow-up query dilution** (`app.py:276-279`): the full previous assistant message is concatenated into the retrieval query. On a long prior answer the user's actual new question becomes a small fraction of the embedded text and retrieval drifts toward the previous topic. The code comment justifies this on token cost; the real cost is embedding signal, not tokens.
- **Keyword boost missed this query** (`app.py:283`): `property_keywords` contains `property, properties, field, fields, variable, variables, data, attribute`. The test prompt contains none of them. No enhancement fired.
- **Relevance filter opacity** (`app.py:126-186`, Pinecone `min_score=0.35`): you request 10 and the model may receive far fewer, with no visibility at answer time. `app.py:325` already treats "≤3 sources" as a warning condition, which suggests this fires in practice.
- **Global namespace is thin but that's fine** — `docs/global/` holds 5 files, mostly Shopify and strategy. `n_results=2` is not the bottleneck here, because the Klaviyo mechanics doc lives in the `klaviyo` namespace, not global. Leave global alone for now.

---

## 2. Change 1 — System prompt (format-preserving)

### 2.1 Principle

Add a **mandatory internal check** that runs before drafting, and explicitly scope the existing brevity instruction so it governs the *output* rather than the *reasoning*. The model must still emit numbered steps in the same voice.

### 2.2 Proposed `system_prompt`

```
You are an email marketing specialist and a loyalty retention specialist at once.

Your goal is to recommend flows and campaigns to setup in the user's ESP using loyalty data.
You will provide helpful feedback on how to create the flow, how to setup the right triggers, filters, audiences and email content, following industry best practices. In the handbook you will find some templates, but you will also help create more unique and outside the box flows and campaigns.

Answer in a step by step manner, and walk through the process and in-platform navigation. Answer like you are talking to a person who knows how to work with the ESP, but isn't super in-depth. Make sure you double check your answers across your knowledgebase.

CRITICAL: When referencing customer properties, field names, or API endpoints, you MUST use the EXACT names from the documentation. Never invent, guess, or paraphrase property names. If you cannot find the exact property name in the provided documentation, explicitly tell the user you need to verify the correct property name rather than making one up.

CRITICAL: Before you write any steps, silently work through this checklist. Do not show this reasoning in your answer — it changes what your steps say, not how they are formatted.
1. Trigger mechanics. What is the trigger type (event/metric, date property, list, segment)? How many times does it fire per customer, and on what schedule? Does the documentation state a firing frequency?
2. Repetition. If the trigger fires more than once per customer, a linear sequence of time delays will duplicate sends. Say so and choose a structure that does not duplicate.
3. Delay-window state. For every condition that matters, does it get re-evaluated at send time or only at entry? Anything that can change while a customer sits in a delay must be placed where it is re-checked, not at the trigger.
4. Premise check. The user has often already assumed a structure. If their assumed structure breaks under 1-3, your steps must describe the structure that works, not the one they assumed.
5. Grounding. Every mechanic you rely on must be traceable to the provided documentation. If it is not in the documentation, do not assert it — ask the user or state the gap.

If the user's assumed approach does not work, your first numbered step is the corrected setup, and you state in one sentence why the obvious approach fails. Keep this to one sentence and stay in the same step-by-step format.

Always prioritize the quality of answer, never try to answer too quickly. Also, if you are missing any information, never assume or guess anything, always ask the user to provide the missing information or context.

Don't flatter and don't "glaze" the user. Be brief, direct and helpful. Tell them when they are wrong and provide helpful feedback.

Keep the final answer as short as the task allows and act more as a tool than a person. Brevity applies to what you output, never to the checking you do before you output it. Do not pad, but do not omit a step that is required for the setup to actually work.
```

### 2.3 What changed and why

| Change | Reason |
|---|---|
| Added second `CRITICAL:` block (5-point checklist) | Mirrors the structure of the property-name clause, which already demonstrably works in this prompt. Explicitly marked silent so it cannot leak into output. |
| "your first numbered step is the corrected setup" | Keeps the correction *inside* the numbered format rather than as a preamble. Format preserved. |
| `"Aim to answer as short as possible"` → scoped version | The single highest-leverage edit. The old wording suppresses reasoning; the new wording suppresses padding. |

### 2.4 Deployment note

`app_config.json` is the live prompt source and is also editable from the admin panel (`POST /api/admin/settings/system-prompt`, audit-logged via `config_manager.py`). Deploy through the admin panel rather than editing the file, so the change lands in `config_audit_log.json` and is revertable via `/api/admin/settings/restore`.

---

## 3. Change 2 — ESP mechanics invariants layer

### 3.1 Why a separate layer

§1.2 shows the mechanics facts exist but lose the retrieval lottery. Rather than hoping the right chunk wins, inject a short, curated, human-verified block on **every** query for that ESP. It is ~300 tokens and removes the dependency on retrieval for the facts that most often decide correctness.

This is not a duplicate knowledge base. It holds only **invariants** — behavioral rules that are true regardless of the question asked. Facts, copy, and property definitions stay in RAG.

### 3.2 Draft: Klaviyo invariants

Every line below is sourced from documents already in the corpus. **Have a Klaviyo-fluent human sign off before shipping** — a wrong invariant is worse than a missing one, because it will be asserted with confidence on every query.

```
# Klaviyo Flow Mechanics — Verified Invariants

- Klaviyo trigger types: list, segment, metric (event), price drop, date property.
  [articles_115002774932.txt:68-74]
- Trigger filters are evaluated only at flow entry. They are NOT re-checked at send time.
  [articles_115002774932.txt:84]
- Profile filters ARE re-checked before every component (email, SMS, split).
  Any condition that can change during a delay belongs in a profile filter, not a trigger filter.
  [articles_115002774932.txt:84, :86]
- A metric/event trigger creates one flow entry PER event occurrence. If a Yotpo event
  fires N times per customer, a linear chain of time delays will send duplicates.
  [derived from :78-84 + event firing frequencies below]
- Date-property triggers schedule relative to a date on the profile. The offset is configured
  in the trigger's target-date setup. [articles_115002774932.txt:73]

# Yotpo Events With Multiple Fires Per Customer

- Points Expiration Reminder (shown as "Loyalty Expiration Reminder" in Klaviyo):
  fires 3 times per expiration — 30, 14, and 7 days before. Only for the points with the
  nearest expiration date. [docs_loyalty-emails-setup-guide-for-klaviyo.txt:833-835]
- Yotpo Tier Expiration Reminder: fires at 30, 14, or 7 days before tier expiry, per settings,
  and only if requirements are unmet. [same file, :891]
- Swell Redemption Created: fires on every coupon generation, including VIP/birthday/referral.
  Documented mitigation is a trigger split filtered on redemption_option_name or source.
  [same file, :821-827]

# Yotpo Profile Properties (exact names — never paraphrase)

loyalty_next_points_expire_on ...... expiration date of the customer's points
loyalty_next_points_expire_amount .. number of points about to expire
swell_point_balance ................ current available points balance
swell_credit_balance ............... current available credits (points-as-credit only)
swell_points_earned ................ total historical points earned
swell_vip_tier_name ................ current tier name
swell_vt_ends_at_date .............. date tier eligibility ends
[docs_loyalty-emails-setup-guide-for-klaviyo.txt:969-982]
```

> **Known source inconsistency to resolve before shipping**: the setup guide's sample copy at `:782` and `:792` uses `swell_vip_tier_ends_at`, while its own property list at `:977` says `swell_vt_ends_at_date`. One of these is wrong in Yotpo's documentation. Confirm which is live before encoding it.

### 3.3 Implementation

Storage — pick one:

- **(a) File-based**, `backend/invariants/{esp}.md`, loaded at startup into a dict. Simplest; ships with the repo; requires a deploy to change.
- **(b) Database column**, `esps.invariants TEXT`, editable from the admin panel. Consistent with the Phase 4 ESP-in-Postgres direction and lets non-engineers correct an invariant without a deploy. **Recommended.**

Injection point — `app.py`, immediately before the `context` string is built at line 300:

```python
invariants = get_esp_invariants(esp_normalized)   # returns '' if none defined
context = ""
if invariants:
    context += (
        "# Verified Platform Mechanics (authoritative — overrides "
        "inference from documentation excerpts below):\n\n"
        f"{invariants}\n\n"
    )
context += "# Relevant Documentation:\n\n"
```

Placing it *before* the retrieved chunks matters: it should frame how the excerpts are read, and it must not be displaceable by the relevance filter.

Precedence must be explicit. If an invariant and a retrieved chunk conflict, the invariant wins — it is human-verified, the chunk may be a stale crawl.

### 3.4 Scaling

One invariants block per ESP, 10-20 lines each. New ESPs launch with an empty block and work exactly as today; the block gets filled in as the ESP matures. This is additive and carries no regression risk for ESPs you have not written one for.

---

## 4. Change 3 — Retrieval fixes

Ordered by expected impact per unit of effort.

### 4.1 Dual-query retrieval — split the slot budget by intent (highest impact)

The failure in §1.3 is that one query cannot rank both "what is this Yotpo event" and "how do Klaviyo triggers behave". Issue two queries and merge.

```python
# Query A — task/domain (as today)
task_results = vectorizer.search(enhanced_query, esp_filter=esp_normalized, n_results=7)

# Query B — platform mechanics, deliberately vocabulary-shifted toward the mechanics docs
mechanics_query = (
    f"{message} flow trigger type metric event date property "
    "trigger filter profile filter time delay evaluated at send time"
)
mech_results = vectorizer.search(mechanics_query, esp_filter=esp_normalized, n_results=5)

# Merge, de-duplicate by chunk id, preserve order A-then-B
esp_results = merge_dedupe(task_results, mech_results)
```

Cost: one extra Pinecone query (~50-100ms) and ~1,500 tokens. Both are cheap relative to the accuracy gain. This is the change most likely to have fixed the test case on its own.

### 4.2 Apply the relevance filter per-source, not globally

With dual-query, run `filter_by_relevance` on each result set separately. The mechanics chunks will legitimately score lower against the user's literal wording — a global threshold would strip exactly the chunks you added the second query to obtain. Consider a lower floor for the mechanics set (e.g. `min_score=0.25` on Pinecone).

### 4.3 Fix follow-up query dilution

Replace the full-previous-message concatenation at `app.py:276-279` with a bounded extraction. Options in order of preference:

1. Extract only entity-like tokens from the previous assistant message (property names matching `[a-z]+_[a-z_]+`, quoted UI labels, event names) and append those.
2. Failing that, truncate to the first ~200 characters.

Current behavior lets a 600-word prior answer dominate the embedding of a 15-word follow-up.

### 4.4 Retire or widen the keyword boost

`property_keywords` at `app.py:283` is narrow and did not fire on the test prompt. Once §4.1 ships, the mechanics query covers the same ground more robustly. Either delete the boost or widen it to include `trigger, flow, delay, filter, timing, sequence, series, automation`. Do not do both — overlapping boosts make behavior hard to attribute during evals.

### 4.5 Log what the model actually received

Add a per-request debug log: query text (both variants), chunk IDs returned, scores, source filenames, post-filter count. Without it you cannot tell a reasoning failure from a retrieval failure — which is exactly the ambiguity that made this investigation necessary. **Do this first**, before any other change in §4, so you have a before/after.

---

## 5. Change 4 — Evaluation

### 5.1 Build the regression set

Start with 12-15 prompts where a Klaviyo-fluent human has written the correct answer. Bias toward questions that hinge on a mechanism rather than a fact. Seed set:

1. The points-expiration 3-email case (§1.1) — **gold answer already established**
2. Same question for Tier Expiration Reminder (fires 30/14/7 too — should reach a similar structure)
3. Redemption Created used for a VIP-only coupon email (must produce a trigger split, per `:825-827`)
4. "Send a reminder only if they haven't redeemed yet" (must land in profile filter, not trigger filter)
5. A birthday flow (date-property trigger — should *not* get the multi-fire treatment; guards against overcorrection)
6. A pure property-lookup question (guards the existing `CRITICAL:` property clause against regression)
7. A question with genuinely insufficient documentation (must ask for clarification rather than invent)

Items 5-7 are the overcorrection guards. A prompt that makes the model suspicious of everything will start hedging on simple questions and inventing failure modes that do not exist. Watch for it.

### 5.2 Scoring

Per response, score independently:

- **Mechanism correct** (0/1) — right trigger type, no duplicate-send structure, filters in the right place
- **Properties exact** (0/1) — no invented or paraphrased property names
- **Grounded** (0/1) — no asserted mechanic absent from docs + invariants
- **Format unchanged** (0/1) — see §5.3

### 5.3 Format-invariance check — the guard on your constraint

This is what enforces the brief. For each eval prompt, capture the baseline (`b1a95a5`) answer and the new answer, then assert:

- Both are numbered step lists
- Step count within ±2
- Word count within +25% (the corrected answer will be slightly longer — it describes a different structure — but must not become an essay)
- No new section headers, no preamble paragraph before step 1, no meta-commentary about its own reasoning process

**Any change that improves accuracy but fails the format check is rejected.** That is the whole point of the constraint.

### 5.4 Attribution

Run the four changes as separate arms so you know what earned the gain:

| Arm | Config |
|---|---|
| A | baseline `b1a95a5` |
| B | + system prompt only (§2) |
| C | + invariants layer (§3) |
| D | + retrieval fixes (§4) |

Expectation: C and D carry most of the gain on mechanism-correctness; B mostly determines whether the model *acts* on what C and D put in front of it. B alone will underperform — it cannot reason about a rule it never sees.

---

## 6. Sequencing

| # | Change | Effort | Risk | Blocking |
|---|---|---|---|---|
| 1 | Retrieval debug logging (§4.5) | 30 min | none | — |
| 2 | Build eval set + format harness (§5) | half day | none | needs #1 for attribution |
| 3 | System prompt revision (§2) | 15 min | low — revert via admin restore | — |
| 4 | Klaviyo invariants block (§3) | half day, mostly human verification | **medium — a wrong invariant is asserted on every query** | needs sign-off |
| 5 | Dual-query retrieval (§4.1, §4.2) | half day | low | — |
| 6 | Query dilution fix (§4.3) | 1 hr | low | — |
| 7 | Re-run evals, compare arms | — | — | all of the above |

Ship 1-3 first: cheap, reversible, and #3 alone may show measurable movement.

---

## 7. Housekeeping

`CLAUDE.md` has drifted from the code and misled the initial analysis in this session. Corrections needed:

| `CLAUDE.md` says | Actual |
|---|---|
| ESP search 3 results, global 2 | ESP **10** (`app.py:288`), global 2 (`app.py:294`) |
| Chunks 500 words / 50 overlap | **300 / 100** (`adapters/vector/base.py:87`); legacy `vectorize.py:31` still 500/50 |
| Model: Gemini Flash default | **`openai` / `gpt-4o`** (`app_config.json`) |
| System prompt (verbatim block) | Missing the live `CRITICAL:` property-name paragraph and "in-platform navigation" |
| ESPs: Klaviyo, DotDigital, Attentive, Ometria, Other/Webhook | Also `listrak`, `omnisend`, `postscript` (+ `demoesp`, `testesp` test fixtures) |
| No query enhancement mentioned | Exists at `app.py:270-285` |

Worth a pass, since a stale architecture doc will keep costing debugging time.

---

## 8. What this plan deliberately does not do

- **Add documents.** §1.2 establishes the knowledge is present. Crawling more would have masked the real defect.
- **Raise `n_results`.** The problem is which document the slots go to, not how many slots there are.
- **Change model or temperature.** Untested variables; introduce them only after §5 can measure them.
- **Add visible reasoning to the output.** Explicitly out of scope per the format constraint.
