import threading
import time

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import COLLECTION_NAME, EMBEDDING_DIM, QDRANT_URL
from app.core.logger import logger

_client: QdrantClient | None = None
_client_lock = threading.Lock()


def get_qdrant_client() -> QdrantClient:
    """Return a shared QdrantClient instance, connecting lazily on first use."""
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        if not QDRANT_URL:
            logger.error("QDRANT_URL environment variable is not set")
            raise ValueError("QDRANT_URL environment variable is required")

        try:
            qdrant_client = QdrantClient(url=QDRANT_URL)
            qdrant_client.get_collections()
            logger.info("Qdrant connection established")
            _client = qdrant_client
            return _client
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise


def _create_collection(qdrant_client: QdrantClient) -> None:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )
    logger.info("Created Qdrant collection %r (dim=%d)", COLLECTION_NAME, EMBEDDING_DIM)


def ensure_collection(retries: int = 5, retry_delay: float = 2.0) -> None:
    """Ensure the Qdrant collection exists and matches EMBEDDING_DIM."""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            qdrant_client = get_qdrant_client()
            collections = qdrant_client.get_collections()
            names = [c.name for c in collections.collections]

            if COLLECTION_NAME in names:
                info = qdrant_client.get_collection(COLLECTION_NAME)
                vectors_cfg = info.config.params.vectors
                existing_size = getattr(vectors_cfg, "size", None)
                if existing_size == EMBEDDING_DIM:
                    return
                logger.warning(
                    "Qdrant collection %r dimension mismatch (found=%s, expected=%d); recreating collection",
                    COLLECTION_NAME,
                    existing_size,
                    EMBEDDING_DIM,
                )
                qdrant_client.delete_collection(COLLECTION_NAME)

            _create_collection(qdrant_client)
            return
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                logger.warning(
                    "Qdrant not ready (attempt %d/%d), retrying in %.1fs: %s",
                    attempt,
                    retries,
                    retry_delay,
                    exc,
                )
                time.sleep(retry_delay)

    if last_error is not None:
        raise last_error
