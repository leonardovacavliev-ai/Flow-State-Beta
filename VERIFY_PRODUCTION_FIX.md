# Production Verification Guide (Non-Technical)

## Step 1: Wait for Deployment (3-5 minutes)

Railway needs time to:
- Pull the new code from GitHub ✅ (Done)
- Build the application
- Deploy to production servers

**Action:** Wait 3-5 minutes, then continue to Step 2.

---

## Step 2: Open Your Production Admin Panel

1. **Open your web browser** (Chrome, Safari, Firefox, etc.)
2. **Go to your production URL:**
   - If Railway: `https://your-app-name.up.railway.app`
   - Or whatever your live URL is
3. **Click the "Admin" button** (usually in the corner or header)
4. **Enter admin password:** `RICHCSM`
5. **Click "ESP Management" tab**

---

## Step 3: Check ESP Link Status

You should see a list of ESPs (Klaviyo, DotDigital, Attentive, etc.)

### ✅ GOOD (Fixed):
Each ESP shows links with **colored badges**:
- **Green badge "CRAWLED"** ← Means the link is working
- **Yellow badge "PENDING"** ← Means not crawled yet (normal)

Example of what you SHOULD see:
```
Klaviyo (4 documents)
  ├─ ✅ CRAWLED  https://support.yotpo.com/docs/loyalty-emails...
  ├─ ✅ CRAWLED  https://help.klaviyo.com/hc/en-us/articles/...
  ├─ ✅ CRAWLED  https://help.klaviyo.com/hc/en-us/articles/...
  └─ ✅ CRAWLED  https://support.yotpo.com/docs/klaviyo-oauth...
```

### ❌ BAD (Still broken):
Links show **"UNDEFINED"** or blank status

Example of what you should NOT see:
```
Klaviyo (4 documents)
  ├─ UNDEFINED  https://support.yotpo.com/docs/loyalty-emails...
  ├─ UNDEFINED  https://help.klaviyo.com/hc/en-us/articles/...
```

---

## Step 4: Tell Me What You See

**If you see GREEN/YELLOW badges:**
✅ **Production is FIXED!** You're done.

**If you still see "UNDEFINED":**
❌ **Production needs Pinecone re-vectorization.** Tell me and I'll fix it remotely.

---

## Step 5: Test AI Response (Optional - Extra Verification)

1. **Go back to the main chat interface**
2. **Select "Klaviyo" from the ESP dropdown**
3. **Type this exact question:**
   ```
   How do I pull in the referral link and points till next tier in Klaviyo?
   ```

### ✅ GOOD Response:
The AI should mention:
- `loyalty_nt_points` (for points till next tier)
- `swell_referral_link` (for referral link)
- Show Liquid template code like:
  ```liquid
  {{ person|lookup:'loyalty_nt_points' }}
  {{ person|lookup:'swell_referral_link' }}
  ```

### ❌ BAD Response:
The AI makes up property names like:
- `next_tier_points` ← Wrong
- `referral_url` ← Wrong
- Or says "I don't have that information"

---

## Quick Reference: What to Look For

| Location | What to Check | Good ✅ | Bad ❌ |
|----------|---------------|---------|--------|
| Admin Panel → ESP Management | Link Status | "CRAWLED" or "PENDING" | "UNDEFINED" |
| Chat Interface | AI Response | Uses `loyalty_nt_points` and `swell_referral_link` | Makes up property names or says "I don't know" |

---

## If Something's Wrong

Just tell me:
- "I see UNDEFINED in admin panel" → I'll fix Pinecone remotely
- "AI is still making up property names" → I'll check RAG retrieval
- "Can't access admin panel" → I'll check Railway deployment

---

## Timeline

- **Now (0 min):** Code pushed to GitHub ✅
- **+3 min:** Railway builds app ⏳
- **+5 min:** New version live, ready to test 🎯
- **+10 min:** You verify and let me know results 👍

---

**Current Time:** Deployment started ~2 minutes ago
**Check Production In:** ~3 more minutes
