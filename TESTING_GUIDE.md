# Testing Guide for Analytics System

## Quick Start Testing

### 1. Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
export GEMINI_API_KEY="your-api-key"
python3 app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python3 -m http.server 8000
```

Open browser to: `http://localhost:8000`

### 2. Generate Test Data

**Create multiple sessions:**
1. Open the app in a normal browser window
2. Select different ESPs (Klaviyo, DotDigital, etc.)
3. Send a few messages
4. Submit feedback (optional)
5. Close the tab (ends session)

**Repeat in incognito/private windows** to create multiple unique sessions.

### 3. View Analytics

1. Click "Admin" button in sidebar
2. Enter password: `RICHCSM`
3. Click "Usage Analytics" tab
4. Select time range: "All Time"

You should see:
- Number of sessions created
- Average messages per session
- Most selected ESP
- Feedback count
- Average session time
- Average message length
- Country breakdown (likely "Unknown" for localhost)

### 4. Test Time Range Filters

1. Keep app open for several days to generate historical data
2. Switch between time ranges:
   - **All Time** - No percentage changes shown
   - **Last 7 Days** - Shows % change vs previous 7 days
   - **Last 90 Days** - Shows % change vs previous 90 days

## Manual Testing Checklist

### Session Tracking
- [ ] New session created on page load
- [ ] Session ID stored in browser
- [ ] Session ends on page unload/close
- [ ] Multiple browser tabs create separate sessions
- [ ] Incognito mode creates new session

### Message Tracking
- [ ] User messages tracked with correct length
- [ ] Assistant messages tracked with correct length
- [ ] Messages associated with correct session
- [ ] ESP selection tracked for each message
- [ ] Message count increases in analytics

### ESP Selection Tracking
- [ ] Initial ESP selection tracked (Klaviyo by default)
- [ ] ESP change tracked when switching platforms
- [ ] Most selected ESP updates correctly
- [ ] Multiple selections in same session counted

### Feedback Tracking
- [ ] Feedback form includes session_id
- [ ] Feedback count increases in analytics
- [ ] Feedback saved to both CSV and database
- [ ] Optional session_id handled correctly

### Analytics Dashboard
- [ ] All 6 KPI cards display correct values
- [ ] Percentage changes display for non-"All Time" ranges
- [ ] Green (↑) for positive changes
- [ ] Red (↓) for negative changes
- [ ] Country breakdown table populates
- [ ] Time range selector updates data
- [ ] Loading state shows during data fetch

### Admin Panel
- [ ] Tab navigation works (ESP Management ↔ Usage Analytics)
- [ ] Tab styling updates on click
- [ ] Content sections show/hide correctly
- [ ] Analytics loads on first visit to tab
- [ ] Analytics refreshes when changing time range

## Automated Test Scenarios

### Scenario 1: High Traffic Simulation

Create Python script to simulate concurrent users:

```python
import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:5000/api"
ESPS = ['klaviyo', 'dotdigital', 'attentive', 'other_webhook']

def simulate_user():
    # Initialize session
    session = requests.post(f"{API_URL}/session/init").json()
    session_id = session['session_id']
    
    # Select random ESP
    esp = random.choice(ESPS)
    requests.post(f"{API_URL}/esp/select", json={
        'session_id': session_id,
        'esp': esp
    })
    
    # Send 3-7 messages
    num_messages = random.randint(3, 7)
    for i in range(num_messages):
        message = f"Test message {i} - " + "x" * random.randint(20, 200)
        requests.post(f"{API_URL}/chat", json={
            'message': message,
            'esp': esp,
            'session_id': session_id,
            'history': []
        })
        time.sleep(random.uniform(0.5, 2))
    
    # End session
    requests.post(f"{API_URL}/session/end", json={
        'session_id': session_id
    })
    
    print(f"Completed session: {session_id}")

# Run 50 concurrent users
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(simulate_user) for _ in range(50)]
    for future in futures:
        future.result()

print("Load test completed!")
```

**Expected Results:**
- All 50 sessions complete successfully
- No database lock errors
- Analytics dashboard shows 50+ sessions
- Batch write queue handles concurrent writes

### Scenario 2: Multi-Day Data Generation

```python
import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "backend/analytics.db"

def generate_historical_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generate data for past 30 days
    for days_ago in range(30, 0, -1):
        date = datetime.now() - timedelta(days=days_ago)
        
        # Create 10-20 sessions per day
        sessions_per_day = random.randint(10, 20)
        
        for _ in range(sessions_per_day):
            session_id = f"test-{date.date()}-{random.randint(1000, 9999)}"
            
            # Insert session
            cursor.execute("""
                INSERT INTO sessions (session_id, start_time, end_time, country)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                date.isoformat(),
                (date + timedelta(minutes=random.randint(2, 30))).isoformat(),
                random.choice(['USA', 'UK', 'Canada', 'Australia', 'Unknown'])
            ))
            
            # Insert messages
            num_messages = random.randint(2, 10)
            for _ in range(num_messages):
                cursor.execute("""
                    INSERT INTO messages (session_id, role, message_length, esp, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    random.choice(['user', 'assistant']),
                    random.randint(20, 300),
                    random.choice(['klaviyo', 'dotdigital', 'attentive', 'other_webhook']),
                    date.isoformat()
                ))
    
    conn.commit()
    conn.close()
    print("Historical data generated!")

generate_historical_data()
```

**Expected Results:**
- 300+ sessions created across 30 days
- Time range filters show different data
- Percentage changes display correctly
- Daily aggregates computed accurately

## Edge Cases to Test

### Empty State
- [ ] Dashboard shows "No data available" when no sessions exist
- [ ] Country table shows empty state
- [ ] KPI cards show "-" or "0"

### Single Session
- [ ] Percentage changes show correctly (or 100% if comparing to 0)
- [ ] Most selected ESP shows single ESP
- [ ] Average calculations work with n=1

### Long Session
- [ ] Session duration calculated correctly for multi-hour sessions
- [ ] Messages span across multiple hours
- [ ] Session end time updates correctly

### Rapid ESP Switching
- [ ] Multiple ESP selections in same session tracked
- [ ] Most selected ESP aggregates correctly
- [ ] No duplicate tracking issues

### Special Characters
- [ ] Messages with emojis tracked correctly
- [ ] Long messages (>5000 chars) handled
- [ ] SQL injection attempts sanitized

## Performance Testing

### Database Query Performance
```bash
cd backend
sqlite3 analytics.db

-- Test query speed
.timer on

-- Sessions by date range
SELECT COUNT(*) FROM sessions 
WHERE start_time >= date('now', '-7 days');

-- Average message length
SELECT AVG(message_length) FROM messages 
WHERE timestamp >= date('now', '-90 days');

-- Country breakdown
SELECT country, COUNT(*) FROM sessions 
GROUP BY country;
```

**Expected Results:**
- Queries complete in <100ms with 1000+ sessions
- Queries complete in <500ms with 10000+ sessions

### Frontend Load Time
- [ ] Analytics dashboard loads in <2 seconds
- [ ] Time range change updates in <1 second
- [ ] No UI freezing during data load
- [ ] Smooth tab switching

## Regression Testing

After any code changes, verify:
- [ ] Session tracking still works
- [ ] Message tracking still works
- [ ] Analytics dashboard loads
- [ ] No console errors
- [ ] Backend starts without errors
- [ ] Database migrations work (if schema changed)

## Debugging Tips

### Check Backend Logs
```bash
cd backend
python3 app.py
# Watch for:
# "✓ Analytics database initialized"
# "✓ Calculated aggregates for YYYY-MM-DD"
```

### Inspect Database Directly
```bash
cd backend
sqlite3 analytics.db

-- Check sessions
SELECT * FROM sessions ORDER BY start_time DESC LIMIT 5;

-- Check messages
SELECT session_id, COUNT(*) FROM messages GROUP BY session_id;

-- Check daily aggregates
SELECT * FROM daily_aggregates ORDER BY date DESC;

-- Check aggregation metadata
SELECT * FROM aggregation_metadata;
```

### Browser Console
Open browser dev tools (F12) and check:
- Network tab for API calls
- Console for JavaScript errors
- Look for session_id in request payloads

### Common Issues

**"No data available" in dashboard:**
- Check if sessions exist: `SELECT COUNT(*) FROM sessions;`
- Check if daily aggregates exist: `SELECT COUNT(*) FROM daily_aggregates;`
- Manually trigger aggregation by waiting 24 hours or calling API

**Percentage changes not showing:**
- Verify time range is not "All Time"
- Check if previous period has data
- Run historical data generation script

**Country shows "Unknown":**
- Expected for localhost/127.0.0.1
- Check ipapi.co rate limits (1000/day)
- Test with real public IP

**Database locked errors:**
- Check if multiple backend instances running
- Verify batch queue is flushing
- Increase SQLite timeout in analytics.py

## Production Deployment Checklist

Before deploying to production:
- [ ] Change admin password from default
- [ ] Set up database backups
- [ ] Configure CORS for production domain
- [ ] Set up monitoring/alerting
- [ ] Test with production-like traffic
- [ ] Document backup/restore procedures
- [ ] Set up log rotation
- [ ] Configure rate limiting on analytics API
- [ ] Test IP geolocation with real IPs
- [ ] Set up SSL/HTTPS
