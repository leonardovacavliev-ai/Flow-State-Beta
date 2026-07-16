# ✅ Pre-Deployment Checklist

Before you push to GitHub and deploy, verify these items:

## 🔒 Security

- [ ] `.env` file is in `.gitignore` ✅ (already done)
- [ ] Choose a strong admin password for production
- [ ] API keys are ready:
  - [ ] Gemini API key: `AQ.Ab8RN6...` ✅
  - [ ] Pinecone API key: `pcsk_2aKY6Q_...` ✅

## 🗄️ Databases

- [ ] PostgreSQL on Railway: ✅ Connected and tested
  - URL: `postgresql://postgres:kWTbHNi...@tokaido.proxy.rlwy.net:14038/railway`
- [ ] Pinecone index exists: ✅ `esp-loyalty-docs1`
  - Status: Ready to use

## 📦 Dependencies

- [ ] `requirements.txt` includes all packages ✅
  - Flask, ChromaDB, Pinecone, PostgreSQL, etc.

## 🚀 Deployment Files

- [ ] `Procfile` exists ✅
- [ ] `Dockerfile` exists ✅
- [ ] `.env.example` updated ✅

## ⚙️ Environment Variables for Railway

Copy these to Railway dashboard when deploying:

```bash
# AI Provider
GEMINI_API_KEY=AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw

# Security (⚠️ CHANGE THIS!)
ADMIN_PASSWORD=RICHCSM

# Vector Database
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
PINECONE_INDEX_NAME=esp-loyalty-docs1
PINECONE_ENVIRONMENT=us-east-1

# Analytics Database
DATABASE_PROVIDER=postgres
DATABASE_URL=postgresql://postgres:kWTbHNiMEoSTLJGdZWidWgVwMzplAuYH@tokaido.proxy.rlwy.net:14038/railway

# App Config
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5000
```

## 📋 Quick Test Locally (Optional)

Before deploying, test with production settings:

```bash
# 1. Update .env to use production databases
DATABASE_PROVIDER=postgres
VECTOR_DB_PROVIDER=pinecone

# 2. Start app
./start.sh

# 3. Test in browser
open http://localhost:8000

# 4. Verify:
# - Chat works with Pinecone
# - Admin panel shows analytics from PostgreSQL
# - No errors in terminal
```

## 🎯 Deployment Steps

### 1. Push to GitHub (5 min)

```bash
git add .
git commit -m "Ready for production deployment"
git push origin main
```

### 2. Deploy to Railway (10 min)

1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repo
4. Add environment variables (from list above)
5. Wait for deployment (~2 min)

### 3. Test Live App (5 min)

1. Get Railway URL
2. Test chat interface
3. Test admin panel
4. Check logs for errors

---

## 🚨 Important Security Note

**Before sharing with users:**

1. **Change admin password** in Railway variables:
   ```
   ADMIN_PASSWORD=YourSecurePassword123!
   ```

2. **Optional**: Add IP whitelist in Railway (Pro plan)
   - Settings → Networking → Allowlist
   - Add Yotpo office IPs

3. **Monitor usage**:
   - Check Railway logs daily for first week
   - Watch for unusual activity
   - Set up alerts

---

## 🎉 Ready to Deploy?

If all checkboxes above are ✅, follow the guide in:
- **[DEPLOY_NOW.md](DEPLOY_NOW.md)** - Step-by-step deployment

---

## 🆘 Need Help?

**Common Issues:**

1. **"git: command not found"**
   - Install Git: https://git-scm.com/downloads

2. **"Authentication failed" (GitHub)**
   - Generate Personal Access Token: GitHub → Settings → Developer settings → Personal access tokens
   - Use token as password when pushing

3. **"Deployment failed" (Railway)**
   - Check Railway logs
   - Verify all environment variables are set
   - Ensure `requirements.txt` is complete

4. **"Can't connect to database"**
   - Check PostgreSQL is running in Railway
   - Verify `DATABASE_URL` is correct
   - Test connection: `python3 backend/test_postgres.py`
