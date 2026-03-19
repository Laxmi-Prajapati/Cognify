from typing import List, Dict
from sentence_transformers import SentenceTransformer
from app.rag.vector_store import vector_store
from app.config import settings

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def retrieve(query: str, top_k: int = None) -> List[Dict]:
    """
    Embeds the query and retrieves the top_k most relevant anomaly chunks.
    Returns list of metadata dicts with similarity scores.
    """
    if not vector_store.is_ready():
        return []

    k = top_k or settings.FAISS_TOP_K
    model = _get_model()
    query_embedding = model.encode([query], show_progress_bar=False)[0]
    return vector_store.query(query_embedding, top_k=k)
