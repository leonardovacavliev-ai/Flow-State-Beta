# Vector Database Migration Guide

## Overview

The app now supports **two vector database providers**:
- **ChromaDB** (local, file-based) - for development
- **Pinecone** (cloud, managed) - for production

You can switch between them by changing a single environment variable.

---

## Quick Start with Pinecone

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create or update your `.env` file:

```bash
# Use Pinecone
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
PINECONE_INDEX_NAME=esp-loyalty-docs1
PINECONE_ENVIRONMENT=us-east-1
```

### 3. Test Connection

```bash
cd backend
python test_pinecone.py
```

Expected output:
```
✅ All tests passed!
Your Pinecone index is ready to use.
```

### 4. Migrate Data from ChromaDB

If you have existing data in ChromaDB:

```bash
cd backend
python migrate_to_pinecone.py
```

This will:
- Read all documents from `docs/` folder
- Re-vectorize and upload to Pinecone
- Preserve ESP namespaces and metadata

### 5. Start Application

```bash
./start.sh
```

The app will now use Pinecone instead of ChromaDB.

---

## Configuration Options

### ChromaDB (Local Development)

```bash
VECTOR_DB_PROVIDER=chromadb
CHROMA_PERSIST_DIR=./chroma_db
```

**Pros:**
- No API key needed
- Fast for local testing
- No internet required

**Cons:**
- Single instance only
- File-based (not cloud-native)
- No horizontal scaling

### Pinecone (Cloud Production)

```bash
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=esp-loyalty-docs1
PINECONE_ENVIRONMENT=us-east-1
```

**Pros:**
- Managed service (no infrastructure)
- Horizontal scaling built-in
- Multi-region support
- Persistent across deployments

**Cons:**
- Requires API key
- Costs money (free tier available)
- Network latency for queries

---

## How It Works

### Adapter Pattern

The app uses an **adapter pattern** to abstract vector database operations:

```python
# Factory function picks the right adapter
from adapters.vector.vector_manager import get_vector_adapter

# Reads VECTOR_DB_PROVIDER from environment
vectorizer = get_vector_adapter()

# Same interface for both providers
results = vectorizer.search(query, esp_filter='klaviyo', n_results=5)
vectorizer.add_document(text, metadata)
vectorizer.refresh_esp('klaviyo', docs_path)
```

### Code Structure

```
backend/
├── adapters/
│   └── vector/
│       ├── base.py              # VectorAdapter interface
│       ├── chroma_adapter.py    # ChromaDB implementation
│       ├── pinecone_adapter.py  # Pinecone implementation
│       └── vector_manager.py    # Factory function
├── app.py                       # Uses get_vector_adapter()
├── migrate_to_pinecone.py       # Migration script
└── test_pinecone.py             # Connection test
```

---

## Migration Workflow

### From Local to Cloud

**Current state**: Running locally with ChromaDB

**Step 1**: Set up Pinecone
```bash
# Add to .env (but keep VECTOR_DB_PROVIDER=chromadb for now)
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=esp-loyalty-docs1
```

**Step 2**: Test connection
```bash
python backend/test_pinecone.py
```

**Step 3**: Migrate data
```bash
python backend/migrate_to_pinecone.py
```

**Step 4**: Switch provider
```bash
# Update .env
VECTOR_DB_PROVIDER=pinecone
```

**Step 5**: Restart app
```bash
./start.sh
```

**Step 6**: Verify in admin panel
- Check ESP document counts
- Test search queries
- Compare responses with ChromaDB version

### Rollback

If something goes wrong:

```bash
# Switch back to ChromaDB
VECTOR_DB_PROVIDER=chromadb

# Restart
./start.sh
```

Your local ChromaDB data is untouched by the migration.

---

## Adding New Documents

### With ChromaDB
1. Admin → Add ESP or Add Link
2. Crawl → **Immediate vectorization** (blocking)
3. New docs available instantly

### With Pinecone
1. Admin → Add ESP or Add Link
2. Crawl → **Vectorization happens during crawl** (same flow)
3. New docs available after upload completes (~2-5 seconds)

Both providers use the **same admin UI workflow** - no code changes needed.

---

## Search Performance

### ChromaDB
- **Latency**: ~50-100ms (local file reads)
- **Throughput**: ~10 queries/second (single process)
- **Scalability**: Single instance only

### Pinecone
- **Latency**: ~100-200ms (network + query)
- **Throughput**: 100+ queries/second (distributed)
- **Scalability**: Horizontal (add more pods)

For most queries, the difference is negligible (AI model response time dominates).

---

## Pinecone Index Configuration

Your current index:
- **Name**: `esp-loyalty-docs1`
- **Dimension**: 384 (all-MiniLM-L6-v2 embeddings)
- **Metric**: Cosine similarity
- **Cloud**: AWS
- **Region**: us-east-1

### Free Tier Limits
- 1 index
- 10,000 vectors (enough for ~100-200 docs)
- No credit card required

### Paid Tiers
- Starter: $70/month (100K vectors)
- Standard: $250/month (1M vectors)
- Enterprise: Custom

---

## Environment Variables Reference

### Required for Pinecone

| Variable | Description | Example |
|----------|-------------|---------|
| `VECTOR_DB_PROVIDER` | Provider name | `pinecone` |
| `PINECONE_API_KEY` | API key from Pinecone dashboard | `pcsk_xxx...` |
| `PINECONE_INDEX_NAME` | Index name | `esp-loyalty-docs1` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `PINECONE_ENVIRONMENT` | AWS region | `us-east-1` |

### For ChromaDB

| Variable | Description | Default |
|----------|-------------|---------|
| `VECTOR_DB_PROVIDER` | Provider name | `chromadb` |
| `CHROMA_PERSIST_DIR` | Database directory | `./chroma_db` |

---

## Troubleshooting

### "Pinecone API key required"

**Cause**: `PINECONE_API_KEY` not set or invalid

**Fix**:
```bash
# Check .env file
cat .env | grep PINECONE

# Verify API key in Pinecone dashboard
# https://app.pinecone.io/
```

### "Index not found"

**Cause**: Index name mismatch or not created

**Fix**:
```bash
# Check index name in Pinecone dashboard
# Update .env
PINECONE_INDEX_NAME=your-actual-index-name
```

### "Module not found: pinecone"

**Cause**: Dependencies not installed

**Fix**:
```bash
cd backend
pip install -r requirements.txt
```

### Search returns no results

**Cause**: Index is empty (migration not run)

**Fix**:
```bash
python backend/migrate_to_pinecone.py
```

### ChromaDB warnings in logs

**Cause**: ChromaDB imports still present in code

**Fix**: Ignore - ChromaDB is imported but not used when `VECTOR_DB_PROVIDER=pinecone`

---

## Next Steps

After vector DB migration:

1. ✅ **Vector DB**: ChromaDB → Pinecone (current guide)
2. ⏭️ **Analytics DB**: SQLite → PostgreSQL
3. ⏭️ **Session Store**: In-memory → Redis
4. ⏭️ **Document Storage**: Local files → S3
5. ⏭️ **Deployment**: Local → Railway/Replit/GCP

See [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) for full roadmap.

---

## Support

- **Pinecone Docs**: https://docs.pinecone.io/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Migration Issues**: Create GitHub issue or contact DevOps team
