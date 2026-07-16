from .base import VectorAdapter
from .chroma_adapter import ChromaDBAdapter

# Only import PineconeAdapter if pinecone is installed
try:
    from .pinecone_adapter import PineconeAdapter
    __all__ = ['VectorAdapter', 'ChromaDBAdapter', 'PineconeAdapter']
except ImportError:
    # Pinecone not installed - only ChromaDB available
    __all__ = ['VectorAdapter', 'ChromaDBAdapter']
