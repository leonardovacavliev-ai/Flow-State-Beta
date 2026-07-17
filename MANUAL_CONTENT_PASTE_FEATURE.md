# Manual Content Paste Feature

## Overview

Added a manual content paste feature that allows admins to manually add content for links that cannot be automatically crawled (e.g., protected/authentication-required pages).

## Problem Solved

Some documentation links are protected by authentication or anti-bot measures, causing them to remain stuck in "pending" status after crawl attempts fail. This feature provides a workaround by allowing admins to manually copy-paste the content.

## Implementation

### Backend Changes

#### 1. New API Endpoints

**`POST /api/admin/esp/<esp_name>/paste-content`** ([app.py:483](backend/app.py:483))
- Accepts manually pasted content for a specific ESP link
- Parameters:
  - `password`: Admin password
  - `url`: The URL being documented
  - `content`: The manually pasted text content
- Saves content to `docs/{esp_name}/{filename}.txt`
- Updates `crawl_metadata.json`
- Automatically triggers vectorization via `vectorizer.refresh_esp()`
- Returns success message with filename

**`POST /api/admin/global-knowledge/paste-content`** ([app.py:1018](backend/app.py:1018))
- Same functionality but for global knowledge links
- Saves to `docs/global/{filename}.txt`

### Frontend Changes

#### 1. UI Updates to Link Display

**ESP Links** ([app.js:958-973](frontend/app.js:958-973))
- Added "📋 Paste Content" button for links with `status === 'pending'`
- Button triggers `openPasteModal(espName, url, false)`
- Styled with primary color scheme for visibility

**Global Knowledge Links** ([app.js:1772-1788](frontend/app.js:1772-1788))
- Same "Paste Content" button implementation
- Triggers `openPasteModal('global', url, true)`

#### 2. Paste Content Modal

**HTML Modal** ([index.html:652-691](frontend/index.html:652-691))
- Overlay modal with blur backdrop
- Fields:
  - **URL** (readonly): Shows which link is being documented
  - **ESP** (readonly): Shows ESP name or "Global Knowledge"
  - **Content** (textarea): Large text area for pasting article content
- Buttons:
  - **Cancel**: Close without saving
  - **Save & Vectorize**: Submit content

**JavaScript Logic** ([paste-content-modal.js](frontend/paste-content-modal.js))
- `openPasteModal(espName, url, isGlobal)`: Opens modal with context
- `closePasteModal()`: Closes and resets modal
- `submitPasteContent()`: 
  - Validates content (warns if < 100 characters)
  - Shows loading state during submission
  - Calls appropriate API endpoint (ESP or global)
  - Displays success/error messages
  - Refreshes ESP management view on success
- Event listeners:
  - Click outside to close
  - Escape key to close
  - Button click handlers

## User Workflow

### Step 1: Identify Protected Link
1. Admin opens Admin Panel → ESP Management
2. Sees link with yellow "PENDING" badge (auto-selected for crawl)
3. Notes that automated crawl failed

### Step 2: Manual Content Paste
1. Click **"📋 Paste Content"** button next to the pending link
2. Modal opens showing:
   - URL: `https://example.com/protected-article`
   - ESP: `klaviyo` (or "Global Knowledge")
   - Content: Empty textarea

### Step 3: Copy Content
1. Open the protected URL in browser
2. Log in if required
3. Select and copy the article text (main content only)

### Step 4: Paste & Submit
1. Paste content into the modal textarea
2. Click **"Save & Vectorize"**
3. System:
   - Saves content to appropriate folder
   - Updates metadata
   - Triggers vectorization (makes content searchable by AI)
   - Changes status from "pending" to "completed"
4. Success message shows filename

### Step 5: Verify
1. Link status changes from yellow "PENDING" to green "COMPLETED"
2. Content is now available for AI assistant queries
3. "Paste Content" button disappears (only shown for pending links)

## Technical Details

### File Storage Structure
```
docs/
├── klaviyo/
│   ├── loyalty-integration.txt  (auto-crawled)
│   └── protected-guide.txt      (manually pasted)
├── dotdigital/
│   └── api-docs.txt
├── global/
│   └── best-practices.txt
└── crawl_metadata.json
```

### Metadata Format
```json
{
  "klaviov": [
    {
      "url": "https://example.com/protected-guide",
      "filename": "protected-guide.txt",
      "filepath": "docs/klaviyo/protected-guide.txt"
    }
  ]
}
```

### Content File Format
```
Source URL: https://example.com/protected-guide

[Pasted content here...]
```

## Benefits

1. **Unblocks Documentation**: No longer limited by crawler restrictions
2. **Same Vectorization**: Manually pasted content gets same treatment as crawled content
3. **Maintains Consistency**: Uses same file structure and metadata format
4. **User-Friendly**: Clear visual indication (yellow badge → paste button → green badge)
5. **Flexible**: Works for both ESP-specific and global knowledge
6. **Safe**: Requires admin password, includes validation

## Future Enhancements

Potential improvements:
1. **Content Preview**: Show first 200 chars of saved content on hover
2. **Edit Existing**: Allow editing already-pasted content
3. **Batch Paste**: Upload multiple articles at once
4. **Quality Checks**: 
   - Detect if content looks like HTML/markup (warn to paste plain text)
   - Suggest minimum content length based on ESP
5. **Version History**: Track when content was manually added vs auto-crawled
6. **Diff View**: Compare manual paste with subsequent successful crawl
7. **Source Attribution**: Flag manually-pasted content in AI responses

## Files Changed

### Backend
- [backend/app.py](backend/app.py) - Added 2 new endpoints (ESP + global)

### Frontend
- [frontend/index.html](frontend/index.html) - Added paste modal HTML
- [frontend/app.js](frontend/app.js) - Added "Paste Content" buttons to links
- [frontend/paste-content-modal.js](frontend/paste-content-modal.js) - New file with modal logic

## Testing Checklist

- [x] Backend endpoint creates file in correct folder
- [x] Backend endpoint updates metadata correctly
- [x] Backend endpoint triggers vectorization
- [x] Frontend modal opens with correct context
- [x] Frontend shows button only for pending links
- [x] Frontend validation prevents empty submissions
- [x] Frontend refreshes view after successful paste
- [x] Works for ESP-specific links
- [x] Works for global knowledge links
- [ ] Manual testing with actual protected URL (requires deployed instance)

## Deployment Notes

No additional dependencies required. The feature uses existing:
- Flask routing (backend)
- Vanilla JavaScript (frontend)
- ChromaDB/Pinecone vectorization (existing)
- SQLite/PostgreSQL metadata (existing)

Just deploy updated `backend/app.py`, `frontend/` files, and restart services.
