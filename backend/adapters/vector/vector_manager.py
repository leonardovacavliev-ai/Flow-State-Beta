import os
from typing import Optional
from .base import VectorAdapter
from .chroma_adapter import ChromaDBAdapter
from .pinecone_adapter import PineconeAdapter

def get_vector_adapter(
    provider: Optional[str] = None,
    **kwargs
) -> VectorAdapter:
    """
    Factory function to get the appropriate vector database adapter

    Args:
        provider: Vector DB provider ('chromadb' or 'pinecone')
                 If None, reads from VECTOR_DB_PROVIDER env var (default: chromadb)
        **kwargs: Provider-specific configuration

    Returns:
        VectorAdapter instance

    Environment Variables:
        VECTOR_DB_PROVIDER: 'chromadb' or 'pinecone' (default: chromadb)

        For ChromaDB:
            CHROMA_PERSIST_DIR: Path to ChromaDB directory (default: ./chroma_db)

        For Pinecone:
            PINECONE_API_KEY: API key (required)
            PINECONE_INDEX_NAME: Index name (required)
            PINECONE_ENVIRONMENT: Environment (default: us-east-1)

    Examples:
        # Use environment variables
        vectorizer = get_vector_adapter()

        # Override provider
        vectorizer = get_vector_adapter(provider='pinecone')

        # Direct configuration
        vectorizer = get_vector_adapter(
            provider='pinecone',
            api_key='your-key',
            index_name='esp-docs'
        )
    """
    if provider is None:
        provider = os.getenv('VECTOR_DB_PROVIDER', 'chromadb').lower()

    if provider == 'chromadb':
        persist_dir = kwargs.get(
            'persist_directory',
            os.getenv('CHROMA_PERSIST_DIR', './chroma_db')
        )
        return ChromaDBAdapter(persist_directory=persist_dir)

    elif provider == 'pinecone':
        api_key = kwargs.get('api_key') or os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("Pinecone API key required. Set PINECONE_API_KEY or pass api_key")

        index_name = kwargs.get('index_name') or os.getenv('PINECONE_INDEX_NAME')
        if not index_name:
            raise ValueError("Pinecone index name required. Set PINECONE_INDEX_NAME or pass index_name")

        environment = kwargs.get('environment') or os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')

        return PineconeAdapter(
            api_key=api_key,
            index_name=index_name,
            environment=environment
        )

    else:
        raise ValueError(f"Unknown vector DB provider: {provider}. Use 'chromadb' or 'pinecone'")
