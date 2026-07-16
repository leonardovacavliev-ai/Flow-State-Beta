# Admin Panel Changes - Testing Guide

## How to Test the New Features

### Prerequisites
1. Start the backend: `cd backend && python3 app.py`
2. Start the frontend: `cd frontend && python3 -m http.server 8000`
3. Open: `http://localhost:8000`
4. Click "Admin" button in sidebar
5. Enter password: `RICHCSM`

---

## Test 1: Create New ESP & Sidebar Auto-Update

### Steps:
1. In admin panel, scroll to "Create New ESP" section
2. Enter a test ESP name (e.g., "braze" or "mailchimp")
3. Click "Create ESP"

### Expected Result:
✅ Alert: "ESP created successfully!"  
✅ **New ESP appears in sidebar immediately** (no page refresh needed)  
✅ New ESP section appears in admin panel with empty links

### What Changed:
- Before: Required full page refresh to see new ESP
- After: Sidebar dynamically reloads via `reloadSidebar()` function

---

## Test 2: Link Spacing & Formatting

### Steps:
1. Look at any ESP section with existing links (Klaviyo, DotDigital, Attentive)

### Expected Result:
✅ Each link is in its own styled card with spacing  
✅ Status badge shows "pending" (orange) or "crawled" (green)  
✅ Checkbox appears on the left of each link  
✅ Links have hover effects (border color changes to orange)  
✅ Better vertical spacing between links (0.75rem)

### Visual Check:
- Links should be easy to distinguish from each other
- Status badges are clearly visible
- No more cramped plain text list

---

## Test 3: Add New Link (Pre-Checked)

### Steps:
1. Pick any ESP (e.g., Klaviyo)
2. In the "Add new link" input, enter a test URL:
   - Example: `https://support.yotpo.com/docs/test-article`
3. Click "Add Link"

### Expected Result:
✅ Alert: "Link added successfully. It will be pre-checked for crawling."  
✅ New link appears at the bottom with:
   - **"pending" status badge (orange)**
   - **Checkbox is PRE-CHECKED** ✓
✅ "Bulk actions" section appears with buttons:
   - "Crawl Selected" (orange)
   - "Delete Selected" (red outline)

### What Changed:
- Before: Generic message "Click Refresh All to crawl"
- After: New links auto-checked, ready for selective crawling

---

## Test 4: Checkbox Selection & Bulk Actions

### Steps:
1. Uncheck all checkboxes in an ESP section
2. Observe the bulk actions section

### Expected Result:
✅ "Crawl Selected" and "Delete Selected" buttons **disappear** when nothing is selected

### Steps (continued):
3. Check 2-3 checkboxes

### Expected Result:
✅ Bulk action buttons **reappear** when links are selected  
✅ Buttons are styled and ready to click

### What Changed:
- Before: "Refresh All" button always visible, processed everything
- After: Bulk actions only show when needed, process only selected links

---

## Test 5: Crawl Selected Links

### Steps:
1. Select 1-2 links by checking their checkboxes (prefer "pending" status links)
2. Click "Crawl Selected" button
3. Wait for processing (may take a few seconds per link)

### Expected Result:
✅ Alert: "Successfully crawled X links!"  
✅ Selected links change from "pending" to "crawled" status  
✅ Status badge changes from orange to green  
✅ Admin panel refreshes to show updated status  
✅ Vector database updated (links now searchable in chat)

### What Changed:
- Before: Had to crawl ALL links even for one new link
- After: Process only what you select

---

## Test 6: Delete Selected Links

### Steps:
1. Check 1-2 links you want to remove
2. Click "Delete Selected" button
3. Confirm the deletion dialog

### Expected Result:
✅ Confirmation dialog: "Are you sure you want to delete X link(s)?"  
✅ After confirming:
   - Alert: "Deleted X links"
   - Links removed from display
   - Links removed from CSV file
   - Documentation files deleted
   - Vector database updated

### Safety Features:
- Confirmation dialog prevents accidental deletion
- Can undo by re-adding the same URL

---

## Test 7: Mixed Selection (Pending + Crawled)

### Steps:
1. Check both "pending" and "crawled" status links
2. Click "Crawl Selected"

### Expected Result:
✅ All selected links are re-crawled (useful for updating changed documentation)  
✅ Status updates appropriately  
✅ Vector database refreshed with latest content

---

## Test 8: Visual Styling Check

### Expected Visual Elements:

#### Link Items:
- ✅ White background cards with rounded corners
- ✅ Hover effect: Orange border + subtle shadow
- ✅ Pending links: Light orange background (#fff9f0)
- ✅ Proper spacing (0.75rem between items)

#### Status Badges:
- ✅ **Pending**: Orange background (#fff3e0), dark orange text
- ✅ **Crawled**: Green background (#e8f5e9), dark green text
- ✅ Uppercase text with letter spacing
- ✅ Rounded corners, padding

#### Action Buttons:
- ✅ **Crawl Selected**: Orange background, dark text
- ✅ **Delete Selected**: White background, coral/red border
- ✅ Hover effects: Slight lift + shadow
- ✅ Full-width buttons with good padding

#### ESP Management Items:
- ✅ Light gray background (#EFEFEF)
- ✅ Larger padding (1.5rem)
- ✅ Better spacing between ESP sections (1.5rem margin)
- ✅ ESP titles are bold and larger

---

## Common Issues & Solutions

### Issue: New ESP doesn't appear in sidebar
**Solution**: Check browser console for errors. Ensure backend is running on port 5000.

### Issue: Checkboxes don't show/hide buttons
**Solution**: Clear browser cache and reload. Check console for JavaScript errors.

### Issue: Crawl fails
**Solution**: 
1. Check backend logs for errors
2. Ensure URLs are valid and accessible
3. Verify GEMINI_API_KEY is set

### Issue: Links look unstyled
**Solution**: 
1. Hard refresh browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
2. Check if styles.css loaded properly (Network tab in DevTools)

---

## Performance Notes

### Crawling Time:
- Each link takes ~1-2 seconds to crawl
- Selecting 5 links = ~5-10 seconds total
- Much faster than "Refresh All" which processes everything

### Database Updates:
- Vector database only updates for selected ESP
- No full re-vectorization needed
- Faster feedback loop

---

## Keyboard Shortcuts (Browser)

- `Space` on checkbox: Toggle selection
- `Tab`: Navigate between checkboxes
- `Enter` on button: Activate button

---

## Screenshots (Where to Look)

### Before:
- Plain text list of links
- One "Refresh All" button
- No status indicators
- Required page refresh for new ESPs

### After:
- Styled link cards with badges
- Checkboxes + selective buttons
- Visual status (pending/crawled)
- Dynamic sidebar updates

---

## Success Criteria

All features working if:
- ✅ New ESP appears in sidebar without refresh
- ✅ Links are well-spaced and easy to read
- ✅ Checkboxes control bulk action visibility
- ✅ Can crawl only selected links
- ✅ Can delete only selected links
- ✅ Status badges show correct state
- ✅ Hover effects work smoothly

---

**Test completed by**: _______________  
**Date**: _______________  
**Result**: ✅ Pass / ❌ Fail  
**Notes**: _______________
