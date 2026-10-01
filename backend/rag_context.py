"""
Retrieval and context assembly for chat.

Lives outside app.py so the chat route and the retrieval eval
(eval/product_eval.py) run exactly the same code: importing app.py registers
routes, initialises the database and can start the crawl worker, none of which
an eval should do.

With every keyword argument of build_rag_context() left at its default, the
context is byte-identical to what chat() built inline before this module
existed (eval/check_context_unchanged.py proves it). Chat passes `product` and,
for Reviews, `reviews_coverage`; the other keyword arguments are the
product-line experiment's arms.

Environment is read at call time, not import time: app.py imports this module
before it loads .env, and a module-level read would silently see no
VECTOR_DB_PROVIDER locally and apply the ChromaDB threshold to Pinecone scores.
"""
import os
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from mechanics_cache import cache_mechanics_results, get_cached_mechanics


def _vector_provider():
    # ChromaDB returns L2 distances (lower = more similar); Pinecone returns
    # cosine similarity (higher = more similar).
    return os.environ.get('VECTOR_DB_PROVIDER', 'chromadb').lower()


def retrieval_debug():
    # Per-request retrieval tracing. Off by default; set RETRIEVAL_DEBUG=1.
    # Without this you cannot tell a reasoning failure from a retrieval
    # failure -- the answer looks equally wrong either way.
    return os.environ.get('RETRIEVAL_DEBUG', '').lower() in ('1', 'true', 'yes')


def filter_by_relevance(results, min_score=None, result_type=''):
    """
    Filter vector search results by minimum relevance score.
    Removes low-quality chunks that could cause hallucinations.

    Args:
        results: Vector search results dict with 'documents', 'metadatas', 'distances'
        min_score: Minimum similarity score (0-1). Defaults per provider.
        result_type: Label for logging (e.g., 'ESP', 'Global')

    Returns:
        Filtered results dict, preserving the 'ids' and 'distances' keys of the
        input. Both are required downstream: 'ids' to de-duplicate when merging
        several result sets, 'distances' so a filtered set can still be scored
        or re-filtered. Dropping them also made a second filter call a silent
        no-op via the "no distance info" guard below.
    """
    is_similarity_metric = _vector_provider() == 'pinecone'
    if min_score is None:
        # Cosine similarity (Pinecone) and 1/(1+L2) (ChromaDB) live on
        # different scales, so each needs its own default threshold.
        min_score = 0.35 if is_similarity_metric else 0.60
    # If no distance info, return as-is
    if 'distances' not in results or not results['distances'] or not results['distances'][0]:
        return results

    # Check if we have matching documents and metadatas
    if not results['documents'] or not results['documents'][0]:
        return results
    if not results['metadatas'] or not results['metadatas'][0]:
        return results

    filtered_docs = []
    filtered_metadatas = []
    filtered_ids = []
    filtered_distances = []
    original_count = len(results['documents'][0])

    # 'ids' is optional defensively, but both adapters supply it. Pad so the
    # zip below never truncates the result set when it is missing.
    source_ids = (results.get('ids') or [[]])[0]
    if len(source_ids) < original_count:
        source_ids = list(source_ids) + [None] * (original_count - len(source_ids))

    for doc, metadata, distance, chunk_id in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0],
        source_ids
    ):
        if is_similarity_metric:
            # Pinecone already returns cosine similarity (higher = better)
            similarity = distance
        else:
            # ChromaDB uses L2 distance (lower = more similar)
            # Convert to similarity score: 1 / (1 + distance)
            similarity = 1 / (1 + distance)

        if similarity >= min_score:
            filtered_docs.append(doc)
            filtered_metadatas.append(metadata)
            filtered_ids.append(chunk_id)
            filtered_distances.append(distance)

    filtered_count = len(filtered_docs)

    # Log filtering stats
    if filtered_count < original_count:
        print(f"[RELEVANCE FILTER] {result_type} results: {original_count} → {filtered_count} "
              f"(removed {original_count - filtered_count} low-relevance chunks, "
              f"min_score={min_score})")
    else:
        print(f"[RELEVANCE FILTER] {result_type} results: {original_count} kept, "
              f"none below min_score={min_score}")

    # Return filtered results
    return {
        'ids': [filtered_ids],
        'documents': [filtered_docs],
        'metadatas': [filtered_metadatas],
        'distances': [filtered_distances]
    }


# Platform-mechanics retrieval query, issued alongside the user's own query.
#
# Why a second query at all: a question phrased in loyalty vocabulary ("points
# expire", "Loyalty Expiration Reminder") is lexically saturated with the Yotpo
# setup guide and never surfaces the Klaviyo flow-mechanics article, which does
# not contain the words "loyalty" or "expiration" anywhere. Measured against the
# live index, the mechanics article took 0 of the 10 ESP slots and first
# appeared at rank 24 of 30.
#
# Why it contains NO user text: measured on the same index, the chunk carrying
# "trigger filters are not checked again at send time" ranks 1st for this query
# alone, but falls to 11th when the user's message is concatenated in front of
# it — the question's own vocabulary pulls the embedding back toward the
# loyalty docs, which is the exact failure this query exists to correct.
MECHANICS_QUERY = (
    "How triggers and profile filters qualify subscribers: trigger filters are "
    "not checked again at send time, profile filters are re-checked before each "
    "component. Flow trigger types: list, segment, metric event, price drop, "
    "date property. Understanding time delays between flow components."
)

# Per-ESP override, for platforms whose docs use different vocabulary.
# ESPs absent from this dict use MECHANICS_QUERY.
MECHANICS_QUERY_BY_ESP = {}

# Boost query for property-related questions to retrieve definitions.
PROPERTY_KEYWORDS = ['property', 'properties', 'field', 'fields', 'variable',
                     'variables', 'data', 'attribute']


def log_retrieval(label, query, results):
    """Log what a retrieval actually returned: query, chunk ids, scores, sources."""
    if not retrieval_debug():
        return

    docs = (results.get('documents') or [[]])[0]
    metas = (results.get('metadatas') or [[]])[0]
    ids = (results.get('ids') or [[]])[0]
    dists = (results.get('distances') or [[]])[0]

    query_preview = query if len(query) <= 160 else query[:157] + '...'
    print(f"[RETRIEVAL:{label}] n={len(docs)} query={query_preview!r}")
    for i in range(len(docs)):
        chunk_id = ids[i] if i < len(ids) else None
        score = dists[i] if i < len(dists) else None
        meta = metas[i] if i < len(metas) else {}
        score_str = f"{score:.3f}" if isinstance(score, (int, float)) else "n/a"
        print(f"    {i+1:2d}. score={score_str} "
              f"chunk={meta.get('chunk_index')} "
              f"file={meta.get('filename')} id={chunk_id}")


def merge_dedupe(*result_sets):
    """
    Merge vector search result sets, preserving order and dropping duplicates.

    De-duplicates on chunk id, falling back to the document text when an
    adapter omits ids. Earlier result sets win, so the caller controls
    precedence by argument order.
    """
    merged_ids, merged_docs, merged_metas, merged_dists = [], [], [], []
    seen = set()

    for results in result_sets:
        if not results or not results.get('documents') or not results['documents'][0]:
            continue
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        ids = (results.get('ids') or [[]])[0]
        dists = (results.get('distances') or [[]])[0]

        for i, doc in enumerate(docs):
            chunk_id = ids[i] if i < len(ids) and ids[i] is not None else None
            key = chunk_id if chunk_id is not None else doc
            if key in seen:
                continue
            seen.add(key)
            merged_ids.append(chunk_id)
            merged_docs.append(doc)
            merged_metas.append(metas[i] if i < len(metas) else {})
            merged_dists.append(dists[i] if i < len(dists) else None)

    return {
        'ids': [merged_ids],
        'documents': [merged_docs],
        'metadatas': [merged_metas],
        'distances': [merged_dists]
    }


def get_mechanics_results(vectorizer, esp_normalized, n_results=5):
    """Query B, memoized per ESP. Thread-safe: gunicorn runs gthread workers.

    Query B's input does not depend on the user's message, so for a given ESP
    it returns byte-identical results every time. Measured un-cached, it cost
    ~200ms per chat request -- including ~217ms on ESPs where it returns zero
    usable chunks. The store, its lock and its TTL live in mechanics_cache so
    the admin routes and the crawl worker can invalidate it.
    """
    query = MECHANICS_QUERY_BY_ESP.get(esp_normalized, MECHANICS_QUERY)
    # Key on the query text as well as the ESP, so editing MECHANICS_QUERY or
    # adding an override invalidates the entry instead of serving stale chunks.
    cache_key = (esp_normalized, query, n_results)
    now = time.time()

    cached = get_cached_mechanics(cache_key)
    if cached is not None:
        return query, cached, True

    # Executed outside the cache lock: a slow Pinecone call must not block
    # other threads. A concurrent miss may query twice, which is harmless.
    results = vectorizer.search(query, esp_filter=esp_normalized, n_results=n_results)
    log_retrieval('B/mechanics/pre-filter', query, results)
    results = filter_by_relevance(results, result_type='ESP-mechanics')

    cache_mechanics_results(cache_key, results, now)

    return query, results, False


# ---------------------------------------------------------------------------
# Product line (PRODUCT_LINE_SPLIT_SCOPE.md). The coverage note is used by chat;
# labels in the context and the filter are experiment arms (step 7).
# ---------------------------------------------------------------------------

PRODUCT_NAMES = {
    'loyalty': 'Yotpo Loyalty & Referrals',
    'reviews': 'Yotpo Reviews',
    'shared': 'shared (ESP or Yotpo platform documentation that applies to both products)',
}

# Chunks fetched before dropping other products, to emulate a metadata
# pre-filter. Pinecone caps top_k at 1000 when metadata is returned; every
# ESP is well below that today (the largest, Klaviyo, holds 118 vectors).
FILTER_FETCH = 1000

PRODUCT_INSTRUCTION = (
    "## Answering across Yotpo products\n"
    "The sources below may cover Yotpo Loyalty & Referrals, Yotpo Reviews, or both. "
    "Say which Yotpo product your steps are for, and use only sources for that product. "
    "If the question does not make clear which product it is about and the answer "
    "differs between them, ask which one the user means.\n\n"
)


@dataclass
class RagContext:
    context: str
    metadatas: List[dict] = field(default_factory=list)
    esp_normalized: str = ''
    enhanced_query: str = ''


def _search(vectorizer, query, esp, n_results, keep):
    """vectorizer.search, optionally restricted to chunks `keep` accepts.

    With `keep`, fetches FILTER_FETCH results and keeps the first n_results
    that pass, which is what a Pinecone metadata pre-filter would return.
    """
    if keep is None:
        return vectorizer.search(query, esp_filter=esp, n_results=n_results)
    raw = vectorizer.search(query, esp_filter=esp, n_results=FILTER_FETCH)
    metas = (raw.get('metadatas') or [[]])[0]
    idx = [i for i, m in enumerate(metas) if keep(m)][:n_results]
    return {key: [[(raw.get(key) or [[]])[0][i] for i in idx]]
            for key in ('ids', 'documents', 'metadatas', 'distances')
            if raw.get(key) is not None}


def build_rag_context(
    vectorizer,
    message: str,
    esp: str,
    conversation_history: list,
    *,
    product: Optional[str] = None,
    reviews_coverage: Optional[bool] = None,
    esp_display: Optional[str] = None,
    product_of: Optional[Callable[[dict], Optional[str]]] = None,
    product_instruction: bool = False,
    filter_to_product: bool = False,
) -> RagContext:
    """
    Retrieve for one chat turn and assemble the context the model reads.

    Product options (all off by default, which is today's context):
        product: the product line the user picked, 'loyalty' | 'reviews', or
            None when unknown. Only changes the context through the options
            below; the system prompt is filled from it separately.
        reviews_coverage: False adds a note that this ESP has no Yotpo Reviews
            documentation (the coverage guard) -- definite when product is
            'reviews', conditional when the product is unknown. None adds nothing.
        esp_display: the ESP's name as users see it, for that note. Defaults
            to the normalized key (e.g. other_webhook).
        product_of: chunk metadata -> 'loyalty' | 'reviews' | 'shared' | None.
            When given, every source header states its product line (arm C2).
        product_instruction: tell the model to name the product and to ask
            when the question does not say (arm C1).
        filter_to_product: keep only chunks of `product` or 'shared' (arm B).
            Requires product_of and product. Bypasses the mechanics cache,
            which holds unfiltered results.
    """
    if filter_to_product and (product_of is None or product is None):
        raise ValueError("filter_to_product needs product_of and product")

    esp_normalized = esp.lower().replace('/', '_') if esp else 'klaviyo'

    # Enhance query with conversation context for better follow-up question handling
    enhanced_query = message
    if len(conversation_history) > 0:
        # Include FULL previous assistant message (no char limit)
        # Token cost is negligible (~400-650 tokens) vs context window (128k)
        # This preserves ALL property names, technical terms, and context for follow-ups
        recent_messages = [msg['content'] for msg in conversation_history[-2:] if msg['role'] == 'assistant']
        if recent_messages:
            recent_context = " ".join(recent_messages)
            enhanced_query = f"{message} {recent_context}"

    # Boost query for property-related questions to retrieve definitions
    # This helps when users ask about multiple properties in one query
    if any(keyword in message.lower() for keyword in PROPERTY_KEYWORDS):
        enhanced_query = f"{enhanced_query} property definition list documentation"

    keep = None
    if filter_to_product:
        allowed = {product, 'shared'}
        keep = lambda meta: product_of(meta) in allowed  # noqa: E731

    # Query A — task/domain. Answers "what is this thing the user is asking about".
    esp_results = _search(vectorizer, enhanced_query, esp_normalized, 10, keep)
    log_retrieval('A/task/pre-filter', enhanced_query, esp_results)

    # Filter ESP results by relevance score to reduce hallucinations
    esp_results = filter_by_relevance(esp_results, result_type='ESP')

    # Query B — platform mechanics. Answers "how does this platform actually
    # behave", which Query A reliably misses when the question is phrased in
    # domain vocabulary. See MECHANICS_QUERY for the measurements behind this.
    #
    # The relevance threshold inside is the same as Query A's, deliberately. A
    # lower floor was considered and rejected: measured scores on this corpus
    # run 0.47-0.70, well clear of 0.35, so loosening it would only admit
    # noise. For an ESP with no mechanics documentation, the standard threshold
    # is what stops this query injecting loosely-related chunks.
    if keep is None:
        mechanics_query, mech_results, cache_hit = get_mechanics_results(vectorizer, esp_normalized)
        if retrieval_debug() and cache_hit:
            print(f"[MECHANICS CACHE] hit for esp={esp_normalized}")
    else:
        mechanics_query = MECHANICS_QUERY_BY_ESP.get(esp_normalized, MECHANICS_QUERY)
        mech_results = filter_by_relevance(
            _search(vectorizer, mechanics_query, esp_normalized, 5, keep),
            result_type='ESP-mechanics')

    # Mechanics chunks are presented FIRST, in their own section, and removed
    # from the task set so they are not repeated.
    #
    # Ordering is not cosmetic. When mechanics trailed the task results, the
    # sentence stating that trigger filters are not re-checked at send time
    # arrived as source 11 of 17, after ten sources describing what the Yotpo
    # event is -- and the model read past it, producing the same duplicate-
    # sending flow as before the retrieval fix. A rule that should govern how
    # every other excerpt is read has to arrive before them, not after.
    esp_results = merge_dedupe(esp_results)
    mech_ids = set((mech_results.get('ids') or [[]])[0])
    if mech_ids:
        keep_idx = [i for i, cid in enumerate((esp_results.get('ids') or [[]])[0])
                    if cid not in mech_ids]
        esp_results = {
            key: [[(esp_results[key][0])[i] for i in keep_idx]]
            for key in ('ids', 'documents', 'metadatas', 'distances')
        }
    log_retrieval('mechanics/final', mechanics_query, mech_results)
    log_retrieval('task/final', enhanced_query, esp_results)

    # Search global knowledge (2 results) - also use enhanced query
    global_results = _search(vectorizer, enhanced_query, 'global', 2, keep)
    log_retrieval('global/pre-filter', enhanced_query, global_results)

    # Filter global results by relevance score
    global_results = filter_by_relevance(global_results, result_type='Global')

    def product_line(metadata):
        if product_of is None:
            return ""
        label = product_of(metadata)
        return f"Yotpo product line: {PRODUCT_NAMES.get(label, 'not labelled')}\n"

    # Product preamble. Empty unless an option asks for it, so the default
    # context is unchanged.
    context = ""
    if reviews_coverage is False:
        esp_name = esp_display or esp_normalized
        if product == 'reviews':
            context += ("## Coverage note\n"
                        "The user is asking about Yotpo Reviews, and Flow State has no Yotpo "
                        f"Reviews documentation for {esp_name}. Say so plainly and do not "
                        "answer from Yotpo Loyalty & Referrals sources.\n\n")
        else:
            context += ("## Coverage note\n"
                        f"Flow State has no Yotpo Reviews documentation for {esp_name}. "
                        "If the user is asking about Yotpo Reviews, say so plainly and do not "
                        "answer from Loyalty sources.\n\n")
    if product_instruction:
        context += PRODUCT_INSTRUCTION

    # Build context from search results
    context += "# Relevant Documentation:\n\n"

    source_index = 1

    # Platform mechanics first. These describe how the platform behaves --
    # trigger types, how often a trigger fires, which filters are re-evaluated
    # at send time. They constrain whether a setup actually works, so they are
    # placed ahead of the task documentation rather than after it.
    if mech_results['documents'] and mech_results['documents'][0]:
        context += "## Platform Mechanics (read these first — they determine "
        context += "whether a setup works, not just what it is called):\n"
        for doc, metadata in zip(mech_results['documents'][0], mech_results['metadatas'][0]):
            context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
            context += f"ESP: {metadata.get('esp', 'Unknown')}\n"
            context += f"URL: {metadata.get('source_url', 'N/A')}\n"
            context += product_line(metadata)
            context += f"{doc}\n\n"
            source_index += 1

    # Add ESP-specific results
    if esp_results['documents'] and esp_results['documents'][0]:
        context += "## ESP-Specific Knowledge:\n"
        for doc, metadata in zip(esp_results['documents'][0], esp_results['metadatas'][0]):
            context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
            context += f"ESP: {metadata.get('esp', 'Unknown')}\n"
            context += f"URL: {metadata.get('source_url', 'N/A')}\n"
            context += product_line(metadata)
            context += f"{doc}\n\n"
            source_index += 1

    # Add global knowledge results
    if global_results['documents'] and global_results['documents'][0]:
        context += "## Global Knowledge:\n"
        for doc, metadata in zip(global_results['documents'][0], global_results['metadatas'][0]):
            context += f"### Source {source_index}: {metadata.get('filename', 'Unknown')}\n"
            context += f"Type: Global Knowledge Base\n"
            context += f"URL: {metadata.get('source_url', 'N/A')}\n"
            context += product_line(metadata)
            context += f"{doc}\n\n"
            source_index += 1

    if source_index == 1:
        context += "No specific documentation found. Provide general guidance based on ESP best practices.\n\n"
    elif source_index <= 4:  # Very few sources (3 or fewer)
        context += "\n⚠️ WARNING: Limited documentation found for this specific query. Provide guidance but acknowledge any documentation gaps.\n\n"

    # Combine results for source display, in the same order as the context.
    all_metadatas = []
    if mech_results['metadatas'] and mech_results['metadatas'][0]:
        all_metadatas.extend(mech_results['metadatas'][0])
    if esp_results['metadatas'] and esp_results['metadatas'][0]:
        all_metadatas.extend(esp_results['metadatas'][0])
    if global_results['metadatas'] and global_results['metadatas'][0]:
        all_metadatas.extend(global_results['metadatas'][0])

    return RagContext(context=context, metadatas=all_metadatas,
                      esp_normalized=esp_normalized, enhanced_query=enhanced_query)
