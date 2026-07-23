"""
Reranking module to improve relevance of retrieved chunks.
Uses cross-encoder model for more accurate semantic matching.
"""

from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize reranker with cross-encoder model.

        Args:
            model_name: HuggingFace model for reranking
        """
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"Reranker initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
            self.model = None

    def rerank(self, query, chunks, top_k=10):
        """
        Rerank retrieved chunks using cross-encoder.

        Args:
            query: User query string
            chunks: List of chunk dicts with 'text' key
            top_k: Number of top results to return

        Returns:
            Reranked list of chunks with updated scores
        """
        if not self.model or not chunks:
            return chunks[:top_k]

        try:
            # Prepare query-chunk pairs
            pairs = [[query, chunk['text']] for chunk in chunks]

            # Get reranking scores
            scores = self.model.predict(pairs)

            # Add scores to chunks and sort
            for chunk, score in zip(chunks, scores):
                chunk['rerank_score'] = float(score)
                chunk['original_score'] = chunk.get('score', 0)

            reranked = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)

            logger.debug(f"Reranked {len(chunks)} chunks, returning top {top_k}")
            return reranked[:top_k]

        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original results")
            return chunks[:top_k]


# Singleton instance
_reranker_instance = None

def get_reranker():
    """Get or create reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    return _reranker_instance
