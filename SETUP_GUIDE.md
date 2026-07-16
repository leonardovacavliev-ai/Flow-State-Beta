# Setup Guide for New Admin Features

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Active Gemini API key (and/or Claude API key)

## Installation Steps

### 1. Install New Dependencies

```bash
cd "AI ESP Loyalty Helper APP"
pip install -r backend/requirements.txt
```

This will install the new `anthropic` package along with existing dependencies.

### 2. Set Environment Variables

You need at least one API key to start. You can set both if you want to switch between them.

#### Option A: Set in Terminal (Temporary)

**For Gemini:**
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

**For Claude:**
```bash
export ANTHROPIC_API_KEY="your_claude_api_key_here"
```

#### Option B: Create .env File (Recommended)

Create a file called `.env` in the root directory:

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
```

Then install python-dotenv and load it:
```bash
pip install python-dotenv
```

Add to the top of `backend/app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### 3. Initialize Configuration

On first run, the app will automatically create:
- `backend/app_config.json` - Current configuration
- `backend/config_audit_log.json` - Change history

These files will be created with default values.

### 4. Start the Backend

```bash
cd backend
python app.py
```

You should see:
```
✓ Gemini API configured successfully
 * Running on http://127.0.0.1:5000
```

### 5. Start the Frontend

In a new terminal:

```bash
cd frontend
python3 -m http.server 3001
```

### 6. Access the Application

Open your browser to:
```
http://localhost:3001
```

## Initial Configuration

### 1. Test the Current Setup

1. Click "Admin" button in sidebar
2. Enter password: `RICHCSM`
3. Go to "General Settings" tab
4. Check the AI Model Configuration section
5. Verify API status shows "✓ Working"

### 2. Add Your First Global Knowledge Source

1. Go to "ESP Management" tab
2. Find "Global Knowledge Base" section
3. Add a URL (e.g., loyalty best practices guide)
4. Click "Add Link"
5. Check the box next to the new link
6. Click "Crawl Selected" in the sticky header
7. Wait for crawling to complete

### 3. Optional: Switch to Claude

If you have a Claude API key:

1. Go to "General Settings" tab
2. In "API Key Management":
   - Select "Anthropic Claude"
   - Enter your Claude API key
   - Enter your email
   - Click "Update API Key"
3. In "AI Model Configuration":
   - Select "claude" as provider
   - Choose a Claude model (e.g., "Claude 3.5 Sonnet")
   - Enter your email
   - Click "Update AI Model"
4. Verify status shows "✓ Working"

## Verifying the Setup

### 1. Test Chat Interface

1. Select an ESP from the sidebar
2. Ask a question like "How do I set up a welcome series?"
3. Verify you get a response
4. Check that the response feels appropriate for the selected model

### 2. Test Global Knowledge

1. Add a global knowledge source about loyalty programs
2. Crawl it
3. Ask a question that should use global knowledge
4. Verify the response includes information from global sources

### 3. Test Change Tracking

1. Make a change (e.g., update system prompt)
2. Go to "Change History"
3. Verify the change is logged with your email
4. Click "View backup details" to see what was saved
5. Try restoring from backup

## Troubleshooting

### Issue: "API key not configured" Error

**Solution:**
1. Verify environment variable is set: `echo $GEMINI_API_KEY`
2. If empty, set it: `export GEMINI_API_KEY="your_key"`
3. Restart the backend server
4. Or update via admin panel

### Issue: "anthropic package not installed"

**Solution:**
```bash
pip install anthropic
```

### Issue: Configuration files not created

**Solution:**
1. Check backend directory permissions
2. Manually create empty files:
   ```bash
   touch backend/app_config.json
   touch backend/config_audit_log.json
   ```
3. Restart backend

### Issue: Global knowledge not showing in searches

**Solution:**
1. Verify files are in `docs/global/` directory
2. Check `docs/crawl_metadata.json` has 'global' entry
3. Re-run vectorization if needed
4. Check backend logs for errors

### Issue: Frontend not connecting to backend

**Solution:**
1. Verify backend is running on port 5000
2. Check browser console for CORS errors
3. Verify `API_URL` in `frontend/app.js` is correct
4. Try hard refresh (Cmd+Shift+R)

## Default Configuration

On first run, the system creates this default configuration:

```json
{
  "ai_model": {
    "provider": "gemini",
    "model_name": "gemini-flash-latest",
    "api_key_set": true,
    "claude_api_key_set": false
  },
  "system_prompt": "You are an email marketing specialist and a loyalty retention specialist at once...",
  "last_updated": "2026-07-16T...",
  "updated_by": "system"
}
```

## File Permissions

Ensure these files are writable:
- `backend/app_config.json`
- `backend/config_audit_log.json`
- `docs/crawl_metadata.json`
- `docs/global/` directory

## Security Notes

1. **Admin Password**: Change the default password in `backend/app.py`:
   ```python
   ADMIN_PASSWORD = "your_secure_password"
   ```

2. **API Keys**: Never commit API keys to version control
   - Add `.env` to `.gitignore`
   - Keep API keys in environment variables

3. **Audit Log**: Regularly review change history for unauthorized changes

4. **Backups**: Periodically backup:
   - `backend/app_config.json`
   - `backend/config_audit_log.json`
   - `docs/` directory

## Maintenance

### Weekly Tasks
1. Review change history in admin panel
2. Check API status for all providers
3. Add new global knowledge sources
4. Update outdated documentation links

### Monthly Tasks
1. Backup configuration files
2. Review and update system prompt based on feedback
3. Test both Gemini and Claude models
4. Clean up old/irrelevant knowledge sources

### As Needed
1. Update API keys when they expire
2. Switch models based on performance/cost
3. Restore from backup if issues occur
4. Add new ESPs to the platform

## Getting Help

1. **Documentation**: Read `ADMIN_FEATURES_DOCUMENTATION.md`
2. **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
3. **Change History**: Check admin panel for recent changes
4. **Logs**: Check backend console output for errors

## Quick Reference

### Admin Panel Sections
- **Usage Analytics**: View app usage statistics
- **ESP Management**: Manage ESP docs + Global Knowledge
- **General Settings**: AI config, API keys, system prompt

### Key Files
- `backend/app_config.json` - Current config
- `backend/config_audit_log.json` - Change history
- `docs/global/` - Global knowledge docs
- `docs/crawl_metadata.json` - Crawl tracking

### Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key
- `ANTHROPIC_API_KEY` - Anthropic Claude API key

### Admin Password
Default: `RICHCSM` (change in `backend/app.py`)

---

**Ready to Use!** Once you complete these steps, all new features will be fully functional.
