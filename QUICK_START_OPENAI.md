# Quick Start: OpenAI Integration

## 🚀 5-Minute Setup Guide

### Step 1: Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...` or `sk-...`)
5. **Important**: Save it securely - you won't see it again!

### Step 2: Add API Key

**Option A: Admin UI (Easiest)**
```
1. Open your app → Admin Panel (password: RICHCSM)
2. Go to "General Settings" tab
3. Select "OpenAI" from dropdown
4. Choose model: "GPT-4o (Optimized)" (recommended)
5. Paste your API key
6. Enter your email and click "Apply Changes"
```

**Option B: Environment File**
```bash
# Edit .env file
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

### Step 3: Install Package (if needed)

```bash
pip install openai
```

Or reinstall all dependencies:
```bash
pip install -r backend/requirements.txt
```

### Step 4: Restart Server

```bash
# Kill existing server
pkill -f "python.*app.py"

# Start fresh
./start.sh
```

### Step 5: Verify It Works

1. Check server logs for: `✓ OpenAI configured with model: gpt-4o`
2. Admin UI → Status badge should show: `✓ Working`
3. Send a test chat message

---

## 🎯 Recommended Model by Use Case

| Use Case | Model | Why |
|----------|-------|-----|
| **Production (default)** | `gpt-4o` | Best balance: fast, smart, affordable |
| **High volume** | `gpt-4o-mini` | 20x cheaper, still excellent quality |
| **Complex reasoning** | `gpt-4-turbo` | Enhanced logic, longer context |
| **Budget testing** | `gpt-3.5-turbo` | Cheapest option |

---

## 💰 Cost Estimates (per 1,000 chat messages)

Assuming average message = 500 tokens input + 800 tokens output:

| Model | Cost per 1K messages | Monthly (10K msgs) |
|-------|---------------------|--------------------|
| `gpt-4o` | ~$12 | ~$120 |
| `gpt-4o-mini` | ~$0.60 | ~$6 |
| `gpt-3.5-turbo` | ~$1.50 | ~$15 |

---

## 🔧 Troubleshooting

### "openai package not installed"
```bash
pip install openai
```

### "OPENAI_API_KEY not set"
1. Check `.env` file
2. Restart Flask server
3. Or set via Admin UI

### Invalid API Key
1. Keys start with `sk-proj-` (new) or `sk-` (legacy)
2. Check at https://platform.openai.com/api-keys
3. Create new key if expired

### No response from OpenAI
1. Check https://status.openai.com for outages
2. Verify API key has sufficient credits
3. Check server logs for detailed error

---

## 📊 Compare All Providers

| Provider | Best Model | Speed | Cost | Context Window |
|----------|-----------|-------|------|----------------|
| **Gemini** | `gemini-flash-latest` | ⚡ Very Fast | 💰 Cheap | 1M tokens |
| **Claude** | `claude-3-5-sonnet` | ⚡ Fast | 💰💰 Medium | 200K tokens |
| **OpenAI** | `gpt-4o` | ⚡ Fast | 💰💰 Medium | 128K tokens |

**Recommendation**: Test all three and see which gives best results for your ESP documentation!

---

## 🎛️ Switching Between Providers

```
Admin Panel → General Settings → AI Provider dropdown

Gemini    → Fast, cheap, great for high volume
Claude    → Excellent instruction following
OpenAI    → Strong general knowledge, reliable
```

Changes take effect **immediately** for all users!

---

## 📦 Deployment

### Railway
```bash
railway variables set OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
railway up
```

### Replit
Add to Secrets:
```
OPENAI_API_KEY = sk-proj-xxxxxxxxxxxxx
```

### Manual Server
```bash
export OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
python backend/app.py
```

---

## ✅ Done!

Your app now supports **all three major AI providers**. Switch anytime via Admin UI with zero downtime!

**Need help?** Check [OPENAI_INTEGRATION.md](OPENAI_INTEGRATION.md) for full technical details.
