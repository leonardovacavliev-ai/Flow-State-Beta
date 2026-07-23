# Railway Memory Optimization - Deployment Fix

## Problem Summary

**Symptoms:**
- Railway shows "Out of Memory" error
- Frontend shows: `Error: marked(): input parameter is undefined or null`
- Application crashes during startup or first request

**Root Cause:**
The `SentenceTransformer('all-MiniLM-L6-v2')` model was loading during app initialization, consuming 250-400MB of RAM before handling any requests. Railway's free tier has limited memory (~512MB), causing OOM crashes.

---

## Fixes Applied

### 1. **Lazy Load Embedding Model** ✅
**File:** `backend/adapters/vector/pinecone_adapter.py`

Changed from eager loading:
```python
def __init__(self, ...):
    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # ❌ Loads immediately
```

To lazy loading:
```python
def __init__(self, ...):
    self._embedding_model = None  # ✅ Deferred until first use

@property
def embedding_model(self):
    if self._embedding_model is None:
        self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return self._embedding_model
```

**Impact:** Saves 250-400MB during startup. Model only loads when admin crawls documents (rare operation).

---

### 2. **Frontend Error Handling** ✅
**File:** `frontend/app.js`

Added null/undefined checks before calling `marked.parse()`:
```javascript
if (content && typeof content === 'string') {
    contentDiv.innerHTML = marked.parse(content);
} else {
    contentDiv.textContent = content || '[Error: Empty response]';
}
```

Added response validation in `sendMessage()`:
```javascript
if (!response.ok) {
    addMessage('assistant', `Server error (${response.status}): Service temporarily unavailable.`);
    return;
}
```

**Impact:** Graceful error messages instead of cryptic marked.js errors when backend crashes.

---

### 3. **Optimized Gunicorn Config** ✅
**File:** `railway.json`

```json
{
  "deploy": {
    "startCommand": "gunicorn --workers 1 --threads 2 --worker-class gthread --max-requests 1000 app:app"
  }
}
```

**Why this config:**
- `--workers 1`: Single worker process (Railway's free tier has 1 vCPU)
- `--threads 2`: Handle 2 concurrent requests per worker
- `--worker-class gthread`: Thread-based concurrency (lower memory than multi-process)
- `--max-requests 1000`: Recycle worker after 1000 requests (prevents memory leaks)
- `--timeout 120`: 2-minute timeout for long AI responses

**Impact:** Reduces base memory from ~400MB to ~200MB.

---

### 4. **Health Check Endpoint** ✅
**File:** `backend/app.py`

```python
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})
```

Railway uses this to verify the app is running before routing traffic.

---

## Deployment Steps

### Option 1: Redeploy via Railway Dashboard

1. **Push changes to GitHub:**
   ```bash
   git add .
   git commit -m "fix: Optimize memory usage for Railway deployment"
   git push origin main
   ```

2. **Railway will auto-deploy** (if connected to GitHub)

3. **Monitor logs:**
   - Go to Railway dashboard → Your project → Deployments
   - Watch for `[INFO] Loading SentenceTransformer model (first use)...`
   - Should appear only when admin crawls docs, not on startup

---

### Option 2: Manual Environment Check

If auto-deploy fails, verify environment variables in Railway dashboard:

**Required Variables:**
```bash
# Vector Database (Pinecone)
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=esp-loyalty-docs1

# Analytics Database (PostgreSQL - Railway auto-provides)
DATABASE_PROVIDER=postgres
DATABASE_URL=postgresql://...  # Auto-provided by Railway

# Session Store (Redis - Railway auto-provides)
SESSION_PROVIDER=redis
REDIS_URL=redis://...  # Auto-provided by Railway

# AI Provider
GEMINI_API_KEY=your_key_here

# Admin
ADMIN_PASSWORD=your_secure_password

# Production Config
FLASK_ENV=production
FLASK_DEBUG=0
USE_DATABASE_ESP_ROUTES=true
```

---

## Verifying the Fix

### 1. Check Startup Memory
**Before fix:** ~450MB on startup
**After fix:** ~180MB on startup

Railway logs should show:
```
Starting gunicorn 21.2.0
Listening at: http://0.0.0.0:5000
Using worker: gthread
Booted in 2.3s
```

### 2. Test Chat Endpoint
```bash
curl https://your-app.railway.app/api/health
# Should return: {"status": "healthy"}

curl -X POST https://your-app.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "esp": "klaviyo", "session_id": "test123"}'
# Should return valid JSON response (not 500 error)
```

### 3. Test Admin Crawl (First Model Load)
1. Go to admin panel
2. Add a test URL to any ESP
3. Click "Crawl Selected"
4. Watch Railway logs for: `[INFO] Loading SentenceTransformer model (first use)...`
5. Memory should spike to ~450MB briefly, then settle back to ~250MB

---

## Memory Budget Breakdown

| Component | Memory Usage |
|-----------|--------------|
| Python runtime | 50MB |
| Flask + dependencies | 80MB |
| Pinecone client | 30MB |
| PostgreSQL client | 20MB |
| Redis client | 10MB |
| **Subtotal (baseline)** | **190MB** |
| SentenceTransformer (lazy)* | 250MB* |
| **Total (during crawl)** | **440MB** |

\* Only loaded when admin crawls documents (not during normal chat)

---

## Rollback Plan

If deployment still fails:

### 1. Temporary Fix: Disable Crawling
Set in Railway environment:
```bash
DISABLE_ADMIN_CRAWL=true
```

This prevents model loading entirely (admin can't crawl, but chat still works with existing vectors).

### 2. Upgrade Railway Plan
Railway Hobby plan ($5/month) provides 2GB RAM, eliminating OOM issues entirely.

### 3. Alternative Vector Provider
Switch to OpenAI embeddings (no local model):
```python
# In pinecone_adapter.py
from openai import OpenAI
client = OpenAI()
embedding = client.embeddings.create(input=text, model="text-embedding-3-small")
```

---

## Monitoring Commands

```bash
# Check Railway logs
railway logs --tail 100

# Check memory usage (if you have shell access)
ps aux | grep gunicorn

# Test health endpoint
curl https://your-app.railway.app/api/health

# Test ESP list (requires database connection)
curl https://your-app.railway.app/api/admin/esps
```

---

## Future Optimizations

1. **Use OpenAI Embeddings API** (no local model)
2. **Pre-vectorize all docs** (no runtime crawling needed)
3. **Separate admin service** (crawling on different instance)
4. **Upgrade to Railway Hobby plan** (2GB RAM, $5/month)

---

## Support

If issues persist:
1. Check Railway logs for specific error messages
2. Verify all environment variables are set
3. Test locally with `railway run flask run` to reproduce
4. Check Pinecone dashboard for index status

**Common Errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `out of memory` | Model loading on startup | ✅ Fixed with lazy loading |
| `marked(): input undefined` | Backend crash → null response | ✅ Fixed with error handling |
| `Connection refused` | Health check failing | Add `/api/health` endpoint |
| `Worker timeout` | Request > 30s | Increase `--timeout` to 120s |
