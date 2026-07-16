# 🚀 Deploy to Railway - Quick Guide

## ⏱️ Time: 15 minutes

This guide will get your ESP Loyalty Helper app live on the internet.

---

## ✅ Pre-Flight Checklist

You already have:
- ✅ PostgreSQL database (Railway)
- ✅ Pinecone vector database
- ✅ Gemini API key
- ✅ Code ready to deploy

---

## Step 1: Push to GitHub (5 minutes)

### 1.1 Initialize Git (if not done)

Open Terminal in your project folder:

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"
git init
git add .
git commit -m "Ready for deployment - Phase 2 complete"
```

### 1.2 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `esp-loyalty-helper` (or your choice)
3. **Make it Private** (contains API keys in .env)
4. ⚠️ **DO NOT** initialize with README (we have one)
5. Click "Create repository"

### 1.3 Push Code

Copy the commands GitHub shows you (should look like):

```bash
git remote add origin https://github.com/YOUR_USERNAME/esp-loyalty-helper.git
git branch -M main
git push -u origin main
```

**✅ Check**: Visit your GitHub repo - code should be there!

---

## Step 2: Deploy to Railway (10 minutes)

### 2.1 Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your `esp-loyalty-helper` repository

Railway will start building automatically!

### 2.2 Configure Environment Variables

Click on your new project → **Variables** tab

Add these environment variables (copy from your `.env` file):

```bash
# Required
GEMINI_API_KEY=AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw
ADMIN_PASSWORD=RICHCSM
PINECONE_API_KEY=pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
PINECONE_INDEX_NAME=esp-loyalty-docs1
PINECONE_ENVIRONMENT=us-east-1
DATABASE_URL=postgresql://postgres:kWTbHNiMEoSTLJGdZWidWgVwMzplAuYH@tokaido.proxy.rlwy.net:14038/railway

# Configuration
VECTOR_DB_PROVIDER=pinecone
DATABASE_PROVIDER=postgres
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5000
```

**⚠️ IMPORTANT**: Change `ADMIN_PASSWORD` to something secure!

### 2.3 Connect PostgreSQL Database

1. In Railway dashboard, click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Wait for it to provision (30 seconds)
3. Railway will automatically add `DATABASE_URL` variable
4. ✅ Check that `DATABASE_URL` in Variables matches your PostgreSQL

### 2.4 Wait for Deployment

Railway will:
1. Install Python dependencies (~2 minutes)
2. Start Flask app (~30 seconds)
3. Show "Active" status with a URL

**Your app is now LIVE!** 🎉

---

## Step 3: Test Your Deployment (5 minutes)

### 3.1 Get Your App URL

In Railway dashboard:
- Click on your service
- Go to **Settings** tab
- Find **Domains** section
- Copy the URL (looks like: `https://esp-loyalty-helper-production.up.railway.app`)

### 3.2 Test the App

Open your URL in browser:

1. **Main Page**: Should load the chat interface
2. **Admin Panel**: 
   - Click "Admin Panel"
   - Enter your `ADMIN_PASSWORD`
   - Check Analytics dashboard
   - Verify ESPs are showing

3. **Test Chat**:
   - Select an ESP (e.g., Klaviyo)
   - Ask: "How do I set up a welcome email?"
   - Should get AI response with ESP-specific info

### 3.3 Check Logs (if something breaks)

Railway dashboard → **Deployments** tab → Click latest deployment → **View Logs**

Common issues:
- Missing environment variable
- Database connection error
- Pinecone quota exceeded

---

## Step 4: Secure Your Deployment (5 minutes)

### 4.1 Change Admin Password

In Railway dashboard → **Variables**:

```bash
ADMIN_PASSWORD=YourSecurePassword123!
```

Click **"Save"** - Railway will redeploy automatically.

### 4.2 Optional: Add Custom Domain

Railway → **Settings** → **Domains** → **"Add Custom Domain"**

Example: `loyalty-helper.yotpo.com`

You'll need to add a CNAME record in your DNS settings.

### 4.3 Optional: Enable Access Control

Railway → **Settings** → **Networking**:
- Add IP allowlist (e.g., Yotpo office IPs only)
- Requires Railway Pro plan ($5/month)

---

## 🎉 You're Live!

Your app is now:
- ✅ Running on Railway's cloud infrastructure
- ✅ Using PostgreSQL database (scalable)
- ✅ Using Pinecone vector database (cloud-native)
- ✅ Auto-deploys on every GitHub push
- ✅ HTTPS enabled automatically
- ✅ Can handle multiple concurrent users

---

## Costs

**Railway Free Tier**:
- $5 free credit per month
- Enough for ~500 hours of uptime
- Perfect for beta testing

**Estimated Monthly Cost** (after free tier):
- App hosting: ~$5-10/month
- PostgreSQL: ~$5/month
- **Total: $10-15/month**

Pinecone is separate: $70/month (Starter plan)

---

## Next Steps

### Week 1: Beta Testing
1. Share your Railway URL with 5-10 internal users
2. Monitor Railway logs for errors
3. Check analytics dashboard daily
4. Collect feedback

### Week 2: Iterate
Based on feedback:
- Add more ESPs
- Improve AI prompts
- Fix any bugs discovered

### Week 3+: Scale
If usage grows:
- Upgrade Railway plan
- Add Redis for session caching
- Add user authentication
- Add multi-tenancy

---

## Troubleshooting

### App won't start

**Check Railway Logs**:
```
Error: DATABASE_URL not found
```
→ Add DATABASE_URL to Variables

```
Error: No module named 'psycopg2'
```
→ Check `requirements.txt` includes `psycopg2-binary`

### Can't connect to PostgreSQL

**Check**:
1. PostgreSQL database is running in Railway
2. `DATABASE_URL` variable is set
3. `DATABASE_PROVIDER=postgres` in Variables

### Vector search not working

**Check**:
1. `VECTOR_DB_PROVIDER=pinecone` in Variables
2. Pinecone API key is valid
3. Index name matches: `esp-loyalty-docs1`

### Admin panel won't load

**Check**:
1. `ADMIN_PASSWORD` is set in Variables
2. Try clearing browser cache
3. Check browser console for errors (F12)

---

## Monitoring Your App

### Railway Dashboard
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: History of all deploys

### Set Up Alerts (Optional)

Railway → **Settings** → **Notifications**:
- Email on deployment failure
- Email on high resource usage
- Slack webhooks

---

## Updating Your App

Every time you push to GitHub, Railway auto-deploys:

```bash
# Make changes locally
git add .
git commit -m "Added new ESP: Mailchimp"
git push

# Railway automatically:
# 1. Pulls latest code
# 2. Installs dependencies
# 3. Restarts app
# 4. ~2 minutes downtime
```

---

## Rollback (if deployment breaks)

Railway dashboard → **Deployments** tab:
1. Find last working deployment
2. Click **⋮** menu
3. Select **"Redeploy"**

Your app rolls back to previous version!

---

## Support

**Railway**:
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**Your App Issues**:
- Check Railway logs first
- Review environment variables
- Test locally with same `.env` config

---

## 🚢 Ready to Deploy?

**Run these commands now**:

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"

# 1. Commit everything
git add .
git commit -m "Deploy: Phase 2 complete, ready for production"

# 2. Push to GitHub (create repo first on github.com)
git remote add origin https://github.com/YOUR_USERNAME/esp-loyalty-helper.git
git push -u origin main

# 3. Then go to railway.app and deploy!
```

**Questions?** Let me know and I'll help troubleshoot!
