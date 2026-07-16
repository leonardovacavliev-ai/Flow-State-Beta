# Complete Build Prompt: ESP Loyalty Helper App

Build a full-stack AI-powered chatbot application that helps users set up loyalty campaigns and email flows in Email Service Providers (ESPs) integrated with Yotpo Loyalty. The app should provide expert guidance based on crawled documentation and industry best practices.

---

## Tech Stack

### Backend
- **Python 3.9+**
- **Flask** - REST API server
- **Flask-CORS** - CORS handling
- **ChromaDB** - Vector database for document storage and RAG
- **sentence-transformers** (all-MiniLM-L6-v2) - Text embeddings
- **BeautifulSoup4** - Web scraping
- **Google Gemini API** (gemini-flash-latest) - AI chat responses
- **pypdf** - PDF text extraction

### Frontend
- **Vanilla HTML/CSS/JavaScript** (no framework)
- **Marked.js** - Markdown rendering
- **Google Fonts** - Dancing Script (cursive signature)

### Storage
- **ChromaDB** - Persistent vector storage in `backend/chroma_db/`
- **SessionStorage** - Browser session for conversation history
- **CSV files** - User feedback storage

---

## Application Overview

### Core Functionality
1. **AI Chat Interface** - Users ask questions about loyalty flows, campaigns, triggers, and email content
2. **RAG System** - Searches vectorized documentation to provide context-aware answers
3. **ESP Selection** - Switch between Klaviyo, DotDigital, and Other/Webhook integrations
4. **Conversation History** - Per-ESP session-based history with modal viewer
5. **Admin Panel** - Password-protected management for adding/managing ESP documentation
6. **Feedback System** - Users submit ratings and comments saved to CSV

---

## Design System

### Brand Colors (Yotpo)
```css
--yotpo-navy: #00205B
--yotpo-black: #333333
--yotpo-lime: #C5E86C
--yotpo-teal: #72D1C8
--yotpo-coral: #F8937D
--yotpo-orange: #FDB768
--yotpo-white: #FFFFFF
--yotpo-gray: #666666
--yotpo-light-gray: #EFEFEF
```

### Dark Sidebar Gradient
```css
background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f1419 100%);
```

### Orange Gradient (Welcome Message)
```css
background: linear-gradient(135deg, #FDB768 0%, #F8937D 50%, #F5a84d 100%);
```

### Typography
- **Primary Font**: Helvetica Neue (all UI)
- **Signature Font**: Dancing Script (cursive, for "Created by Leo Vacavliev, CSM")
- **Weights**: 300 (light), 400 (regular), 500 (medium), 600 (semibold)

### Layout
- **Sidebar**: 280px width, dark gradient, fixed position
- **Main content**: Flex, full height minus input
- **Border radius**: 6px for buttons, 8px for modals, 12px for messages
- **Spacing**: 0.5rem gaps, 1rem padding standard

---

## File Structure

```
AI ESP Loyalty Helper APP/
├── backend/
│   ├── app.py              # Flask API server
│   ├── crawler.py          # Web scraper for ESP docs
│   ├── vectorize.py        # ChromaDB vectorization system
│   └── chroma_db/          # Vector database storage
├── docs/
│   ├── klaviyo/            # Klaviyo crawled docs (.txt files)
│   ├── dotdigital/         # DotDigital crawled docs (.txt files)
│   ├── other_webhook/      # Other/Webhook docs (empty initially)
│   └── crawl_metadata.json # Tracking file for crawled URLs
├── frontend/
│   ├── index.html          # Main UI
│   ├── styles.css          # All styling
│   └── app.js              # Frontend logic
├── feedback.csv            # User feedback (auto-created)
├── start.sh                # Startup script
├── ESP_Support_Links - Sheet1.csv  # URLs to crawl
└── Yotpo New Rules of Loyalty Strategies.pdf  # Best practices doc
```

---

## Detailed Component Specifications

### 1. Backend: Flask API (`backend/app.py`)

#### Environment Variables Required
```bash
GEMINI_API_KEY="your-google-gemini-api-key"
```

#### API Endpoints

**POST /api/chat**
- Input: `{ message: string, esp: string, history: array }`
- Process:
  1. Normalize ESP name (replace `/` with `_`)
  2. Search vector database for relevant docs (5 results)
  3. Build context from search results
  4. Call Gemini API with system prompt + context + history
  5. Return response + sources
- Output: `{ response: string, sources: array }`

**POST /api/feedback**
- Input: `{ email: string, esp: string, rating: string, comments: string }`
- Action: Append to `feedback.csv` with timestamp
- Output: `{ success: true }`

**POST /api/admin/verify**
- Input: `{ password: string }`
- Validate: password === "RICHCSM"
- Output: `{ valid: boolean }`

**GET /api/admin/esps**
- Returns list of ESPs with document counts
- Includes display name mapping (other_webhook → "Other/Webhook")
- Output: `{ esps: [{ name, display_name, doc_count }] }`

**GET /api/admin/esp/<name>/links**
- Returns array of URLs for specified ESP
- Reads from `crawl_metadata.json`
- Output: `{ links: string[] }`

**POST /api/admin/esp/<name>/add-link**
- Input: `{ password: string, url: string }`
- Action: Append URL to CSV file
- Output: `{ success: true }`

**POST /api/admin/esp/create**
- Input: `{ password: string, name: string }`
- Action: Create directory and CSV section
- Output: `{ success: true }`

**POST /api/admin/refresh**
- Input: `{ password: string }`
- Action: Re-crawl all URLs and re-vectorize
- Output: `{ success: true, message: string }`

#### System Prompt
```
You are an email marketing specialist and a loyalty retention specialist at once.

Your goal is to recommend flows and campaigns to setup in the user's ESP using loyalty data. 
You will provide helpful feedback on how to create the flow, how to setup the right triggers, filters, audiences and email content, following industry best practices. In the handbook you will find some templates, but you will also help create more unique and outside the box flows and campaigns.

Answer in a step by step manner, and walk through the process. Answer like you are talking to a person who knows how to work with the ESP, but isn't super in-depth. Make sure you double check your answers across your knowledgebase.

Always prioritize the quality of answer, never try to answer too quickly. Also, if you are missing any information, never assume or guess anything, always ask the user to provide the missing information or context.

Don't flatter and don't "glaze" the user. Be brief, direct and helpful. Tell them when they are wrong and provide helpful feedback.

Aim to answer as short as possible. Act more as a tool than a person.
```

#### Gemini Integration
```python
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name='models/gemini-flash-latest',
    system_instruction=SYSTEM_PROMPT
)

# Convert history format
history_formatted = [
    {"role": "user" if msg['role'] == 'user' else "model", 
     "parts": [msg['content']]}
    for msg in conversation_history
]

chat = model.start_chat(history=history_formatted)
response = chat.send_message(user_message)
```

---

### 2. Web Crawler (`backend/crawler.py`)

#### Functions
**extract_main_content(url)**
- Fetch URL with requests
- Parse with BeautifulSoup
- Remove script, style, nav, footer, header tags
- Extract main/article/div.content
- Clean whitespace
- Return plain text

**crawl_and_save(csv_path, docs_path)**
- Read CSV line by line
- Detect ESP sections: "Klaviyo Integration URLs", "DotDigital Integration URLs", "Other/Webhook Integration URLs"
- For each URL under a section:
  - Crawl content
  - Generate filename from URL path
  - Save to `docs/{esp_name}/{filename}.txt`
  - Track in metadata.json
- Add 1 second delay between requests

#### CSV Format
```
Klaviyo Integration URLs
https://url1.com
https://url2.com

DotDigital Integration URLs
https://url3.com
https://url4.com

Other/Webhook Integration URLs
```

---

### 3. Vector Database (`backend/vectorize.py`)

#### Class: DocumentVectorizer

**__init__(persist_directory)**
- Initialize ChromaDB PersistentClient
- Use SentenceTransformerEmbeddingFunction (all-MiniLM-L6-v2)
- Create/get collection "esp_docs"

**chunk_text(text, chunk_size=500, overlap=50)**
- Split text into word chunks
- Overlap for context continuity
- Return array of chunks

**add_document(text, metadata)**
- Chunk the document
- Add each chunk with metadata: `{esp, filename, source_url, filepath, chunk_index, total_chunks}`
- Generate unique ID: `{esp}_{filename}_{chunk_index}`

**vectorize_all_docs(docs_path)**
- Load crawl_metadata.json
- For each ESP and its documents:
  - Read file content
  - Extract source URL
  - Call add_document with metadata
- Add best practices PDF separately with esp="global"

**search(query, esp_filter, n_results=5)**
- Query collection with optional WHERE filter
- Return documents and metadata

**refresh_esp(esp_name, docs_path)**
- Delete existing chunks for ESP
- Re-add all documents for that ESP

---

### 4. Frontend UI (`frontend/index.html`)

#### Structure
```html
<div class="app-container">
  <aside class="sidebar">
    <div class="logo">
      <svg>yotpo.</svg>
      <p class="subtitle">ESP Loyalty Helper</p>
    </div>
    
    <div class="esp-selector">
      <h3>Select ESP</h3>
      <div class="esp-list">
        <!-- Split button groups -->
        <div class="esp-button-group active">
          <button class="esp-item active" data-esp="klaviyo">Klaviyo</button>
          <button class="esp-history-btn" data-esp="klaviyo">
            <svg><!-- clock icon --></svg>
          </button>
        </div>
        <!-- Repeat for dotdigital and other/webhook -->
      </div>
    </div>
    
    <div class="sidebar-footer">
      <button class="feedback-btn">📝 Feedback</button>
      <button class="admin-btn">⚙️ Admin</button>
      <div class="sidebar-signature">Created by Leo Vacavliev, CSM</div>
    </div>
  </aside>
  
  <main class="main-content">
    <div class="chat-container">
      <div class="chat-messages" id="chatMessages">
        <div class="welcome-message">
          <h2>Yotpo x Klaviyo</h2>
          <p>Ask me anything about setting up loyalty campaigns...</p>
        </div>
      </div>
      
      <div class="chat-input-container">
        <textarea id="messageInput" rows="3"></textarea>
        <button id="sendBtn" class="send-btn">Send</button>
      </div>
    </div>
  </main>
</div>

<!-- Modals: History, Feedback, Admin -->
```

#### Logo SVG
Use simple SVG text element:
```html
<svg width="120" height="40" viewBox="0 0 120 40">
  <text x="0" y="30" font-family="Helvetica Neue" font-size="32" font-weight="700" fill="white">yotpo.</text>
</svg>
```

---

### 5. Frontend Styling (`frontend/styles.css`)

#### Key CSS Features

**Split Button Animation**
```css
.esp-button-group .esp-history-btn {
    width: 0;
    padding: 0;
    opacity: 0;
    transition: all 0.3s ease;
}

.esp-button-group.active .esp-history-btn {
    width: 42px;
    padding: 0.875rem 0.5rem;
    opacity: 1;
}
```

**Markdown Formatting**
- Style h1-h4 with proper hierarchy
- Code blocks: gray background, monospace font
- Inline code: `rgba(0, 0, 0, 0.05)` background
- Links: orange color
- Blockquotes: orange left border
- Tables: bordered with gray headers
- Lists: proper indentation

**Scrollable Modal**
```css
.modal-content {
    max-height: 85vh;
    overflow-y: auto;
}
```

**Signature Style**
```css
.sidebar-signature {
    font-family: 'Dancing Script', cursive;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.5);
}
```

---

### 6. Frontend Logic (`frontend/app.js`)

#### Global State
```javascript
let selectedESP = 'klaviyo';
let adminPassword = '';
let conversationHistories = {
    'klaviyo': [],
    'dotdigital': [],
    'other/webhook': []
};
```

#### Session Storage
- Load histories on init: `sessionStorage.getItem('espConversationHistories')`
- Save after each message: `sessionStorage.setItem(...)`
- Store format: `{ role, content, timestamp }`

#### Key Functions

**sendMessage()**
1. Get message from textarea
2. Add user message to chat UI
3. Show loading indicator
4. Normalize ESP name (replace `/` with `_`)
5. Fetch POST to `/api/chat` with message, esp, history
6. Parse response
7. Render markdown with `marked.parse()`
8. Add assistant message to chat UI
9. Save both messages to history
10. Scroll to bottom

**addMessage(role, content)**
- Create message div with label and content
- If role is "assistant", render markdown with marked.js
- If role is "user", render plain text
- Append to chat and scroll

**ESP Selection**
- On click: update active class on button group
- Set selectedESP variable
- Clear chat and show welcome message "Yotpo x {ESP}"

**History Modal**
- On history button click: open modal with conversation pairs
- Group messages in pairs (user + assistant)
- Render markdown for assistant messages
- Show timestamp for each conversation
- Clear history button with confirmation

**Admin Panel**
- Verify password: "RICHCSM"
- Load ESPs: fetch `/api/admin/esps`
- For each ESP: fetch links and display
- Add link: append to CSV via API
- Refresh all: re-crawl and re-vectorize

#### Markdown Rendering
```javascript
if (role === 'assistant' && typeof marked !== 'undefined') {
    contentDiv.innerHTML = marked.parse(content);
} else {
    contentDiv.textContent = content;
}
```

---

## Initial Data Setup

### CSV File (`ESP_Support_Links - Sheet1.csv`)
```csv
Klaviyo Integration URLs
https://support.yotpo.com/docs/klaviyo-oauth-integration-yotpo-loyalty-referrals
https://support.yotpo.com/docs/loyalty-emails-setup-guide-for-klaviyo
https://help.klaviyo.com/hc/en-us/articles/115002774932
https://help.klaviyo.com/hc/en-us/articles/40939669530011

DotDigital Integration URLs
https://support.yotpo.com/docs/integrating-yotpo-loyalty-referrals-with-dotdigital
https://marketing.help.dotdigital.com/en/articles/8199355-easyeditor-extensions-app-blocks-overview
https://marketing.help.dotdigital.com/en/articles/8198850-email-campaigns-overview
https://marketing.help.dotdigital.com/en/articles/8198854-campaign-setup
https://marketing.help.dotdigital.com/en/articles/8198950-triggered-campaigns-overview
https://marketing.help.dotdigital.com/en/articles/8198952-convert-a-standard-campaign-into-a-triggered-campaign

Other/Webhook Integration URLs
```

### Metadata JSON (`docs/crawl_metadata.json`)
```json
{
  "klaviyo": [
    {
      "url": "https://...",
      "filename": "docs_loyalty-emails-setup-guide.txt",
      "filepath": "/path/to/docs/klaviyo/docs_loyalty-emails-setup-guide.txt"
    }
  ],
  "dotdigital": [...],
  "other_webhook": []
}
```

---

## Startup Script (`start.sh`)

```bash
#!/bin/bash

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: GEMINI_API_KEY is not set"
    echo "Please set it before starting:"
    echo "  export GEMINI_API_KEY='your-api-key-here'"
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting backend server..."
cd "$DIR/backend"
python3 app.py &
BACKEND_PID=$!

sleep 2

echo "Starting frontend server..."
cd "$DIR/frontend"
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo "✓ App is running!"
echo "Backend:  http://localhost:5000"
echo "Frontend: http://localhost:8000"

cleanup() {
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM
wait
```

Make executable: `chmod +x start.sh`

---

## Step-by-Step Build Instructions

### Step 1: Setup Project Structure
```bash
mkdir -p "AI ESP Loyalty Helper APP"/{backend,frontend,docs/{klaviyo,dotdigital,other_webhook}}
cd "AI ESP Loyalty Helper APP"
```

### Step 2: Install Python Dependencies
```bash
pip3 install flask flask-cors beautifulsoup4 requests chromadb sentence-transformers pypdf google-generativeai
```

### Step 3: Create CSV with URLs
Create `ESP_Support_Links - Sheet1.csv` with the format shown above.

### Step 4: Build Crawler
Write `backend/crawler.py` with:
- `extract_main_content(url)` function
- `crawl_and_save(csv_path, docs_path)` function
- Run it to populate `docs/` folders

### Step 5: Build Vectorizer
Write `backend/vectorize.py` with:
- `DocumentVectorizer` class
- Chunking logic (500 words, 50 overlap)
- ChromaDB integration
- Run it to create `backend/chroma_db/`

### Step 6: Build Flask API
Write `backend/app.py` with:
- All 8 API endpoints
- Gemini integration
- CORS enabled
- Admin password "RICHCSM"

### Step 7: Build Frontend HTML
Write `frontend/index.html` with:
- Sidebar with logo, ESP buttons, feedback/admin buttons, signature
- Main chat area with messages and input
- Three modals (history, feedback, admin)
- Include marked.js CDN
- Include Dancing Script font

### Step 8: Build Frontend CSS
Write `frontend/styles.css` with:
- Dark gradient sidebar
- Split button animation (0→42px width)
- Orange active states
- Markdown formatting styles
- Modal styling (85vh scrollable)
- Signature cursive font

### Step 9: Build Frontend JS
Write `frontend/app.js` with:
- Session storage for histories
- ESP selection with split button logic
- Send message with RAG
- Markdown rendering with marked.js
- History modal with conversation pairs
- Admin panel with link management
- Feedback form submission

### Step 10: Create Startup Script
Write `start.sh` with dual server startup.

### Step 11: Initial Data Population
```bash
cd backend
python3 crawler.py      # Crawl all URLs
python3 vectorize.py    # Vectorize into ChromaDB
```

### Step 12: Start Application
```bash
export GEMINI_API_KEY="your-key"
./start.sh
```

Open: `http://localhost:8000`

---

## Testing Checklist

### Chat Functionality
- [ ] Can send messages
- [ ] Markdown renders properly (bold, lists, code, links)
- [ ] Conversation history maintained during session
- [ ] Responses include relevant documentation context
- [ ] Loading indicator appears while waiting

### ESP Selection
- [ ] Clicking ESP button switches context
- [ ] Welcome message shows "Yotpo x {ESP}"
- [ ] Active button shows orange background
- [ ] History button appears only when ESP is selected (split animation)
- [ ] Each ESP has separate conversation history

### History Modal
- [ ] Clock icon button opens history
- [ ] Shows all conversations for selected ESP
- [ ] Timestamps display correctly
- [ ] Markdown rendered in assistant messages
- [ ] Clear history works with confirmation
- [ ] Empty state shows when no history

### Admin Panel
- [ ] Password "RICHCSM" grants access
- [ ] All ESPs listed with document counts
- [ ] Links display as clickable URLs (not [object Object])
- [ ] Can add new links
- [ ] Can create new ESP
- [ ] Refresh all re-crawls and updates database

### Feedback System
- [ ] Modal opens from sidebar button
- [ ] ESP auto-populated
- [ ] Submission creates/appends to feedback.csv
- [ ] CSV has headers: Date, Email, Selected ESP, Rating, Comments

### Design
- [ ] Sidebar uses dark gradient
- [ ] Orange buttons match brand
- [ ] Helvetica Neue used throughout
- [ ] Signature in Dancing Script cursive
- [ ] Split button animation smooth (0.3s)
- [ ] Modals scrollable at 85vh

---

## Common Issues & Solutions

**Issue: "[object Object]" in admin links**
- Fix: Ensure `linksData.links.map(link => ...)` where link is a string, not object

**Issue: Markdown not rendering**
- Fix: Include marked.js CDN before app.js
- Fix: Use `marked.parse()` not `marked()`

**Issue: History button always visible**
- Fix: CSS should set width: 0, opacity: 0 by default
- Fix: Only `.active` group shows history button

**Issue: Gemini API 404 error**
- Fix: Use `models/gemini-flash-latest` not `gemini-1.5-flash`

**Issue: CORS errors**
- Fix: Add `CORS(app)` in Flask
- Fix: Backend on 5000, frontend on 8000

**Issue: Split button not splitting**
- Fix: Parent div needs `.esp-button-group` class
- Fix: Apply `.active` class to parent, not just button

---

## Environment Variables

```bash
# Required
export GEMINI_API_KEY="your-google-gemini-api-key"

# Get free key at:
https://makersuite.google.com/app/apikey
```

---

## Final File Sizes (Approximate)

- `backend/app.py`: ~200 lines
- `backend/crawler.py`: ~80 lines
- `backend/vectorize.py`: ~150 lines
- `frontend/index.html`: ~150 lines
- `frontend/styles.css`: ~600 lines
- `frontend/app.js`: ~500 lines

---

## Success Criteria

The app is complete when:
1. ✅ User can chat and get relevant loyalty campaign advice
2. ✅ Responses include markdown formatting (bold, lists, code blocks, links)
3. ✅ Each ESP maintains separate conversation history
4. ✅ History modal shows past conversations with timestamps
5. ✅ Admin can add new ESP documentation URLs
6. ✅ Admin can refresh database to crawl new links
7. ✅ Feedback submissions save to CSV
8. ✅ Split button animation works (history appears on selection)
9. ✅ Design matches Yotpo brand (orange, dark gradient, Helvetica Neue)
10. ✅ Signature displays in cursive at bottom of sidebar

---

## Optional Enhancements (Future)

- Export conversation history as PDF/JSON
- Persistent database (PostgreSQL) instead of session storage
- User accounts and authentication
- More ESPs (Mailchimp, Braze, SendGrid)
- Email template library with copy-paste snippets
- Analytics dashboard for popular questions
- Scheduled documentation refresh (cron job)
- Multi-language support

---

**Build Time Estimate**: 4-6 hours for experienced developer
**Difficulty**: Intermediate (requires Python, Flask, JavaScript, RAG concepts)
**AI Model**: Google Gemini Flash (free tier available)
