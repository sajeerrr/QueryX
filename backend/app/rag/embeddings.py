import threading
from sentence_transformers import SentenceTransformer

from app.core.config import EMBEDDING_MODEL

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """Lazily load the SentenceTransformer model on first use."""
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is None:
            _model = SentenceTransformer(EMBEDDING_MODEL)
        return _model


def embed_text(text: str) -> list[float]:
    """Generate a normalized embedding for a text chunk."""
    embedding = _get_model().encode(
        text,
        normalize_embeddings=True,
    )
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate normalized embeddings for a list of text chunks in batches."""
    if not texts:
        return []
    embeddings = _get_model().encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return embeddings.tolist()
