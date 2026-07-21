# Test Instructions: Listrak Crawl Fix

## What Was Fixed
The ESP routes were calling a non-existent function `crawl_and_save(url, esp_name, base_path)`. This function doesn't exist - the crawler only had the old CSV-based `crawl_and_save(csv_path, base_docs_path)`.

**Fix**: Created new `crawl_single_url(url, esp_name, base_path)` function that works with individual URLs.

---

## Testing Steps

### 1. Wait for Railway Deployment
- Push completed at: `[timestamp]`
- Railway typically deploys in 3-5 minutes
- Check: https://railway.app → Your project → Deployments
- Wait for "SUCCESS" status

### 2. Option A: Try Re-Crawling via Admin UI (Simplest)

1. Go to your Railway app URL
2. Click **Admin Panel** (enter password: `RICHCSM`)
3. Find **Listrak** in the ESP list
4. You should see 4 URLs with **"FAILED"** status
5. **Select all 4 checkboxes**
6. Click **"Crawl Selected Links"**
7. Wait 30 seconds
8. **Expected result**:
   - Success message: "Crawled 4 URLs successfully"
   - All checkboxes should be **checked** (status: COMPLETED)
   - NOT "Successfully crawled NaN links"

### 3. Option B: Use Script (More Detailed)

If you want to see exactly what's happening:

```bash
# Update the API_BASE URL in the script first
nano recrawl_listrak.py

# Change this line:
API_BASE = "https://your-railway-url.up.railway.app"

# Run the script
python3 recrawl_listrak.py
```

Expected output:
```
=== Listrak Re-Crawl Script ===

Found 4 failed Listrak documents:
  - https://help.listrak.com/en/articles/2283752-integration-guide-yotpo
  - https://help.listrak.com/en/articles/6909272-loyalty-automations-in-listrak-conductor
  - https://help.listrak.com/en/articles/2465793-listrak-conductor-steps
  - https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-listrak

Resetting status to 'pending'...
✓ Reset complete

Triggering re-crawl via API...
✓ API response: Crawled 4 URLs successfully
  Success: 4
  Failed: 0

=== Final Status Check ===
✓ https://help.listrak.com/en/articles/2283752-integration-guide-yotpo: completed
✓ https://help.listrak.com/en/articles/6909272-loyalty-automations-in-listrak-conductor: completed
✓ https://help.listrak.com/en/articles/2465793-listrak-conductor-steps: completed
✓ https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-listrak: completed
```

### 4. Verify Pinecone Has Data

```bash
python3 check_listrak_pinecone.py
```

Expected output:
```
=== Pinecone Index Stats ===
Total vectors: 249+  (should be more than before)

Namespaces:
  : 249 vectors
  listrak: 10-20 vectors  <-- NEW!

=== Checking for Listrak data ===
✓ Found Listrak namespace with 15 vectors

Sample Listrak vectors:
  ID: listrak_doc1_chunk0
  Metadata: {'esp': 'listrak', 'url': '...', 'filename': '...'}
```

### 5. Test the Chat Interface

1. Go to your Railway app
2. Click **"Start New Session"**
3. Select **"Listrak"** from ESP dropdown
4. Ask: **"How do I integrate Yotpo Loyalty with Listrak?"**

**Expected Result**: 
- AI gives a detailed answer with specific Listrak steps
- NOT: "I don't have information about that"
- NOT: Generic answer without Listrak-specific details

**Good Answer Example**:
```
To integrate Yotpo Loyalty with Listrak:

1. First, connect your Listrak account in the Yotpo admin panel...
2. Configure the webhook settings to send loyalty events...
3. In Listrak Conductor, create a new automation...
4. Use the loyalty data fields available from Yotpo...

[etc with specific details from the docs]
```

---

## If It Still Fails

### Check Railway Logs
1. Railway Dashboard → Your project → Deployments → Latest
2. Click "View Logs"
3. Look for `[CRAWLER]` log messages when you try to crawl
4. Send me the error logs

### Check Database Directly
```bash
python3 check_listrak_database.py
```

Look at the `crawl_status` and `last_crawled_at` fields. If still "failed", check the error message.

### Manual Test
If the API is still broken, we can test the crawler directly:
```bash
python3 test_listrak_crawl.py
```

This bypasses the API and tests the crawler function directly.

---

## Success Criteria

- ✅ Admin UI shows "Crawled 4 URLs successfully" (NOT "NaN")
- ✅ All 4 Listrak URLs marked as "COMPLETED" in database
- ✅ Pinecone has a `listrak` namespace with 10-20 vectors
- ✅ Chat interface gives Listrak-specific answers

---

## Timeline

1. **Now**: Fix pushed to GitHub
2. **+3-5 min**: Railway auto-deploys
3. **+5-10 min**: You test via admin UI or script
4. **+15 min**: Confirm working in chat

Total: ~15 minutes to verified fix

---

## What to Share With Me

After testing, send me:

1. **Admin UI Result**: 
   - Screenshot or text of the crawl success message
   - Whether checkboxes are checked

2. **Pinecone Check**:
   - Output of `python3 check_listrak_pinecone.py`
   - Does it show a `listrak` namespace?

3. **Chat Test**:
   - What question you asked
   - What answer the AI gave
   - Whether it's Listrak-specific or generic

---

**Good luck!** The fix is solid - tested locally and all 4 URLs crawl successfully. Should work in production now.
