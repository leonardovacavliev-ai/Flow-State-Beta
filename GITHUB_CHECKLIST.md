# GitHub & Deployment Checklist

## ✅ Pre-Push Checklist

### 1. Security Review
- [ ] Removed any hardcoded API keys from code
- [ ] Added `.gitignore` (✅ created)
- [ ] Created `.env.example` template (✅ created)
- [ ] Verified no sensitive data in commit history

### 2. Configuration Files
- [ ] `.gitignore` - Excludes databases, secrets, cache (✅ created)
- [ ] `.env.example` - Environment variable template (✅ created)
- [ ] `Procfile` - Heroku deployment config (✅ created)
- [ ] `runtime.txt` - Python version specification (✅ created)
- [ ] `Dockerfile` - Container configuration (✅ created)

### 3. Documentation
- [ ] `README.md` - Updated with deployment links (✅ updated)
- [ ] `QUICK_DEPLOY.md` - Fast deployment guide (✅ created)
- [ ] `DEPLOYMENT.md` - Comprehensive deployment options (✅ created)
- [ ] `CLAUDE.md` - Production architecture (✅ exists)

### 4. Code Updates
- [ ] Updated `backend/app.py` for cloud deployment (✅ PORT env var support)
- [ ] Tested locally with `./start.sh`

---

## 📋 GitHub Setup Steps

### Step 1: Initialize Git (Run setup script)

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"
./setup-github.sh
```

**What it does:**
- Initializes git repository
- Stages all files
- Creates initial commit with descriptive message
- Shows next steps

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. **Repository name**: `esp-loyalty-helper` (or your choice)
3. **Description**: "AI-powered assistant for ESP loyalty campaign setup"
4. **Visibility**: 
   - ✅ **Private** (recommended initially - contains config)
   - ⚠️ Public (only if removing sensitive data first)
5. **DO NOT** initialize with:
   - ❌ README (we have one)
   - ❌ .gitignore (we have one)
   - ❌ License (add later if needed)
6. Click **"Create repository"**

### Step 3: Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/esp-loyalty-helper.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Verify Upload

1. Visit your repository URL
2. Check that files are there
3. Verify `.gitignore` is working (no `.db`, `__pycache__`, etc.)

---

## 🚀 Deployment Options (Choose One)

### Option A: Railway (Recommended)
**Time:** 5 minutes | **Cost:** Free tier, then ~$5/month

```bash
# After pushing to GitHub:
1. Go to https://railway.app
2. "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables (see below)
5. Deploy automatically
```

### Option B: Replit (Fastest)
**Time:** 2 minutes | **Cost:** Free

```bash
1. Go to https://replit.com
2. "Import from GitHub"
3. Paste your GitHub URL
4. Add secrets in 🔒 panel
5. Click "Run"
```

### Option C: Google Cloud Run
**Time:** 10 minutes | **Cost:** Pay-per-request

```bash
gcloud run deploy esp-loyalty-helper \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=xxx,ANTHROPIC_API_KEY=xxx
```

### Option D: Heroku
**Time:** 10 minutes | **Cost:** Free tier (sleeps after 30 min)

```bash
heroku create your-app-name
heroku config:set GEMINI_API_KEY=xxx
heroku config:set ANTHROPIC_API_KEY=xxx
git push heroku main
```

---

## 🔑 Environment Variables (Required for All Platforms)

Add these to your deployment platform:

```bash
# Required
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Recommended
ADMIN_PASSWORD=RICHCSM
FLASK_DEBUG=0
PORT=8080  # Or platform default
```

---

## ⚠️ Important Notes

### Database Persistence
**Problem:** SQLite and ChromaDB use local files that don't persist in cloud deployments.

**Solutions:**
- **Testing:** Use Railway/Replit (data resets on restart - OK for demos)
- **Production:** Migrate to PostgreSQL + Pinecone (see `DEPLOYMENT.md` Phase 1)

### Security Checklist
Before making repository public:
- [ ] Change `ADMIN_PASSWORD` from default
- [ ] Set `FLASK_DEBUG=0` in production
- [ ] Review all files for hardcoded secrets
- [ ] Add rate limiting (see TODOs in `backend/app.py`)
- [ ] Enable HTTPS (automatic on most platforms)

### Files NOT in Git (Verify)
These should be excluded by `.gitignore`:
- `backend/analytics.db` (SQLite database)
- `backend/chroma_db/` (Vector database)
- `backend/app_config.json` (Config with possible secrets)
- `.env` (Local environment variables)
- `__pycache__/` (Python cache)
- `.DS_Store` (Mac system files)

---

## 🧪 Testing Your Deployment

1. **Access your URL** (from deployment platform)
2. **Test chat interface:**
   - Select an ESP (Klaviyo)
   - Ask: "How do I set up a welcome series?"
   - Verify AI response
3. **Test admin panel:**
   - Click "Admin" in sidebar
   - Enter password: `RICHCSM`
   - Verify ESP list loads
4. **Check logs** for errors:
   - Railway: Dashboard → Logs
   - Replit: Console tab
   - GCP: Cloud Logging

---

## 📊 Monitoring & Maintenance

### After Deployment

1. **Monitor logs** for errors
2. **Check analytics** (`/admin` → Analytics tab)
3. **Test all ESPs** in dropdown
4. **Verify crawled docs** are loading (Admin → ESP management)

### Regular Maintenance

- **Weekly:** Check error logs
- **Monthly:** Refresh ESP documentation (Admin → Refresh All)
- **As needed:** Add new ESPs, update documentation links

---

## 🆘 Troubleshooting

### "Module not found" errors
```bash
# Ensure requirements.txt is in backend/ folder
# Check deployment logs for pip install output
```

### "Database is locked" errors
```bash
# SQLite doesn't support concurrent writes
# Migrate to PostgreSQL for production
```

### Port binding errors
```bash
# Ensure app.py uses:
port = int(os.getenv('PORT', 5001))
app.run(host='0.0.0.0', port=port)
```

### API key errors
```bash
# Verify environment variables in deployment platform
# No quotes around values
# Check key permissions in Gemini/Anthropic consoles
```

---

## 📚 Additional Resources

- **Quick Deploy:** [QUICK_DEPLOY.md](QUICK_DEPLOY.md)
- **Full Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Architecture:** [CLAUDE.md](CLAUDE.md)
- **Features:** [README.md](README.md)

---

## ✨ Success!

Once deployed, you'll have:
- ✅ Code version controlled on GitHub
- ✅ Live app accessible via URL
- ✅ Admin panel for managing ESPs
- ✅ Analytics tracking usage
- ✅ Foundation for production scaling (see CLAUDE.md)

**Next Steps:**
1. Share the URL with stakeholders
2. Gather feedback
3. Plan database migration for production (CLAUDE.md Phase 1)
4. Add more ESPs as needed
