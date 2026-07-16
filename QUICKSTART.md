# Quick Start Guide

## What's Been Built

Your ESP Loyalty Helper app is **complete and ready to use**. Here's what you have:

### ✅ Complete Features

1. **Web Crawler** - Automatically fetched content from 9 documentation pages:
   - 3 Klaviyo integration docs
   - 6 DotDigital integration docs

2. **Vector Database** - All documentation + loyalty best practices PDF are vectorized and searchable using ChromaDB

3. **Flask Backend API** - Full REST API with:
   - RAG-powered chat using Claude Sonnet 4
   - Admin panel endpoints
   - Feedback submission
   - Dynamic ESP management

4. **Web Frontend** - Clean, branded interface with:
   - Yotpo brand colors and Helvetica Neue font
   - ESP selector sidebar (Klaviyo, DotDigital, Other/Webhook)
   - Chat interface with conversation history
   - Feedback form (saves to CSV)
   - Admin panel (password: RICHCSM)

## How to Run

### Step 1: Set Your API Key

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

Get your free Gemini API key at: https://makersuite.google.com/app/apikey

### Step 2: Start the App

```bash
cd "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP"
./start.sh
```

### Step 3: Open in Browser

Navigate to: **http://localhost:8000**

## Using the App

### For Users

1. **Select ESP** - Click on Klaviyo, DotDigital, or Other/Webhook in the left sidebar
2. **Ask Questions** - Type your question about loyalty flows, campaigns, triggers, etc.
3. **Get AI Guidance** - The assistant provides step-by-step instructions based on the documentation
4. **Submit Feedback** - Click the "Feedback" button to rate and comment

### For Admins (Password: RICHCSM)

1. **Click Admin** button in sidebar
2. **Enter password**: `RICHCSM`
3. **Manage ESPs**:
   - View existing ESPs and their documentation links
   - Add new links to existing ESPs
   - Create entirely new ESP integrations
4. **Refresh Documentation** - Re-crawl all links to update the knowledge base

## System Prompt

The AI assistant follows this behavior:

> You are an email marketing specialist and a loyalty retention specialist at once.
>
> Your goal is to recommend flows and campaigns to setup in the user's ESP using loyalty data. You will provide helpful feedback on how to create the flow, how to setup the right triggers, filters, audiences and email content, following industry best practices.
>
> Answer in a step by step manner, and walk through the process. Answer like you are talking to a person who knows how to work with the ESP, but isn't super in-depth. Make sure you double check your answers across your knowledgebase.
>
> Always prioritize the quality of answer, never try to answer too quickly. Also, if you are missing any information, never assume or guess anything, always ask the user to provide the missing information or context.
>
> Don't flatter and don't "glaze" the user. Be brief, direct and helpful. Tell them when they are wrong and provide helpful feedback.
>
> Aim to answer as short as possible. Act more as a tool than a person.

## File Structure

```
ESP Loyalty Helper APP/
├── backend/
│   ├── app.py              # Flask API server
│   ├── crawler.py          # Documentation web scraper
│   ├── vectorize.py        # ChromaDB vectorization
│   └── chroma_db/          # Vector database (47 chunks)
│
├── docs/
│   ├── klaviyo/            # 3 crawled docs
│   ├── dotdigital/         # 6 crawled docs
│   └── crawl_metadata.json # Tracking file
│
├── frontend/
│   ├── index.html          # Main UI
│   ├── styles.css          # Yotpo brand styling
│   └── app.js              # Frontend logic
│
├── feedback.csv            # User feedback (auto-created)
├── start.sh                # Startup script
├── test_setup.py           # Verification script
└── README.md               # Full documentation
```

## Brand Colors Used

- **Navy**: `#00205B` (primary brand color)
- **Lime**: `#C5E86C` (accent)
- **Teal**: `#72D1C8` (buttons, highlights)
- **Coral**: `#F8937D` (warnings)
- **Orange**: `#FDB768` (gradient)
- **Font**: Helvetica Neue

## API Endpoints

### Public Endpoints
- `POST /api/chat` - Send a chat message
- `POST /api/feedback` - Submit user feedback

### Admin Endpoints (require password)
- `POST /api/admin/verify` - Verify admin password
- `GET /api/admin/esps` - List all ESPs
- `GET /api/admin/esp/<name>/links` - Get links for an ESP
- `POST /api/admin/esp/<name>/add-link` - Add a link to ESP
- `POST /api/admin/esp/create` - Create new ESP
- `POST /api/admin/refresh` - Re-crawl and re-vectorize all docs

## Testing

Run the setup verification:
```bash
python3 test_setup.py
```

## Adding New ESPs

1. Go to Admin panel (password: RICHCSM)
2. Enter ESP name in "Create New ESP" section
3. Click "Create ESP"
4. Add documentation URLs for that ESP
5. Click "Refresh All" to crawl and vectorize

The new ESP will appear in the sidebar automatically.

## Troubleshooting

**Q: Chat isn't working**
A: Make sure you set `ANTHROPIC_API_KEY` environment variable with a valid key

**Q: Port 5000 already in use**
A: Edit `backend/app.py` and change the port number at the bottom

**Q: Frontend not loading**
A: Make sure you're accessing `http://localhost:8000` (not 5000, which is the API)

**Q: Admin panel won't login**
A: Password is `RICHCSM` (all caps)

## Next Steps

1. **Add More ESPs**: Use the admin panel to add Mailchimp, Braze, SendGrid, etc.
2. **Enhance Prompts**: Modify the system prompt in `backend/app.py` if needed
3. **Customize Styling**: Edit `frontend/styles.css` for design changes
4. **Deploy**: Consider deploying to a cloud service for team access

---

**Built with:** Flask, ChromaDB, Claude Sonnet 4, Vanilla JS
**Created:** July 2026
