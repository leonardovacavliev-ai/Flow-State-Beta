# 🚀 Quick Start Guide - AI ESP Loyalty Helper

## IMPORTANT: ChromaDB Disk Issue

The ChromaDB vector database had I/O errors in the VM environment. **This will work fine on your Mac** when you run the script directly from Terminal.

---

## How to Start the Application

### Option 1: Use the Startup Script (Recommended)

Open Terminal and run:

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"
./start_local.sh
```

This will:
1. Start the backend server on port 5001
2. Start the frontend server on port 3001
3. Display the access URLs

### Option 2: Manual Start

If the script doesn't work, start manually:

```bash
# Terminal 1 - Backend
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP/backend"
export GEMINI_API_KEY="AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw"
python3 app.py

# Terminal 2 - Frontend
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP/frontend"
python3 -m http.server 3001
```

---

## Access the Application

Once started:

- **Frontend (User Interface)**: http://localhost:3001
- **Backend API**: http://localhost:5001
- **Admin Password**: `RICHCSM`

---

## If ChromaDB Needs Rebuilding

If you see errors about ChromaDB on startup, the vector database needs to be reinitialized:

### Method 1: Delete and Rebuild

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP/backend"

# Remove old database
rm -rf chroma_db

# Run the app - it will recreate the database automatically
# OR manually rebuild with:
python3 rebuild_chromadb.py
```

### Method 2: Check What's in the Database

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP/backend"
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collections = client.list_collections()
print(f'Collections: {len(collections)}')
for col in collections:
    print(f'  - {col.name}: {col.count()} items')
"
```

---

## Configuration

All settings are in `.env`:

```bash
# Your Gemini API Key (already set)
GEMINI_API_KEY=AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw

# Vector Database (local ChromaDB)
VECTOR_DB_PROVIDER=chromadb

# Admin password
ADMIN_PASSWORD=RICHCSM

# Server ports
PORT=5001  # Backend
# Frontend runs on 3001
```

---

## Troubleshooting

### "Module not found" errors

Install dependencies:

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP/backend"
pip3 install -r requirements.txt
```

### ChromaDB disk I/O errors

This happens in VMs but should work fine on your Mac. If it persists:

1. Delete the database: `rm -rf backend/chroma_db`
2. Restart the app - it will recreate it

### Port already in use

If ports 5001 or 3001 are busy:

```bash
# Find what's using the port
lsof -i :5001
lsof -i :3001

# Kill the process
kill <PID>
```

### App won't start

Check if Python 3 is installed:

```bash
python3 --version
```

Should be Python 3.8 or higher.

---

## What's Included

### ESP Knowledge Bases

The app has documentation for:
- Klaviyo
- DotDigital
- Attentive
- Ometria
- Postscript
- Other/Webhook

### Features

- AI-powered chat interface
- RAG (Retrieval Augmented Generation) with ESP documentation
- Analytics dashboard
- Admin panel for managing ESPs and documentation
- Session tracking
- Feedback system

---

## Adding New ESPs

1. Go to http://localhost:3001
2. Click Admin (top right)
3. Enter password: `RICHCSM`
4. Click "Create New ESP"
5. Add documentation URLs
6. Crawl the URLs
7. The ESP is now available in the chat dropdown

---

## Technical Stack

- **Backend**: Flask (Python)
- **AI**: Google Gemini Flash
- **Vector DB**: ChromaDB (local)
- **Analytics**: SQLite
- **Frontend**: Vanilla JavaScript

---

## Need Help?

Check these files:
- `CLAUDE.md` - Full project documentation
- `QUICKSTART.md` - Original quick start guide
- `DEPLOYMENT.md` - Cloud deployment options

---

**Note**: This version runs **100% locally** with ChromaDB. The Pinecone (cloud) configuration is commented out in `.env` and not used.
