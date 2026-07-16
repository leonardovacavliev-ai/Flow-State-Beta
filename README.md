# ESP Loyalty Helper App

An AI-powered assistant for setting up loyalty campaigns and flows in Email Service Providers (ESPs) integrated with Yotpo Loyalty.

## 🚀 Quick Deploy

Want to get this online? See:
- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - Get online in 10 minutes (Railway, Replit, GCP)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Full deployment guide with all options
- **[CLAUDE.md](CLAUDE.md)** - Production architecture & cloud migration strategy

## Features

- **Chat Interface**: Ask questions about loyalty flows, campaign setup, triggers, and best practices
- **ESP Selection**: Switch between Klaviyo, DotDigital, Attentive, Ometria, and Other/Webhook
- **RAG-Powered**: Uses vectorized documentation for accurate, context-aware answers
- **AI Models**: Google Gemini Flash (default) or Claude 3.5 Sonnet
- **Admin Panel**: Password-protected admin area to manage ESPs, add links, and refresh documentation
- **Analytics Dashboard**: Track usage, sessions, feedback, and geographic data
- **Web Crawler**: Automatically extract and vectorize ESP documentation

## Local Setup

### Prerequisites

- Python 3.9+
- Google Gemini API Key or Anthropic API Key

### Quick Start

1. **Clone the repository** (after pushing to GitHub):
   ```bash
   git clone https://github.com/YOUR_USERNAME/esp-loyalty-helper.git
   cd esp-loyalty-helper
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Run the app**:
   ```bash
   ./start.sh
   ```
   
   Or manually:
   ```bash
   # Terminal 1: Backend
   cd backend && python app.py
   
   # Terminal 2: Frontend
   cd frontend && python -m http.server 8000
   ```

5. **Access the app**: Open `http://localhost:8000`

## Project Structure

```
.
├── backend/
│   ├── app.py              # Flask API server
│   ├── crawler.py          # Web scraper for ESP docs
│   ├── vectorize.py        # ChromaDB vectorization
│   └── chroma_db/          # Vector database storage
├── docs/
│   ├── klaviyo/            # Klaviyo documentation
│   ├── dotdigital/         # DotDigital documentation
│   └── crawl_metadata.json # Crawl tracking
├── frontend/
│   ├── index.html          # Main UI
│   ├── styles.css          # Yotpo brand styling
│   └── app.js              # Frontend logic
├── feedback.csv            # User feedback (auto-created)
└── ESP_Support_Links - Sheet1.csv  # ESP URLs to crawl

```

## Admin Panel

**Password**: `RICHCSM`

Admin features:
- View all ESPs and their documentation links
- Add new links to existing ESPs
- Create new ESP integrations
- Refresh all documentation (re-crawl and re-vectorize)

## Adding New ESPs

1. Click "Admin" in the sidebar
2. Enter password: `RICHCSM`
3. Create a new ESP by entering its name
4. Add documentation URLs for that ESP
5. Click "Refresh All" to crawl and vectorize

## Brand Colors

The app uses Yotpo's official brand colors:
- Navy: `#00205B`
- Lime: `#C5E86C`
- Teal: `#72D1C8`
- Coral: `#F8937D`
- Orange: `#FDB768`

Font: **Helvetica Neue**

## API Endpoints

- `POST /api/chat` - Send chat message
- `POST /api/feedback` - Submit feedback
- `POST /api/admin/verify` - Verify admin password
- `GET /api/admin/esps` - List ESPs
- `GET /api/admin/esp/<name>/links` - Get ESP links
- `POST /api/admin/esp/<name>/add-link` - Add link to ESP
- `POST /api/admin/esp/create` - Create new ESP
- `POST /api/admin/refresh` - Refresh all documentation

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**: Make sure you've exported the API key in your terminal before running the backend.

**Port already in use**: Change the port in `app.py` (backend) or when starting the frontend server.

**CORS errors**: Make sure the backend is running on port 5000 and frontend is accessing it correctly.

## Future Enhancements

- More ESP integrations (Mailchimp, Braze, etc.)
- Export chat history
- Multi-language support
- Advanced filtering in admin panel
- Scheduled auto-refresh of documentation
