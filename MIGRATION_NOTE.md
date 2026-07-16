# Database Migration Note

## Changes in Latest Update

### New Features Added
1. **Unique Users Metric** - Tracks distinct IP addresses to show actual unique visitors
2. **Country Flag Emojis** - Visual country indicators in the dashboard (🏴‍☠️ for Unknown)

### Database Schema Changes

The `daily_aggregates` table now includes a new column:
- `unique_users INTEGER DEFAULT 0`

### Automatic Migration

The migration is **automatic** and happens when you restart the backend. The code includes:

```python
# Add unique_users column if it doesn't exist (migration)
try:
    cursor.execute("ALTER TABLE daily_aggregates ADD COLUMN unique_users INTEGER DEFAULT 0")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Column already exists
```

### If You Have Existing Data

If you have existing analytics data, you'll need to:

1. **Recalculate Daily Aggregates** to populate the new `unique_users` field:

```python
# Run this script to backfill unique_users for existing data
import sqlite3
from datetime import datetime, timedelta
import sys
sys.path.append('backend')
from analytics import calculate_daily_aggregates

DB_PATH = "backend/analytics.db"

# Get all dates with data
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT date FROM daily_aggregates ORDER BY date")
dates = [row[0] for row in cursor.fetchall()]
conn.close()

# Recalculate for each date
for date_str in dates:
    date = datetime.fromisoformat(date_str)
    print(f"Recalculating {date_str}...")
    calculate_daily_aggregates(date)

print("Migration complete!")
```

2. **Or Start Fresh** (if you don't need historical data):

```bash
cd backend
rm analytics.db
python3 app.py  # Will create new database with correct schema
```

### No Migration Needed If:
- This is a fresh installation
- You haven't collected any analytics data yet
- You're okay with unique_users showing 0 for historical data

### Verifying the Migration

After restarting the backend, check the logs for:
```
✓ Analytics database initialized
```

Then verify in SQLite:
```bash
cd backend
sqlite3 analytics.db
sqlite> PRAGMA table_info(daily_aggregates);
# Should see unique_users in the column list
```

### Country Flag Mapping

The frontend now includes a comprehensive country-to-flag mapping covering 50+ countries. The mapping includes:

- North America: 🇺🇸 🇨🇦 🇲🇽
- Europe: 🇬🇧 🇩🇪 🇫🇷 🇮🇹 🇪🇸 and more
- Asia-Pacific: 🇯🇵 🇨🇳 🇮🇳 🇦🇺 and more
- Middle East: 🇮🇱 🇸🇦 🇦🇪 🇹🇷
- Latin America: 🇧🇷 🇦🇷 🇨🇱 🇨🇴
- **Unknown/Localhost: 🏴‍☠️ (Pirate flag)**

If a country is not in the mapping, it defaults to the pirate flag 🏴‍☠️.

### Dashboard Updates

The Usage Analytics dashboard now shows:
- **7 KPI cards** (added Unique Users)
- **Country flags** next to each country name in the breakdown table
- **Pirate flag** 🏴‍☠️ for Unknown countries (typically localhost/development)

### Testing the New Features

1. Start the backend:
```bash
cd backend
python3 app.py
```

2. Generate some test sessions with different IPs (or use the load testing script)

3. Open Admin Panel → Usage Analytics

4. Verify:
   - Unique Users card shows distinct IP count
   - Country breakdown shows flags next to country names
   - Unknown countries show 🏴‍☠️

### Rollback Instructions

If you need to rollback:

1. Stop the backend
2. Restore from backup:
```bash
cd backend
cp analytics.db.backup analytics.db
```

3. Checkout previous version of code files:
```bash
git checkout HEAD~1 backend/analytics.py
git checkout HEAD~1 frontend/app.js
git checkout HEAD~1 frontend/index.html
```

### Questions?

Check the logs:
```bash
cd backend
python3 app.py 2>&1 | tee app.log
```

Or inspect the database directly:
```bash
cd backend
sqlite3 analytics.db
sqlite> SELECT * FROM daily_aggregates LIMIT 1;
```
