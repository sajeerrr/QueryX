import threading
from sentence_transformers import SentenceTransformer

from app.core.config import EMBEDDING_MODEL
from app.core.logger import logger

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """Load the SentenceTransformer model from local cache first, falling back to Hub."""
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        try:
            _model = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
            logger.info("EMBEDDINGS | loaded %s from local cache", EMBEDDING_MODEL)
        except Exception:
            logger.info("EMBEDDINGS | local cache miss, loading %s from HuggingFace Hub", EMBEDDING_MODEL)
            _model = SentenceTransformer(EMBEDDING_MODEL)
        return _model


def preload_embedding_model() -> None:
    """Warm up the embedding model in the background so first upload is instant."""
    try:
        _get_model()
    except Exception as exc:
        logger.warning("EMBEDDINGS | background preload failed: %s", exc)


def embed_text(text: str) -> list[float]:
    """Generate a normalized embedding for a text chunk."""
    embedding = _get_model().encode(
        text,
        normalize_embeddings=True,
        show_progress_bar=False,
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
