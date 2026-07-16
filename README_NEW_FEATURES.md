# 🎉 New Admin Features - Quick Start Guide

## ✅ What's New

Your AI ESP Loyalty Helper app now has powerful new administrative features:

1. **General Settings Tab** - Configure AI models, API keys, and system prompts
2. **Global Knowledge Base** - Add knowledge that works across all ESPs
3. **Change Tracking** - Full audit log with email-based accountability
4. **Multi-Model Support** - Switch between Gemini and Claude seamlessly

## 🚀 Quick Start

### 1. Start the App

**Option A: Using the startup script**
```bash
cd "AI ESP Loyalty Helper APP"
./start.sh
```

**Option B: Manual start**
```bash
# Terminal 1 - Backend
cd backend
python3 app.py

# Terminal 2 - Frontend
cd frontend
python3 -m http.server 3001
```

### 2. Access the App

Open your browser to: **http://localhost:3001**

### 3. Access Admin Panel

1. Click "Admin" button in the sidebar
2. Enter password: **RICHCSM**
3. You'll see 3 tabs:
   - **Usage Analytics** (existing)
   - **ESP Management** (updated with Global Knowledge)
   - **General Settings** (NEW!)

## 🔧 Using the New Features

### General Settings Tab

#### Switch AI Model
1. Go to "General Settings" tab
2. In "AI Model Configuration":
   - Select provider (Gemini or Claude)
   - Choose model
   - Enter your email
   - Click "Update AI Model"
3. Status badge shows if it's working

#### Update API Key
1. In "API Key Management":
   - Select provider
   - Enter new API key
   - Enter your email
   - Click "Update API Key"
2. Changes apply immediately (no restart needed!)

#### Edit System Prompt
1. In "System Prompt" section:
   - Edit the text area
   - Enter your email
   - Click "Update System Prompt"
2. Affects all new conversations

#### View Change History
1. Scroll to "Change History"
2. See all recent changes with timestamps
3. Click "Restore" on any entry to revert
4. View backup details to see what was saved

### Global Knowledge Base

1. Go to "ESP Management" tab
2. Find "Global Knowledge Base" section
3. Add a URL (e.g., loyalty best practices)
4. Click "Add Link"
5. Check the box next to the new link
6. Click "Crawl Selected" (in the sticky header at top)
7. Knowledge is now available in all chats!

## 📝 Important Notes

### Port Configuration
- **Backend**: http://localhost:5001
- **Frontend**: http://localhost:3001

*Note: Changed from port 5000 to 5001 to avoid conflicts with AirPlay on macOS*

### API Keys
You can set API keys in two ways:

**Option 1: Environment Variables (recommended for startup)**
```bash
export GEMINI_API_KEY="your_key_here"
export ANTHROPIC_API_KEY="your_key_here"
```

**Option 2: Admin Panel (recommended for updates)**
- Use the API Key Management section
- No need to restart the server!

### Security
- All changes require admin password
- All changes require your email address
- Automatic backups before every change
- Full audit trail with timestamps

## 🔄 Stopping the Servers

**If you used the start script:**
```bash
pkill -f 'python3 app.py' && pkill -f 'python3 -m http.server'
```

**If you started manually:**
Press `Ctrl+C` in each terminal window

## 📚 Full Documentation

- **ADMIN_FEATURES_DOCUMENTATION.md** - Complete feature guide
- **IMPLEMENTATION_SUMMARY.md** - Technical details
- **SETUP_GUIDE.md** - Detailed installation instructions

## 🆘 Troubleshooting

### "API key not configured" error
1. Set environment variable: `export GEMINI_API_KEY="your_key"`
2. Or update via Admin Panel → General Settings → API Key Management
3. Check status badge to verify it's working

### Port already in use
- Backend changed to port 5001 (was 5000)
- If still issues, check: `lsof -i :5001`
- Kill process: `kill -9 <PID>`

### Changes not appearing
1. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+F5` (Windows)
2. Check browser console for errors
3. Verify backend is running: `curl http://localhost:5001/api/admin/esps`

### Can't restore from backup
1. Go to General Settings → Change History
2. Click "Restore" on working configuration
3. Enter your email to confirm
4. If still issues, check `backend/config_audit_log.json`

## ✨ What You Can Do Now

1. **Test different AI models** - Try Claude vs Gemini and see which works better
2. **Add global knowledge** - Add loyalty best practices that work across all ESPs
3. **Track all changes** - See who changed what and when
4. **Restore mistakes** - One-click restore if something breaks
5. **Update API keys** - No more server restarts needed!

## 🎯 Next Steps

1. Add your API keys (via environment or admin panel)
2. Test the General Settings tab
3. Add some global knowledge sources
4. Try switching between AI models
5. Make a change and restore it to test the audit log

---

**Your app is ready to use!** 🎉

Access it at: **http://localhost:3001**

Admin password: **RICHCSM** (change in `backend/app.py` for production)
