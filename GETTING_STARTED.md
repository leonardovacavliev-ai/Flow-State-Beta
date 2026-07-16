# Getting Started with ESP Loyalty Helper

## Quick Start (3 Steps)

### 1. Get Your Free Gemini API Key

1. Visit: **https://makersuite.google.com/app/apikey**
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AI...`)

### 2. Set the API Key

Open Terminal and run:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Start the App

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"
./start.sh
```

Then open: **http://localhost:8000**

---

## What You Get

### For End Users
- **Chat Interface**: Ask questions about loyalty flows, campaigns, and email setup
- **ESP Selection**: Choose Klaviyo, DotDigital, or Other/Webhook
- **Smart Answers**: AI searches vectorized documentation to provide accurate guidance
- **Feedback System**: Rate responses and provide comments

### For Admins (Password: RICHCSM)
- **Manage ESPs**: View all integrations and their documentation
- **Add Links**: Expand documentation for any ESP
- **Create New ESPs**: Add Mailchimp, Braze, SendGrid, etc.
- **Refresh Documentation**: Re-crawl and update the knowledge base

---

## Current Documentation

✅ **Klaviyo**: 3 documents  
✅ **DotDigital**: 6 documents  
✅ **Other/Webhook**: Empty (ready for your links)  
✅ **Best Practices**: Yotpo Loyalty Strategies PDF

---

## Example Questions to Ask

**Setting Up Flows:**
- "How do I create a points earning notification in Klaviyo?"
- "What's the best way to set up a VIP tier upgrade email?"
- "How do I trigger an email when someone redeems rewards?"

**Campaign Creation:**
- "What should I include in a welcome series for new loyalty members?"
- "How do I segment customers by tier in DotDigital?"
- "What are best practices for loyalty email frequency?"

**Technical Setup:**
- "How do I configure the Yotpo webhook integration?"
- "What data fields are available from Yotpo?"
- "How do I test my loyalty flows before going live?"

---

## Adding More Documentation

1. **Open Admin Panel**: Click "Admin" → Password: `RICHCSM`
2. **Find Your ESP**: Look for Klaviyo, DotDigital, or Other/Webhook
3. **Add URL**: Paste documentation link in "Add new link" field
4. **Click "Add Link"**
5. **Refresh**: Click "Refresh All" to crawl and vectorize new docs

---

## Cost & Usage

### Gemini API (Free Tier)
- **15 requests per minute**
- **1 million tokens per day**
- **$0/month** for typical usage

### If You Exceed Free Tier
- **Paid tier**: ~$0.35 per 1M input tokens
- **Still very cheap**: Expect <$1/month even with heavy use

---

## Troubleshooting

### "GEMINI_API_KEY not set"
```bash
# Make sure you run this in the same terminal window:
export GEMINI_API_KEY="your-key-here"
```

### "Port already in use"
```bash
# Kill existing processes:
lsof -ti:5000 | xargs kill
lsof -ti:8000 | xargs kill

# Then restart:
./start.sh
```

### "Admin password not working"
Password is: `RICHCSM` (all caps)

### "Chat not responding"
1. Check backend terminal for errors
2. Verify API key is set correctly
3. Check you haven't exceeded rate limits (15/min)

---

## File Structure

```
ESP Loyalty Helper APP/
├── backend/
│   ├── app.py           # Flask API (uses Gemini)
│   ├── crawler.py       # Web scraper
│   ├── vectorize.py     # ChromaDB manager
│   └── chroma_db/       # Vector database
├── docs/
│   ├── klaviyo/         # 3 documents
│   ├── dotdigital/      # 6 documents
│   └── other_webhook/   # Empty, ready for links
├── frontend/
│   ├── index.html       # UI
│   ├── styles.css       # Yotpo branding
│   └── app.js           # Logic
├── feedback.csv         # User feedback (auto-created)
└── start.sh             # Easy startup
```

---

## Next Steps

1. **Start the app** with your Gemini API key
2. **Test it out** by asking a question
3. **Add documentation** for Other/Webhook ESP
4. **Customize** the system prompt if needed
5. **Add more ESPs** (Mailchimp, Braze, etc.)

---

## Support Documents

- **README.md** - Full documentation
- **QUICKSTART.md** - Quick reference
- **GEMINI_MIGRATION.md** - Why we use Gemini
- **OTHER_WEBHOOK_SETUP.md** - Webhook ESP guide
- **CHANGELOG.md** - Recent changes

---

## Ready to Go!

Your app is fully configured and ready to use. Just set your Gemini API key and start the app!

Questions? Check the troubleshooting section or review the full README.md.
