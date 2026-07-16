# Granular Link Management System

## Overview

Switched from a global "Refresh All" system to granular link-by-link management with checkboxes, status indicators, and selective actions.

## New Features

### 1. **Link Status Indicators**
- **⏳ Pending** (orange): Link added but not yet crawled
- **✓ Crawled** (green): Link successfully crawled and in knowledge base

### 2. **Checkbox Selection**
- Select individual links for specific actions
- Select multiple links at once
- No forced "refresh everything" approach

### 3. **Granular Actions**
- **🔄 Crawl Selected**: Only crawl the checked links
- **🗑️ Delete Selected**: Remove checked links from CSV and knowledge base

### 4. **Smart Close Button**
- **Normal**: Shows "×" when no pending links
- **Pending**: Changes to "Crawl & Close" button (orange) when there are uncrawled links
- Clicking "Crawl & Close" crawls all pending links before closing

### 5. **Real-time Counts**
- Shows document count per ESP
- Shows pending link count per ESP
- Updates immediately after actions

## How to Use

### Adding a New Link
1. Enter URL in "Add new link" field
2. Click "Add Link"
3. Link appears with ⏳ pending status
4. Select it and click "🔄 Crawl Selected" to crawl

### Crawling Specific Links
1. Check the boxes next to links you want to crawl
2. Click "🔄 Crawl Selected"
3. Wait for success message
4. Links change from ⏳ to ✓ status

### Deleting Links
1. Check the boxes next to links you want to remove
2. Click "🗑️ Delete Selected"
3. Confirm the deletion
4. Links removed from CSV and knowledge base

### Crawl & Close
1. When pending links exist, close button becomes "Crawl & Close"
2. Click it to crawl all pending links before closing
3. Or click normal "×" to close without crawling (if no pending)

## Backend Endpoints

### `GET /api/admin/esp/<name>/links`
Returns links with status:
```json
{
  "links": [
    {"url": "...", "status": "crawled"},
    {"url": "...", "status": "pending"}
  ]
}
```

### `POST /api/admin/esp/<name>/crawl-selected`
Crawls specific URLs:
```json
{
  "password": "RICHCSM",
  "urls": ["url1", "url2"]
}
```

### `POST /api/admin/esp/<name>/delete-links`
Deletes specific URLs:
```json
{
  "password": "RICHCSM",
  "urls": ["url1", "url2"]
}
```

## Benefits

### Efficiency
- No more re-crawling everything for one new link
- Only process what you need
- Faster iteration

### Control
- See exactly what's crawled vs pending
- Choose what to keep or remove
- Granular management per ESP

### Visual Feedback
- Status indicators show at a glance
- Pending count in header
- Orange "Crawl & Close" button alerts you

## UI Components

### Link Item Structure
```
[✓] ✓ https://example.com/doc
[checkbox] [status] [clickable URL]
```

### Action Buttons
- **Crawl Selected**: Teal hover
- **Delete Selected**: Coral hover
- **Add Link**: Orange (existing)

### Close Button States
- Normal: `×` (white text, transparent)
- Pending: `Crawl & Close` (orange button)

## Example Workflow

1. **Add multiple links**:
   - Add URL 1 → ⏳ pending
   - Add URL 2 → ⏳ pending
   - Add URL 3 → ⏳ pending

2. **Selective crawling**:
   - Check URL 1 and URL 2
   - Click "🔄 Crawl Selected"
   - URL 1 and 2 → ✓ crawled
   - URL 3 still ⏳ pending

3. **Delete unwanted**:
   - Realize URL 3 was wrong
   - Check URL 3
   - Click "🗑️ Delete Selected"
   - URL 3 removed

4. **Close**:
   - No pending links
   - Click "×" to close

---

**Status**: ✅ Fully implemented
**Efficiency**: Much faster than "Refresh All"
**Control**: Complete granular management
