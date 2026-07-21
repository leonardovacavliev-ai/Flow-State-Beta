# Async Crawl - Deployment Checklist

Use this checklist to deploy the async crawl system step-by-step.

---

## Pre-Deployment

### 1. Code Review
- [ ] Read `ASYNC_CRAWL_IMPLEMENTATION_SUMMARY.md` - Understand what was built
- [ ] Read `ASYNC_CRAWL_QUICK_START.md` - Know the basics
- [ ] Review all new files in `git diff`
- [ ] Confirm backward compatibility (feature flag controlled)

### 2. Backup & Safety
- [ ] Railway auto-backs up database daily - confirm last backup date
- [ ] Create manual database backup (optional): Railway dashboard → PostgreSQL → Backups
- [ ] Note current commit hash: `git rev-parse HEAD`
- [ ] Verify you can instant rollback: Know how to set `USE_ASYNC_CRAWL=false`

### 3. Dependencies
- [ ] Confirm `apscheduler` added to `requirements.txt`
- [ ] Confirm Railway will auto-install on deploy
- [ ] No other dependencies needed (all existing)

---

## Deployment

### Step 1: Apply Database Migration ✅

**Command**:
```bash
python backend/migrations/apply_migration.py
```

**Expected output**:
```
============================================================
ASYNC CRAWL MIGRATION - Database Schema Update
============================================================

✓ Connected to database: postgres
Applying migration...
✓ Migration applied successfully

Verifying migration...
✓ Table 'crawl_jobs' exists
✓ Column 'esp_documents.crawl_job_id' exists
✓ Column 'esp_documents.is_crawling' exists
✓ Created 5 indexes on 'crawl_jobs' table

============================================================
MIGRATION COMPLETE ✓
============================================================
```

**Checkpoints**:
- [ ] Migration script ran without errors
- [ ] All 3 verification checks passed
- [ ] No SQL errors in output
- [ ] Can run script again (idempotent) - should say "already exists"

**If migration fails**:
- ❌ STOP - Don't deploy code
- Check database connection
- Check DATABASE_URL environment variable
- Review error message
- Script is idempotent - safe to re-run after fixing issue

---

### Step 2: Deploy Code (Feature Flag OFF) ✅

**Command**:
```bash
git status  # Verify all changes staged
git add .
git commit -m "feat: Add async crawl system (feature flag OFF by default)"
git push origin main
```

**Railway auto-deploys**:
- [ ] Wait for Railway build to complete (~2-3 minutes)
- [ ] Check Railway logs for "Build successful"
- [ ] Check app is running: Visit your Railway URL
- [ ] Frontend loads without errors

**Verify old crawl still works**:
- [ ] Navigate to admin panel (enter password)
- [ ] Go to ESP Management → Select Klaviyo
- [ ] Select 1 URL
- [ ] Click "Crawl Selected"
- [ ] Should work exactly as before (blocking, ~10-30 seconds)
- [ ] Checkmark appears next to URL when done

**Checkpoints**:
- [ ] App deployed successfully
- [ ] Frontend loads
- [ ] Admin panel accessible
- [ ] Old sync crawl works
- [ ] No errors in Railway logs
- [ ] USE_ASYNC_CRAWL not set (defaults to false)

**If deployment fails**:
- Check Railway logs for build errors
- Check for missing dependencies
- Verify requirements.txt includes `apscheduler`
- Can rollback: `git revert HEAD && git push origin main`

---

### Step 3: Enable Async Crawl (Staging/Test) ✅

**Railway Dashboard**:
1. [ ] Open Railway project
2. [ ] Click "Variables" tab
3. [ ] Click "Add Variable"
4. [ ] Name: `USE_ASYNC_CRAWL`
5. [ ] Value: `true`
6. [ ] Click "Add" (triggers automatic redeploy)
7. [ ] Wait for redeploy (~2-3 minutes)

**Check logs for worker startup**:
```
[DEBUG] ESP database routes (ASYNC) registered successfully
[ASYNC CRAWL] Worker started with 3 threads
[ASYNC CRAWL] Stale job cleanup scheduler started (every 5 minutes)
```

**Checkpoints**:
- [ ] Variable added
- [ ] App redeployed automatically
- [ ] Logs show "Worker started with 3 threads"
- [ ] Logs show "Stale job cleanup scheduler started"
- [ ] No error messages
- [ ] App still running

**If worker fails to start**:
- Check logs for import errors
- Verify database connection
- Check `apscheduler` installed
- Can rollback: Set `USE_ASYNC_CRAWL=false` → auto-redeploys

---

### Step 4: Test Async Crawl ✅

#### Test 1: Automated Test Suite
```bash
python backend/test_async_crawl.py
```

**Expected**:
```
✓ [PASS] Async endpoints exist
✓ [PASS] Queued 2 jobs
✓ [PASS] All 2 jobs completed successfully
✓ [PASS] Cancelled jobs
✓ [PASS] Stale job cleanup configured

PASSED: 5/5
✓ ALL TESTS PASSED
```

**Checkpoints**:
- [ ] Test script runs without errors
- [ ] All 5 tests pass
- [ ] Jobs completed successfully

#### Test 2: Single URL (Manual)
1. [ ] Admin panel → ESP Management → Klaviyo
2. [ ] Select 1 URL
3. [ ] Click "Crawl Selected"
4. [ ] **See progress tracker appear** (instead of blocking)
5. [ ] Progress bar shows 0% → 100%
6. [ ] Status shows "⏳ Processing" → "✓ Completed"
7. [ ] ESP list auto-refreshes
8. [ ] Checkmark appears next to URL

**Checkpoints**:
- [ ] Progress tracker appears
- [ ] Updates in real-time (every 2 seconds)
- [ ] Completes in ~10-20 seconds
- [ ] Auto-refreshes on completion
- [ ] No errors

#### Test 3: Multiple URLs (Stress Test)
1. [ ] Select 5-10 URLs across different ESPs
2. [ ] Click "Crawl Selected"
3. [ ] Progress tracker shows all jobs
4. [ ] Jobs process concurrently (3 at a time)
5. [ ] All complete within 40-60 seconds
6. [ ] Summary shows "X completed, Y failed"

**Checkpoints**:
- [ ] All jobs queued instantly (< 1 second)
- [ ] Progress updates every 2 seconds
- [ ] Multiple jobs processing simultaneously
- [ ] All complete successfully (or < 10% fail)
- [ ] No timeouts
- [ ] No errors

#### Test 4: Cancel Jobs
1. [ ] Select 10 URLs
2. [ ] Click "Crawl Selected"
3. [ ] Immediately click "Cancel All"
4. [ ] Pending jobs show "🚫 Cancelled"
5. [ ] Processing jobs finish normally

**Checkpoints**:
- [ ] Cancel button works
- [ ] Pending jobs cancelled
- [ ] No errors

#### Test 5: Error Handling
1. [ ] Add fake URL: `https://invalid-url-xyz.com/test`
2. [ ] Crawl it
3. [ ] Shows "✗ Failed" with error message
4. [ ] Other jobs continue normally

**Checkpoints**:
- [ ] Failed job shows error message
- [ ] Other jobs not affected
- [ ] Summary accurate (X failed)

#### Test 6: Concurrent Users (Optional)
1. [ ] Open admin in 2 browsers
2. [ ] Both select URLs
3. [ ] Both crawl simultaneously
4. [ ] Both see their own progress
5. [ ] No conflicts

**Checkpoints**:
- [ ] Both trackers work independently
- [ ] No duplicate jobs
- [ ] All complete successfully

---

### Step 5: Monitor Production (24 Hours) ✅

#### Day 1: Active Monitoring

**Every 2 hours, check**:
- [ ] Railway logs - no errors
- [ ] App still running
- [ ] Database connections < 20
- [ ] Memory usage stable

**SQL Queries** (Railway → PostgreSQL → Query):

1. **Job success rate**:
```sql
SELECT 
  COUNT(*) FILTER (WHERE status = 'completed') as completed,
  COUNT(*) FILTER (WHERE status = 'failed') as failed,
  COUNT(*) as total
FROM crawl_jobs
WHERE created_at > NOW() - INTERVAL '24 hours';
```
Target: Completed > 90%

2. **Stale jobs**:
```sql
SELECT COUNT(*) FROM crawl_jobs 
WHERE status = 'processing' 
AND started_at < NOW() - INTERVAL '10 minutes';
```
Target: 0

3. **Database connections**:
```sql
SELECT count(*) FROM pg_stat_activity;
```
Target: < 20

**Checkpoints**:
- [ ] Success rate > 90%
- [ ] No stale jobs
- [ ] Connections < 20
- [ ] No memory leaks
- [ ] No errors in logs

**If issues found**:
- See "Troubleshooting" section below
- Can instant rollback: `USE_ASYNC_CRAWL=false`

---

## Post-Deployment

### Verification (After 24 Hours)

- [ ] No user complaints
- [ ] No timeout errors reported
- [ ] Job completion rate > 90%
- [ ] Stale jobs = 0
- [ ] Database connections stable
- [ ] Memory usage stable
- [ ] All tests still pass

### Documentation Updates

- [ ] Update team wiki (if applicable)
- [ ] Share deployment guide with team
- [ ] Document any issues encountered
- [ ] Note any tuning changes made

### Cleanup (After 1 Week)

**If async crawl is stable**:
- [ ] Remove old sync code: Delete `backend/app_admin_esp_routes.py` (old version)
- [ ] Remove feature flag checks (always use async)
- [ ] Deploy cleanup commit

---

## Troubleshooting

### Issue: Jobs stuck in "processing"

**Check**:
```sql
SELECT id, url, started_at, worker_id, attempts
FROM crawl_jobs j
JOIN esp_documents d ON j.document_id = d.id
WHERE j.status = 'processing'
AND j.started_at < NOW() - INTERVAL '10 minutes';
```

**Fix**: Wait 5 minutes (auto-cleanup) or manually reset:
```sql
UPDATE crawl_jobs
SET status = 'pending', worker_id = NULL, started_at = NULL
WHERE status = 'processing'
AND started_at < NOW() - INTERVAL '10 minutes';
```

### Issue: No progress tracker in frontend

**Check**:
1. Browser console - JavaScript errors?
2. Network tab - `/api/admin/crawl-status` calls?
3. Backend logs - "Worker started"?

**Fix**:
- Clear browser cache (Cmd+Shift+Delete)
- Hard refresh (Cmd+Shift+R)
- Verify `USE_ASYNC_CRAWL=true`

### Issue: High database connections

**Check**:
```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```

**Fix**: Reduce worker threads:
```bash
# Railway Variables
CRAWL_WORKER_THREADS=2
```

### Issue: Worker not starting

**Check logs for**:
- Import errors (missing dependencies)
- Database connection errors
- Permission errors

**Fix**:
- Check `apscheduler` installed
- Check database connection
- Check Railway logs for specific error

---

## Rollback Procedures

### Instant Rollback (< 1 minute)

**Railway Dashboard**:
1. Variables → `USE_ASYNC_CRAWL`
2. Change to `false`
3. Save (auto-redeploys)

**Result**: Old sync crawl resumes, no data loss

### Full Rollback (< 5 minutes)

**Revert code**:
```bash
git revert HEAD
git push origin main
```

**Railway auto-redeploys to previous version**

### Database Cleanup (Optional)

**Only if removing async crawl permanently**:
```sql
DROP TABLE IF EXISTS crawl_jobs;
ALTER TABLE esp_documents DROP COLUMN IF EXISTS crawl_job_id;
ALTER TABLE esp_documents DROP COLUMN IF EXISTS is_crawling;
```

---

## Success Criteria

### Deployment Success ✅
- [x] Migration applied cleanly
- [x] Code deployed without errors
- [x] Worker started successfully
- [x] Old sync crawl still works (flag OFF)
- [x] New async crawl works (flag ON)
- [x] All tests pass
- [x] No errors in logs

### Production Success (24 hours) ⏳
- [ ] No timeouts reported
- [ ] Job completion rate > 90%
- [ ] Stale jobs = 0
- [ ] Database connections < 20
- [ ] Memory usage stable
- [ ] User feedback positive

---

## Sign-Off

**Deployed by**: _________________  
**Date**: _________________  
**Time**: _________________  
**Railway URL**: _________________  
**Commit hash**: _________________  

**Verified by**: _________________  
**Date**: _________________  

**Notes**:
_______________________________________________
_______________________________________________
_______________________________________________

---

## Quick Reference

**Enable async**: `USE_ASYNC_CRAWL=true`  
**Disable async**: `USE_ASYNC_CRAWL=false`  
**Test suite**: `python backend/test_async_crawl.py`  
**Check jobs**: `SELECT status, COUNT(*) FROM crawl_jobs GROUP BY status;`  
**Reset stale**: `UPDATE crawl_jobs SET status='pending' WHERE status='processing' AND started_at < NOW() - INTERVAL '10 minutes';`  

**Full guides**:
- `ASYNC_CRAWL_QUICK_START.md` - 1-page reference
- `ASYNC_CRAWL_DEPLOYMENT_GUIDE.md` - Complete guide
- `ASYNC_CRAWL_IMPLEMENTATION_SUMMARY.md` - Technical details

---

**Ready to deploy!** 🚀
