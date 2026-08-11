# Retrieval Fixes — Implementation Record

Implements the five corrections identified when `OPTIMIZATION_PLAN.md` was
reviewed against the live code and the live Pinecone index.

**Baseline**: `b1a95a5`
**Scope**: retrieval composition, observability, and eval reproducibility.
The system prompt and the invariants layer (plan §2, §3) are **not** touched here.

Every claim below was measured against the live index, not predicted.

---

## Why the plan needed correcting

The plan's diagnosis was right — the failure is retrieval *composition*, not
coverage. The mechanics article `articles_115002774932.txt` contains zero
occurrences of "loyalty" or "expiration", so a loyalty-phrased question never
retrieves it. Reproduced on the live index:

```
ESP search (n=10) -> mechanics article: 0 of 10 slots
                     first appearance:  rank 24 of 30
```

But the plan's headline fix did not work. Its mechanics query concatenates the
user's message, and that pulls the embedding back toward loyalty vocabulary —
the exact failure the query exists to correct:

| Mechanics query variant | Rank of chunk 9 (the load-bearing chunk) |
|---|---|
| Plan §4.1, with user message prepended | **11** — outside its own n=5 budget |
| Vocabulary only, no user text | 3 |
| Doc-vocabulary phrasing, no user text | **1** (score 0.697) |

Chunk 9 is the only one of 24 mechanics chunks containing *"trigger filters are
not checked again at send time"*. The plan's version retrieves chunk 15
("Understanding time delays") instead — right document, wrong chunk.

---

## 1. `filter_by_relevance` now preserves `ids` and `distances`

**File**: [backend/app.py](backend/app.py)

The function returned only `documents` and `metadatas`, discarding `ids` and
`distances`. Two consequences:

- De-duplicating merged result sets by chunk id was impossible — which blocks
  the dual-query merge in §2 below.
- A second filter call hit the `'distances' not in results` guard and returned
  early, so it was a silent no-op rather than a filter.

Both keys are now carried through, `ids` is padded when an adapter omits it,
and the filter logs on every call (including when nothing is dropped, which is
the case that matters — see §3).

Verified: ids/distances survive, output stays rectangular, a second pass
genuinely re-filters, and a missing-`ids` input no longer truncates the set.

## 2. Dual-query retrieval, with no user text in the mechanics query

**File**: [backend/app.py](backend/app.py)

Added `MECHANICS_QUERY`, `MECHANICS_QUERY_BY_ESP` (per-ESP override, empty by
default) and `merge_dedupe()`. The chat endpoint now issues:

- **Query A** — the user's query, `n_results=10`. Unchanged from baseline.
- **Query B** — a static mechanics-vocabulary query, `n_results=5`.
  Contains **no user text**, for the reason measured above.

Results are merged with Query A first, de-duplicated by chunk id.

Measured through the real `/api/chat` path (AI call, analytics and session
stubbed; Pinecone live):

```
Query B returns chunk 9 at rank 1, score 0.697
  -> the highest-scoring chunk in the entire retrieval
context contains "trigger filters are not checked again at send time": YES
sources: 15 ESP + 2 global, no duplicates
```

### Cost, and the cache it forced

Query B's input does not depend on the user's message, so for a given ESP it
returns byte-identical results every time. Measured un-cached it cost **~200ms
on every chat request** (165ms Pinecone roundtrip + 34ms embedding) — including
~217ms on attentive, omnisend and postscript, where it returns zero usable
chunks. The plan estimated 50–100ms; the real figure is roughly double.

So results are memoized per ESP (`get_mechanics_results`), guarded by a lock
because gunicorn runs `--workers 1 --threads 4 --worker-class gthread`.
Measured after warm-up: **cache miss 164ms, cache hit ~0ms.**

- TTL: `MECHANICS_CACHE_TTL_SECONDS`, default 900 (15 min).
- Invalidated explicitly on all four `refresh_esp` / `vectorize_all_docs`
  sites in `app.py`. Per-URL admin edits are TTL-bounded.
- Negative results are cached too — the ESPs returning nothing were the ones
  paying full price for it.

**This is not free.** Context grows +32% for Klaviyo (7,950 → 10,462 chars,
roughly +600 input tokens per request); 0% for ESPs where Query B returns
nothing. That is a real per-request cost increase on Klaviyo traffic, accepted
in exchange for the correctness fix.

### How far this generalizes — measured, not assumed

`MECHANICS_QUERY` is phrased in Klaviyo's documentation vocabulary. Running it
against every ESP namespace:

| ESP | Chunks kept | Top score | Verdict |
|---|---|---|---|
| klaviyo | 5 | 0.697 | Works — 3/5 chunks mechanism-dense |
| ometria | 1 | 0.422 | Weakly works — retrieves "How entry triggers work" |
| listrak | 2 | 0.447 | Marginal — "conductor steps", low mechanism density |
| dotdigital | 1 | 0.370 | Marginal — barely over threshold |
| attentive | 0 | — | **No contribution** |
| omnisend | 0 | — | **No contribution** |
| postscript | 0 | — | **No contribution** |

So the *structure* (two queries for two different information needs) is
general, but this *implementation* is calibrated to Klaviyo. It degrades safely
— the 0.35 threshold suppresses it to a no-op where there is no mechanics
documentation, so it injects no noise — but it only meaningfully helps Klaviyo.

This also surfaces something the plan asserts is not the problem. Plan §8 says
"do not add documents" because the knowledge is already present. That is true
**for Klaviyo**. For attentive, omnisend and postscript, no chunk in the
namespace scores above 0.35 on a flow-mechanics query at all — those ESPs have
integration docs but apparently no flow-mechanics documentation. For them it
*is* a coverage problem, and neither this fix nor plan §2/§3 addresses it.

A genuinely ESP-agnostic version would derive the second query from the
question instead of hardcoding it — e.g. an LLM rewrite step ("what platform
behaviors must be true for this answer to work?") feeding Query B. That removes
the per-ESP tuning entirely. Not built here; noted as the real generalization.

## 3. Retrieval logging added; the relevance threshold left alone

**File**: [backend/app.py](backend/app.py), [.env.example](.env.example)

`RETRIEVAL_DEBUG=1` logs, per request: both query texts, and every chunk's id,
score, `chunk_index` and source filename, before and after filtering.

The plan proposed lowering `min_score` to 0.25 for the mechanics set. **Not
done** — but the reasoning needs stating carefully, because an earlier draft of
this document overstated it.

On the Klaviyo test case the filter does not fire at all:

```
[RELEVANCE FILTER] ESP results:           10 kept, none below min_score=0.35
[RELEVANCE FILTER] ESP-mechanics results:  5 kept, none below min_score=0.35
[RELEVANCE FILTER] Global results:         2 kept, none below min_score=0.35
```

Scores there run 0.470–0.702, comfortably clear of 0.35, so loosening the floor
would admit noise and fix nothing.

**But it fires hard elsewhere.** "what properties are available" against
dotdigital returns 10 chunks scoring 0.156–0.277 — *all* below threshold, so
Query A contributes **zero** chunks and the endpoint's "≤3 sources" warning
fires. Plan §1.5's concern about relevance-filter opacity was therefore
correct; it just does not manifest on the query the plan was diagnosing.

The threshold is still not the thing to change. Scores that low indicate the
content genuinely is not there, not a miscalibrated floor — dropping to 0.25
would admit chunks that are 0.27-relevant and invite exactly the hallucination
the filter exists to prevent. The real issue for dotdigital is coverage.

This is now visible rather than silent, which was the point of §3. Revisit the
threshold only if the logs show it dropping chunks that scored *well*.

## 4. Index/filesystem drift audit

**File**: [backend/audit_index_drift.py](backend/audit_index_drift.py) (new)

> **Correction.** An earlier draft of this section called the divergence "bad"
> and implied it needed fixing. That was wrong, and the framing has been
> corrected below. The divergence is the **expected** result of crawling in
> production: `docs/` is a container filesystem, crawled files never return to
> the repo, and Pinecone is the source of truth. Verified: the Klaviyo orphan
> was never in git history, and local `crawl_metadata.json` matches local files
> exactly — local state is internally consistent, just behind production.
> Runtime is unaffected. The audit's value is as a **precondition check before
> authoring anything from local files**, not as a health alarm.

The plan's corpus audit was run against `docs/`, but retrieval serves from
Pinecone, and the two hold different sets of files. Full audit:

| ESP | Difference | Assessment |
|---|---|---|
| **emarsys** | 5 files / 18 chunks indexed, 0 on disk | Normal — ESP added via admin panel in production |
| **klaviyo** | `docs_klaviyo-integration-guide.txt`, 40 of 118 chunks (**34% of the corpus**) indexed, not on disk | Normal, but see consequence below |
| **ometria** | 3 files indexed under names carrying the article ID, 3 on-disk equivalents without it | Cosmetic — **verified same source URLs, one copy indexed, no duplication** |
| **omnisend** | 1 file / 16 chunks indexed, not on disk | Normal — production crawl |
| attentive, dotdigital, global, listrak, postscript | none | — |

None of this is runtime breakage. The single consequence that matters is
narrow and specific: **plan §3's invariants cannot be authored by reading local
files.** For Klaviyo you would be reading 4 of 5 documents and citing line
numbers into a third of a corpus you cannot see. That is the reason this tool
exists — not general corpus hygiene.

The Ometria naming difference is worth knowing only because it shows the
crawler's filename derivation changed at some point. It creates no duplication
today, and `refresh_esp()` deletes the whole ESP before re-adding, so a full
refresh would resolve it rather than double it.

```bash
python3 backend/audit_index_drift.py
```

Exits 1 on drift, so it can gate a deploy. `--export-orphans DIR` recovers the
text of index-only files for review (read-only; chunks are emitted separately
with their `chunk_index` because they overlap by ~100 words — stitching them
would invent a document and any line numbers taken from it would be fiction).

I inspected the recovered Klaviyo orphan: it is a general integration guide,
contains no property names, and **does not contradict** the proposed
invariants. So §3 is not blocked — but it should cite chunk indexes from the
recovered text, not line numbers from disk.

**Not done, needs a decision**: actually reconciling the drift means either
re-crawling (hits external sites) or deleting vectors (destroys data). Both are
your call — see "Open decisions" below.

## 5. Reproducible eval sampling

**File**: [backend/ai_client.py](backend/ai_client.py), [.env.example](.env.example)

The live path is OpenAI `gpt-4o` at a hardcoded `temperature=0.7`. The plan's
§5.3 format check asserts step count within ±2 and word count within +25% —
at 0.7, reruns of the *same* config would fail that, so the harness would have
measured noise.

Added `get_temperature()`, reading `AI_TEMPERATURE`:

- **Unset** → behavior is exactly as before (OpenAI 0.7; Claude and Gemini
  keep their own defaults). Production is unchanged.
- **Set** → applied to whichever provider is active, all three now supported.
- Unparseable values are ignored with a warning.

Verified across providers: unset gives `0.7` / omitted; `AI_TEMPERATURE=0`
gives `0.0` on both OpenAI and Claude; `junk` falls back to `0.7`.

Run evals with `AI_TEMPERATURE=0`.

---

## Verification

| Check | Result |
|---|---|
| `filter_by_relevance` preserves ids/distances, idempotent, no truncation | PASS |
| `/api/chat` context contains the load-bearing sentence | PASS |
| Mechanics article present in sources, no duplicate chunks | PASS |
| Retrieval logging emits queries, ids, scores, filenames | PASS |
| Drift audit runs across all 9 ESPs, exits 1 on drift | PASS |
| Temperature honoured per provider; defaults preserved | PASS |
| `py_compile` on all changed files | PASS |

Endpoint verification stubs the AI call, analytics writes and session store, so
it spends no tokens and writes no rows to the production analytics database.
Pinecone is read live.

**Not verified**: no end-to-end answer-quality test was run — that needs the
eval set from plan §5, which does not exist yet. These changes put the right
chunk in front of the model; whether the model then uses it is what §2's prompt
work and the eval set are for.

---

## Open decisions

1. **Drift reconciliation** — re-crawl the missing files, or delete the stale
   vectors? Re-crawling hits external sites; deleting destroys the only copy of
   34% of the Klaviyo corpus. The `emarsys` ESP in particular appears nowhere
   in the docs; worth deciding whether it should exist at all.
2. **`ometria` duplicates** — the old-name vectors look strictly superseded by
   the on-disk files, but those files are not indexed. Re-vectorizing Ometria
   would resolve both halves at once.
3. **Dead code** — [backend/reranker.py](backend/reranker.py) and
   [backend/property_validator.py](backend/property_validator.py) are imported
   nowhere. I tested the cross-encoder over an n=30 pool: it does **not**
   surface chunk 9, so it is not a substitute for §2. Either wire them up
   deliberately or delete them.
4. **Plan §2 and §3** remain unimplemented and are still the load-bearing
   changes for answer quality. Note that §3's invariants hand-write the same
   rule §2-here now retrieves — with chunk 9 reaching the model, it is worth
   re-measuring whether the invariants block is still needed before investing
   in the human sign-off it requires.
