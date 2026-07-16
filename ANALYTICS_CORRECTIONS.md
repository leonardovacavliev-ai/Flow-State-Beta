# Analytics Logic Corrections & Updates

## Overview

This document outlines the three major corrections made to the analytics system based on clarifications about business requirements and user experience improvements.

---

## 1. Fixed ESP Usage Tracking Logic

### Problem
ESP usage was tracking **clicks/selections** instead of actual **conversations**.

**Previous Logic:**
- Counted every time a user clicked on an ESP in the sidebar
- Resulted in inflated numbers (clicking Klaviyo 10 times = 10 "usages")
- Didn't reflect actual engagement with the ESP

**Corrected Logic:**
- Tracks unique **conversations** = unique `session_id + ESP` combinations where messages were sent
- Only counts when a user actually sends a message with that ESP selected
- Accurately reflects meaningful engagement

### Technical Implementation

**Backend (`analytics.py`):**

```python
# OLD - Counted selections/clicks
SELECT esp, COUNT(*) as count
FROM esp_selections
WHERE selected_at >= ?
GROUP BY esp

# NEW - Counts conversations (session+ESP with messages)
SELECT esp, COUNT(DISTINCT session_id) as count
FROM messages
WHERE timestamp >= ? AND role = 'user'
GROUP BY esp
```

**Frontend:**
- Changed table header from "Selections" to "Conversations"
- Changed data field from `item.selections` to `item.conversations`

### Result
The ESP breakdown table now shows:
```
ESP              | Conversations
Klaviyo          |    45
DotDigital       |    23
Attentive        |    12
Other/Webhook    |     8
```

Each number represents a unique conversation (user actually used that ESP to send messages).

---

## 2. Renamed Metric to "Average Messages per Conversation"

### Problem
The metric was called "Average messages per **session**" but sessions can contain multiple conversations.

**Scenario:**
- User opens app (1 session)
- Selects Klaviyo, sends 3 messages
- Switches to DotDigital, sends 5 messages
- This is 1 session but 2 conversations

The previous calculation divided total messages by sessions, which was inaccurate.

### Corrected Logic

**Calculation Method:**
- A **conversation** = unique `session_id + ESP` combination where user messages exist
- Count distinct conversations across the time period
- Divide total messages by conversation count

**Backend (`analytics.py`):**

```python
# Count unique conversations
SELECT COUNT(DISTINCT session_id || '-' || esp) as conversation_count
FROM messages
WHERE DATE(timestamp) = ? AND role = 'user'

# Calculate average
avg_messages_per_conversation = total_messages / total_conversations
```

**Database Schema:**
- Renamed column: `avg_messages_per_session` → `avg_messages_per_conversation`
- Automatic migration included in code

**Frontend:**
- Updated KPI card label
- Updated sparkline label to "Avg Messages"

### Result
More accurate metric that reflects actual conversation patterns:
- Old: "20 messages / 5 sessions = 4.0 avg per session"
- New: "20 messages / 8 conversations = 2.5 avg per conversation"

The new metric better represents how users interact with each ESP in distinct conversations.

---

## 3. Changed Default Admin Tab to Usage Analytics

### Problem
Admin panel defaulted to "ESP Management" tab, but most frequent use case is viewing analytics.

### Changes Made

**Tab Order:**
```
OLD: [ESP Management*] [Usage Analytics]
NEW: [Usage Analytics*] [ESP Management]
     (* = active by default)
```

**On Admin Login:**
- Analytics tab is active and visible
- Analytics data loads immediately
- No need to click to see metrics

**Benefits:**
- Faster access to most commonly viewed information
- Analytics-first approach for data-driven decisions
- ESP Management still easily accessible via tab

### Technical Implementation

**HTML:**
- Swapped tab order in navigation
- Made `usageAnalyticsTab` default (no `hidden` class)
- Made `espManagementTab` hidden by default

**JavaScript:**
- Call `loadAnalytics()` on admin login
- Call `loadESPManagement()` only when switching to that tab
- Both tabs load their data when accessed

---

## Database Migrations

### Automatic Migrations Included

The code includes automatic migrations that run on backend startup:

1. **Add `unique_users` column** (if missing)
2. **Rename `avg_messages_per_session` to `avg_messages_per_conversation`** (if needed)

```python
try:
    cursor.execute("ALTER TABLE daily_aggregates RENAME COLUMN avg_messages_per_session TO avg_messages_per_conversation")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Already renamed
```

### For Existing Data

If you have existing analytics data:

**Option 1: Recalculate (Recommended)**
Run daily aggregation for past dates to populate new metrics correctly:

```python
from datetime import datetime, timedelta
from analytics import calculate_daily_aggregates

# Recalculate last 30 days
for i in range(30):
    date = datetime.now() - timedelta(days=i)
    calculate_daily_aggregates(date)
```

**Option 2: Fresh Start**
If historical accuracy isn't critical:

```bash
cd backend
rm analytics.db
python3 app.py  # Creates fresh database with correct schema
```

---

## Testing the Changes

### 1. Test ESP Conversation Tracking

**Scenario:**
1. Open app, select Klaviyo
2. Send 3 messages (1 conversation)
3. Switch to DotDigital  
4. Send 2 messages (1 conversation)
5. Click back to Klaviyo (no new conversation yet)
6. Click back to DotDigital (no new conversation yet)
7. Send 1 more message in DotDigital (same conversation)

**Expected ESP Breakdown:**
```
Klaviyo: 1 conversation
DotDigital: 1 conversation
```

**NOT:**
```
Klaviyo: 2 (would be old click-tracking behavior)
DotDigital: 2 (would be old click-tracking behavior)
```

### 2. Test Average Messages per Conversation

**Scenario:**
- Session A: User sends 4 messages in Klaviyo
- Session B: User sends 6 messages in Klaviyo, then 2 in DotDigital

**Calculation:**
- Total messages: 12 (assistant messages don't count)
- Total conversations: 3 (SessionA+Klaviyo, SessionB+Klaviyo, SessionB+DotDigital)
- Average: 12 / 3 = 4.0

### 3. Test Default Tab Behavior

**Steps:**
1. Open app
2. Click "Admin" button
3. Enter password
4. Click "Login"

**Expected:**
- Usage Analytics tab is active (blue underline)
- Analytics data is loading/loaded
- Can see KPI cards and metrics
- ESP Management tab is inactive (gray text)

---

## Updated KPIs Summary

The dashboard now shows:

### 6 KPI Cards (with sparklines)
1. **Number of Sessions** - Total unique user sessions
2. **Unique Users** - Distinct IP addresses
3. **Avg Messages per Conversation** ✨ (renamed from "per session")
4. **Feedback Tickets** - Total feedback submissions
5. **Avg Session Time** - Mean duration in seconds
6. **Avg Message Length** - Mean character count

### 2 Breakdown Tables
1. **Usage by ESP** ✨ (tracks conversations, not clicks)
   - Shows all ESPs with conversation counts
   - Ordered by most used to least used
2. **Sessions by Country**
   - Geographic breakdown with flag emojis

---

## Files Modified

### Backend
- **`backend/analytics.py`**
  - Fixed ESP breakdown query to count conversations
  - Renamed column and updated calculations
  - Added automatic migrations

### Frontend
- **`frontend/index.html`**
  - Swapped tab order (Analytics first)
  - Renamed metric label
  - Changed table header "Selections" → "Conversations"

- **`frontend/app.js`**
  - Load analytics on admin login
  - Updated data field references
  - Load ESP management only when tab clicked

### Documentation
- **`ANALYTICS_README.md`** - Updated metrics descriptions
- **`ANALYTICS_CORRECTIONS.md`** - This file

---

## Backwards Compatibility

These changes are **backwards compatible** with existing installations:

✅ Automatic database migrations
✅ Graceful handling of missing columns
✅ No manual intervention required
✅ Existing data preserved

Just restart the backend and the migrations run automatically.

---

## Summary of Business Logic

### What We Track Now

**Conversations (Not Clicks):**
- ESP breakdown counts unique `session + ESP + messages sent`
- Reflects actual engagement, not just interface clicks
- More meaningful for business insights

**Conversations (Not Sessions):**
- Average messages calculated per conversation
- Accounts for multiple ESP uses within one session
- More accurate representation of user behavior

**Analytics First:**
- Most common admin task is now default
- Faster access to key metrics
- Better user experience

---

## Questions & Answers

**Q: Why count conversations instead of clicks?**
A: Clicks don't indicate usage. A user might click 10 ESPs while exploring, but only use 2. Conversations = actual work done.

**Q: What's the difference between a session and a conversation?**
A: 
- **Session** = One browser tab/window from open to close
- **Conversation** = One session using one ESP to send messages
- A session can have multiple conversations (use multiple ESPs)

**Q: Will my existing analytics data be wrong?**
A: Historical ESP data may be inflated (counted clicks). Run recalculation script or accept that new data from today forward will be accurate.

**Q: Can I switch back to the old behavior?**
A: Not recommended, but you could revert the git commits. The new logic is more accurate for business decisions.

---

## Next Steps

1. ✅ Restart backend to apply migrations
2. ✅ Test with new session data
3. ✅ Verify ESP breakdown shows conversations
4. ✅ Verify average messages calculation is accurate
5. ✅ Confirm analytics loads by default
6. Optional: Recalculate historical data for consistency
