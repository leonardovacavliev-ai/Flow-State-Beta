# AI ESP Loyalty Helper - Startup Complete! 🎉

## Application Status: ✅ RUNNING

The ESP Loyalty Helper application has been successfully initialized and is now running.

---

## Access Information

### Frontend (User Interface)
- **URL**: http://localhost:3001
- **Description**: Main chat interface for loyalty campaign assistance

### Backend (API Server)
- **URL**: http://localhost:5001
- **Description**: Flask REST API with RAG-powered AI responses

### Admin Access
- **Password**: `RICHCSM`
- Access admin features through the frontend interface

---

## Configuration

### Environment Setup
- ✅ Python dependencies installed
- ✅ Gemini API key configured
- ✅ Vector database set to **Pinecone** (cloud)
- ✅ Analytics database (SQLite) initialized

### Vector Database
**Using**: Pinecone (Cloud)
- **Index**: esp-loyalty-docs1
- **Reason**: Switched from ChromaDB due to local disk I/O errors
- **Status**: Connected and operational

### Available ESPs
The following ESP knowledge bases are available:
- **Ometria** (4 documents)
- **Attentive** (3 documents)
- **Klaviyo** (4 documents)
- **DotDigital** (8 documents)
- **Postscript** (2 documents)
- **Listrak** (0 documents)
- **Other/Webhook** (0 documents)

---

## How to Use

### For Users
1. Open http://localhost:3001 in your browser
2. Select your ESP from the dropdown
3. Ask questions about setting up loyalty campaigns
4. Get step-by-step guidance powered by AI and ESP documentation

### For Admins
1. Click the admin button (top right)
2. Enter password: `RICHCSM`
3. Access features:
   - Manage ESPs and documentation
   - View analytics dashboard
   - Configure AI model settings
   - Add/remove documentation links

---

## Server Management

### View Logs
```bash
# Backend logs
tail -f /tmp/backend_setsid.log

# Frontend logs
tail -f /tmp/frontend_setsid.log
```

### Stop Servers
```bash
# Find and kill processes
pkill -f "python3 app.py"
pkill -f "python3 -m http.server"
```

### Restart Application
```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"
./start_production.sh
```

---

## Technical Details

### Backend
- **Framework**: Flask
- **AI Model**: Google Gemini Flash
- **Port**: 5001
- **Mode**: Production (debug off)

### Frontend
- **Type**: Static HTML/JS
- **Server**: Python HTTP server
- **Port**: 3001

### Database Architecture
- **Vector DB**: Pinecone (cloud-hosted)
- **Analytics**: SQLite (local file)
- **Session Storage**: In-memory

---

## Known Issues & Notes

### Warnings (Safe to Ignore)
- Google API deprecation warning (Python 3.10)
- `google.generativeai` package deprecation (functionality still works)
- HuggingFace Hub authentication warning

### ChromaDB Issue
- Local ChromaDB experienced disk I/O errors
- Successfully migrated to Pinecone cloud vector database
- No functionality lost in migration

### Disk Space
- VM disk usage: 82% (7.6G used of 9.8G)
- Cleared pip cache to free 3GB
- sentence-transformers installation required cache clearing

---

## Environment Variables

The following are configured in `.env`:

```bash
GEMINI_API_KEY=AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
PINECONE_INDEX_NAME=esp-loyalty-docs1
PINECONE_ENVIRONMENT=us-east-1
ADMIN_PASSWORD=RICHCSM
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5001
```

---

## Next Steps

### Immediate
1. Open http://localhost:3001 and test the chat interface
2. Try asking about different ESP integrations
3. Explore the admin panel features

### Future Enhancements
- Add more ESPs (Mailchimp, Braze, Iterable, etc.)
- Populate empty ESPs (Listrak, Other/Webhook)
- Monitor analytics for usage patterns
- Consider full cloud migration (see CLAUDE.md for architecture)

---

## Support & Documentation

- **Project Overview**: See `CLAUDE.md`
- **Migration Guide**: See `VECTOR_DB_MIGRATION.md`
- **Pinecone Setup**: See `QUICK_START_PINECONE.md`
- **Quick Deploy**: See `QUICK_DEPLOY.md`

---

**Startup Date**: July 16, 2026
**Status**: Operational ✅
