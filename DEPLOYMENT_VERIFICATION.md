# Railway Deployment Verification Checklist

## Immediate Actions After Push

Railway will automatically redeploy from GitHub. Monitor the deployment:

### 1. Check Railway Dashboard
- Go to https://railway.app/dashboard
- Navigate to your project
- Click "Deployments" tab
- Watch the latest deployment status

### 2. Monitor Build Logs
Look for these key indicators:

✅ **Success indicators:**
```
Building...
Installing dependencies from requirements.txt
Build completed successfully
Starting gunicorn 21.2.0
Listening at: http://0.0.0.0:5000
Using worker: gthread
Booted in 2.3s
```

❌ **Failure indicators:**
```
out of memory
killed
Error: Command failed
```

### 3. Test Health Check (Once Deployed)
```bash
# Replace with your Railway URL
curl https://your-app.railway.app/api/health

# Expected response:
{"status": "healthy", "timestamp": "2026-07-23T..."}
```

### 4. Test Chat Endpoint
```bash
curl -X POST https://your-app.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I set up a welcome series?",
    "esp": "klaviyo",
    "session_id": "test-123"
  }'

# Should return JSON with "response" field (not 500 error)
```

### 5. Test Frontend
1. Open app URL in browser
2. Select an ESP (e.g., Klaviyo)
3. Send a test message
4. **Expected:** Response appears (no marked.js error)
5. **Expected:** No console errors in browser DevTools

---

## Environment Variables Checklist

Verify these are set in Railway dashboard (Settings → Variables):

### Required Variables
- [ ] `VECTOR_DB_PROVIDER=pinecone`
- [ ] `PINECONE_API_KEY=pcsk_...` (your key)
- [ ] `PINECONE_INDEX_NAME=esp-loyalty-docs1`
- [ ] `DATABASE_PROVIDER=postgres`
- [ ] `DATABASE_URL=postgresql://...` (Railway auto-provides)
- [ ] `SESSION_PROVIDER=redis`
- [ ] `REDIS_URL=redis://...` (Railway auto-provides)
- [ ] `GEMINI_API_KEY=...` (your key)
- [ ] `ADMIN_PASSWORD=...` (change from default!)
- [ ] `FLASK_ENV=production`
- [ ] `USE_DATABASE_ESP_ROUTES=true`

### Optional Variables
- [ ] `ANTHROPIC_API_KEY=...` (if using Claude)
- [ ] `OPENAI_API_KEY=...` (if using GPT)
- [ ] `FLASK_DEBUG=0` (disable debug mode)

---

## Memory Usage Verification

### Check Startup Memory
1. Railway Dashboard → Metrics tab
2. Check memory graph during deployment
3. **Expected:** ~180-200MB baseline (not 450MB+)

### Test Admin Crawl (First Model Load)
1. Login to admin panel (URL/admin.html)
2. Add a test URL to any ESP
3. Click "Crawl Selected"
4. Watch Railway logs for: `[INFO] Loading SentenceTransformer model (first use)...`
5. **Expected:** Memory spikes to ~400MB briefly, then drops to ~250MB
6. **Expected:** No OOM crash

---

## Troubleshooting

### Issue: Deployment Still Fails with OOM

**Diagnosis:**
```bash
# Check Railway logs
railway logs --tail 50
```

**Solutions:**

1. **Verify lazy loading is active:**
   ```bash
   # In Railway logs, you should NOT see this on startup:
   "Loading SentenceTransformer model"
   
   # You SHOULD only see it during admin crawl
   ```

2. **Check if other services are consuming memory:**
   ```bash
   # Railway dashboard → Metrics
   # Verify PostgreSQL and Redis aren't overloading
   ```

3. **Temporary workaround - disable crawling:**
   ```bash
   # Add in Railway environment variables:
   DISABLE_ADMIN_CRAWL=true
   ```

4. **Consider upgrading Railway plan:**
   - Free tier: 512MB RAM
   - Hobby tier ($5/mo): 2GB RAM
   - Pro tier ($20/mo): 8GB RAM

---

### Issue: marked.js Error Still Appears

**Diagnosis:**
Check browser console (F12 → Console tab)

**If you see:**
```
marked(): input parameter is undefined or null
```

**Causes:**
1. Backend returned null/empty response
2. Network error before response completed
3. Response format changed

**Solution:**
```bash
# Test API directly
curl -v https://your-app.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","esp":"klaviyo","session_id":"test"}'

# Check response body - should have "response" field
```

---

### Issue: Health Check Fails

**Diagnosis:**
```bash
curl https://your-app.railway.app/api/health
# Returns: connection refused, timeout, or 404
```

**Solutions:**

1. **Verify Railway service is running:**
   - Dashboard → Deployments → Check status

2. **Check Procfile/railway.json:**
   - Should have: `gunicorn ... app:app` (not `flask run`)

3. **Verify port binding:**
   ```python
   # In app.py, should have:
   port = int(os.environ.get('PORT', 5000))
   app.run(host='0.0.0.0', port=port)
   ```

---

## Success Criteria

✅ **Deployment is successful if:**
1. Railway build completes without OOM errors
2. `/api/health` returns `{"status": "healthy"}`
3. Chat endpoint returns valid responses (not 500 errors)
4. Frontend loads and displays ESP selector
5. Sending a message works without marked.js errors
6. Memory stays under 300MB during normal operation

---

## Rollback Plan

If deployment fails completely:

### Option 1: Revert to Previous Commit
```bash
git revert HEAD
git push origin main
# Railway auto-deploys previous working version
```

### Option 2: Disable New Features
Add Railway environment variables:
```bash
VECTOR_DB_PROVIDER=chromadb  # Revert to local (won't work on Railway!)
USE_DATABASE_ESP_ROUTES=false  # Use filesystem routes
```

### Option 3: Use Previous Railway Deployment
Railway Dashboard → Deployments → Select previous successful deployment → "Redeploy"

---

## Next Steps After Successful Deployment

1. **Test all ESP selections** (Klaviyo, DotDigital, Attentive, etc.)
2. **Test admin panel** (login, view ESPs, add links)
3. **Test feedback submission** (send message, click feedback button)
4. **Monitor for 24 hours** (check Railway metrics for memory leaks)
5. **Update DNS/domain** (if using custom domain)

---

## Contact

If issues persist:
- Check Railway community forum
- Review logs with: `railway logs --tail 100`
- Test locally with: `railway run flask run`
- Verify Pinecone connection: https://app.pinecone.io/
