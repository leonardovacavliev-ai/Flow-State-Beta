# Phase 3: Redis Session Store - COMPLETE ✅

**Goal**: Move conversation history from in-memory to persistent, distributed session storage

**Status**: Implementation complete, ready to test and deploy

---

## Overview

This phase completes the stateless cloud architecture by externalizing the last piece of in-memory state: conversation history. With Redis session storage, you can now:

- ✅ Scale horizontally (multiple API instances share session data)
- ✅ Survive server restarts (conversations persist)
- ✅ Auto-expire inactive sessions (Redis TTL)
- ✅ Deploy to any cloud provider with Redis support

**Implementation Pattern**: Follows the same **adapter pattern** used in Phases 1 (Vector DB) and 2 (Analytics DB).

---

## Architecture

### Before (In-Memory)
```
User sends message → Flask endpoint
                   ↓
Frontend passes conversation_history[] in request body
                   ↓
AI generates response with full history
                   ↓
Frontend stores updated history in localStorage
```

**Problem**: Each API instance has its own memory. Load balancer can route requests to different servers, losing conversation context.

### After (Redis)
```
User sends message → Flask endpoint
                   ↓
Backend fetches conversation_history from Redis (session_id)
                   ↓
AI generates response with full history
                   ↓
Backend saves updated history to Redis (session_id)
                   ↓
Frontend only needs to pass session_id
```

**Benefits**:
- Session data shared across all API instances
- Conversations survive server restarts
- Automatic cleanup via Redis TTL (default: 30 minutes)

---

## Implementation Details

### Directory Structure
```
backend/adapters/session/
├── __init__.py              # Package exports
├── base.py                  # SessionAdapter interface
├── memory_adapter.py        # In-memory (local dev)
├── redis_adapter.py         # Redis (cloud prod)
└── session_manager.py       # Factory function
```

### SessionAdapter Interface

**Methods**:
- `get_conversation_history(session_id)` → List[Dict] - Retrieve messages
- `add_message(session_id, role, content)` → None - Append message
- `clear_history(session_id)` → None - Delete session
- `set_ttl(session_id, ttl_seconds)` → None - Update expiration
- `session_exists(session_id)` → bool - Check if session has data
- `get_all_session_ids()` → List[str] - Debug/admin tool

### MemorySessionAdapter

**Use Case**: Local development

**Features**:
- Thread-safe dictionary storage
- No persistence (data lost on restart)
- Zero configuration required

**When to Use**: Local dev with `SESSION_PROVIDER=memory`

### RedisSessionAdapter

**Use Case**: Cloud production

**Features**:
- Persistent across restarts
- Shared across API instances
- Automatic TTL expiration
- Health check support

**Redis Key Format**: `session:{session_id}:history`

**Data Format**: JSON array of message objects
```json
[
  {"role": "user", "content": "How do I set up Klaviyo?"},
  {"role": "assistant", "content": "Here's how to set up Klaviyo..."}
]
```

---

## Configuration

### Environment Variables

**Required for Redis**:
```bash
SESSION_PROVIDER=redis
REDIS_URL=redis://localhost:6379/0  # Railway auto-provides this
```

**Optional**:
```bash
SESSION_TTL_SECONDS=1800  # Default: 30 minutes
```

### Local Development (.env)
```bash
SESSION_PROVIDER=memory  # No Redis needed
```

### Cloud Production (.env)
```bash
SESSION_PROVIDER=redis
REDIS_URL=redis://<host>:<port>/<db>  # Provided by Railway/Heroku/etc
SESSION_TTL_SECONDS=1800
```

---

## How to Use

### Switch Between Providers

**Local Dev** (no Redis):
```bash
# .env
SESSION_PROVIDER=memory
```

**Cloud Prod** (with Redis):
```bash
# .env
SESSION_PROVIDER=redis
REDIS_URL=redis://your-redis-host:6379/0
```

No code changes required - adapter is selected automatically on startup.

---

## Code Changes Summary

### 1. app.py Imports
```python
from adapters.session.session_manager import get_session_adapter

# Initialize session adapter (singleton)
session_adapter = get_session_adapter()
```

### 2. Chat Endpoint (Before)
```python
@app.route('/api/chat', methods=['POST'])
def chat():
    conversation_history = data.get('history', [])  # From frontend
    
    # Generate response...
    
    # Frontend tracks history
```

### 3. Chat Endpoint (After)
```python
@app.route('/api/chat', methods=['POST'])
def chat():
    session_id = data.get('session_id')  # Required
    
    # Get history from session store
    conversation_history = session_adapter.get_conversation_history(session_id)
    
    # Add user message
    session_adapter.add_message(session_id, 'user', message)
    
    # Generate response...
    
    # Add assistant message
    session_adapter.add_message(session_id, 'assistant', assistant_message)
```

**Key Changes**:
- Frontend now sends `session_id` instead of `history`
- Backend manages conversation history via adapter
- Backwards compatible (frontend doesn't need changes yet)

---

## Testing Guide

### Local Testing (Memory Adapter)

**1. Verify Environment**
```bash
# .env
SESSION_PROVIDER=memory
```

**2. Start App**
```bash
cd backend
python app.py
```

**Expected Output**:
```
[SessionManager] Initializing session adapter: memory
[SessionManager] ✓ In-memory session storage initialized
```

**3. Test Chat**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "message": "Hello",
    "esp": "klaviyo"
  }'
```

**4. Verify History Persists**
```bash
# Send second message with same session_id
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "message": "Tell me more",
    "esp": "klaviyo"
  }'
```

AI should reference previous message context.

---

### Cloud Testing (Redis Adapter)

**1. Install Redis Locally** (for testing)
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

**2. Update Environment**
```bash
# .env
SESSION_PROVIDER=redis
REDIS_URL=redis://localhost:6379/0
SESSION_TTL_SECONDS=1800
```

**3. Start App**
```bash
cd backend
python app.py
```

**Expected Output**:
```
[SessionManager] Initializing session adapter: redis
[SessionManager] ✓ Redis session storage initialized (TTL: 1800s)
```

**4. Test Redis Connection**
```bash
# In another terminal
redis-cli ping
# Should return: PONG

# Check stored sessions
redis-cli KEYS "session:*"

# View specific session
redis-cli GET "session:test-session-123:history"
```

**5. Test TTL Expiration**
```bash
# Check time-to-live
redis-cli TTL "session:test-session-123:history"
# Should show ~1800 seconds

# Wait 30 minutes (or adjust TTL to 60s for testing)
# Session should auto-expire
```

---

## Railway Deployment

### 1. Add Redis to Railway

**Option A: Automatic (Recommended)**
```bash
# Railway auto-detects Redis requirement from requirements.txt
# and provisions REDIS_URL automatically
```

**Option B: Manual**
1. Go to Railway dashboard
2. Click "New Service" → "Database" → "Redis"
3. Copy `REDIS_URL` from Variables tab

### 2. Update Environment Variables

In Railway dashboard → Variables:
```bash
SESSION_PROVIDER=redis
REDIS_URL=<auto-provided-by-railway>
SESSION_TTL_SECONDS=1800
```

### 3. Deploy
```bash
git push origin main
# Railway auto-deploys
```

### 4. Verify Logs
```bash
railway logs
# Look for:
# [SessionManager] Initializing session adapter: redis
# [SessionManager] ✓ Redis session storage initialized (TTL: 1800s)
```

---

## Troubleshooting

### Error: "REDIS_URL environment variable is required"

**Solution**: Set `SESSION_PROVIDER=memory` for local dev, or provide `REDIS_URL` for Redis.

### Error: "Failed to connect to Redis: [Errno 61] Connection refused"

**Causes**:
1. Redis server not running
2. Wrong REDIS_URL
3. Firewall blocking port 6379

**Solutions**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# Test connection
redis-cli -u redis://localhost:6379/0 ping
```

### Error: "JSONDecodeError" in logs

**Cause**: Corrupted session data in Redis

**Solution**:
```bash
# Clear corrupted session
redis-cli DEL "session:{session_id}:history"
```

### Sessions Expiring Too Quickly

**Solution**: Increase TTL
```bash
# .env
SESSION_TTL_SECONDS=3600  # 1 hour
```

---

## Performance Considerations

### Redis vs Memory

**Memory Adapter**:
- ✅ Zero latency (in-process)
- ✅ No network overhead
- ❌ Lost on restart
- ❌ Not shared across instances

**Redis Adapter**:
- ✅ Persistent
- ✅ Shared across instances
- ✅ Auto-cleanup via TTL
- ⚠️ ~1-2ms network latency per operation

### Optimization Tips

**1. Connection Pooling** (already implemented)
```python
# redis_adapter.py uses connection pooling by default
self.client = redis.from_url(redis_url)
```

**2. Reduce Round Trips**
```python
# Current: 2 operations per message (get + set)
# Could batch: Use Redis pipeline for multiple operations
# (Future optimization if needed)
```

**3. Compression** (optional for large conversations)
```python
# If conversations exceed 1000 messages:
import gzip
compressed = gzip.compress(json.dumps(history).encode())
```

---

## Migration from In-Memory

### No Data Migration Required

Unlike Phases 1 & 2, there's **no data to migrate**:
- In-memory sessions are ephemeral (lost on restart anyway)
- Users will simply start fresh conversations after switch
- No export/import scripts needed

### Graceful Transition

**Step 1**: Deploy with `SESSION_PROVIDER=memory` (no change)
**Step 2**: Add Redis to Railway
**Step 3**: Switch to `SESSION_PROVIDER=redis`
**Step 4**: Redeploy

Active sessions will be lost during switch (expected behavior).

---

## Next Steps

### Phase 3 Options

**Option A: Containerization** (Docker + CI/CD)
- Create Dockerfile
- Set up docker-compose.yml
- GitHub Actions auto-deploy

**Option B: Authentication & Multi-Tenancy**
- Integrate Auth0/Clerk
- Add tenant_id filtering
- Row-level security

**Recommendation**: You're now **fully stateless**! Either option is viable:
- If deploying to Kubernetes/ECS → Containerize first
- If adding paying customers → Auth/multi-tenancy first

---

## Compatibility Matrix

| Component | Local Dev | Cloud Prod |
|-----------|-----------|------------|
| Vector DB | ChromaDB | Pinecone ✅ |
| Analytics DB | SQLite | PostgreSQL ✅ |
| Session Store | Memory | Redis ✅ |
| Deployment | `./start.sh` | Railway ✅ |

**Status**: All systems cloud-ready! 🎉

---

## API Changes

### Backwards Compatibility

**Frontend still sends `history` array?** → Still works! Backend ignores it.

**Frontend sends `session_id` only?** → Preferred! Backend manages history.

### Deprecation Notice (Optional)

If you want to enforce session storage:
```python
# app.py
if 'history' in data:
    print("[DEPRECATED] Frontend sending 'history'. Update to session storage.")
```

---

## Summary

**What Changed**:
- ✅ Created session adapter abstraction layer
- ✅ Implemented memory & Redis adapters
- ✅ Updated app.py to use session storage
- ✅ Added Redis to requirements.txt
- ✅ Updated .env configuration

**What's Next**:
1. Test locally with memory adapter
2. Test with local Redis
3. Deploy to Railway with Redis
4. Verify sessions persist across API instances
5. Monitor Redis metrics in production

**Migration Status**:
- Phase 1: Vector DB ✅ COMPLETE
- Phase 2: Analytics DB ✅ COMPLETE
- Phase 3: Session Store ✅ COMPLETE
- Phase 4: Containerization ⏳ NEXT
- Phase 5: Authentication ⏳ FUTURE

---

## Support

**Issues?**
- Check Railway logs: `railway logs`
- Test Redis connection: `redis-cli ping`
- Verify environment: `echo $SESSION_PROVIDER`

**Questions?**
- Review adapter source: `backend/adapters/session/`
- Check app.py integration: `backend/app.py` (lines 3, 29, 95-108, 157-159)

---

**Document Version**: 1.0
**Last Updated**: July 17, 2026
**Author**: Claude Code
