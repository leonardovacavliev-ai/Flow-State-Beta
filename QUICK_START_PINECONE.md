# Quick Start: Pinecone Migration

## 1-Minute Setup

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Test connection (should pass)
export PINECONE_API_KEY=pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
export PINECONE_INDEX_NAME=esp-loyalty-docs1
python test_pinecone.py
```

## 2-Minute Migration

```bash
# Migrate your data (30-60 seconds)
python migrate_to_pinecone.py

# Edit .env - change these lines:
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
PINECONE_INDEX_NAME=esp-loyalty-docs1

# Restart
cd .. && ./start.sh
```

## Rollback (if needed)

```bash
# Edit .env - change one line:
VECTOR_DB_PROVIDER=chromadb

# Restart
./start.sh
```

## What This Does

- ✅ Switches from local ChromaDB to cloud Pinecone
- ✅ Zero code changes - just environment variables
- ✅ Same admin panel workflow
- ✅ Backwards compatible (can switch back anytime)
- ✅ Ready for cloud deployment

## Your Credentials

```
Index: esp-loyalty-docs1
API Key: pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
Region: us-east-1
```

## Next Steps

After Pinecone works:
1. PostgreSQL for analytics (SQLite replacement)
2. Redis for sessions (in-memory replacement)
3. S3 for documents (local files replacement)
4. Deploy to Railway/Replit/GCP

See [VECTOR_DB_MIGRATION.md](VECTOR_DB_MIGRATION.md) for full guide.
