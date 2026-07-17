from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class VectorAdapter(ABC):
    """Base interface for vector database adapters"""

    @abstractmethod
    def add_document(self, text: str, metadata: Dict[str, Any]) -> None:
        """
        Add a document to the vector store

        Args:
            text: Document content to embed
            metadata: Metadata dict with keys: esp, filename, source_url, filepath
        """
        pass

    @abstractmethod
    def search(self, query: str, esp_filter: Optional[str] = None, n_results: int = 5) -> Dict:
        """
        Search for relevant documents

        Args:
            query: Search query text
            esp_filter: Filter by ESP name (e.g., 'klaviyo', 'global')
            n_results: Number of results to return

        Returns:
            Dict with keys:
                - ids: List of document IDs
                - documents: List of text chunks
                - metadatas: List of metadata dicts
                - distances: List of similarity scores (optional)
        """
        pass

    @abstractmethod
    def refresh_esp(self, esp_name: str, docs_path: str) -> None:
        """
        Refresh documents for a specific ESP

        Args:
            esp_name: ESP identifier (e.g., 'klaviyo')
            docs_path: Path to docs directory
        """
        pass

    @abstractmethod
    def vectorize_all_docs(self, docs_path: str) -> None:
        """
        Vectorize all documents in the docs folder

        Args:
            docs_path: Path to docs directory containing crawl_metadata.json
        """
        pass

    @abstractmethod
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by ID

        Args:
            ids: List of document IDs to delete
        """
        pass

    @abstractmethod
    def get_collection_count(self) -> int:
        """Get total number of chunks in the database"""
        pass

    @abstractmethod
    def url_exists(self, url: str, esp_name: str) -> bool:
        """
        Check if a URL has been vectorized

        Args:
            url: The source URL to check
            esp_name: ESP name to filter by

        Returns:
            True if URL has vectorized content, False otherwise
        """
        pass

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks (common implementation)

        Args:
            text: Text to chunk
            chunk_size: Number of words per chunk
            overlap: Number of words to overlap between chunks

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks
