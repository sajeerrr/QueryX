import threading
import time

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from app.core.config import COLLECTION_NAME, EMBEDDING_DIM, QDRANT_API_KEY, QDRANT_URL
from app.core.logger import logger

_client: QdrantClient | None = None
_client_lock = threading.Lock()


def get_qdrant_client() -> QdrantClient:
    """Return a shared QdrantClient instance configured for Qdrant Cloud or local Qdrant."""
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        if not QDRANT_URL:
            logger.error("QDRANT_URL environment variable is not set")
            raise ValueError("QDRANT_URL environment variable is required")

        if QDRANT_URL.startswith("https://") and not QDRANT_API_KEY:
            logger.warning("QDRANT_URL uses HTTPS (Qdrant Cloud), but QDRANT_API_KEY is not set")

        try:
            qdrant_client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=30,
            )
            qdrant_client.get_collections()
            logger.info("Qdrant connection established (%s)", QDRANT_URL)
            _client = qdrant_client
            return _client
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise


def _ensure_payload_indexes(qdrant_client: QdrantClient) -> None:
    """Ensure keyword payload index on document_id for Qdrant Cloud filtered queries/deletes."""
    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="document_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )


def _create_collection(qdrant_client: QdrantClient) -> None:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )
    _ensure_payload_indexes(qdrant_client)
    logger.info("Created Qdrant collection %r (dim=%d)", COLLECTION_NAME, EMBEDDING_DIM)


def ensure_collection(retries: int = 5, retry_delay: float = 2.0) -> None:
    """Ensure the Qdrant collection exists, matches EMBEDDING_DIM, and has required indexes."""
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
                    _ensure_payload_indexes(qdrant_client)
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
