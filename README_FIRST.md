# ⚡ Vector DB Migration - Quick Reference

## ✅ What's Done
Complete adapter layer for ChromaDB ↔ Pinecone switching.

## 🚀 Quick Test (5 minutes)

```bash
# 1. Install
cd backend && pip install -r requirements.txt

# 2. Test Pinecone
export PINECONE_API_KEY=pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU
export PINECONE_INDEX_NAME=esp-loyalty-docs1
python test_pinecone.py

# 3. Migrate
python migrate_to_pinecone.py

# 4. Switch (edit .env)
VECTOR_DB_PROVIDER=pinecone

# 5. Run
cd .. && ./start.sh
```

## 📚 Documentation

- **Fast**: [QUICK_START_PINECONE.md](QUICK_START_PINECONE.md)
- **Full**: [VECTOR_DB_MIGRATION.md](VECTOR_DB_MIGRATION.md)
- **Tech**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Summary**: [SESSION_SUMMARY.md](SESSION_SUMMARY.md)

## 🔧 Your Credentials

```
Index:   esp-loyalty-docs1
API Key: pcsk_2aKY6Q_... (see .env)
```

## 📍 What's Next

Phase 2: Analytics DB (SQLite → PostgreSQL)

---

✨ **Ready to test!**
