import os
import json
from typing import Dict, List, Optional, Any
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from .base import VectorAdapter

class PineconeAdapter(VectorAdapter):
    """Pinecone implementation of VectorAdapter"""

    def __init__(
        self,
        api_key: str,
        index_name: str,
        environment: str = "us-east-1",
        dimension: int = 384  # all-MiniLM-L6-v2 embedding size
    ):
        """
        Initialize Pinecone client

        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            environment: Pinecone environment (default: us-east-1)
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension

        # Initialize embedding model (same as ChromaDB)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Get or create index
        if index_name not in self.pc.list_indexes().names():
            print(f"Creating Pinecone index: {index_name}")
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=environment
                )
            )

        self.index = self.pc.Index(index_name)

    def add_document(self, text: str, metadata: Dict[str, Any]) -> None:
        """Add a document to the vector store"""
        chunks = self.chunk_text(text)
        vectors_to_upsert = []

        for i, chunk in enumerate(chunks):
            # Generate unique ID
            doc_id = f"{metadata['esp']}_{metadata['filename']}_{i}"

            # Embed chunk
            embedding = self.embedding_model.encode(chunk).tolist()

            # Prepare metadata
            chunk_metadata = {
                **metadata,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'text': chunk  # Pinecone requires storing text in metadata
            }

            vectors_to_upsert.append({
                'id': doc_id,
                'values': embedding,
                'metadata': chunk_metadata
            })

        # Batch upsert (Pinecone recommends batches of 100)
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            self.index.upsert(vectors=batch)

    def search(self, query: str, esp_filter: Optional[str] = None, n_results: int = 5) -> Dict:
        """
        Search for relevant documents

        Returns ChromaDB-compatible result format:
        {
            'ids': [[...]],
            'documents': [[...]],
            'metadatas': [[...]],
            'distances': [[...]]
        }
        """
        # Embed query
        query_embedding = self.embedding_model.encode(query).tolist()

        # Build filter
        filter_dict = None
        if esp_filter and esp_filter.lower() != 'other/webhook':
            filter_dict = {"esp": {"$eq": esp_filter.lower()}}

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=n_results,
            filter=filter_dict,
            include_metadata=True
        )

        # Convert to ChromaDB format
        ids = [[match['id'] for match in results['matches']]]
        documents = [[match['metadata'].get('text', '') for match in results['matches']]]
        metadatas = [[
            {k: v for k, v in match['metadata'].items() if k != 'text'}
            for match in results['matches']
        ]]
        distances = [[match['score'] for match in results['matches']]]

        return {
            'ids': ids,
            'documents': documents,
            'metadatas': metadatas,
            'distances': distances
        }

    def refresh_esp(self, esp_name: str, docs_path: str) -> None:
        """Refresh documents for a specific ESP"""
        print(f"Refreshing {esp_name} documentation...")

        # Delete existing documents for this ESP
        # Note: Pinecone requires fetching IDs before deleting
        # We'll use metadata filtering to get all docs for this ESP
        try:
            # Query all vectors for this ESP (using dummy vector)
            dummy_vector = [0.0] * self.dimension
            existing = self.index.query(
                vector=dummy_vector,
                top_k=10000,  # Large number to get all
                filter={"esp": {"$eq": esp_name.lower()}},
                include_metadata=False
            )

            existing_ids = [match['id'] for match in existing['matches']]
            if existing_ids:
                # Delete in batches
                batch_size = 1000
                for i in range(0, len(existing_ids), batch_size):
                    batch = existing_ids[i:i + batch_size]
                    self.index.delete(ids=batch)
                print(f"  Deleted {len(existing_ids)} existing chunks")
        except Exception as e:
            print(f"  Warning: Could not delete existing docs: {e}")

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
        """Vectorize all documents in the docs folder"""
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

    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        if ids:
            # Delete in batches
            batch_size = 1000
            for i in range(0, len(ids), batch_size):
                batch = ids[i:i + batch_size]
                self.index.delete(ids=batch)

    def get_collection_count(self) -> int:
        """Get total number of vectors in the index"""
        stats = self.index.describe_index_stats()
        return stats.get('total_vector_count', 0)

    def url_exists(self, url: str, esp_name: str) -> bool:
        """Check if a URL has been vectorized"""
        try:
            # Query for any vectors matching this URL and ESP
            # We use a dummy query vector since we just want to filter by metadata
            dummy_query = [0.0] * 384  # Match embedding dimension

            results = self.index.query(
                vector=dummy_query,
                filter={
                    "esp": {"$eq": esp_name},
                    "source_url": {"$eq": url}
                },
                top_k=1,
                include_metadata=True
            )

            return len(results.get('matches', [])) > 0
        except Exception as e:
            print(f"Error checking URL existence: {e}")
            return False
