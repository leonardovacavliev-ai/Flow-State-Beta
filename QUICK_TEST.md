# Quick Test Guide - Global Bulk Actions

## What You Should See Now

### 1. When Admin Panel Opens (No Links Selected)
```
┌──────────────────────────────┐
│ Admin Panel                  │
├──────────────────────────────┤
│                              │
│ Manage ESPs                  │
│                              │
│ [Ometria (0 documents)]      │
│   No links added yet.        │ ← Styled message with dashed border
│   Add a link below...        │
│   [Input field] [Add Link]   │
│                              │
│ [Attentive (1 documents)]    │
│   ☑ link1 [pending]          │ ← Link displays with checkbox + badge
│   [Input field] [Add Link]   │
│                              │
└──────────────────────────────┘
```

### 2. When You Check Some Boxes
```
┌─────────────────────────────────────────────────────────┐
│ 🟠 [3 links selected] [Crawl Selected] [Delete Selected]│ ← ORANGE STICKY BAR
└─────────────────────────────────────────────────────────┘
│                                                           │
│ [Klaviyo (3 documents)]                                  │
│   ☑ link1 [pending]  ← Checked                          │
│   □ link2 [crawled]                                      │
│   [Input field] [Add Link]                               │
│                                                           │
│ [DotDigital (6 documents)]                               │
│   ☑ link1 [pending]  ← Checked                          │
│   □ link2 [crawled]                                      │
│   [Input field] [Add Link]                               │
│                                                           │
│ [Attentive (1 documents)]                                │
│   ☑ link1 [pending]  ← Checked                          │
│   [Input field] [Add Link]                               │
└───────────────────────────────────────────────────────────┘
```

---

## Visual Elements

### ✅ Links ARE Displayed
Each link should show:
- ☑ Checkbox (checked if pending)
- `[pending]` or `[crawled]` badge (orange or green)
- Blue clickable URL
- White card background
- Hover effect (orange border)

### ✅ Global Bar Appears
When ANY checkbox is checked:
- Orange gradient bar at top
- White badge with count
- Two buttons (dark "Crawl", white "Delete")
- Stays visible while scrolling

### ✅ No Links Message
For ESPs with no links (like Ometria):
- Gray italic text
- Dashed border box
- Centered alignment
- "No links added yet" message

---

## How to Test Right Now

### Test 1: Check if Links Display
1. Open `http://localhost:8000`
2. Click "Admin" → Enter password `RICHCSM`
3. **Look for Attentive section** - Should show at least 1 link
4. **Look for link cards** - Should see checkboxes, badges, URLs

**Expected**: Links render as styled cards with checkboxes

**If broken**: Check browser console (F12) for JavaScript errors

---

### Test 2: Check Global Bar
1. Click ONE checkbox in Attentive
2. **Orange bar should appear at top** with "1 links selected"
3. Click another checkbox in DotDigital
4. **Counter should update** to "2 links selected"
5. Uncheck both
6. **Bar should disappear**

**Expected**: Bar toggles based on selection

**If broken**: Check console for `updateGlobalBulkActions` errors

---

### Test 3: Cross-ESP Crawl
1. Check 2 links from Klaviyo
2. Check 1 link from DotDigital  
3. Orange bar shows "3 links selected"
4. Click **"Crawl Selected"** in orange bar
5. Wait for processing
6. **Should see**: "Successfully crawled 3 links!"
7. All 3 links should change to `[crawled]` status

**Expected**: All selected links process in one operation

**If broken**: Check backend logs for errors

---

## Browser Console Debugging

If something is wrong, open console (F12) and check:

```javascript
// Check if links are loaded
document.querySelectorAll('.link-checkbox').length
// Should return number of total links

// Check if global bar exists
document.getElementById('globalBulkActions')
// Should return the bar element

// Check selected count
document.querySelectorAll('.link-checkbox:checked').length
// Should match the badge number

// Check ESP data on checkboxes
document.querySelector('.link-checkbox').dataset.esp
// Should return ESP name like "klaviyo"
```

---

## Common Issues & Quick Fixes

### Issue: "No links show up at all"
**Fix**: 
1. Check backend is running: `cd backend && python3 app.py`
2. Check browser console for fetch errors
3. Try visiting `http://localhost:5000/api/admin/esps` directly

### Issue: "Links show but no checkboxes"
**Fix**: 
1. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
2. Check if CSS loaded in Network tab
3. Clear browser cache

### Issue: "Global bar doesn't appear"
**Fix**:
1. Check browser console for JavaScript errors
2. Verify `updateGlobalBulkActions()` is defined
3. Try clicking a checkbox and check console

### Issue: "Counter doesn't update"
**Fix**:
1. Check if `addEventListener` is working on checkboxes
2. Look for errors in `updateGlobalBulkActions()` function
3. Verify checkbox has `data-esp` attribute

---

## Screenshot Comparison

### ❌ BEFORE (What you showed me):
- White empty space where links should be
- Just "Add Link" button visible
- No checkboxes, no badges, no URLs

### ✅ AFTER (What you should see):
- Styled link cards with borders
- Checkboxes on left
- Orange/green status badges
- Clickable blue URLs
- Orange sticky bar when selected

---

## Next Steps After Testing

1. **If links show**: ✅ Issue #1 fixed - proceed to test global actions
2. **If global bar works**: ✅ Issue #2 fixed - test cross-ESP operations
3. **If everything works**: ✅ All done! Update is complete

4. **If something is still broken**: 
   - Share browser console errors
   - Share screenshot of what you see
   - Check backend terminal for errors

---

**Quick Visual Check**:
- [ ] Links display with checkboxes
- [ ] Status badges show (orange/green)
- [ ] Orange bar appears when checking boxes
- [ ] Counter updates in real-time
- [ ] Can select from multiple ESPs
- [ ] One "Crawl Selected" button at top

---

**Last Updated**: July 15, 2026
