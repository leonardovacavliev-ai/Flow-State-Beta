# Accuracy Improvement: Relevance Score Filtering

**Status**: Ready to implement  
**Risk**: Very Low  
**Effort**: 30 minutes  
**Impact**: 10-15% accuracy improvement + reduced hallucinations

---

## The Problem

Vector search returns 10 ESP chunks **regardless of quality**. If a query matches poorly, you still get 10 results where:
- Top 3-4 chunks: Highly relevant (similarity >0.75)
- Middle 3-4 chunks: Somewhat relevant (0.6-0.75)
- Bottom 2-3 chunks: **Barely relevant (<0.6)** ← These cause hallucinations

**Current behavior**: All 10 chunks go to LLM, including garbage.

**Example bad scenario**:
```
Query: "How do I trigger a flow when a customer earns 100 VIP points?"
Top 3 results: About Klaviyo triggers, loyalty points, flow setup ✅
Results 7-10: Generic loyalty program marketing tips ❌
```

The LLM sees those irrelevant chunks and tries to incorporate them → hallucination.

---

## The Fix

Filter out low-relevance chunks before sending to LLM.

### Implementation (30 minutes)

**File**: `backend/app.py`

**Step 1**: Update vector search to retrieve **distances** (similarity scores)

ChromaDB returns `distances` by default in query results. We just need to use them.

**Step 2**: Filter results by minimum relevance threshold

```python
# After line 179 in app.py
MIN_RELEVANCE_SCORE = 0.60  # Tune this (lower = more permissive, higher = stricter)

# Search ESP-specific docs (10 results)
esp_results = vectorizer.search(enhanced_query, esp_filter=esp_normalized, n_results=10)

# Filter by relevance score (if distances available)
if 'distances' in esp_results and esp_results['distances']:
    filtered_docs = []
    filtered_metadatas = []
    
    for doc, metadata, distance in zip(
        esp_results['documents'][0], 
        esp_results['metadatas'][0],
        esp_results['distances'][0]
    ):
        # ChromaDB uses L2 distance (lower = more similar)
        # Convert to similarity: similarity = 1 / (1 + distance)
        similarity = 1 / (1 + distance)
        
        if similarity >= MIN_RELEVANCE_SCORE:
            filtered_docs.append(doc)
            filtered_metadatas.append(metadata)
    
    # Update results
    esp_results['documents'] = [filtered_docs]
    esp_results['metadatas'] = [filtered_metadatas]
    
    # Log filtering stats
    original_count = len(esp_results['distances'][0])
    filtered_count = len(filtered_docs)
    if filtered_count < original_count:
        print(f"[FILTER] Filtered ESP results: {original_count} → {filtered_count} (removed {original_count - filtered_count} low-relevance chunks)")

# Apply same filtering to global results (line 182)
global_results = vectorizer.search(enhanced_query, esp_filter='global', n_results=2)

if 'distances' in global_results and global_results['distances']:
    filtered_docs = []
    filtered_metadatas = []
    
    for doc, metadata, distance in zip(
        global_results['documents'][0], 
        global_results['metadatas'][0],
        global_results['distances'][0]
    ):
        similarity = 1 / (1 + distance)
        if similarity >= MIN_RELEVANCE_SCORE:
            filtered_docs.append(doc)
            filtered_metadatas.append(metadata)
    
    global_results['documents'] = [filtered_docs]
    global_results['metadatas'] = [filtered_metadatas]
```

**Step 3**: Add warning when insufficient documentation found (line 208)

```python
# After line 208
if source_index == 1:
    context += "No specific documentation found. Provide general guidance based on ESP best practices.\n\n"
elif source_index <= 4:  # Very few sources (3 or fewer)
    context += "\n⚠️ WARNING: Limited documentation found for this specific query. Provide guidance but note the documentation gaps.\n\n"
```

---

## Why This Works

1. **Removes noise**: Low-quality chunks don't confuse the LLM
2. **Reduces hallucinations**: LLM only sees relevant context
3. **Signals low confidence**: When few chunks pass filter, AI knows to hedge
4. **Saves tokens**: Fewer chunks = lower costs
5. **Zero risk**: If filtering removes too much, you see the warning and can lower threshold

---

## Tuning the Threshold

Start with `MIN_RELEVANCE_SCORE = 0.60` (60% similarity).

**After 1 week, check logs**:
- If too many queries have <3 results: Lower to 0.55
- If users report irrelevant info in answers: Raise to 0.65

**Optimal range**: 0.55-0.70 (depends on your embedding model quality)

---

## Expected Results

**Before**:
```
Query: "Abandoned cart reminder setup"
Returns: 10 chunks (3 excellent, 4 okay, 3 garbage)
LLM sees all 10 → sometimes uses garbage info
```

**After**:
```
Query: "Abandoned cart reminder setup"
Returns: 7 chunks (3 excellent, 4 okay) ← garbage filtered out
LLM only sees good info → more accurate answer
```

**Metrics to track**:
- Average chunks per query (expect: 10 → 6-7)
- User feedback ratings (expect: +10-15% positive)
- "I don't know" responses (expect: slight increase, which is GOOD - means less hallucination)

---

## Alternative: Extract Function

For cleaner code, extract filtering logic:

```python
def filter_by_relevance(results: Dict, min_score: float = 0.60) -> Dict:
    """Filter vector search results by minimum relevance score"""
    if 'distances' not in results or not results['distances']:
        return results  # No distance info, return as-is
    
    filtered_docs = []
    filtered_metadatas = []
    
    for doc, metadata, distance in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        # ChromaDB L2 distance: lower = more similar
        similarity = 1 / (1 + distance)
        
        if similarity >= min_score:
            filtered_docs.append(doc)
            filtered_metadatas.append(metadata)
    
    return {
        'documents': [filtered_docs],
        'metadatas': [filtered_metadatas]
    }

# Usage
esp_results = vectorizer.search(enhanced_query, esp_filter=esp_normalized, n_results=10)
esp_results = filter_by_relevance(esp_results, min_score=0.60)
```

---

## Next Steps

1. Implement filtering (30 min)
2. Deploy to production
3. Monitor for 1 week:
   - Check logs for "Filtered ESP results" messages
   - Compare user feedback before/after
   - Adjust threshold if needed
4. Document optimal threshold value
