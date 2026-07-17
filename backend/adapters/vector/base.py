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

    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 100) -> List[str]:
        """
        Split text into semantically meaningful chunks (improved implementation)

        Strategy:
        - Respects document structure (headers, sections, lists)
        - Keeps related content together (property definitions, code blocks)
        - Smaller chunks (300 words) for better retrieval precision
        - More overlap (100 words) to prevent information loss

        Args:
            text: Text to chunk
            chunk_size: Max number of words per chunk (default: 300, reduced from 500)
            overlap: Number of words to overlap between chunks (default: 100, increased from 50)

        Returns:
            List of semantically meaningful text chunks
        """
        import re

        chunks = []

        # First, try to split on major section boundaries
        # Look for patterns like:
        # - "List of customer properties"
        # - "## Header" or "### Subheader"
        # - "Properties for X"
        # - Blank lines followed by capitalized text
        section_pattern = r'\n(?=(?:##+ |List of |Properties |Customer |Events? |Attributes? |Note:|Important:|Tip:)[A-Z])'
        sections = re.split(section_pattern, text)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # If section is small enough, keep it as one chunk
            section_words = section.split()
            if len(section_words) <= chunk_size:
                chunks.append(section)
                continue

            # Section is too large, split it intelligently
            # Try to split on paragraph boundaries first
            paragraphs = section.split('\n\n')
            current_chunk = []
            current_word_count = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                para_words = para.split()
                para_word_count = len(para_words)

                # If adding this paragraph would exceed chunk_size
                if current_word_count + para_word_count > chunk_size and current_chunk:
                    # Save current chunk
                    chunks.append('\n\n'.join(current_chunk))

                    # Start new chunk with overlap
                    overlap_words = ' '.join(current_chunk[-1].split()[-overlap:]) if current_chunk else ''
                    current_chunk = [overlap_words + '\n\n' + para] if overlap_words else [para]
                    current_word_count = len(overlap_words.split()) + para_word_count
                else:
                    # Add paragraph to current chunk
                    current_chunk.append(para)
                    current_word_count += para_word_count

            # Don't forget the last chunk
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))

        # Clean up chunks
        cleaned_chunks = []
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk and len(chunk.split()) >= 20:  # Minimum 20 words per chunk
                cleaned_chunks.append(chunk)

        return cleaned_chunks if cleaned_chunks else [text.strip()]
