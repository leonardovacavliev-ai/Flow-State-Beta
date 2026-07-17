# API Key Persistence Fix

## Problem

When updating API keys through the Admin Panel → General Settings, the keys were only saved to the current Python process (`os.environ`). This caused issues in hosted environments:

1. **Container restarts**: Keys lost when container restarts
2. **Multi-instance deployments**: Each instance has separate environment
3. **Process isolation**: Worker processes don't share environment variables

## Solution

Updated the system to persist API keys to a `.env` file that loads on app startup.

### Changes Made

1. **[backend/config_manager.py](backend/config_manager.py)**: Added `_update_env_file()` method to persist keys
2. **[backend/app.py](backend/app.py)**: Added `load_dotenv()` at startup
3. **[backend/requirements.txt](backend/requirements.txt)**: Added `python-dotenv` dependency

### How It Works Now

**When you update an API key via Admin Panel:**

1. Key is saved to `os.environ` (current process)
2. Key is written to `.env` file (persists across restarts)
3. Config audit log records the change
4. AI client is reinitialized with new key

**When the app starts:**

1. `load_dotenv()` reads `.env` file
2. Environment variables are set before any code runs
3. AI client initializes with correct keys

## Setup Instructions

### Option 1: Admin Panel (Easiest)

1. Navigate to **Admin Panel → General Settings**
2. Enter your email (for audit trail)
3. Enter your API key
4. Click "Save API Key"
5. Verify: Check "API Status" shows "Connected"

### Option 2: Manual .env File

Create `.env` in project root:

```bash
# AI Provider API Keys
GEMINI_API_KEY=AIza...your_actual_key
ANTHROPIC_API_KEY=sk-ant-...your_actual_key

# Admin Configuration
ADMIN_PASSWORD=your_secure_password

# Vector Database
VECTOR_DB_PROVIDER=chromadb

# Analytics Database
DATABASE_PROVIDER=sqlite
```

**Security**: Never commit `.env` to git (already in `.gitignore`)

### Option 3: Platform Environment Variables

For hosted deployments, you can still use platform-native environment variables:

**Railway:**
```
Dashboard → Variables tab → Add:
GEMINI_API_KEY=AIza...
```

**Replit:**
```
Tools → Secrets → Add:
GEMINI_API_KEY=AIza...
```

**Google Cloud Run:**
```bash
gcloud run services update esp-loyalty-helper \
  --update-env-vars GEMINI_API_KEY=AIza...
```

**Priority**: Platform variables override `.env` file values.

## Testing the Fix

### Local Testing

```bash
# 1. Install new dependency
pip install python-dotenv

# 2. Start the app
cd backend
python app.py

# 3. Test admin panel
# Open http://localhost:5000
# Admin Panel → General Settings → Update API key
# Check that .env file is created with your key
cat ../.env

# 4. Restart app
# Keys should persist across restarts
pkill -f "python app.py"
python app.py

# 5. Test chat
# Select ESP → Send message → Should work
```

### Hosted Environment Testing

```bash
# 1. Redeploy with updated requirements.txt
git add .
git commit -m "fix: Persist API keys to .env file"
git push

# 2. Set API key via Admin Panel
# (Platform will restart automatically)

# 3. Verify persistence
# Send chat message → Should work
# Check logs for authentication errors
```

## Verification Checklist

- [ ] `python-dotenv` in [backend/requirements.txt](backend/requirements.txt)
- [ ] `load_dotenv()` at top of [backend/app.py](backend/app.py)
- [ ] `_update_env_file()` method in [backend/config_manager.py](backend/config_manager.py)
- [ ] `.env` in [.gitignore](.gitignore)
- [ ] `.env.example` template exists
- [ ] Admin panel API key update creates `.env` file
- [ ] App restart loads keys from `.env`
- [ ] Chat messages work after restart

## Troubleshooting

### Keys still not persisting

**Check file permissions:**
```bash
# App needs write permission in project root
ls -la .env
```

**Check platform restrictions:**
- Some platforms (Replit, Cloud Run) use read-only filesystems
- Use platform environment variables instead
- Or mount persistent volume for `.env` file

### Authentication still failing

**Verify API key format:**
```bash
# Gemini keys start with AIza
echo $GEMINI_API_KEY | grep "^AIza"

# Claude keys start with sk-ant-
echo $ANTHROPIC_API_KEY | grep "^sk-ant-"
```

**Check provider selection:**
```bash
# In Admin Panel → General Settings
# Model Provider must match the API key you set
```

**Check API quotas:**
- Gemini: https://aistudio.google.com/app/apikey
- Claude: https://console.anthropic.com/settings/keys

### .env file not created

**Check base path:**
```python
# In backend/config_manager.py
# Verify BASE_PATH points to project root
print(self.base_path)  # Should be /path/to/AI-ESP-Loyalty-Helper-APP
```

**Check write permissions:**
```bash
# App user must have write permission
touch .env
```

## Security Notes

- `.env` file is in `.gitignore` (never commit secrets)
- API keys are **not** stored in `app_config.json` (only stored in `.env`)
- Config audit log records key updates but not the actual keys
- Platform environment variables take precedence over `.env`

## Migration Path

If you previously set keys via platform environment variables:

1. **Keep using platform variables** (recommended for production)
2. **OR** migrate to `.env` file:
   - Use Admin Panel to set keys
   - Remove from platform dashboard
   - Redeploy

**Best practice**: Use platform variables for production, `.env` for local development.
