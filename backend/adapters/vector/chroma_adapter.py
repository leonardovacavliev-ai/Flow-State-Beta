import chromadb
from chromadb.utils import embedding_functions
import os
import json
from typing import Dict, List, Optional, Any
from .base import VectorAdapter, require_product_metadata, refuse_bulk_reindex

class ChromaDBAdapter(VectorAdapter):
    """ChromaDB implementation of VectorAdapter"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB with sentence transformers"""
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Use sentence transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="esp_docs",
            embedding_function=self.embedding_function
        )

    def add_document(self, text: str, metadata: Dict[str, Any]) -> None:
        """Add a document to the vector store"""
        require_product_metadata(metadata)
        chunks = self.chunk_text(text)

        for i, chunk in enumerate(chunks):
            doc_id = f"{metadata['esp']}_{metadata['filename']}_{i}"

            self.collection.add(
                documents=[chunk],
                metadatas=[{
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }],
                ids=[doc_id]
            )

    def search(self, query: str, esp_filter: Optional[str] = None, n_results: int = 5) -> Dict:
        """Search for relevant documents"""
        where = None
        if esp_filter and esp_filter.lower() != 'other/webhook':
            where = {"esp": esp_filter.lower()}

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

        return results

    def refresh_esp(self, esp_name: str, docs_path: str) -> None:
        """Refresh documents for a specific ESP (disabled, see refuse_bulk_reindex)"""
        refuse_bulk_reindex('refresh_esp')
        print(f"Refreshing {esp_name} documentation...")

        # Delete existing documents for this ESP
        esp_docs = self.collection.get(where={"esp": esp_name.lower()})
        if esp_docs['ids']:
            self.collection.delete(ids=esp_docs['ids'])
            print(f"  Deleted {len(esp_docs['ids'])} existing chunks")

        # Re-add documents
        metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
        with open(metadata_path, 'r') as f:
            crawl_metadata = json.load(f)

        if esp_name.lower() in crawl_metadata:
            for doc in crawl_metadata[esp_name.lower()]:
                filepath = doc['filepath']
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    metadata = {
                        'esp': esp_name.lower(),
                        'filename': doc['filename'],
                        'source_url': doc['url'],
                        'filepath': filepath
                    }

                    self.add_document(content, metadata)
                    print(f"  ✓ {doc['filename']}")

        print(f"✓ {esp_name} refresh complete")

    def vectorize_all_docs(self, docs_path: str) -> None:
        """Vectorize all documents in the docs folder (disabled, see refuse_bulk_reindex)"""
        refuse_bulk_reindex('vectorize_all_docs')
        print("Starting vectorization...")

        # Load metadata
        metadata_path = os.path.join(docs_path, 'crawl_metadata.json')
        with open(metadata_path, 'r') as f:
            crawl_metadata = json.load(f)

        total_docs = 0
        for esp, docs in crawl_metadata.items():
            print(f"\nProcessing {esp}...")

            for doc in docs:
                filepath = doc['filepath']
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    metadata = {
                        'esp': esp,
                        'filename': doc['filename'],
                        'source_url': doc['url'],
                        'filepath': filepath
                    }

                    self.add_document(content, metadata)
                    total_docs += 1
                    print(f"  ✓ {doc['filename']}")

        print(f"\n✓ Vectorization complete! {total_docs} documents processed.")
        print(f"  Total chunks in database: {self.collection.count()}")

    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        if ids:
            self.collection.delete(ids=ids)

    def delete_by_url(self, url: str, esp_name: str) -> int:
        """Delete all chunks belonging to a specific source URL."""
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"esp": esp_name.lower()},
                        {"source_url": url}
                    ]
                }
            )
            ids = results.get('ids', [])
            if ids:
                self.collection.delete(ids=ids)
                print(f"  Deleted {len(ids)} chunks for {url}")
            return len(ids)
        except Exception as e:
            print(f"Error deleting vectors for {url}: {e}")
            return 0

    def ids_for_url(self, url: str, esp_name: str) -> List[str]:
        """Ids of every chunk of one document (raises on errors)."""
        # ChromaDB rejects a two-key where; it needs $and
        results = self.collection.get(
            where={"$and": [{"esp": esp_name.lower()}, {"source_url": url}]})
        return list(results.get('ids') or [])

    def update_metadata(self, ids: List[str], patch: Dict[str, Any]) -> None:
        """Merge `patch` into each vector's metadata (raises on errors).

        Merged here, not by ChromaDB, so the other keys survive whatever its
        update does with a partial dict.
        """
        if not ids:
            return
        current = self.collection.get(ids=list(ids), include=['metadatas'])
        self.collection.update(
            ids=current['ids'],
            metadatas=[{**(m or {}), **patch} for m in current['metadatas']])

    def get_collection_count(self) -> int:
        """Get total number of chunks in the database"""
        return self.collection.count()

    def url_exists(self, url: str, esp_name: str) -> bool:
        """Check if a URL has been vectorized"""
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"esp": esp_name},
                        {"source_url": url}
                    ]
                },
                limit=1
            )
            return len(results['ids']) > 0
        except Exception as e:
            print(f"Error checking URL existence: {e}")
            return False
