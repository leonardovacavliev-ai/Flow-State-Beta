# How to Re-Index Production Pinecone

## The Problem

✅ Code is fixed and deployed to Railway
✅ Local Pinecone has new improved chunks
❌ **Production Pinecone (on Railway) still has OLD chunks**

That's why the AI is still hallucinating - Railway is querying the old, badly-chunked vectors.

---

## Solution: Re-Index Production Pinecone

You have 2 options:

### Option A: Run Re-Index Script on Railway (Recommended)

**Step 1:** Add the re-index script to your repo
```bash
git add reindex_all_esps.py
git commit -m "Add production re-index script"
git push origin main
```

**Step 2:** SSH into Railway and run the script
```bash
# Railway CLI command (if you have it installed)
railway run python3 reindex_all_esps.py

# OR via Railway dashboard:
# 1. Go to Railway dashboard
# 2. Open your service
# 3. Click "Settings" → "Deploy"
# 4. Add a one-time command: python3 reindex_all_esps.py
```

This will re-crawl and re-vectorize all docs directly on Railway's Pinecone.

---

### Option B: Point Railway to Your Local Pinecone Index (Faster)

If your local Pinecone (`esp-loyalty-docs1`) is accessible from Railway:

**Check Railway environment variables:**
1. Go to Railway dashboard
2. Your service → Variables tab
3. Verify `PINECONE_INDEX_NAME=esp-loyalty-docs1`
4. Verify `PINECONE_API_KEY` matches your local `.env`

If they match, **Railway IS using the same Pinecone as local!**

In that case, the new chunks (249 vectors) should already be there.

**Verify by checking Railway logs:**
```
# Check if Railway app can see the new vectors
# Look for startup logs mentioning vector count
```

---

## Quick Verification

Run this on Railway (via railway CLI or add as a debug endpoint):

```python
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))

stats = index.describe_index_stats()
print(f"Total vectors: {stats.total_vector_count}")

# Should show 249 if re-index worked, 101 if still old data
```

---

## Troubleshooting

### If Railway shows 101 vectors:
- Railway is using a DIFFERENT Pinecone index
- OR Railway environment vars are different
- OR re-index didn't run on production

**Fix:** Run Option A (re-index script on Railway)

### If Railway shows 249 vectors but AI still hallucinates:
- Vectors are there but not being retrieved correctly
- Check app.py search logic deployed correctly
- Check Railway restarted after code push

**Fix:** Force Railway redeploy

---

## Nuclear Option: Force Railway to Re-Index on Deploy

Add this to Railway's start command:

```bash
# In Railway dashboard → Settings → Deploy Command
python3 reindex_all_esps.py && gunicorn app:app
```

**Warning:** This will re-index EVERY time Railway deploys (slow)

Better: Run it once manually, then remove from start command

---

## How to Check If It Worked

**Test query:** "How do I pull in points till next tier?"

**Expected response:**
```
Use the property {{ person|lookup:'loyalty_nt_points' }}
```

**NOT expected:**
```
Use points_until_next_tier (hallucination)
Use swell_points_to_next_tier (hallucination)
```

---

## Next Steps

1. **Verify Pinecone config**: Check Railway env vars match local
2. **Run re-index on Railway**: Option A or B above
3. **Force redeploy**: If needed, trigger Railway redeploy
4. **Test again**: Same query, check for `loyalty_nt_points`

Let me know what you find!
