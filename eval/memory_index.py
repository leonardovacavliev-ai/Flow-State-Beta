"""
An in-memory vector index built from the documents stored in Postgres.

For trying a chunking change before re-indexing production: it chunks every
labelled document with the chunker in the working tree, embeds the chunks with
the production model, and answers search() and get_chunks() the way the
Pinecone adapter does (cosine similarity, ESP metadata filter, the same chunk
ids and metadata). build_rag_context() cannot tell it from the live index.

Reads esp_documents only; writes nothing.
"""
import numpy as np


class MemoryIndex:
    def __init__(self, chunk_text=None, esps=None):
        """chunk_text(text) -> [chunk]; defaults to the working tree's
        VectorAdapter.chunk_text. esps: ESP names to load (default: all)."""
        from adapters.vector.base import VectorAdapter
        from adapters.vector.pinecone_adapter import SentenceTransformer
        from esp_manager import get_esp_manager

        chunk_text = chunk_text or (lambda text: VectorAdapter.chunk_text(None, text))
        manager = get_esp_manager()
        names = esps or [e['name'] for e in manager.list_esps()]

        self.ids, self.documents, self.metadatas = [], [], []
        for esp in names:
            for doc in manager.get_documents_with_content(esp):
                if not doc.get('content') or doc.get('product') not in ('loyalty', 'reviews', 'shared'):
                    continue    # rebuild_esp_vectors skips these too
                chunks = chunk_text(doc['content'])
                for i, chunk in enumerate(chunks):
                    self.ids.append(f"{esp}_{doc['filename']}_{i}")
                    self.documents.append(chunk)
                    self.metadatas.append({
                        'esp': esp, 'filename': doc['filename'], 'source_url': doc['url'],
                        'product': doc['product'], 'chunk_index': float(i),
                        'total_chunks': float(len(chunks)),
                    })

        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vectors = self.model.encode(self.documents, normalize_embeddings=True,
                                         batch_size=64, show_progress_bar=False).astype(np.float64)
        self.esp_of = np.array([m['esp'] for m in self.metadatas])
        self.product_of = np.array([m['product'] for m in self.metadatas])
        self.by_id = {chunk_id: i for i, chunk_id in enumerate(self.ids)}

    def search(self, query, esp_filter=None, n_results=5, products=None):
        q = self.model.encode(query, normalize_embeddings=True).astype(np.float64)
        with np.errstate(all='ignore'):     # spurious warnings from macOS Accelerate
            scores = self.vectors @ q
        candidates = np.arange(len(self.ids))
        if esp_filter and esp_filter.lower() != 'other/webhook':
            candidates = candidates[self.esp_of == esp_filter.lower()]
        if products:
            candidates = candidates[np.isin(self.product_of[candidates], list(products))]
        order = candidates[np.argsort(-scores[candidates], kind='stable')][:n_results]
        return {
            'ids': [[self.ids[i] for i in order]],
            'documents': [[self.documents[i] for i in order]],
            'metadatas': [[dict(self.metadatas[i]) for i in order]],
            'distances': [[float(scores[i]) for i in order]],
        }

    def get_chunks(self, ids):
        return {chunk_id: {'document': self.documents[self.by_id[chunk_id]],
                           'metadata': dict(self.metadatas[self.by_id[chunk_id]])}
                for chunk_id in ids if chunk_id in self.by_id}

    def stats(self, window=256):
        """Chunk count, chunks under 60 words, chunks past the embedding window."""
        tokenizer = self.model.tokenizer
        short = sum(1 for d in self.documents if len(d.split()) < 60)
        over = sum(1 for d in self.documents if len(tokenizer.tokenize(d)) + 2 > window)
        return {'chunks': len(self.documents), 'under_60_words': short, 'over_window': over}
