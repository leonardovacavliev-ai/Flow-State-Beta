# Database Migration Guide - Abstraction Layer Implementation

## Mission

Migrate ESP Loyalty Helper from local databases (SQLite + ChromaDB) to cloud-native databases (PostgreSQL + Pinecone) using an **abstraction layer pattern** that:
1. Supports both local and cloud environments
2. Makes future provider changes trivial (1-2 hours instead of days)
3. Maintains backwards compatibility
4. Enables horizontal scaling

---

## Current State

### Files Using Databases
1. **`backend/analytics.py`** (699 lines)
   - SQLite at `backend/analytics.db`
   - Tables: `sessions`, `messages`, `esp_selections`, `feedback`, `daily_aggregates`
   - Batch write queue (threading.Timer)
   - IP geolocation tracking

2. **`backend/vectorize.py`** (172 lines)
   - ChromaDB at `backend/chroma_db/`
   - Collection: `esp_docs`
   - SentenceTransformers: `all-MiniLM-L6-v2`
   - Chunking: 500 words, 50 word overlap
   - ESP-based filtering

3. **`backend/app.py`** (960 lines)
   - Imports and uses both analytics + vectorize
   - Lines 19-20: imports
   - Multiple calls throughout for chat, admin, analytics endpoints

---

## Target Architecture

### Abstraction Layer Pattern

```
Application Code (app.py, analytics.py, etc.)
           ↓
    Factory Functions
           ↓
    Abstract Base Classes (Interface)
           ↓
    Concrete Adapters (SQLite, PostgreSQL, ChromaDB, Pinecone, etc.)
```

**Key Principle**: Application code never imports provider-specific libraries. It only uses abstract interfaces.

---

## Implementation Plan

### Phase 1: Database Abstraction Layer

#### Step 1.1: Create Directory Structure

```bash
mkdir -p backend/adapters/database
mkdir -p backend/adapters/vector
touch backend/adapters/__init__.py
touch backend/adapters/database/__init__.py
touch backend/adapters/vector/__init__.py
```

#### Step 1.2: Create Database Base Interface

**File**: `backend/adapters/database/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseAdapter(ABC):
    """Abstract interface for database operations"""
    
    @abstractmethod
    def connect(self):
        """Establish database connection"""
        pass
    
    @abstractmethod
    def close(self):
        """Close database connection"""
        pass
    
    # Session operations
    @abstractmethod
    def insert_session(self, session_id: str, start_time: datetime, ip_address: str, country: str) -> bool:
        """Insert new session"""
        pass
    
    @abstractmethod
    def end_session(self, session_id: str, end_time: datetime) -> bool:
        """Update session end time"""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        pass
    
    # Message operations
    @abstractmethod
    def insert_message(self, session_id: str, role: str, content: str, 
                      timestamp: datetime, message_length: int) -> bool:
        """Insert message"""
        pass
    
    @abstractmethod
    def get_messages_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session"""
        pass
    
    # ESP selection operations
    @abstractmethod
    def insert_esp_selection(self, session_id: str, esp_name: str, 
                            timestamp: datetime) -> bool:
        """Record ESP selection"""
        pass
    
    # Feedback operations
    @abstractmethod
    def insert_feedback(self, session_id: str, rating: int, comment: str, 
                       timestamp: datetime) -> bool:
        """Insert user feedback"""
        pass
    
    # Analytics operations
    @abstractmethod
    def get_analytics(self, time_range: str) -> Dict[str, Any]:
        """Get analytics for dashboard
        
        Args:
            time_range: '24h', '7d', '30d', or 'all'
            
        Returns:
            Dict with keys: total_sessions, unique_users, total_messages,
                          avg_session_duration, avg_message_length,
                          esp_breakdown, feedback_stats, country_breakdown,
                          sparkline_data
        """
        pass
    
    @abstractmethod
    def update_daily_aggregates(self, date: str) -> bool:
        """Update daily aggregate statistics"""
        pass
    
    # Schema management
    @abstractmethod
    def create_tables(self):
        """Create all required tables if they don't exist"""
        pass
    
    @abstractmethod
    def migrate_schema(self, from_version: int, to_version: int):
        """Run schema migrations"""
        pass
```

#### Step 1.3: Create SQLite Adapter (Existing System)

**File**: `backend/adapters/database/sqlite_adapter.py`

Extract ALL database logic from `backend/analytics.py` into this adapter. This is the reference implementation.

**Key sections to extract**:
- Lines 14-65: `create_tables()` function
- Lines 67-89: `insert_session()` function  
- Lines 91-108: `end_session()` function
- Lines 110-142: `insert_message()` function
- Lines 144-161: `insert_esp_selection()` function
- Lines 163-180: `insert_feedback()` function
- Lines 328-425: `get_analytics()` function
- Lines 431-544: Daily aggregates logic

**Implementation**:
```python
import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import DatabaseAdapter

class SQLiteAdapter(DatabaseAdapter):
    def __init__(self, db_path: str = 'backend/analytics.db'):
        self.db_path = db_path
        self.batch_queue = []
        self.queue_lock = threading.Lock()
        self.flush_timer = None
        self.create_tables()
    
    def connect(self):
        return sqlite3.connect(self.db_path)
    
    def close(self):
        self._flush_batch_queue()
        if self.flush_timer:
            self.flush_timer.cancel()
    
    def create_tables(self):
        # Copy logic from analytics.py lines 14-65
        conn = self.connect()
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                ip_address TEXT,
                country TEXT
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message_length INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # ... rest of tables (esp_selections, feedback, daily_aggregates)
        
        conn.commit()
        conn.close()
    
    def insert_session(self, session_id: str, start_time: datetime, 
                      ip_address: str, country: str) -> bool:
        # Copy from analytics.py lines 67-89
        # Use batch queue pattern
        pass
    
    # ... implement all other methods from base interface
```

#### Step 1.4: Create PostgreSQL Adapter

**File**: `backend/adapters/database/postgres_adapter.py`

```python
import psycopg2
from psycopg2 import pool
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import DatabaseAdapter

class PostgresAdapter(DatabaseAdapter):
    def __init__(self, connection_url: str, min_conn: int = 1, max_conn: int = 10):
        self.connection_url = connection_url
        # Use connection pooling for better performance
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            min_conn, max_conn, connection_url
        )
        self.create_tables()
    
    def connect(self):
        return self.connection_pool.getconn()
    
    def close(self):
        self.connection_pool.closeall()
    
    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()
        
        # Sessions table (note: SERIAL instead of AUTOINCREMENT)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                ip_address TEXT,
                country TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                message_length INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time)')
        
        # ... rest of tables
        
        conn.commit()
        self.connection_pool.putconn(conn)
    
    def insert_session(self, session_id: str, start_time: datetime, 
                      ip_address: str, country: str) -> bool:
        conn = self.connect()
        try:
            cursor = conn.cursor()
            # Note: %s placeholder instead of ?
            cursor.execute('''
                INSERT INTO sessions (session_id, start_time, ip_address, country)
                VALUES (%s, %s, %s, %s)
            ''', (session_id, start_time, ip_address, country))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error inserting session: {e}")
            return False
        finally:
            self.connection_pool.putconn(conn)
    
    # ... implement all other methods
    
    # Key differences from SQLite:
    # 1. Placeholder: ? → %s
    # 2. AUTOINCREMENT → SERIAL
    # 3. DATETIME('now') → NOW()
    # 4. strftime() → TO_CHAR()
    # 5. Use connection pooling
```

**SQL Syntax Differences to Handle**:
| SQLite | PostgreSQL |
|--------|------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| `TEXT` column for timestamps | `TIMESTAMP` column |
| `DATETIME('now')` | `NOW()` |
| `strftime('%Y-%m-%d', timestamp)` | `TO_CHAR(timestamp, 'YYYY-MM-DD')` |
| `?` placeholder | `%s` placeholder |
| `||` string concat | `||` or `CONCAT()` |

#### Step 1.5: Create Database Factory

**File**: `backend/db_manager.py`

```python
import os
from typing import Optional
from adapters.database.base import DatabaseAdapter
from adapters.database.sqlite_adapter import SQLiteAdapter
from adapters.database.postgres_adapter import PostgresAdapter

_db_instance: Optional[DatabaseAdapter] = None

def get_database() -> DatabaseAdapter:
    """Factory function to get database adapter based on environment"""
    global _db_instance
    
    if _db_instance is not None:
        return _db_instance
    
    provider = os.getenv('DATABASE_PROVIDER', 'sqlite').lower()
    
    if provider == 'postgres' or provider == 'postgresql':
        connection_url = os.getenv('DATABASE_URL')
        if not connection_url:
            raise ValueError("DATABASE_URL environment variable not set for PostgreSQL")
        _db_instance = PostgresAdapter(connection_url)
        print("✅ Using PostgreSQL database")
        
    elif provider == 'sqlite':
        db_path = os.getenv('SQLITE_DB_PATH', 'backend/analytics.db')
        _db_instance = SQLiteAdapter(db_path)
        print("✅ Using SQLite database (local mode)")
        
    else:
        raise ValueError(f"Unknown database provider: {provider}")
    
    return _db_instance

def close_database():
    """Close database connection"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
```

#### Step 1.6: Update analytics.py

Replace ALL direct database calls with adapter calls:

```python
# OLD:
import sqlite3
conn = sqlite3.connect('analytics.db')
# ... direct SQL

# NEW:
from db_manager import get_database

db = get_database()
db.insert_session(session_id, start_time, ip_address, country)
```

**Changes needed**:
1. Remove all `import sqlite3`
2. Remove all direct SQL operations
3. Add `from db_manager import get_database`
4. Replace function calls with adapter method calls
5. Keep batch queue logic (or move to adapter)

---

### Phase 2: Vector Database Abstraction Layer

#### Step 2.1: Create Vector Base Interface

**File**: `backend/adapters/vector/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

class VectorAdapter(ABC):
    """Abstract interface for vector database operations"""
    
    @abstractmethod
    def initialize(self):
        """Initialize vector database (create index/collection if needed)"""
        pass
    
    @abstractmethod
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Insert or update documents
        
        Args:
            documents: List of dicts with keys:
                - id: str (unique identifier)
                - text: str (document content)
                - embedding: List[float] (vector representation)
                - metadata: Dict (esp, url, filename, chunk_index, etc.)
        
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5, 
              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Metadata filters (e.g., {'esp': 'klaviyo'})
        
        Returns:
            List of dicts with keys: id, text, metadata, score
        """
        pass
    
    @abstractmethod
    def delete_by_filter(self, filters: Dict[str, Any]) -> bool:
        """Delete documents matching filters
        
        Args:
            filters: Metadata filters (e.g., {'esp': 'klaviyo'})
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection
        
        Returns:
            Dict with keys: total_vectors, esps, index_size, etc.
        """
        pass
    
    @abstractmethod
    def clear_collection(self) -> bool:
        """Delete all vectors (use with caution)"""
        pass
```

#### Step 2.2: Create ChromaDB Adapter

**File**: `backend/adapters/vector/chromadb_adapter.py`

Extract logic from `backend/vectorize.py`:

```python
import chromadb
from typing import List, Dict, Any, Optional
from .base import VectorAdapter

class ChromaDBAdapter(VectorAdapter):
    def __init__(self, persist_directory: str = "./backend/chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "esp_docs"
        self.collection = None
        self.initialize()
    
    def initialize(self):
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        try:
            ids = [doc['id'] for doc in documents]
            embeddings = [doc['embedding'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            documents_text = [doc['text'] for doc in documents]
            
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_text
            )
            return True
        except Exception as e:
            print(f"Error upserting documents: {e}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 5,
              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        where_clause = filters if filters else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )
        
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'score': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted
    
    def delete_by_filter(self, filters: Dict[str, Any]) -> bool:
        try:
            self.collection.delete(where=filters)
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    # ... implement other methods
```

#### Step 2.3: Create Pinecone Adapter

**File**: `backend/adapters/vector/pinecone_adapter.py`

```python
import pinecone
from typing import List, Dict, Any, Optional
from .base import VectorAdapter

class PineconeAdapter(VectorAdapter):
    def __init__(self, api_key: str, environment: str, index_name: str = "esp-docs"):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.index = None
        self.initialize()
    
    def initialize(self):
        pinecone.init(api_key=self.api_key, environment=self.environment)
        
        # Create index if it doesn't exist
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=384,  # all-MiniLM-L6-v2 dimension
                metric='cosine'
            )
        
        self.index = pinecone.Index(self.index_name)
    
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        try:
            # Pinecone uses namespaces for filtering (use ESP name as namespace)
            # Group documents by ESP
            by_namespace = {}
            for doc in documents:
                esp = doc['metadata'].get('esp', 'global')
                if esp not in by_namespace:
                    by_namespace[esp] = []
                
                by_namespace[esp].append((
                    doc['id'],
                    doc['embedding'],
                    doc['metadata']
                ))
            
            # Upsert by namespace
            for namespace, docs in by_namespace.items():
                self.index.upsert(
                    vectors=docs,
                    namespace=namespace
                )
            
            return True
        except Exception as e:
            print(f"Error upserting to Pinecone: {e}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 5,
              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        
        # Use namespace for ESP filtering
        namespace = filters.get('esp', '') if filters else ''
        
        # Remove 'esp' from filters (handled by namespace)
        metadata_filter = {k: v for k, v in (filters or {}).items() if k != 'esp'}
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            filter=metadata_filter if metadata_filter else None
        )
        
        # Format results
        formatted = []
        for match in results['matches']:
            formatted.append({
                'id': match['id'],
                'text': match['metadata'].get('text', ''),
                'metadata': match['metadata'],
                'score': match['score']
            })
        
        return formatted
    
    def delete_by_filter(self, filters: Dict[str, Any]) -> bool:
        try:
            esp = filters.get('esp')
            if esp:
                # Delete entire namespace
                self.index.delete(delete_all=True, namespace=esp)
            else:
                # Delete by filter (more expensive)
                self.index.delete(filter=filters)
            return True
        except Exception as e:
            print(f"Error deleting from Pinecone: {e}")
            return False
    
    # ... implement other methods
```

#### Step 2.4: Create Vector Factory

**File**: `backend/vector_manager.py`

```python
import os
from typing import Optional
from adapters.vector.base import VectorAdapter
from adapters.vector.chromadb_adapter import ChromaDBAdapter
from adapters.vector.pinecone_adapter import PineconeAdapter

_vector_instance: Optional[VectorAdapter] = None

def get_vector_db() -> VectorAdapter:
    """Factory function to get vector database adapter"""
    global _vector_instance
    
    if _vector_instance is not None:
        return _vector_instance
    
    provider = os.getenv('VECTOR_DB_PROVIDER', 'chromadb').lower()
    
    if provider == 'pinecone':
        api_key = os.getenv('PINECONE_API_KEY')
        environment = os.getenv('PINECONE_ENVIRONMENT')
        index_name = os.getenv('PINECONE_INDEX_NAME', 'esp-docs')
        
        if not api_key or not environment:
            raise ValueError("PINECONE_API_KEY and PINECONE_ENVIRONMENT required")
        
        _vector_instance = PineconeAdapter(api_key, environment, index_name)
        print("✅ Using Pinecone vector database")
        
    elif provider == 'chromadb':
        persist_dir = os.getenv('CHROMADB_PATH', './backend/chroma_db')
        _vector_instance = ChromaDBAdapter(persist_dir)
        print("✅ Using ChromaDB vector database (local mode)")
        
    else:
        raise ValueError(f"Unknown vector database provider: {provider}")
    
    return _vector_instance
```

#### Step 2.5: Update vectorize.py

```python
# OLD:
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("esp_docs")

# NEW:
from vector_manager import get_vector_db

vector_db = get_vector_db()

def add_documents(esp_name, docs_directory):
    # ... existing chunking logic ...
    
    # Format for adapter
    documents = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        documents.append({
            'id': f"{esp_name}_{filename}_{i}",
            'text': chunk,
            'embedding': embedding.tolist(),
            'metadata': {
                'esp': esp_name,
                'filename': filename,
                'url': url,
                'chunk_index': i
            }
        })
    
    # Use adapter
    vector_db.upsert_documents(documents)
```

---

### Phase 3: Update Application Code

#### Step 3.1: Update app.py

Replace imports:
```python
# OLD:
from analytics import (insert_session, end_session, insert_message, 
                      insert_esp_selection, insert_feedback, get_analytics)
from vectorize import search_documents, refresh_esp, refresh_all_esps

# NEW:
from db_manager import get_database, close_database
from vector_manager import get_vector_db
```

Update endpoint code:
```python
# Example: /api/session/init
@app.route('/api/session/init', methods=['POST'])
def init_session():
    db = get_database()
    session_id = str(uuid.uuid4())
    
    # Get IP and country
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    country = get_country_from_ip(ip_address)
    
    # Use adapter
    db.insert_session(session_id, datetime.now(), ip_address, country)
    
    return jsonify({'session_id': session_id})

# Example: /api/chat
@app.route('/api/chat', methods=['POST'])
def chat():
    db = get_database()
    vector_db = get_vector_db()
    
    # ... existing logic ...
    
    # Vector search
    query_embedding = embed_model.encode(user_message).tolist()
    results = vector_db.search(
        query_embedding=query_embedding,
        top_k=5,
        filters={'esp': selected_esp} if selected_esp != 'Other/Webhook' else None
    )
    
    # ... rest of chat logic ...
```

Add cleanup on shutdown:
```python
import atexit

@atexit.register
def cleanup():
    close_database()
```

---

### Phase 4: Dependencies and Configuration

#### Step 4.1: Update requirements.txt

Add to `backend/requirements.txt`:
```
# Database adapters
psycopg2-binary>=2.9.0  # PostgreSQL
# OR: psycopg2>=2.9.0 if building from source

# Vector database adapters
pinecone-client>=2.2.0  # Pinecone

# Connection pooling (optional but recommended)
sqlalchemy>=2.0.0  # If using SQLAlchemy pools
```

#### Step 4.2: Update .env.example

Add to `.env.example`:
```bash
# Database Configuration
DATABASE_PROVIDER=sqlite  # Options: sqlite, postgres
DATABASE_URL=postgresql://user:password@host:port/dbname  # For PostgreSQL

# SQLite Configuration (local dev)
SQLITE_DB_PATH=backend/analytics.db

# Vector Database Configuration
VECTOR_DB_PROVIDER=chromadb  # Options: chromadb, pinecone
CHROMADB_PATH=./backend/chroma_db

# Pinecone Configuration (production)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_environment  # e.g., us-east1-gcp
PINECONE_INDEX_NAME=esp-docs
```

---

### Phase 5: Data Migration Scripts

#### Step 5.1: SQLite → PostgreSQL Migration

**File**: `backend/migrate_to_postgres.py`

```python
"""
Migrate data from SQLite to PostgreSQL

Usage:
    python migrate_to_postgres.py --source backend/analytics.db --target $DATABASE_URL
"""

import sqlite3
import psycopg2
import argparse
from datetime import datetime

def migrate_data(sqlite_path, postgres_url):
    # Connect to both databases
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(postgres_url)
    
    print("Connected to both databases")
    
    # Get cursors
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Migrate sessions
    print("Migrating sessions...")
    sqlite_cur.execute("SELECT * FROM sessions")
    sessions = sqlite_cur.fetchall()
    
    for session in sessions:
        pg_cur.execute('''
            INSERT INTO sessions (session_id, start_time, end_time, ip_address, country)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO NOTHING
        ''', (session['session_id'], session['start_time'], session['end_time'],
              session['ip_address'], session['country']))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(sessions)} sessions")
    
    # Migrate messages
    print("Migrating messages...")
    sqlite_cur.execute("SELECT * FROM messages")
    messages = sqlite_cur.fetchall()
    
    for msg in messages:
        pg_cur.execute('''
            INSERT INTO messages (session_id, role, content, timestamp, message_length)
            VALUES (%s, %s, %s, %s, %s)
        ''', (msg['session_id'], msg['role'], msg['content'],
              msg['timestamp'], msg['message_length']))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(messages)} messages")
    
    # Migrate esp_selections
    print("Migrating ESP selections...")
    sqlite_cur.execute("SELECT * FROM esp_selections")
    esp_sels = sqlite_cur.fetchall()
    
    for sel in esp_sels:
        pg_cur.execute('''
            INSERT INTO esp_selections (session_id, esp_name, timestamp)
            VALUES (%s, %s, %s)
        ''', (sel['session_id'], sel['esp_name'], sel['timestamp']))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(esp_sels)} ESP selections")
    
    # Migrate feedback
    print("Migrating feedback...")
    sqlite_cur.execute("SELECT * FROM feedback")
    feedback = sqlite_cur.fetchall()
    
    for fb in feedback:
        pg_cur.execute('''
            INSERT INTO feedback (session_id, rating, comment, timestamp)
            VALUES (%s, %s, %s, %s)
        ''', (fb['session_id'], fb['rating'], fb['comment'], fb['timestamp']))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(feedback)} feedback entries")
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n🎉 Migration complete!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='SQLite database path')
    parser.add_argument('--target', required=True, help='PostgreSQL connection URL')
    args = parser.parse_args()
    
    migrate_data(args.source, args.target)
```

#### Step 5.2: ChromaDB → Pinecone Migration

**File**: `backend/migrate_to_pinecone.py`

```python
"""
Migrate vectors from ChromaDB to Pinecone

Usage:
    python migrate_to_pinecone.py --chroma-path backend/chroma_db
"""

import chromadb
import pinecone
import os
from tqdm import tqdm

def migrate_vectors(chroma_path):
    # Initialize Pinecone
    api_key = os.getenv('PINECONE_API_KEY')
    environment = os.getenv('PINECONE_ENVIRONMENT')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'esp-docs')
    
    pinecone.init(api_key=api_key, environment=environment)
    
    # Create index if needed
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            name=index_name,
            dimension=384,
            metric='cosine'
        )
    
    index = pinecone.Index(index_name)
    
    # Load ChromaDB
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection("esp_docs")
    
    # Get all data
    print("Fetching data from ChromaDB...")
    data = collection.get(include=['embeddings', 'metadatas', 'documents'])
    
    total = len(data['ids'])
    print(f"Found {total} vectors to migrate")
    
    # Batch upsert to Pinecone (100 at a time)
    batch_size = 100
    
    for i in tqdm(range(0, total, batch_size)):
        batch_end = min(i + batch_size, total)
        
        # Group by ESP (namespace)
        by_namespace = {}
        
        for j in range(i, batch_end):
            esp = data['metadatas'][j].get('esp', 'global')
            
            if esp not in by_namespace:
                by_namespace[esp] = []
            
            by_namespace[esp].append((
                data['ids'][j],
                data['embeddings'][j],
                {**data['metadatas'][j], 'text': data['documents'][j]}
            ))
        
        # Upsert by namespace
        for namespace, vectors in by_namespace.items():
            index.upsert(vectors=vectors, namespace=namespace)
    
    print(f"\n✅ Migrated {total} vectors to Pinecone")
    print(f"   Index stats: {index.describe_index_stats()}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--chroma-path', default='backend/chroma_db')
    args = parser.parse_args()
    
    migrate_vectors(args.chroma_path)
```

---

### Phase 6: Testing

#### Step 6.1: Local Testing with PostgreSQL

```bash
# 1. Start PostgreSQL (Docker)
docker run -d \
  --name esp-postgres \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=esp_loyalty \
  -p 5432:5432 \
  postgres:15

# 2. Set environment
export DATABASE_PROVIDER=postgres
export DATABASE_URL="postgresql://postgres:testpass@localhost:5432/esp_loyalty"
export VECTOR_DB_PROVIDER=chromadb  # Still use ChromaDB locally

# 3. Run app
cd backend && python app.py
```

#### Step 6.2: Test Pinecone

```bash
# 1. Sign up for Pinecone free tier
# 2. Get API key and environment
# 3. Set environment
export VECTOR_DB_PROVIDER=pinecone
export PINECONE_API_KEY=your_key
export PINECONE_ENVIRONMENT=us-east1-gcp
export PINECONE_INDEX_NAME=esp-docs-test

# 4. Run migration
python backend/migrate_to_pinecone.py

# 5. Test app
cd backend && python app.py
```

#### Step 6.3: Integration Tests

Create `backend/test_adapters.py`:
```python
import pytest
from db_manager import get_database
from vector_manager import get_vector_db
from datetime import datetime
import uuid

def test_database_adapter():
    db = get_database()
    
    # Test session insert
    session_id = str(uuid.uuid4())
    result = db.insert_session(session_id, datetime.now(), '127.0.0.1', 'US')
    assert result == True
    
    # Test session retrieval
    session = db.get_session(session_id)
    assert session is not None
    assert session['session_id'] == session_id

def test_vector_adapter():
    vector_db = get_vector_db()
    
    # Test document upsert
    docs = [{
        'id': 'test_1',
        'text': 'Test document',
        'embedding': [0.1] * 384,
        'metadata': {'esp': 'klaviyo', 'url': 'test.com'}
    }]
    result = vector_db.upsert_documents(docs)
    assert result == True
    
    # Test search
    results = vector_db.search([0.1] * 384, top_k=1, filters={'esp': 'klaviyo'})
    assert len(results) > 0
```

---

## Environment Variables Summary

### Local Development (Default)
```bash
DATABASE_PROVIDER=sqlite
VECTOR_DB_PROVIDER=chromadb
```

### Production (PostgreSQL + Pinecone)
```bash
DATABASE_PROVIDER=postgres
DATABASE_URL=postgresql://user:pass@host:5432/dbname
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=xxx
PINECONE_ENVIRONMENT=us-east1-gcp
PINECONE_INDEX_NAME=esp-docs
```

### Testing (Mix and match)
```bash
# Test PostgreSQL locally
DATABASE_PROVIDER=postgres
DATABASE_URL=postgresql://localhost:5432/test
VECTOR_DB_PROVIDER=chromadb  # Keep local

# Test Pinecone locally
DATABASE_PROVIDER=sqlite
VECTOR_DB_PROVIDER=pinecone  # Cloud vector DB
PINECONE_API_KEY=xxx
```

---

## Verification Checklist

After implementation, verify:

- [ ] Local dev still works (SQLite + ChromaDB)
- [ ] PostgreSQL adapter works (docker test)
- [ ] Pinecone adapter works (free tier test)
- [ ] Can switch providers via env vars
- [ ] Migration scripts work
- [ ] All analytics endpoints work
- [ ] Vector search works with filters
- [ ] Admin panel ESP management works
- [ ] No hardcoded database imports in app code
- [ ] Connection pooling works (PostgreSQL)
- [ ] Batch operations work (analytics)
- [ ] Cleanup on shutdown works

---

## Future Provider Additions

To add a new database provider (e.g., MySQL, MongoDB):

1. Create `backend/adapters/database/mysql_adapter.py`
2. Implement `DatabaseAdapter` interface
3. Add to factory in `db_manager.py`
4. Update `.env.example`
5. Test (1-2 hours)

To add a new vector provider (e.g., Weaviate, Qdrant):

1. Create `backend/adapters/vector/weaviate_adapter.py`
2. Implement `VectorAdapter` interface
3. Add to factory in `vector_manager.py`
4. Update `.env.example`
5. Test (1-2 hours)

---

## Common Pitfalls

1. **SQL syntax differences**: Use parameterized queries, test both adapters
2. **Connection leaks**: Always use try/finally, return connections to pool
3. **Embedding dimensions**: Ensure Pinecone index matches model (384 for all-MiniLM-L6-v2)
4. **Namespace confusion**: In Pinecone, ESP filter = namespace (not metadata filter)
5. **Batch size limits**: Pinecone max 100 vectors/request, ChromaDB more flexible
6. **Data types**: PostgreSQL TIMESTAMP vs TEXT, handle conversions
7. **Transaction handling**: PostgreSQL needs explicit commit/rollback

---

## Success Criteria

✅ Application works identically in both local and cloud modes  
✅ Zero code changes needed to switch providers (only env vars)  
✅ All existing features still work  
✅ Migration scripts successfully transfer data  
✅ Performance is equivalent or better  
✅ Future provider changes take < 2 hours  

---

## Estimated Timeline

- Phase 1 (Database abstraction): 3-4 hours
- Phase 2 (Vector abstraction): 2-3 hours
- Phase 3 (Update app code): 1-2 hours
- Phase 4 (Dependencies/config): 30 minutes
- Phase 5 (Migration scripts): 1 hour
- Phase 6 (Testing): 2 hours

**Total**: ~10-12 hours of focused development

---

## Questions to Resolve Before Starting

1. **PostgreSQL provider**: ElephantSQL (20MB free), Neon (10GB free), or Railway?
2. **Pinecone tier**: Free tier sufficient? (100K vectors, 1 index)
3. **Keep SQLite support**: Yes (for local dev) or migrate entirely?
4. **Migration timing**: All at once or phase by phase?
5. **Existing data**: Migrate to cloud or start fresh?

---

END OF MIGRATION GUIDE
