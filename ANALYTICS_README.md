# Usage Analytics System

## Overview

The app now includes a comprehensive analytics system that tracks user behavior and provides insights through an admin dashboard. Analytics data is retained permanently and scaled for concurrent usage.

## Features Tracked

### Key Performance Indicators (KPIs)
1. **Number of Sessions** - Total unique user sessions
2. **Unique Users** - Count of distinct IP addresses (actual unique visitors)
3. **Average Messages per Session** - Mean number of messages exchanged per session
4. **Feedback Tickets Submitted** - Total number of feedback submissions
5. **Average Session Time** - Mean duration of user sessions (in seconds)
6. **Average Message Length** - Mean character count of messages

### Breakdown Tables
1. **Usage by ESP** - Complete breakdown of all ESP selections with counts, ordered by popularity
2. **Sessions by Country** - Geographic breakdown based on IP address with flag emojis (🏴‍☠️ for Unknown)

### Time Range Filters
- **All Time** - Complete historical data (no percentage changes shown)
- **Last 90 Days** - Data from the past 90 days (compared to previous 90 days)
- **Last 7 Days** - Data from the past week (compared to previous week)

### Percentage Change Indicators
- Green text (↑) indicates positive growth
- Red text (↓) indicates decline
- Percentages compare current period to equivalent previous period

## Technical Architecture

### Database Schema

**SQLite database** (`backend/analytics.db`) with the following tables:

1. **sessions** - User session tracking
   - session_id (PK)
   - start_time, end_time
   - country, ip_address

2. **messages** - Message-level tracking
   - session_id (FK)
   - role (user/assistant)
   - message_length
   - esp
   - timestamp

3. **esp_selections** - ESP selection tracking
   - session_id (FK)
   - esp
   - selected_at

4. **feedback** - Feedback submissions
   - session_id (FK)
   - email, esp, rating, comments
   - submitted_at

5. **daily_aggregates** - Pre-computed daily metrics for performance
   - date (PK)
   - total_sessions, total_messages, etc.
   - Updated once per day

### Performance Optimizations

1. **Batch Write Queue**
   - Thread-safe queue that batches writes
   - Flushes after 100 operations or 5 seconds
   - Prevents database contention under high load

2. **Daily Aggregation**
   - Metrics computed once per day
   - Reduces query complexity for historical data
   - Triggered on first session after 24-hour window

3. **Indexed Queries**
   - Indexes on session_id, timestamp, and date fields
   - Optimized for time-range queries

4. **IP Geolocation**
   - Uses ipapi.co free tier (1000 requests/day)
   - Falls back to "Unknown" on rate limit or error
   - Non-blocking, async friendly

## Backend Integration

### New Endpoints

**POST /api/session/init**
- Initializes a new session
- Returns session_id
- Captures IP for country detection

**POST /api/session/end**
- Marks session as ended
- Called on page unload

**POST /api/esp/select**
- Tracks ESP selection
- Body: `{ session_id, esp }`

**GET /api/admin/analytics**
- Returns analytics dashboard data
- Query param: `time_range` (all_time, last_90_days, last_7_days)

### Modified Endpoints

**POST /api/chat**
- Now accepts `session_id` in request body
- Tracks both user and assistant messages

**POST /api/feedback**
- Now accepts `session_id` in request body
- Tracks feedback in analytics database

## Frontend Integration

### Session Tracking

Session lifecycle:
1. Page load → `initializeSession()` → creates session_id
2. User interactions → tracked via session_id
3. Page unload → `beforeunload` → ends session

### Analytics Dashboard

Located in Admin Panel → Usage Analytics tab

**Components:**
- Time range selector dropdown
- 6 KPI cards with:
  - Large value display
  - Percentage change indicator (green ↑ / red ↓)
  - **Integrated sparkline graph** showing trend over time
  - **Interactive hover tooltips** with exact values per date
- **Usage by ESP table** - Complete breakdown of ESP selections (positioned above country breakdown)
- **Sessions by Country table** - Geographic breakdown with flag emojis (🏴‍☠️ for Unknown countries)

**Auto-refresh:**
- Data refreshes when switching to Analytics tab
- Data refreshes when changing time range

**Sparkline Graphs:**
- Each KPI card includes a mini trend line chart
- Shows last 7 days (for 7-day range) or last 30 days (for 90-day range)
- Hover over the graph to see exact values for any date
- Tooltip displays date and value with appropriate unit
- Visual feedback with highlighted data point on hover
- Smooth line rendering with gradient fill underneath

## Setup Instructions

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export GEMINI_API_KEY="your-key-here"
```

3. Run backend:
```bash
python3 app.py
```

The analytics database will be created automatically on first run.

### Frontend Setup

1. Start frontend server:
```bash
cd frontend
python3 -m http.server 8000
```

2. Access app at `http://localhost:8000`

### Admin Access

1. Click "Admin" button in sidebar
2. Enter password: `RICHCSM`
3. Navigate to "Usage Analytics" tab
4. Select time range to view metrics

## Data Privacy & Compliance

- IP addresses are stored for country detection only
- No personal user data is tracked (except in feedback)
- Feedback submissions are opt-in only
- Session data expires can be configured with retention policies

## Scalability Considerations

### Current Capacity
- Batch write queue handles 100+ concurrent users
- Daily aggregation reduces query load
- SQLite suitable for small-to-medium traffic

### Future Enhancements for Scale
If traffic exceeds SQLite capacity:
1. Migrate to PostgreSQL/MySQL
2. Implement connection pooling
3. Add Redis for session caching
4. Use message queue (Celery/RabbitMQ) for async writes

## Maintenance

### Backup Analytics Data
```bash
cd backend
cp analytics.db analytics.db.backup
```

### Reset Analytics (use with caution)
```bash
cd backend
rm analytics.db
# Database will be recreated on next app start
```

### View Raw Data
```bash
cd backend
sqlite3 analytics.db
sqlite> SELECT * FROM sessions LIMIT 10;
```

## Troubleshooting

### Analytics not loading
- Check backend server is running
- Check browser console for API errors
- Verify admin password is correct

### Country showing as "Unknown"
- IP geolocation API may be rate limited
- Local/development IPs default to "Unknown"
- Check ipapi.co service status

### Percentage changes not showing
- Ensure time range is not "All Time"
- Verify sufficient historical data exists
- Check daily aggregates are being computed

## Future Roadmap

Potential enhancements:
- Export analytics to CSV
- Email digest reports
- Custom date range picker
- Real-time dashboard updates
- User retention cohort analysis
- Conversation quality metrics (sentiment analysis)
