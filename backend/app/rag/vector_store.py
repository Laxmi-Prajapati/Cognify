import numpy as np
import faiss
from typing import List, Dict, Tuple


class VectorStore:
    """
    In-memory FAISS index for anomaly embeddings.
    One instance per audit session (rebuilt on each upload).
    """

    def __init__(self):
        self.index = None
        self.metadata: List[Dict] = []
        self.texts: List[str] = []
        self.dim: int = 0

    def build(self, embeddings: np.ndarray, texts: List[str], metadata: List[Dict]):
        """Build a flat L2 FAISS index from embeddings."""
        self.dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dim)

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        self.texts = texts
        self.metadata = metadata

    def query(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """
        Returns top_k most relevant anomaly chunks for a query embedding.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        q = query_embedding.reshape(1, -1).astype("float32")
        faiss.normalize_L2(q)

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(q, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            result = dict(self.metadata[idx])
            result["similarity_score"] = float(1 - dist / 2)  # convert L2 to cosine approx
            results.append(result)

        return results

    def is_ready(self) -> bool:
        return self.index is not None and self.index.ntotal > 0

    def size(self) -> int:
        return self.index.ntotal if self.index else 0


# Global store — one per server process (per audit session)
vector_store = VectorStore()
