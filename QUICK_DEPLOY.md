# Quick Deploy Guide - Get Online in 10 Minutes

## Option 1: Railway (Recommended - Easiest)

**Time: ~5 minutes** | **Cost: Free tier available, then ~$5/month**

### Steps:

1. **Push to GitHub first** (see below)

2. **Deploy to Railway:**
   - Go to https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose `esp-loyalty-helper` repository
   - Railway auto-detects Python and starts deployment

3. **Add environment variables:**
   - In Railway dashboard → Variables tab
   - Add:
     ```
     GEMINI_API_KEY=your_actual_gemini_key
     ANTHROPIC_API_KEY=your_actual_anthropic_key
     ADMIN_PASSWORD=RICHCSM
     FLASK_DEBUG=0
     ```

4. **Get your URL:**
   - Railway generates: `your-app-name.railway.app`
   - Access immediately!

⚠️ **Important:** Local SQLite/ChromaDB won't persist on Railway. For production, you'll need to migrate to PostgreSQL + Pinecone (see DEPLOYMENT.md).

---

## Option 2: Replit (Fastest - No Setup)

**Time: ~2 minutes** | **Cost: Free**

### Steps:

1. Go to https://replit.com
2. Click "Create Repl" → "Import from GitHub"
3. Paste your GitHub repo URL
4. Replit auto-configures everything
5. Click "Run"
6. Add secrets (🔒 icon):
   - `GEMINI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `ADMIN_PASSWORD`
7. Share the generated URL (e.g., `esp-loyalty-helper.username.repl.co`)

**Pros:** Zero configuration  
**Cons:** URL changes on restart, limited resources

---

## Option 3: Google Cloud Run

**Time: ~10 minutes** | **Cost: Pay-per-request (~$0.40/million requests)**

### Prerequisites:
- Google Cloud account
- gcloud CLI installed

### Steps:

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Deploy (from project root)
gcloud run deploy esp-loyalty-helper \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key,ANTHROPIC_API_KEY=your_key,ADMIN_PASSWORD=RICHCSM

# 3. Access the URL provided (e.g., https://esp-loyalty-helper-xxxxx-uc.a.run.app)
```

---

## Step 0: Push to GitHub (Required for Options 1 & 3)

### Quick Commands:

```bash
# 1. Navigate to project
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"

# 2. Run setup script
./setup-github.sh

# 3. Create repo on GitHub: https://github.com/new
#    - Name: esp-loyalty-helper
#    - Private repository
#    - Don't initialize with README

# 4. Push to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/esp-loyalty-helper.git
git branch -M main
git push -u origin main
```

---

## Troubleshooting

### "Port already in use" error
- Another process is using port 5001
- Kill it: `lsof -ti:5001 | xargs kill -9`
- Or change port in `.env`: `PORT=5002`

### "Module not found" errors
- Check `requirements.txt` is in `backend/` folder
- Verify deployment platform installed dependencies

### Database errors in cloud
- **Root cause:** SQLite/ChromaDB use local files (ephemeral in cloud)
- **Quick fix:** Deploy on Railway/Replit for testing (data won't persist across restarts)
- **Production fix:** Migrate to PostgreSQL + Pinecone (see CLAUDE.md)

### API key errors
- Ensure environment variables are set correctly
- No quotes around keys in platform dashboards
- Check key permissions (Gemini/Anthropic consoles)

---

## Next Steps After Deployment

1. **Test the app:** Visit your deployed URL
2. **Access admin panel:** Add `/admin` to URL, login with password
3. **Monitor usage:** Check Railway/GCP logs for errors
4. **Plan database migration:** For production, see DEPLOYMENT.md Phase 1

---

## Comparison

| Platform | Speed | Cost | Persistence | Best For |
|----------|-------|------|-------------|----------|
| Railway | ⚡⚡⚡ | $ | No* | Quick demos |
| Replit | ⚡⚡⚡⚡ | Free | No* | Testing |
| GCP Run | ⚡⚡ | Pay/use | No* | Production |

\* Local databases don't persist. Migrate to cloud DBs for production.

---

## Questions?

- **Documentation:** See [DEPLOYMENT.md](DEPLOYMENT.md) for full options
- **Architecture:** See [CLAUDE.md](CLAUDE.md) for production migration plan
- **Troubleshooting:** Check deployment platform logs
