# Future Accuracy Improvements

Ideas documented for future exploration when resources allow.

---

## Query Reformulation (High Impact, Requires Fast Model)

**Status**: Documented for future implementation  
**Reason Deferred**: Requires dedicated fast model (Claude Haiku, Gemini Flash, GPT-4o-mini)  
**Estimated Impact**: 15-25% accuracy improvement on follow-up questions

### Problem
Follow-up questions like "What about for abandoned carts?" lack context. Current approach (appending previous assistant message) is crude and can add 1000+ characters of noise.

### Proposed Solution
Use fast LLM to reformulate ambiguous follow-ups into standalone queries before vector search:

```python
# Before vector search
if len(conversation_history) > 0 and needs_reformulation(message):
    reformulated = fast_model.reformulate(
        query=message,
        conversation_history=conversation_history[-4:]  # Last 2 turns
    )
    search_query = reformulated
else:
    search_query = message
```

**Example**:
```
Conversation:
User: "How do I set up a welcome flow in Klaviyo?"
Assistant: [explains welcome flows with triggers, filters, etc.]
User: "What properties can I use?"

Reformulated: "What Klavioy properties can I use in a welcome flow?"
```

### Implementation Requirements
- **Fast model access** (200-500ms latency budget)
  - Claude Haiku 3.5 (recommended)
  - OR Gemini Flash 2.0
  - OR GPT-4o-mini
- Fallback mechanism (always use original if reformulation fails)
- A/B testing framework (10% → 50% → 100% rollout)
- Kill switch via environment variable

### Safety Checks
```python
def is_valid_reformulation(original, reformulated):
    # Not too long (no hallucination)
    if len(reformulated) > len(original) * 3:
        return False
    
    # Preserves key entities
    original_keywords = set(original.lower().split())
    reformulated_keywords = set(reformulated.lower().split())
    if len(original_keywords & reformulated_keywords) == 0:
        return False
    
    return True
```

### When to Implement
- After establishing dedicated fast model infrastructure
- When accuracy on follow-up questions becomes a priority metric
- Estimated effort: 2-3 days with proper A/B testing

---

## Other Future Ideas

### Hybrid Search (Semantic + Keyword)
**Impact**: High for exact term matching (property names, technical terms)  
**Effort**: 2-3 days if Pinecone native support, 1 week if custom  
**Requires**: Infrastructure change

### Agentic RAG (Self-Reflection)
**Impact**: High for complex multi-hop questions  
**Effort**: 1 week  
**Requires**: Multiple LLM calls per query

### Multi-Query Retrieval
**Impact**: Medium (better coverage)  
**Effort**: 3 days  
**Requires**: 3x vector search calls per query
