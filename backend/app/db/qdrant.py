from qdrant_client import QdrantClient
from app.core.config import QDRANT_URL
from app.core.logger import logger


def get_qdrant_client():
    """Create Qdrant client with error handling."""
    if not QDRANT_URL:
        logger.error("QDRANT_URL environment variable is not set")
        raise ValueError("QDRANT_URL environment variable is required")

    try:
        client = QdrantClient(url=QDRANT_URL)
        # Test connection
        client.get_collections()
        logger.info("Qdrant connection established")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        raise


client = get_qdrant_client()