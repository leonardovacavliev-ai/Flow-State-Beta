# ESP Loyalty Helper - Project Documentation

## Project Overview

An AI-powered assistant that helps Yotpo customers set up loyalty campaigns and email flows in Email Service Providers (ESPs). Currently runs **locally** as a Flask application with embedded ChromaDB and SQLite databases.

**Goals**: 
1. Migrate to a **stateless cloud architecture** that can scale for online Yotpo customers as a SaaS service
2. Support **dynamic knowledge base expansion**: easily add new ESPs and grow documentation for existing ESPs over time

---

## Current Architecture (Local)

### Tech Stack
- **Backend**: Flask REST API (Python)
- **AI**: Google Gemini Flash / Claude 3.5 Sonnet (configurable)
- **Vector Database**: ChromaDB (local persistent storage)
- **Analytics Database**: SQLite (local file)
- **Frontend**: Vanilla JavaScript (served via Python HTTP server)

### Key Components

#### 1. Flask Backend ([app.py](backend/app.py))
- RESTful API endpoints for chat, admin, and analytics
- Serves as orchestration layer between components
- Manages conversation state in-memory (request-scoped)
- Admin password: `RICHCSM` (hardcoded)

#### 2. Vector Database ([vectorize.py](backend/vectorize.py))
- ChromaDB persistent client at `backend/chroma_db/`
- Uses SentenceTransformers model: `all-MiniLM-L6-v2`
- Chunks documents (500 words, 50 word overlap)
- Filters by ESP for context-specific search
- Supports per-ESP refresh operations

#### 3. Analytics System ([analytics.py](backend/analytics.py))
- SQLite database at `backend/analytics.db`
- Tracks: sessions, messages, ESP selections, feedback, country/IP data
- Daily aggregates with sparkline data
- Batch write queue for performance (100 items or 5-second flush)
- IP geolocation via ipapi.co (1000 requests/day free tier)

#### 4. Configuration Management ([config_manager.py](backend/config_manager.py))
- JSON-based config at `backend/app_config.json`
- Audit trail at `backend/config_audit_log.json`
- Supports model switching (Gemini/Claude) and system prompt updates
- Stores API keys in environment variables (not persisted)

#### 5. AI Client ([ai_client.py](backend/ai_client.py))
- Provider abstraction (Gemini/Claude)
- Handles conversation history formatting
- RAG context injection
- Model selection: Gemini Flash (default) or Claude 3.5 Sonnet

#### 6. Web Crawler ([crawler.py](backend/crawler.py))
- BeautifulSoup-based content extraction
- Saves to `docs/{esp_name}/` folders
- Maintains metadata at `docs/crawl_metadata.json`
- **Manual trigger via admin panel** (supports dynamic ESP/doc addition)
- **Current ESPs**: Klaviyo, DotDigital, Attentive, Ometria, Other/Webhook
- **Adding new ESP**: Create folder, add URLs, crawl, auto-vectorize

#### 7. Frontend ([frontend/](frontend/))
- Single-page app (`index.html`, `app.js`, `styles.css`)
- Yotpo branded (Navy #00205B, Lime #C5E86C, Teal #72D1C8)
- Features: chat interface, ESP selector, admin panel, analytics dashboard
- No build process (vanilla JS)

### Data Flow

```
User → Frontend (JS) 
  ↓
Flask API (/api/chat)
  ↓
Vector Search (ChromaDB) → ESP-specific + Global docs (3+2 results)
  ↓
AI Provider (Gemini/Claude) → RAG-enhanced response
  ↓
Analytics (SQLite) → Track message, session, ESP
  ↓
Response → Frontend
```

### Current Limitations for Cloud

❌ **Stateful components**:
- ChromaDB persistent client (local file storage)
- SQLite database (single file, no concurrency)
- In-memory conversation history (lost on restart)
- Batch write queue (in-process threading)

❌ **Single-instance architecture**:
- No horizontal scaling
- File-based persistence (not cloud-native)
- Local IP-to-country lookups (rate-limited)

❌ **Security issues**:
- Hardcoded admin password
- No user authentication
- API keys in environment (not secret management)
- No rate limiting

---

## Target Architecture (Cloud-Native)

### Goal: Stateless, horizontally scalable SaaS application

### Proposed Stack

#### Application Layer
- **API Server**: Flask → **FastAPI** (async, better performance)
- **Deployment**: Containerized (Docker) on **AWS ECS/Fargate** or **Google Cloud Run**
- **Load Balancer**: AWS ALB / GCP Load Balancer
- **Auto-scaling**: Based on CPU/memory/request rate

#### Data Layer
- **Vector Database**: ChromaDB → **Pinecone** or **Weaviate Cloud**
  - Managed service, no local state
  - Horizontal scaling built-in
  - Namespace by tenant (Yotpo customer account)
  
- **Analytics Database**: SQLite → **PostgreSQL** (AWS RDS or GCP Cloud SQL)
  - Row-level security per tenant
  - Connection pooling (PgBouncer)
  - Read replicas for analytics queries
  
- **Session Store**: In-memory → **Redis** (AWS ElastiCache or GCP Memorystore)
  - Conversation history by session ID
  - TTL-based expiration
  - Shared across API instances

#### External Services
- **AI Providers**: Keep Gemini/Claude APIs (stateless)
- **IP Geolocation**: ipapi.co → **MaxMind GeoIP2** (self-hosted database)
- **Secret Management**: Environment vars → **AWS Secrets Manager** or **GCP Secret Manager**
- **Authentication**: None → **Auth0** or **Clerk** (OAuth, JWT)

#### Storage
- **Static Assets**: `frontend/` → **S3 + CloudFront** or **GCS + Cloud CDN**
- **Document Storage**: `docs/` folder → **S3** or **GCS**
  - Organized by ESP: `s3://bucket/esps/{esp_name}/{document_id}.txt`
  - Metadata in PostgreSQL (url, filename, crawl_date, vector_ids)
  - **Event-driven re-vectorization**: S3 upload → Lambda/Cloud Function → vector DB update
  - Supports adding new docs without downtime

#### Observability
- **Logging**: CloudWatch / Cloud Logging (structured JSON logs)
- **Metrics**: Prometheus + Grafana or native cloud metrics
- **Tracing**: OpenTelemetry → Jaeger/Tempo
- **Error Tracking**: Sentry

---

## Migration Strategy

### ✅ COMPLETED: GitHub & Deployment Setup
- [x] Created `.gitignore` (excludes databases, secrets, cache)
- [x] Created `.env.example` (environment variable template)
- [x] Updated `backend/app.py` for cloud deployment (PORT env var, host binding)
- [x] Created deployment configs (Procfile, Dockerfile, runtime.txt)
- [x] Created deployment documentation:
  - `QUICK_DEPLOY.md` - 10-minute deployment guide
  - `DEPLOYMENT.md` - Comprehensive deployment options
  - `GITHUB_CHECKLIST.md` - Step-by-step setup guide
  - `setup-github.sh` - Automated git initialization script

**Status**: Project ready to push to GitHub and deploy to Railway/Replit/GCP.

### ✅ COMPLETED: Vector Database Abstraction Layer

**See [VECTOR_DB_MIGRATION.md](VECTOR_DB_MIGRATION.md) and [QUICK_START_PINECONE.md](QUICK_START_PINECONE.md) for usage.**

This migration implements an **abstraction layer pattern** that:
- Supports both local (ChromaDB) and cloud (Pinecone) databases
- Allows switching providers via environment variables (no code changes)
- Makes future migrations trivial (1-2 hours instead of days)
- Maintains backwards compatibility with local development

#### Phase 1: Vector Database Abstraction Layer ✅ COMPLETE
- [x] Create `backend/adapters/vector/` structure
- [x] Implement `VectorAdapter` base interface
- [x] Create `ChromaDBAdapter` (extract from vectorize.py)
- [x] Create `PineconeAdapter` (new implementation)
- [x] Create `vector_manager.py` factory function
- [x] Update `vectorize.py` to use adapter (backwards compatible)
- [x] Update `app.py` vector search calls
- [x] Migration script (`migrate_to_pinecone.py`)
- [x] Test script (`test_pinecone.py`)
- [x] Documentation

**Your Pinecone Setup**:
- Index: `esp-loyalty-docs1`
- API Key: `pcsk_2aKY6Q_...` (in `.env`)
- Status: Ready to test

### ✅ COMPLETED: Analytics Database Abstraction Layer

**See [PHASE_2_ANALYTICS_DB.md](PHASE_2_ANALYTICS_DB.md) for complete guide.**

This migration implements an **abstraction layer pattern** for analytics database:
- Supports both local (SQLite) and cloud (PostgreSQL) databases
- Allows switching providers via environment variables (no code changes)
- Makes future migrations trivial
- Maintains backwards compatibility with local development

#### Phase 2: Analytics Database Abstraction Layer ✅ COMPLETE
- [x] Create `backend/adapters/database/` structure
- [x] Implement `DatabaseAdapter` base interface
- [x] Create `SQLiteAdapter` (extract from analytics.py)
- [x] Create `PostgresAdapter` (new implementation)
- [x] Create `db_manager.py` factory function
- [x] Migration script (`migrate_to_postgres.py`)
- [x] Test script (`test_postgres.py`)
- [x] Add `psycopg2-binary` to requirements.txt
- [x] Update `.env` with database config vars
- [x] Test with Railway PostgreSQL
- [x] Documentation

**Your PostgreSQL Setup (Railway)**:
- Database: `railway`
- Host: `tokaido.proxy.rlwy.net:14038`
- Status: ✅ Connected and tested

**To switch to PostgreSQL**: Change `.env` → `DATABASE_PROVIDER=postgres`

**Next**: Choose Phase 3 direction (see options below).

### Phase 2: Redis Session Store
  
- [ ] Set up Redis (ElastiCache/Memorystore)
  - Store conversation history (session_id → messages)
  - Add TTL (30 minutes default)
  - Update [app.py](backend/app.py) to read/write Redis

### Phase 2: Containerize Application
- [ ] Create Dockerfile
  - Multi-stage build (dependencies + app)
  - No local databases in container
  - Environment-based configuration
  
- [ ] Create docker-compose.yml (local dev)
  - App + Postgres + Redis
  - Volume mounts for development
  
- [ ] Set up CI/CD pipeline (GitHub Actions)
  - Build Docker image on push
  - Push to ECR/GCR
  - Deploy to ECS/Cloud Run
  
- [ ] **Build document ingestion pipeline**
  - Async job queue (Celery + Redis or AWS SQS)
  - Crawler worker: fetch URL → extract content → save to S3
  - Vectorization worker: S3 upload event → chunk → embed → upsert vector DB
  - Admin UI: trigger crawls, view queue status, manage ESPs

### Phase 3: Add Authentication & Multi-Tenancy
- [ ] Implement JWT authentication
  - Auth0/Clerk integration
  - Middleware to validate tokens
  - Extract tenant_id from JWT claims
  
- [ ] Add tenant isolation
  - Filter all DB queries by tenant_id
  - Namespace vector searches by tenant
  - Rate limiting per tenant

### Phase 4: Frontend Migration
- [ ] Build process (optional)
  - Vite or Create React App (if modernizing)
  - Or keep vanilla JS + minification
  
- [ ] Deploy to S3/GCS
  - Static hosting + CDN
  - Environment-based API URL configuration
  
- [ ] Update API endpoints
  - CORS configuration for production domain
  - API versioning (/api/v1/)

### Phase 5: Production Hardening
- [ ] Secret management (Secrets Manager)
- [ ] Monitoring & alerting
- [ ] Log aggregation
- [ ] Backup & disaster recovery
- [ ] Load testing & performance tuning

---

## Key Files Reference

### Backend
- [backend/app.py](backend/app.py) - Main Flask API (960 lines)
- [backend/analytics.py](backend/analytics.py) - SQLite analytics (699 lines)
- [backend/vectorize.py](backend/vectorize.py) - ChromaDB vectorization (172 lines)
- [backend/ai_client.py](backend/ai_client.py) - AI provider abstraction (214 lines)
- [backend/config_manager.py](backend/config_manager.py) - Config & audit (206 lines)
- [backend/crawler.py](backend/crawler.py) - Web scraping (minimal)
- [backend/requirements.txt](backend/requirements.txt) - Python dependencies

### Frontend
- [frontend/index.html](frontend/index.html) - Main UI
- [frontend/app.js](frontend/app.js) - Chat logic, admin panel
- [frontend/styles.css](frontend/styles.css) - Yotpo branding

### Data
- `backend/chroma_db/` - Local vector database (needs migration)
- `backend/analytics.db` - Local SQLite (needs migration)
- `docs/` - Crawled ESP documentation (47 chunks)
- `ESP_Support_Links - Sheet1.csv` - URL inventory

### Configuration
- `backend/app_config.json` - AI model, system prompt
- `backend/config_audit_log.json` - Change history

---

## System Prompt

```
You are an email marketing specialist and a loyalty retention specialist at once.

Your goal is to recommend flows and campaigns to setup in the user's ESP using loyalty data.
You will provide helpful feedback on how to create the flow, how to setup the right triggers, filters, audiences and email content, following industry best practices. In the handbook you will find some templates, but you will also help create more unique and outside the box flows and campaigns.

Answer in a step by step manner, and walk through the process. Answer like you are talking to a person who knows how to work with the ESP, but isn't super in-depth. Make sure you double check your answers across your knowledgebase.

Always prioritize the quality of answer, never try to answer too quickly. Also, if you are missing any information, never assume or guess anything, always ask the user to provide the missing information or context.

Don't flatter and don't "glaze" the user. Be brief, direct and helpful. Tell them when they are wrong and provide helpful feedback.

Aim to answer as short as possible. Act more as a tool than a person.
```

---

## API Endpoints Summary

### Chat & Sessions
- `POST /api/session/init` - Create session, get session_id
- `POST /api/session/end` - Mark session ended
- `POST /api/esp/select` - Track ESP selection
- `POST /api/chat` - Send message, get RAG response
- `POST /api/feedback` - Submit user feedback

### Admin - ESPs
- `POST /api/admin/verify` - Check admin password
- `GET /api/admin/esps` - List all ESPs + doc counts
- `GET /api/admin/esp/<name>/links` - Get links for ESP
- `POST /api/admin/esp/<name>/add-link` - Add URL to ESP
- `POST /api/admin/esp/<name>/crawl-selected` - Crawl URLs
- `POST /api/admin/esp/<name>/delete-links` - Remove URLs
- `POST /api/admin/esp/create` - Create new ESP
- `POST /api/admin/refresh` - Re-crawl + re-vectorize all

### Admin - Analytics
- `GET /api/admin/analytics?time_range=<range>` - Dashboard data

### Admin - Settings
- `GET /api/admin/settings/ai-model` - Current model config
- `POST /api/admin/settings/ai-model` - Change model
- `POST /api/admin/settings/api-key` - Update API key
- `GET /api/admin/settings/api-status` - Check AI status
- `GET /api/admin/settings/system-prompt` - Get prompt
- `POST /api/admin/settings/system-prompt` - Update prompt
- `GET /api/admin/settings/audit-log` - Change history
- `POST /api/admin/settings/restore` - Restore from backup

### Admin - Global Knowledge
- `GET /api/admin/global-knowledge/links` - Get global URLs
- `POST /api/admin/global-knowledge/add-link` - Add URL
- `POST /api/admin/global-knowledge/crawl-selected` - Crawl URLs
- `POST /api/admin/global-knowledge/delete-links` - Remove URLs

---

## Adding New ESPs & Documents (Current Flow)

### Workflow: Add a New ESP

**Current (Local)**:
1. Admin → Admin Panel → "Create New ESP"
2. Enter ESP name (e.g., "mailchimp")
3. System creates: `docs/mailchimp/` folder + CSV entry
4. Admin adds URLs to `ESP_Support_Links - Sheet1.csv` under "Mailchimp Integration URLs"
5. Admin → ESP management page → Select URLs → "Crawl Selected"
6. Backend:
   - `crawler.py` fetches content from URLs
   - Saves to `docs/mailchimp/{filename}.txt`
   - Updates `docs/crawl_metadata.json`
   - `vectorizer.refresh_esp('mailchimp')` → adds to ChromaDB
7. New ESP immediately available in chat dropdown

**Cloud (Proposed)**:
1. Admin → Admin Panel → "Add ESP"
2. Enter ESP metadata: name, display_name, logo, description
3. System creates: PostgreSQL `esps` table entry + Pinecone namespace
4. Admin adds URLs (bulk paste or one-by-one)
5. System adds to `crawl_queue` table with priority
6. **Async workers** process queue:
   - Crawler worker → fetches → S3 upload
   - Vectorization worker → chunks → embeds → Pinecone upsert
   - Updates `esp_documents` table (status, vector_ids)
7. Admin monitors crawl progress via UI (queue dashboard)
8. Once crawls complete, ESP auto-appears in chat dropdown (cached list refreshes every 5 min)

### Workflow: Add Documents to Existing ESP

**Current (Local)**:
1. Admin → ESP page (e.g., Klaviyo) → "Add Link"
2. Paste URL → "Crawl"
3. Immediate crawl + vectorization (blocking, ~2-5 seconds)

**Cloud (Proposed)**:
1. Admin → ESP page → "Add URLs" (bulk textarea or file upload)
2. System validates URLs, adds to `crawl_queue`
3. Returns immediately with job IDs
4. Admin sees queue status: "3 URLs queued, 1 processing, 5 completed"
5. WebSocket/polling updates status in real-time
6. On completion, shows preview of extracted content
7. Admin can approve/reject (future: auto-approve trusted domains)

### Workflow: Refresh Existing Documents

**Current (Local)**:
1. Admin → "Refresh All" button
2. Re-crawls all URLs in CSV (blocking, ~30-60 seconds)
3. Deletes entire ChromaDB collection
4. Re-vectorizes from scratch

**Cloud (Proposed)**:
1. Admin → ESP page → "Refresh All" or "Refresh Selected"
2. System:
   - Fetches current content
   - Compares `content_hash` with stored version
   - Only re-vectorizes if changed (incremental update)
   - Keeps old chunks in vector DB during re-indexing (atomic swap)
3. Scheduled refresh: Nightly cron job checks all docs (updates only changed ones)

### Example: Adding Mailchimp

**Step 1**: Research Mailchimp docs
```
https://mailchimp.com/help/integrate-yotpo-with-mailchimp/
https://mailchimp.com/help/use-mailchimp-for-loyalty-programs/
https://mailchimp.com/help/create-an-automation/
```

**Step 2**: Admin UI
- Name: `mailchimp`
- Display: `Mailchimp`
- URLs: (paste 3 URLs above)
- Click "Add ESP & Crawl"

**Step 3**: Backend processing (cloud)
```python
# Pseudo-code for cloud version
def add_esp(name, display_name, urls):
    # 1. Create ESP
    esp = db.create(esps, {name: name, display_name: display_name})
    vector_db.create_namespace(name)
    
    # 2. Queue documents
    for url in urls:
        doc = db.create(esp_documents, {esp_id: esp.id, url: url})
        queue.push(crawl_queue, {document_id: doc.id, priority: 1})
    
    # 3. Return immediately (async processing happens in background)
    return {"esp_id": esp.id, "queued_docs": len(urls)}
```

**Step 4**: Worker processes queue
```python
# Crawler worker
def process_crawl_job(job):
    doc = db.get(esp_documents, job.document_id)
    content = crawler.extract_content(doc.url)
    
    s3_key = f"esps/{doc.esp.name}/{doc.id}.txt"
    s3.upload(s3_key, content)
    
    db.update(esp_documents, doc.id, {
        crawl_status: 'completed',
        content_hash: sha256(content),
        last_crawled_at: now()
    })
```

**Step 5**: Vectorization (triggered by S3 upload event)
```python
# Vectorization worker
def on_s3_upload(event):
    s3_key = event['s3_key']  # esps/mailchimp/{doc_id}.txt
    content = s3.download(s3_key)
    
    doc_id = extract_doc_id_from_s3_key(s3_key)
    doc = db.get(esp_documents, doc_id)
    
    # Chunk + embed
    chunks = chunk_text(content, size=500, overlap=50)
    vectors = embed_model.encode(chunks)
    
    # Upsert to vector DB (namespace = ESP name)
    vector_ids = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        vid = f"{doc.esp.name}_{doc.id}_{i}"
        pinecone.upsert(
            namespace=doc.esp.name,
            id=vid,
            values=vector,
            metadata={
                'esp': doc.esp.name,
                'url': doc.url,
                'filename': doc.filename,
                'chunk_index': i
            }
        )
        vector_ids.append(vid)
    
    # Update document record
    db.update(esp_documents, doc.id, {vector_ids: vector_ids})
```

**Step 6**: Mailchimp now available
- User selects "Mailchimp" from dropdown
- Asks: "How do I set up a welcome series?"
- RAG search: `namespace='mailchimp', query='welcome series', top_k=3`
- AI generates response with Mailchimp-specific context

---

## RAG Context Retrieval

For each user message:
1. ESP-specific search: 3 results (filtered by ESP)
2. Global knowledge search: 2 results (best practices, general info)
3. Context formatting: Source number, filename, URL, text chunk
4. Total: 5 document chunks per query

---

## Analytics Metrics Tracked

- Sessions (unique visitors)
- Unique users (by IP)
- Messages per conversation
- Feedback submissions (rating + comments)
- ESP selection breakdown
- Country breakdown
- Average session duration
- Average message length
- Sparkline data (daily trends)

---

## Dynamic Knowledge Base Expansion

### Current Capability (Local)
The app **already supports** dynamic ESP/document management via admin panel:
- ✅ Add new ESP: `POST /api/admin/esp/create` → creates folder + CSV entry
- ✅ Add URLs to ESP: `POST /api/admin/esp/{name}/add-link`
- ✅ Crawl selected URLs: `POST /api/admin/esp/{name}/crawl-selected`
- ✅ Auto-vectorization: Crawled docs → ChromaDB (per-ESP namespace)
- ✅ Delete docs: `POST /api/admin/esp/{name}/delete-links` → removes from vector DB

### Cloud Enhancement Strategy

#### 1. ESP Catalog Management (PostgreSQL)
```sql
-- New tables for cloud version
CREATE TABLE esps (
  id UUID PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,  -- 'klaviyo', 'mailchimp'
  display_name VARCHAR(200),           -- 'Klaviyo', 'Mailchimp'
  status VARCHAR(20),                  -- 'active', 'beta', 'deprecated'
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE esp_documents (
  id UUID PRIMARY KEY,
  esp_id UUID REFERENCES esps(id),
  url TEXT NOT NULL,
  filename VARCHAR(500),
  content_hash VARCHAR(64),            -- Detect changes
  crawl_status VARCHAR(20),            -- 'pending', 'completed', 'failed'
  last_crawled_at TIMESTAMP,
  vector_namespace VARCHAR(100),       -- Pinecone namespace
  vector_ids JSONB,                    -- Array of chunk IDs in vector DB
  created_at TIMESTAMP
);

CREATE TABLE crawl_queue (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES esp_documents(id),
  priority INTEGER,                    -- Higher = crawl first
  attempts INTEGER DEFAULT 0,
  status VARCHAR(20),                  -- 'queued', 'processing', 'completed', 'failed'
  error_message TEXT,
  created_at TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);
```

#### 2. Event-Driven Ingestion Pipeline

**Architecture**:
```
Admin UI → API → Add to crawl_queue
                ↓
         SQS/Pub-Sub → Crawler Worker
                ↓
         Extract content → S3 upload
                ↓
         S3 Event → Vectorization Worker
                ↓
         Chunk + Embed → Pinecone/Weaviate upsert
                ↓
         Update esp_documents table (status, vector_ids)
```

**Benefits**:
- ✅ **Async processing**: No blocking API calls
- ✅ **Retry logic**: Failed crawls re-queued automatically
- ✅ **Incremental updates**: Add single doc without re-indexing entire ESP
- ✅ **Monitoring**: Queue depth, failure rates, processing time

#### 3. Auto-Discovery & Scheduled Refresh

**Option A: Manual Curation** (Recommended for launch)
- Admin adds URLs via UI
- Scheduled refresh (weekly): re-crawl all URLs, update if content changed (hash comparison)

**Option B: Auto-Discovery** (Future enhancement)
- Sitemap parsing (e.g., `klaviyo.com/docs/sitemap.xml`)
- Link crawling with depth limit (respect robots.txt)
- ML-based relevance filtering

#### 4. Multi-Source Knowledge

Beyond web crawling:
- **PDF uploads**: Admin uploads integration guides → S3 → vectorize
- **API integrations**: Pull from Notion, Confluence, Google Docs (OAuth)
- **Community contributions**: Customer-submitted best practices (moderated)

#### 5. Version Control & Rollback

Track document versions:
```sql
CREATE TABLE document_versions (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES esp_documents(id),
  version INTEGER,
  content_s3_key TEXT,
  content_hash VARCHAR(64),
  vector_ids JSONB,
  created_at TIMESTAMP
);
```

**Rollback flow**: Admin sees bad answer → check source doc → rollback to previous version → re-vectorize

---

## Open Questions for Migration

1. **Multi-tenancy model**:
   - Separate vector namespace per Yotpo customer?
   - **Shared ESP knowledge base** (recommended) + tenant-specific custom docs?

2. **Pricing/rate limiting**:
   - Messages per customer per month?
   - AI token budget per tier?

3. **Document management permissions**:
   - **Global admins** (Yotpo team): Manage all ESPs, crawl public docs
   - **Tenant admins** (customer CSMs): Upload private integration guides (optional)
   - Auto-refresh schedule? (Daily? Weekly? On-demand only?)

4. **Authentication**:
   - SSO with Yotpo main platform?
   - Standalone user accounts?

5. **Deployment region**:
   - US-only? Multi-region?
   - Data residency requirements?

6. **ESP prioritization**:
   - Launch with current 5 ESPs (Klaviyo, DotDigital, Attentive, Ometria, Other)?
   - Roadmap: Mailchimp, Braze, Iterable, SendGrid, Customer.io?
   - Customer vote/request system for new ESPs?

---

## Local Development Setup

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Set API keys
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# 3. Start servers
./start.sh

# 4. Access app
open http://localhost:8000
```

**Admin password**: `RICHCSM`

---

## Next Steps

1. Review this document with Yotpo engineering team
2. Decide on cloud provider (AWS vs GCP)
3. Choose vector database (Pinecone vs Weaviate vs pgvector)
4. Set up development/staging environments
5. Begin Phase 1: Database externalization
