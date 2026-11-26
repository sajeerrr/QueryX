import threading
import time

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import COLLECTION_NAME, QDRANT_URL
from app.core.logger import logger

VECTOR_SIZE = 384

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


def ensure_collection(retries: int = 5, retry_delay: float = 2.0) -> None:
    """Ensure the configured Qdrant collection exists, retrying brief startup delays."""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            qdrant_client = get_qdrant_client()
            collections = qdrant_client.get_collections()
            names = [c.name for c in collections.collections]

            if COLLECTION_NAME in names:
                return

            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection %r", COLLECTION_NAME)
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
