# Phase 4 Quick Start - ESP Database Migration

**Status**: ✅ Code complete and pushed to GitHub
**Next**: Apply schema and run migration on Railway

---

## What This Fixes

**Your Problem**:
> "I tried adding an ESP earlier and it was added during the session, but was deleted with the next deployment and had to add it manually."

**Solution**:
ESPs are now stored in PostgreSQL (not filesystem) and survive deployments.

---

## Quick Deploy (3 Steps)

### Step 1: Apply Database Schema

**SSH into Railway**:
```bash
railway run bash

# Run these commands in Railway shell:
cd backend
python3 -c "
from adapters.database.db_manager import get_database_adapter
db = get_database_adapter()
with open('schema_esp.sql', 'r') as f:
    db.execute_query(f.read(), fetch=False)
print('✓ Schema applied')
"
```

### Step 2: Migrate Existing ESPs

**Still in Railway shell**:
```bash
python3 migrate_esps_to_db.py
```

**Expected Output**:
```
✓ Database schema applied successfully
✓ Migrated 5 ESPs, skipped 0
✓ Added 30 links, skipped 0
✓ Total ESPs in database: 5
```

### Step 3: Verify

**Test admin panel**:
1. Open Railway app URL
2. Go to admin panel
3. ESPs should be listed (from database)
4. Add a new ESP (e.g., "Mailchimp")
5. Push any change to git (trigger redeploy)
6. Check admin panel again - **Mailchimp should still be there!** ✅

---

## What Was Implemented

### Database Schema
- `esps` table - ESP metadata
- `esp_documents` table - URLs with crawl tracking

### ESP Manager
- `create_esp()` - Add ESP to database
- `add_document()` - Add URL to ESP
- `list_esps()` - Get all ESPs
- Singleton: `get_esp_manager()`

### Admin Routes
- All `/api/admin/esp/*` endpoints now use database
- Backward compatible with filesystem (crawler unchanged)

### Migration Script
- Scans `docs/` folder
- Migrates ESPs to database
- Migrates URLs from CSV
- Tracks crawl status

---

## Configuration

**No changes needed!**
- Uses `DATABASE_PROVIDER=postgres` from Phase 2
- Uses `DATABASE_URL` from Railway
- API keys stay in environment variables (secure)

---

## Testing Locally (Optional)

**If you want to test before Railway deploy**:

```bash
# .env should have:
DATABASE_PROVIDER=postgres
DATABASE_URL=postgresql://...  # Railway connection

# Apply schema
cd backend
python3 -c "
from adapters.database.db_manager import get_database_adapter
db = get_database_adapter()
with open('schema_esp.sql', 'r') as f:
    db.execute_query(f.read(), fetch=False)
"

# Migrate data
python3 migrate_esps_to_db.py

# Start app
python3 app.py

# Test in browser
# Add ESP → Restart app → Verify ESP persists
```

---

## Rollback (If Needed)

**If something breaks**:

1. Comment out these lines in `backend/app.py`:
```python
# Lines 51-53
# from app_admin_esp_routes import register_esp_admin_routes
# register_esp_admin_routes(app, BASE_PATH, vectorizer)
```

2. Commit and push:
```bash
git add backend/app.py
git commit -m "Rollback to filesystem ESP routes"
git push origin main
```

Old filesystem routes will work again.

---

## Next Phase Options

**Phase 5: Containerization**
- Docker + docker-compose
- GitHub Actions CI/CD
- Multi-environment orchestration

**Phase 6: Authentication**
- Auth0/Clerk integration
- JWT tokens
- Multi-tenancy

Choose based on priority!

---

## Support

**Full Documentation**: [PHASE_4_ESP_DATABASE.md](PHASE_4_ESP_DATABASE.md)
**Implementation**: `backend/esp_manager.py`, `backend/app_admin_esp_routes.py`
**Migration**: `backend/migrate_esps_to_db.py`
**Schema**: `backend/schema_esp.sql`

---

## Summary

**What You Get**:
✅ Add ESP via admin → Stored in PostgreSQL
✅ Deploy to Railway → ESP persists
✅ No more manual re-adding after restart

**What Stays Same**:
✅ Admin UI unchanged (same UX)
✅ Crawler/vectorizer unchanged
✅ API keys stay in environment variables

**Deployment**:
1. Apply schema (1 command)
2. Run migration (1 script)
3. Test and verify

**Status**: Ready to deploy! 🚀
