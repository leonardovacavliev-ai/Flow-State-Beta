# Hotfix: Column Name Reference Error

## Issue
When filtering analytics by "Last 90 Days", the following error appeared:
```
Error loading analytics: no such column: avg_messages_per_session
```

## Root Cause
The sparkline query was still referencing the old column name `avg_messages_per_session` instead of the renamed `avg_messages_per_conversation`.

## Fix Applied
Updated two references in `backend/analytics.py`:

1. **Line ~643** - SELECT query for sparkline data:
   ```python
   # CHANGED FROM:
   avg_messages_per_session,
   
   # CHANGED TO:
   avg_messages_per_conversation,
   ```

2. **Line ~658** - Accessing column value:
   ```python
   # CHANGED FROM:
   'avg_messages': [round(row['avg_messages_per_session'], 1) for row in daily_data],
   
   # CHANGED TO:
   'avg_messages': [round(row['avg_messages_per_conversation'], 1) for row in daily_data],
   ```

## Why This Happened
The sparkline feature was added after the column rename, and these queries were using the old column name. The error only appeared when:
- User selected "Last 90 Days" or "Last 7 Days" (which fetch sparkline data)
- The daily_aggregates table had the renamed column
- The migration had already run

The "All Time" filter didn't use sparklines, so it worked fine.

## Testing the Fix

### Before Fix
```bash
# Select "Last 90 Days" in analytics dropdown
# Error: "no such column: avg_messages_per_session"
```

### After Fix
```bash
cd backend
python3 app.py  # Restart backend

# In browser:
# 1. Open admin panel
# 2. Go to Usage Analytics
# 3. Select "Last 90 Days"
# ✅ Should load successfully with sparklines
# 4. Select "Last 7 Days"  
# ✅ Should load successfully with sparklines
# 5. Select "All Time"
# ✅ Should load successfully (no sparklines shown)
```

## Verification Steps

1. **Check column exists:**
   ```bash
   cd backend
   sqlite3 analytics.db
   sqlite> PRAGMA table_info(daily_aggregates);
   # Should show "avg_messages_per_conversation" column
   ```

2. **Test all time ranges:**
   - All Time ✅
   - Last 90 Days ✅
   - Last 7 Days ✅

3. **Verify sparklines render:**
   - Hover over sparklines should show tooltips
   - All 6 KPI cards should have working sparklines

## Files Modified
- `backend/analytics.py` (lines ~643 and ~658)

## Related
- Original column rename: See `ANALYTICS_CORRECTIONS.md`
- Migration code: Lines 149-154 in `analytics.py`
- Database schema: Line 132 in `analytics.py`

## Prevention
All column name changes should include:
1. Database schema update
2. Migration code
3. All SELECT queries (including aggregations)
4. All INSERT/UPDATE queries
5. Frontend data field references
6. Search codebase for old column name before committing

Use this command to find all references:
```bash
grep -r "old_column_name" backend/ --include="*.py"
```
