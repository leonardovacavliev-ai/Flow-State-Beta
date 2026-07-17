# Deploy ESP Restoration to Production

Your ESPs are restored **locally** but the **deployed version** needs to be updated.

## The Issue

- ✅ Local database (PostgreSQL): Has all 8 ESPs restored
- ❌ Deployed app: Still running old code before ESP restoration  
- Frontend showing "No ESPs found" because it's loading from the deployed server

## Quick Fix

Your code is already pushed to GitHub (commit 546d928). The deployed app needs to:

1. **Pull the latest code** from GitHub
2. **Run the restoration script** against the production database

## Deploy Steps

### Step 1: Trigger Redeploy

Your app should auto-redeploy from the GitHub push. Check your deployment platform:

- **Railway**: Should auto-deploy from GitHub push (wait 2-3 min)
- **Replit**: Click "Pull from GitHub" then "Run"  
- **Vercel/Netlify**: Should auto-deploy

### Step 2: Restore ESPs to Production Database

The restoration script needs to run against your **production** PostgreSQL:

```bash
# Set production DATABASE_URL then run:
python backend/restore_esps.py
```

Or use Railway CLI:
```bash
railway run python backend/restore_esps.py
```

## Verification

Visit your deployed URL → ESPs should appear in left sidebar

## Need Help?

Check production database:
```sql
SELECT COUNT(*) FROM esps;  -- Should return 8
```

If empty, run `restore_esps.py` against production.
