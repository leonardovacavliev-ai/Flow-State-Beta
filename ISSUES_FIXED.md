# Issues Fixed - ESP Loyalty Helper App

## Date: 2026-07-17

### Issue #1: Logo Not Loading in Production ✅ FIXED

**Problem:**
- Logo files (`flow-state-logo.png`, etc.) were not appearing on the deployed Railway app
- Files were excluded by `.gitignore` pattern `*.png`
- This prevented logo files from being committed and deployed

**Root Cause:**
```gitignore
# .gitignore was blocking ALL image files
*.png
*.jpg
*.jpeg
```

**Solution:**
Updated `.gitignore` to allow frontend assets:
```gitignore
# Images (excluding frontend assets)
*.png
*.jpg
*.jpeg
!frontend/*.png
!frontend/*.jpg
!frontend/*.jpeg
!frontend/*.svg
```

**Files Changed:**
- `.gitignore` - Added exception rules for frontend images
- Committed: `frontend/flow-state-logo.png`, `frontend/sheriff-stop-new.png`, `frontend/sheriff-stop.png`

---

### Issue #2: ESP Links Not Loading in Admin Panel ✅ FIXED

**Problem:**
- Admin panel showed "X documents" for each ESP but displayed "No links added yet"
- ESP management system recognized document counts but couldn't fetch URLs
- "Refresh All" button did nothing

**Root Causes:**

#### Root Cause 2a: Hardcoded Localhost API URL
The frontend was making API calls to `http://localhost:5001/api` even when deployed on Railway.

```javascript
// frontend/app.js (OLD - BROKEN)
const API_URL = 'http://localhost:5001/api';
```

**Impact:** All API requests from the deployed app were failing because they tried to reach localhost instead of the Railway URL.

**Solution:**
```javascript
// frontend/app.js (NEW - FIXED)
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5001/api'
    : `${window.location.protocol}//${window.location.host}/api`;
```

#### Root Cause 2b: Case-Sensitive CSV Parsing
The CSV parsing logic was looking for lowercase `"integration urls"` but the CSV file has title case `"Integration URLs"`.

```python
# backend/app.py (OLD - BROKEN)
if 'integration urls' in line.lower() and esp_normalized in line.lower():
    # This would never match because line.lower() converted everything
```

**CSV File Structure:**
```csv
Klaviyo Integration URLs
https://support.yotpo.com/docs/klaviyo-oauth-integration-yotpo-loyalty-referrals
...

DotDigital Integration URLs
https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-dotdigital
...
```

**Solution:**
Fixed parsing in both `backend/app.py` and `backend/crawler.py`:

```python
# New logic (FIXED)
line_stripped = line.strip()
line_lower = line_stripped.lower()

if 'integration urls' in line_lower or 'knowledge urls' in line_lower:
    header_esp = line_lower.split()[0]  # "klaviyo", "dotdigital", etc.
    if header_esp == esp_normalized:
        in_section = True
        # Now properly collects URLs under this ESP
```

**Additional Improvements:**
- Added support for `"Global Knowledge URLs"` section
- Better handling of `"Other/Webhook"` ESP name normalization
- Handles empty lines within sections
- Supports `local://` URLs (for PDF references)

**Files Changed:**
- `frontend/app.js` - Dynamic API URL detection
- `backend/app.py` - Fixed `get_esp_links()` parsing logic + debug logging
- `backend/crawler.py` - Fixed `crawl_and_save()` parsing logic

---

## System Flow (Now Working)

### Data Flow for ESP Links:

1. **Storage:** Links stored in `esp_support_links.csv`
   ```
   Klaviyo Integration URLs
   https://...
   https://...
   ```

2. **Backend API:** `/api/admin/esp/<esp_name>/links`
   - Reads CSV file
   - Parses ESP sections (case-insensitive)
   - Checks `docs/crawl_metadata.json` for crawl status
   - Returns: `{links: [{url: "...", status: "crawled"|"pending"}]}`

3. **Frontend:** `loadESPManagement()` in `app.js`
   - Fetches from API (now uses correct URL)
   - Renders links with checkboxes
   - Shows "crawled" (green) or "pending" (yellow) status

4. **Crawling:** When user clicks "Crawl Selected"
   - Frontend: Collects checked URLs, groups by ESP
   - Backend: `/api/admin/esp/<esp_name>/crawl-selected`
     - Fetches content from each URL
     - Saves to `docs/<esp_name>/<filename>.txt`
     - Updates `docs/crawl_metadata.json`
     - Triggers vectorization (ChromaDB/Pinecone)

### File Structure:
```
esp_support_links.csv          # Master list of URLs
docs/
  crawl_metadata.json          # Crawl history and status
  klaviyo/
    *.txt                      # Crawled content
  dotdigital/
    *.txt
  attentive/
    *.txt
  ...
```

---

## Testing Performed

### Local Testing:
✅ Python script confirmed CSV parsing logic works correctly:
- Found all 4 Klaviyo URLs
- Correctly stopped at next ESP section
- Handled case-insensitive matching

### Expected Production Behavior:
Once Railway redeploys (automatic on git push):
1. ✅ Logo will be visible
2. ✅ ESP management will show all URLs from CSV
3. ✅ API calls will go to Railway URL (not localhost)
4. ✅ Crawl/refresh operations will work

---

## Commits Made

1. **6341ad6** - `fix: Resolve logo loading and ESP link parsing issues`
   - Fixed `.gitignore` to allow frontend images
   - Added logo files to repo
   - Fixed CSV parsing case sensitivity in `backend/app.py` and `backend/crawler.py`

2. **e756deb** - `fix: Auto-detect API URL and add debug logging`
   - Dynamic API URL detection in frontend
   - Added debug logging to backend for troubleshooting

---

## Verification Steps

After Railway redeploys, verify:

1. **Logo Check:**
   - Visit app URL
   - Logo should appear in header

2. **ESP Links Check:**
   - Log in to Admin Panel (password: from env var `ADMIN_PASSWORD`)
   - Navigate to "Manage ESPs" tab
   - Each ESP should show its URLs with status badges
   - Klaviyo should show 4 URLs
   - DotDigital should show 8 URLs
   - etc.

3. **Crawl Check:**
   - Select pending URLs
   - Click "Crawl Selected"
   - Should show success message with count
   - URLs should change from "pending" (yellow) to "crawled" (green)

---

## Additional Notes

### Debug Logging
Added verbose logging to `get_esp_links()` endpoint:
- Logs which ESP is being requested
- Shows CSV parsing steps
- Indicates when sections are matched
- Tracks URL collection

**To view logs on Railway:**
```bash
# Railway Dashboard -> Your App -> Deployments -> View Logs
# or use Railway CLI:
railway logs
```

### Environment Variables Required
Ensure Railway has these set:
- `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` - AI provider
- `ADMIN_PASSWORD` - Admin panel access
- `PINECONE_API_KEY` - Vector database
- `PINECONE_INDEX_NAME=esp-loyalty-docs1`
- `DATABASE_URL` - PostgreSQL connection string
- `VECTOR_DB_PROVIDER=pinecone`
- `DATABASE_PROVIDER=postgres`

### Known Limitations
- CSV file must follow exact format (ESP name first word of header line)
- Section headers must end with "Integration URLs" or "Knowledge URLs"
- URLs must start with `http` or `local://`
- Empty ESP sections are OK (e.g., "Listrak Integration URLs" with no URLs below)

---

## Next Steps (Optional Improvements)

1. **Remove debug logging** once confirmed working (makes logs cleaner)
2. **Add CSV validation** to catch malformed headers
3. **Bulk operations UI** - Select all pending, crawl by ESP, etc.
4. **Real-time progress** - WebSocket updates during long crawls
5. **URL validation** - Check URLs are reachable before crawling
6. **Duplicate detection** - Warn if same URL added twice
