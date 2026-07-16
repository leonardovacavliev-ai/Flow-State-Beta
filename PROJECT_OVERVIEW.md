# ESP Loyalty Helper - Project Overview

## 🎯 Project Summary

An AI-powered assistant that helps users set up loyalty campaigns and flows in Email Service Providers (ESPs) integrated with Yotpo Loyalty. The app provides step-by-step guidance based on crawled documentation and industry best practices.

## ✅ What Was Built

### 1. Documentation Crawling System
- **Web Crawler** (`backend/crawler.py`)
  - Fetches content from ESP documentation URLs
  - Extracts main text content using BeautifulSoup
  - Saves to organized folders by ESP
  - Generates metadata tracking file
  
- **Status**: ✅ Complete
  - 3 Klaviyo documents crawled
  - 6 DotDigital documents crawled
  - Loyalty best practices PDF extracted

### 2. Vector Database System
- **Vectorizer** (`backend/vectorize.py`)
  - Uses ChromaDB for persistent vector storage
  - Sentence Transformers (all-MiniLM-L6-v2) for embeddings
  - Chunks documents with overlap for context
  - Supports ESP-specific filtering
  - Refresh/update capabilities
  
- **Status**: ✅ Complete
  - 47 document chunks vectorized
  - Database at `backend/chroma_db/`
  - Searchable by ESP and query

### 3. Backend API Server
- **Flask API** (`backend/app.py`)
  - RAG-powered chat using Claude Sonnet 4
  - Vector search integration
  - Conversation history support
  - Admin authentication
  - Feedback CSV writing
  - Dynamic ESP management
  
- **Endpoints**:
  ```
  POST   /api/chat                           # Chat with AI
  POST   /api/feedback                       # Submit feedback
  POST   /api/admin/verify                   # Admin login
  GET    /api/admin/esps                     # List ESPs
  GET    /api/admin/esp/<name>/links         # Get ESP links
  POST   /api/admin/esp/<name>/add-link      # Add link
  POST   /api/admin/esp/create               # Create ESP
  POST   /api/admin/refresh                  # Refresh all docs
  ```

- **Status**: ✅ Complete

### 4. Frontend Interface
- **Web Application** (`frontend/`)
  - Clean, modern UI with Yotpo branding
  - ESP selector sidebar
  - Real-time chat interface
  - Feedback modal form
  - Password-protected admin panel
  - Responsive design
  
- **Technology**: Vanilla JavaScript (no framework dependencies)
- **Status**: ✅ Complete

## 🎨 Design Implementation

### Brand Colors (from Yotpo guidelines)
```css
Navy:   #00205B  (primary, sidebar)
Lime:   #C5E86C  (accents)
Teal:   #72D1C8  (buttons, active states)
Coral:  #F8937D  (warnings)
Orange: #FDB768  (gradients)
White:  #FFFFFF
Gray:   #666666
```

### Typography
- **Font Family**: Helvetica Neue
- **Weights**: 300 (light), 400 (regular), 500 (medium), 600 (semibold)

### Gradient System
Used for welcome message banner - smooth gradient from Lime → Teal → Coral

## 🔧 System Requirements

### Dependencies Installed
```
✓ flask
✓ flask-cors
✓ beautifulsoup4
✓ requests
✓ chromadb
✓ sentence-transformers
✓ pypdf
✓ anthropic
```

### Required Environment Variable
```bash
ANTHROPIC_API_KEY="your-key-here"
```

## 📊 Current Data Status

### ESP Documentation
- **Klaviyo**: 3 documents
  - OAuth integration guide
  - Loyalty emails setup guide
  - Klaviyo general articles

- **DotDigital**: 6 documents
  - Integration guide
  - Campaign setup
  - Triggered campaigns
  - Editor extensions

- **Global**: 1 document
  - Yotpo Loyalty Best Practices (16 pages)

### Vector Database Stats
- **Total Chunks**: 47
- **Embedding Model**: all-MiniLM-L6-v2
- **Chunk Size**: 500 words with 50-word overlap
- **Metadata**: ESP, filename, source URL, filepath

## 🚀 How to Run

### Quick Start
```bash
# 1. Set API key
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# 2. Start both servers
./start.sh

# 3. Open browser
open http://localhost:8000
```

### Manual Start
```bash
# Terminal 1 - Backend
cd backend
python3 app.py

# Terminal 2 - Frontend
cd frontend
python3 -m http.server 8000
```

## 🎯 Key Features

### For End Users
1. **ESP Selection** - Choose between Klaviyo, DotDigital, or Other/Webhook
2. **AI Chat** - Ask questions about:
   - Flow setup and triggers
   - Campaign creation
   - Audience segmentation
   - Email copywriting
   - Best practices
3. **Context-Aware Responses** - AI pulls from relevant documentation
4. **Conversation History** - Multi-turn conversations maintained
5. **Feedback System** - Rate and comment on responses

### For Administrators
1. **View ESPs** - See all integrations and document counts
2. **Add Links** - Expand existing ESP documentation
3. **Create ESPs** - Add new integrations (Mailchimp, Braze, etc.)
4. **Refresh Docs** - Re-crawl all URLs and update vector database
5. **Password Protection** - Secure with `RICHCSM` password

## 🤖 AI System Prompt

The assistant operates with this personality:

- **Role**: Email marketing + loyalty retention specialist
- **Approach**: Step-by-step, practical guidance
- **Tone**: Direct, helpful, no fluff
- **Behavior**: 
  - Never assumes or guesses
  - Asks for missing information
  - Corrects user mistakes
  - Provides constructive feedback
  - Keeps answers concise

## 📁 Project Structure

```
AI ESP Loyalty Helper APP/
│
├── backend/
│   ├── app.py                  # Flask API server
│   ├── crawler.py              # Web scraper
│   ├── vectorize.py            # ChromaDB manager
│   └── chroma_db/              # Vector database
│
├── docs/
│   ├── klaviyo/                # Klaviyo docs (3 files)
│   ├── dotdigital/             # DotDigital docs (6 files)
│   └── crawl_metadata.json     # Tracking metadata
│
├── frontend/
│   ├── index.html              # Main UI
│   ├── styles.css              # Yotpo brand styles
│   └── app.js                  # Frontend logic
│
├── feedback.csv                # User feedback (auto-created)
├── start.sh                    # Startup script
├── test_setup.py               # Setup verification
├── README.md                   # Full documentation
├── QUICKSTART.md               # Quick start guide
├── PROJECT_OVERVIEW.md         # This file
│
└── Resources (in root):
    ├── Screenshot 2026-07-15 at 10.56.08.png   # Brand colors
    ├── Screenshot 2026-07-15 at 10.56.20.png   # Gradient system
    └── Yotpo New Rules of Loyalty Strategies.pdf
```

## 🔄 Workflow Architecture

```
User Question
     ↓
Frontend (JavaScript)
     ↓
Backend API (Flask)
     ↓
Vector Search (ChromaDB) → Retrieve relevant docs
     ↓
Claude Sonnet 4 API → Generate response with context
     ↓
Response + Sources
     ↓
Frontend Display
```

## 🎓 Usage Examples

### Example 1: Setting up a points earning flow
```
User: "How do I set up a flow in Klaviyo that emails customers when they earn points?"

AI: [Searches Klaviyo docs] → Provides:
- Webhook trigger setup
- Flow configuration steps
- Email template suggestions
- Best practices from loyalty report
```

### Example 2: Creating a VIP tier campaign
```
User: "I want to create a campaign for customers who just reached VIP status"

AI: [Searches current ESP + best practices] → Provides:
- Segment creation steps
- Campaign timing recommendations
- Email copy suggestions
- Personalization tactics
```

## 🔐 Security Features

- Admin password protection (`RICHCSM`)
- CORS enabled for local development
- CSV feedback (no PII exposure)
- API key stored as environment variable (not in code)

## 🚦 Status: Production Ready

All core features implemented and tested:
- ✅ Documentation crawling
- ✅ Vector database creation
- ✅ RAG-powered chat
- ✅ Admin panel
- ✅ Feedback system
- ✅ Brand styling
- ✅ Error handling
- ✅ Documentation

## 📈 Future Enhancement Ideas

1. **More ESPs**: Mailchimp, Braze, SendGrid, Iterable, Customer.io
2. **Export Chat**: Download conversation as PDF/Markdown
3. **Analytics Dashboard**: Track popular questions, ESP usage
4. **Multi-language**: Support for Spanish, French, etc.
5. **Code Snippets**: Provide copy-paste code examples
6. **Email Templates**: Built-in template library
7. **Scheduled Refresh**: Auto-update docs weekly
8. **User Accounts**: Save conversation history per user

## 🎉 Ready to Use!

The app is fully functional and ready for deployment. Just set your Anthropic API key and run `./start.sh`.

---

**Built**: July 2026  
**Tech Stack**: Python, Flask, ChromaDB, Claude Sonnet 4, Vanilla JS  
**Admin Password**: RICHCSM
