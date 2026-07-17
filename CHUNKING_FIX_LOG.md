# Document Chunking Fix - Implementation Log

**Date:** 2026-07-17  
**Issue:** AI hallucinating property names due to poor document chunking  
**Goal:** Long-term system fix (not band-aid)  

---

## Problem Summary

### Root Cause
1. **Bad chunking:** 500-word splits ignore document structure
2. **Bad crawling:** HTML-to-text strips all formatting
3. **Result:** Critical info buried in giant text blobs, doesn't rank well in search

### Example Failure
- **Query:** "How do I pull in points till next tier?"
- **Expected:** `loyalty_nt_points`
- **Actual:** `swell_points_to_next_tier` (hallucination)
- **Why:** Chunk 10 has correct info but starts with irrelevant payout content, property list buried at end

---

## Solution Design

### Approach: Semantic Chunking + Structured Crawling

#### 1. Semantic Chunking Strategy
**Old method (base.py):**
```python
# Split on word count (ignores structure)
words = text.split()
for i in range(0, len(words), chunk_size - chunk_overlap):
    chunk = ' '.join(words[i:i + chunk_size])
```

**New method:**
- Split on natural boundaries (headers, sections)
- Keep related content together (property lists, code blocks)
- Smaller chunks (300 words max for better retrieval)
- More overlap (100 words to prevent info loss)

#### 2. Structured Crawling
**Old method (crawler.py):**
```python
soup = BeautifulSoup(html, 'html.parser')
content = soup.get_text()  # Strips ALL formatting
```

**New method:**
- Preserve headers as markdown (`## Header`)
- Preserve lists as markdown (`- Item`)
- Keep code blocks intact
- Maintain document hierarchy

---

## Implementation Steps

### Task 1: Fix Chunking in base.py ✅ COMPLETE

**File:** `backend/adapters/vector/base.py`  
**Method:** `chunk_text()`

**Changes made:**
1. ✅ Detect section boundaries using regex pattern matching
2. ✅ Split on semantic boundaries (headers, "List of", "Properties", etc.)
3. ✅ Reduced chunk size to 300 words (from 500)
4. ✅ Increased overlap to 100 words (from 50)
5. ✅ Added minimum chunk size filter (20 words) to avoid tiny chunks

**Implementation notes:**
- Uses regex to detect section headers: `## Header`, `List of X`, `Properties`, etc.
- Splits large sections by paragraph boundaries (`\n\n`)
- Preserves overlap by including last N words of previous chunk
- Maintains minimum quality bar (20+ words per chunk)

**Key improvements:**
- Property lists will stay together (no longer split mid-list)
- Headers preserved with their related content
- Better semantic coherence within each chunk

---

### Task 2: Fix Crawler in crawler.py ✅ COMPLETE

**File:** `backend/crawler.py`  
**Method:** `extract_main_content()`

**Changes made:**
1. ✅ Convert HTML headers (h1-h6) to markdown headers (##, ###, etc.)
2. ✅ Convert `<ul>/<li>` to markdown lists (`- Item`)
3. ✅ Convert `<ol>/<li>` to numbered lists (`1. Item`)
4. ✅ Preserve `<code>/<pre>` blocks with markdown code fences
5. ✅ Add paragraph spacing (`\n\n`) for clear section breaks
6. ✅ Smart whitespace cleanup (max 1 consecutive blank line)

**Implementation notes:**
- Headers: h1 -> ##, h2 -> ###, etc. (avoiding single # to prevent confusion)
- Lists: BeautifulSoup unwrap() preserves content while removing wrapper tags
- Code blocks: Wrapped in triple backticks for markdown compatibility
- Whitespace: Removes excessive blanks while preserving structure

**Key improvements:**
- Document structure now visible to chunking algorithm
- Property lists formatted consistently
- Headers act as natural chunk boundaries
- Code examples remain intact and readable

---

### Task 3: Test Locally ✅ COMPLETE

**What tested:**
1. ✅ Re-crawled Klaviyo docs with new crawler
2. ✅ Re-chunked with new chunking strategy
3. ✅ Compared old vs new chunks
4. ✅ Verified property list positioning

**Test results:**
- **New content:** 35,477 chars (vs 34,403 old) - gained 1KB from preserved structure
- **Markdown headers:** ✅ Present in new (❌ absent in old)
- **Total chunks:** 29 (vs 12 old) - more chunks due to smaller size
- **Avg chunk size:** 197 words (vs ~500 old)

**Property chunk analysis (Chunk #27):**
- ✅ Starts with "List of customer properties" header
- ✅ Property definitions clearly formatted as bullet list
- ✅ `loyalty_nt_points` at 29.5% through chunk (vs 70%+ in old chunk 10)
- ✅ Contains ALL tier-related properties together
- ✅ Size: 472 words (focused, not bloated)

**Key improvements:**
- Property definitions no longer buried under irrelevant content
- Clear section markers for better semantic search
- Related properties stay together (all `loyalty_nt_*` in same chunk)
- Document structure preserved (headers, lists, spacing)

---

### Task 4: Re-Index Production ⏳ PENDING

**ESPs to re-crawl:**
1. [ ] Klaviyo (4 documents)
2. [ ] DotDigital (X documents)
3. [ ] Attentive (X documents)
4. [ ] Ometria (X documents)
5. [ ] Postscript (X documents)

**Process:**
1. Re-crawl each ESP with new crawler
2. Re-vectorize with new chunking
3. Upsert to Pinecone (replace old chunks)
4. Verify vector counts match

**Results:**
- [To be filled in after re-indexing]

---

### Task 5: Deploy & Verify ⏳ PENDING

**Deployment:**
1. Push code to GitHub
2. Wait for Railway auto-deploy (~3 min)
3. Verify deployment health

**Production testing:**
1. Test original query: "How do I pull in points till next tier?"
2. Expected: Response mentions `loyalty_nt_points`
3. Test 2-3 other queries across different ESPs

**Results:**
- [To be filled in after deployment]

---

## Code Changes Log

### File: backend/adapters/vector/base.py
**Status:** Not started  
**Changes:**
- [To be documented]

### File: backend/crawler.py
**Status:** Not started  
**Changes:**
- [To be documented]

---

## Testing Log

### Local Testing
**Date:** [To be filled in]  
**Results:**
- [To be documented]

### Production Testing  
**Date:** [To be filled in]  
**Queries tested:**
1. [To be documented]
2. [To be documented]
3. [To be documented]

**Accuracy:**
- Before: XX%
- After: XX%

---

## Rollback Plan

If something goes wrong:

### Quick Rollback (No Code Changes)
If new chunks are worse:
1. Git revert the commits
2. Re-deploy old version
3. Old chunks still in Pinecone (we don't delete during upsert)

### Full Rollback (If Pinecone Corrupted)
If we need to restore Pinecone:
1. Keep backup of old chunks (before re-index)
2. Can re-upload from local ChromaDB if needed
3. Worst case: Re-crawl from scratch (2-3 hours)

---

## Success Metrics

### Before Fix (Baseline)
- Accuracy: ~60-70% (estimated)
- Hallucinations: Frequent (property names, API endpoints)
- User trust: Low (need to verify every answer)

### After Fix (Target)
- Accuracy: >90%
- Hallucinations: Rare
- User trust: High (can use answers directly)

### Measurement
- Test suite: 20-30 queries across all ESPs
- Manual verification: Check 5-10 responses for accuracy
- User feedback: Track thumbs up/down after deployment

---

## Notes for Future Sessions

### If Context Window Runs Out
**Resume from this file:** `CHUNKING_FIX_LOG.md`

**Current status check:**
1. Read this file for progress
2. Run `git log -3` to see recent commits
3. Check Pinecone vector count: `python3 check_pinecone_timestamps.py`
4. Review task list: Check which tasks are marked complete

**Key files:**
- `backend/adapters/vector/base.py` - Chunking logic
- `backend/crawler.py` - HTML extraction
- `TIMELINE_ANALYSIS.md` - Root cause analysis
- `RAG_HALLUCINATION_FIX.md` - Solution design

---

## Timeline

**Start:** 2026-07-17 [Current time]  
**Estimated completion:** 6-8 hours  
**Actual completion:** [To be filled in]

---

**Last updated:** [Will be updated after each step]
