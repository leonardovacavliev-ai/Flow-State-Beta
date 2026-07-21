# Async Crawl - Quick Start

## TL;DR

Enable async crawl in 3 steps:

```bash
# 1. Apply migration
python backend/migrations/apply_migration.py

# 2. Set environment variable
USE_ASYNC_CRAWL=true

# 3. Restart app
# Railway: Auto-restarts on variable change
# Local: Ctrl+C and run ./start.sh
```

## Test It Works

```bash
# Run test suite
python backend/test_async_crawl.py
```

Or manually:
1. Open admin panel
2. Select 5 URLs
3. Click "Crawl Selected"
4. See progress bar with real-time updates ✅

## Rollback

```bash
# Disable async crawl
USE_ASYNC_CRAWL=false
```

That's it! Old sync crawl resumes.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_ASYNC_CRAWL` | `false` | Enable async crawl |
| `CRAWL_WORKER_THREADS` | `3` | Worker thread count |

## What Changed

**Before**:
- Crawl 10 URLs → 60s blocking request → timeout ❌

**After**:
- Crawl 10 URLs → Queue in < 1s → Progress bar → Done in 40-60s ✅

## Architecture

```
User clicks "Crawl"
  ↓ (< 1 second)
Create jobs in PostgreSQL → Return job IDs
  ↓
Frontend polls /crawl-status every 2s
  ↓ (in parallel)
Background workers process jobs
  ↓
Progress bar updates in real-time
  ↓
Auto-refreshes when complete
```

## Files Changed

**Backend**:
- `backend/migrations/001_create_crawl_jobs.sql` - Database schema
- `backend/workers/crawl_worker.py` - Background worker
- `backend/app_admin_esp_routes_async.py` - Async API endpoints
- `backend/app.py` - Worker startup, feature flag

**Frontend**:
- `frontend/crawl-progress-tracker.js` - Progress UI
- `frontend/app.js` - Auto-detection, polling
- `frontend/styles.css` - Progress bar styles

**Docs**:
- `ASYNC_CRAWL_DEPLOYMENT_GUIDE.md` - Full guide
- `ASYNC_CRAWL_QUICK_START.md` - This file

## Monitoring

**Check job status**:
```sql
SELECT status, COUNT(*) 
FROM crawl_jobs 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;
```

**Check stale jobs** (should be 0):
```sql
SELECT COUNT(*) FROM crawl_jobs 
WHERE status = 'processing' 
AND started_at < NOW() - INTERVAL '10 minutes';
```

## Troubleshooting

**Jobs stuck?**
- Wait 5 min for auto-cleanup
- Or manually reset: `UPDATE crawl_jobs SET status='pending' WHERE status='processing'`

**No progress bar?**
- Clear browser cache
- Check `USE_ASYNC_CRAWL=true`
- Check backend logs for worker startup

**High DB connections?**
- Reduce `CRAWL_WORKER_THREADS=2`

## Support

- Full guide: [ASYNC_CRAWL_DEPLOYMENT_GUIDE.md](ASYNC_CRAWL_DEPLOYMENT_GUIDE.md)
- Implementation plan: [ASYNC_CRAWL_IMPLEMENTATION_PLAN.md](ASYNC_CRAWL_IMPLEMENTATION_PLAN.md)
- Test script: `backend/test_async_crawl.py`

---

**Ready to deploy!** 🚀
