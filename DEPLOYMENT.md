# Deployment Guide

## Prerequisites

- GitHub account
- Python 3.8+
- Git installed locally

## 1. GitHub Setup

### A. Initialize Git Repository

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"
git init
git add .
git commit -m "Initial commit: ESP Loyalty Helper App"
```

### B. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `esp-loyalty-helper` (or your preferred name)
3. Description: "AI-powered assistant for setting up loyalty campaigns in ESPs"
4. Choose **Private** (recommended initially - contains config files)
5. **Do NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### C. Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/esp-loyalty-helper.git
git branch -M main
git push -u origin main
```

## 2. Local Deployment Options

### Option A: Run Locally (Testing)

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start servers
./start.sh

# 4. Access at http://localhost:8000
```

## 3. Cloud Deployment Options

### Option A: Heroku (Easiest - Free Tier Available)

**Setup:**

1. Create `Procfile`:
```
web: cd backend && python app.py
```

2. Create `runtime.txt`:
```
python-3.11.0
```

3. Deploy:
```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
heroku login
heroku create your-app-name
heroku config:set GEMINI_API_KEY=your_key
heroku config:set ANTHROPIC_API_KEY=your_key
heroku config:set ADMIN_PASSWORD=RICHCSM
git push heroku main
```

**Limitations:**
- Free tier sleeps after 30 min inactivity
- Local SQLite/ChromaDB won't work (files are ephemeral)
- Need to migrate to PostgreSQL + cloud vector DB

---

### Option B: Railway (Modern Alternative)

1. Go to https://railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables (GEMINI_API_KEY, etc.)
5. Railway auto-detects Python and deploys

**Pricing:** ~$5/month for basic usage

---

### Option C: Google Cloud Run (Production-Ready)

**Dockerfile** (create this):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend ./backend
COPY frontend ./frontend
COPY docs ./docs
COPY ESP_Support_Links\ -\ Sheet1.csv .

# Expose port
EXPOSE 8080
ENV PORT=8080

# Run app
CMD ["python", "backend/app.py"]
```

**Deploy:**

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud run deploy esp-loyalty-helper \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key,ANTHROPIC_API_KEY=your_key
```

**Pricing:** Pay-per-request, ~$0.40/million requests

---

### Option D: AWS (Enterprise)

See CLAUDE.md "Target Architecture" section for full AWS deployment:
- ECS/Fargate for containers
- RDS PostgreSQL
- ElastiCache Redis
- Pinecone for vector DB
- S3 + CloudFront for frontend

---

## 4. Database Migration (Required for Cloud)

Current local databases won't work in cloud (files are ephemeral).

### Quick Fix: External Databases

**PostgreSQL (Replace SQLite):**
- Free tier: [ElephantSQL](https://www.elephantsql.com/) (20MB free)
- Paid: AWS RDS, Google Cloud SQL

**Vector DB (Replace ChromaDB):**
- [Pinecone](https://www.pinecone.io/) - Free tier available
- [Weaviate Cloud](https://weaviate.io/pricing) - Free tier available

**Update backend/app.py:**
```python
# Add at top
import os
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
```

---

## 5. Quick Deploy for Testing (Replit)

**Fastest way to make it available online without setup:**

1. Go to https://replit.com
2. "Create Repl" → "Import from GitHub"
3. Paste your GitHub repo URL
4. Replit auto-detects Python
5. Click "Run"
6. Share the generated URL

**Pros:** Zero configuration, free tier
**Cons:** Public URL changes on restart, limited resources

---

## 6. Custom Domain Setup

Once deployed, you can add a custom domain:

**Heroku/Railway:**
```bash
heroku domains:add loyalty-helper.yourdomain.com
# Follow DNS instructions
```

**Google Cloud Run:**
```bash
gcloud run domain-mappings create --service esp-loyalty-helper --domain loyalty-helper.yourdomain.com
```

---

## 7. Security Checklist Before Going Live

- [ ] Change `ADMIN_PASSWORD` from default `RICHCSM`
- [ ] Set `FLASK_DEBUG=0` in production
- [ ] Enable HTTPS (auto on most platforms)
- [ ] Add rate limiting (see `backend/app.py` TODOs)
- [ ] Review API key permissions (restrict to necessary scopes)
- [ ] Set up monitoring/logging (Sentry, LogDNA)
- [ ] Backup databases regularly

---

## 8. Recommended Quick Start

For fastest online deployment:

1. **Push to GitHub** (Option 1 above)
2. **Deploy to Railway** (Option B - 5 minutes)
3. **Add environment variables** in Railway dashboard
4. **Access via Railway URL** (e.g., `your-app.railway.app`)

**Later migration:** Move to AWS/GCP when ready for production scale (see CLAUDE.md migration plan).

---

## Troubleshooting

**"Module not found" errors:**
- Ensure `requirements.txt` is in `backend/` folder
- Check Railway/Heroku build logs

**Database errors in cloud:**
- Cloud platforms have ephemeral filesystems
- Must migrate to PostgreSQL + cloud vector DB
- See "Phase 1" in CLAUDE.md

**Port binding errors:**
- Cloud platforms assign PORT env variable
- Ensure `app.py` uses `os.getenv('PORT', 5000)`

---

## Next Steps

1. Push to GitHub
2. Choose deployment platform (Railway recommended for testing)
3. Add environment variables
4. Test the deployment
5. Plan database migration (see CLAUDE.md for production architecture)

For production scaling, see the full migration strategy in **CLAUDE.md**.
