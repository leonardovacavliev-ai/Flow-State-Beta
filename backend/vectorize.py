import chromadb
from chromadb.utils import embedding_functions
import os
import json
import warnings

# Legacy class - use adapters.vector.vector_manager.get_vector_adapter() for new code
warnings.warn(
    "DocumentVectorizer is deprecated. Use adapters.vector.vector_manager.get_vector_adapter() instead.",
    DeprecationWarning,
    stacklevel=2
)

class DocumentVectorizer:
    def __init__(self, persist_directory="./chroma_db"):
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

    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def add_document(self, text, metadata):
        """Add a document to the vector store"""
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

    def vectorize_all_docs(self, docs_path):
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

                    # Extract source URL
                    source_url = doc['url']

                    metadata = {
                        'esp': esp,
                        'filename': doc['filename'],
                        'source_url': source_url,
                        'filepath': filepath
                    }

                    self.add_document(content, metadata)
                    total_docs += 1
                    print(f"  ✓ {doc['filename']}")

        print(f"\n✓ Vectorization complete! {total_docs} documents processed.")
        print(f"  Total chunks in database: {self.collection.count()}")

    def add_best_practices(self, pdf_text_path):
        """Add the loyalty best practices document"""
        print("\nAdding loyalty best practices document...")

        with open(pdf_text_path, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = {
            'esp': 'global',
            'filename': 'loyalty_best_practices.pdf',
            'source_url': 'internal',
            'filepath': pdf_text_path
        }

        self.add_document(content, metadata)
        print("  ✓ Best practices document added")

    def search(self, query, esp_filter=None, n_results=5):
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

    def refresh_esp(self, esp_name, docs_path):
        """Refresh documents for a specific ESP"""
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

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_path = os.path.join(base_path, "docs")
    db_path = os.path.join(base_path, "backend/chroma_db")

    vectorizer = DocumentVectorizer(persist_directory=db_path)

    # Vectorize all ESP docs
    vectorizer.vectorize_all_docs(docs_path)

    # Add best practices
    best_practices_path = "/tmp/loyalty_report.txt"
    if os.path.exists(best_practices_path):
        vectorizer.add_best_practices(best_practices_path)

    print("\n" + "="*50)
    print("Database ready!")
    print(f"Location: {db_path}")
    print("="*50)
