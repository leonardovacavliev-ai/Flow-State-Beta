# Paste Content Feature Fix

## Problem

Manual paste content feature was returning:
```
❌ Server error: Expected JSON response but got text/html; charset=utf-8
Endpoint: https://flow-state-beta-production.up.railway.app/api/admin/esp/ometria/paste-content
```

## Root Cause

**The endpoint didn't exist in the deployed version.**

### Why?

1. **Phase 4 Migration**: The app uses database-backed ESP routes (`USE_DATABASE_ESP_ROUTES = True` in [app.py:54](backend/app.py:54))
2. **Missing Endpoint**: The `paste-content` endpoint existed in the old filesystem routes ([app.py:594](backend/app.py:594)) but was **never migrated** to the new database-backed routes in `app_admin_esp_routes.py`
3. **404 Response**: When frontend called the endpoint, Flask returned a 404 error page (HTML), not JSON

## Solution

### 1. Added Paste Content Endpoint to Database Routes

**File**: [backend/app_admin_esp_routes.py:215-287](backend/app_admin_esp_routes.py:215)

Added `POST /api/admin/esp/<esp_name>/paste-content` endpoint that:
- ✅ Validates admin password
- ✅ Gets/creates ESP and document in database (Phase 4 pattern)
- ✅ Saves content to `docs/{esp_name}/{filename}.txt`
- ✅ Triggers Pinecone vectorization via `vectorizer.refresh_esp()`
- ✅ Updates database crawl status to 'completed'
- ✅ Returns success message with filename

### 2. Improved Error Handling (Already Done)

**File**: [frontend/paste-content-modal.js:65-85](frontend/paste-content-modal.js:65)

Enhanced error reporting to show:
- Expected vs actual content type
- Endpoint URL
- Console logging for debugging

## How It Works Now

### User Workflow

1. **Admin Panel** → **ESP Management** → Find link with yellow "PENDING" badge
2. Click **"📋 Paste Content"** button
3. Modal opens with URL and ESP pre-filled
4. Paste article content (plain text, not HTML)
5. Click **"Save & Vectorize"**
6. Backend:
   - Saves to `docs/ometria/article-name.txt`
   - Updates PostgreSQL database (`esp_documents` table)
   - Triggers Pinecone vectorization (`vectorizer.refresh_esp('ometria')`)
   - Updates status from 'pending' → 'completed'
7. Success message shows filename
8. Link badge changes from yellow "PENDING" to green "COMPLETED"

### Technical Flow

```
Frontend
  ↓
POST /api/admin/esp/ometria/paste-content
  ↓
app_admin_esp_routes.py:paste_esp_content()
  ↓
1. Verify password
2. Get ESP from database (esp_manager)
3. Get/create document record
4. Save content → docs/ometria/{filename}.txt
5. Vectorize → Pinecone (vectorizer.refresh_esp())
6. Update database → status='completed'
  ↓
Response: { success: true, filename: "..." }
  ↓
Frontend: Show success, refresh ESP list
```

## Database Changes

When content is pasted, the `esp_documents` table is updated:

```sql
UPDATE esp_documents 
SET 
  crawl_status = 'completed',
  content_hash = 'sha256...',
  last_crawled_at = NOW()
WHERE id = {document_id};
```

This ensures:
- ✅ Persistence across deployments (stored in PostgreSQL)
- ✅ Status tracking (pending → completed)
- ✅ Content hash for change detection

## Vectorization

Uses the existing vector adapter pattern:
- **Local**: ChromaDB (for local development)
- **Production**: Pinecone (Railway deployment)

The `vectorizer.refresh_esp('ometria')` call:
1. Reads all `.txt` files in `docs/ometria/`
2. Chunks content (500 words, 50 word overlap)
3. Embeds chunks with SentenceTransformers
4. Upserts to Pinecone namespace `ometria`

## Testing

### On Railway (Production)

1. Wait 2-3 minutes for deployment to complete
2. Go to: https://flow-state-beta-production.up.railway.app/
3. Admin Panel → ESP Management → Find "Ometria" (or any ESP)
4. Add a test URL → It will show as "PENDING"
5. Click **"📋 Paste Content"**
6. Paste test content (e.g., "This is a test article about loyalty integration...")
7. Click **"Save & Vectorize"**
8. Should see: `✅ Content saved successfully! File: test-article.txt`
9. Status should change to "COMPLETED"
10. Test in chat: Select "Ometria" → Ask about the test content → AI should reference it

### Expected Results

**Before Fix:**
```
❌ Server error: Expected JSON response but got text/html
Endpoint: .../api/admin/esp/ometria/paste-content
```

**After Fix:**
```
✅ Content saved successfully!

File: integration-guide.txt

The content has been vectorized and is now 
available for the AI assistant.
```

## Files Changed

### Commit 1: Error Handling
- [frontend/paste-content-modal.js](frontend/paste-content-modal.js) - Better error messages

### Commit 2: Add Endpoint
- [backend/app_admin_esp_routes.py](backend/app_admin_esp_routes.py) - Added paste-content endpoint

## Notes

### Global Knowledge
The global knowledge paste-content endpoint (`/api/admin/global-knowledge/paste-content`) **already works** because it's still in [app.py:1127](backend/app.py:1127) (not migrated to database routes yet).

### Why This Happened
The paste-content feature was built **before** Phase 4 (database-backed ESP management) was implemented. When Phase 4 was completed, the ESP routes were migrated to `app_admin_esp_routes.py`, but the paste-content endpoint was overlooked and never migrated.

### Future Improvements
- [ ] Migrate global knowledge routes to database-backed pattern
- [ ] Add content editing (currently can only delete & re-add)
- [ ] Show content preview on hover
- [ ] Track manual vs auto-crawled in UI
