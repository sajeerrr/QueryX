import threading
import uuid
from datetime import datetime, timezone

from qdrant_client.models import PointStruct

from app.core.config import COLLECTION_NAME
from app.core.logger import logger
from app.db.qdrant import get_qdrant_client
from app.rag.bm25_index import bm25_index
from app.rag.embeddings import embed_texts


def index_document(
    filename: str,
    chunks: list[str],
    document_id: str | None = None,
) -> dict:
    """Embed and upsert document chunks into Qdrant and schedule BM25 refresh."""
    document_id = document_id or str(uuid.uuid4())
    logger.info(
        "INDEXER | started | filename=%r | document_id=%s | chunks=%d",
        filename,
        document_id,
        len(chunks),
    )

    points = []
    created_at = datetime.now(timezone.utc).isoformat()

    if chunks:
        vectors = embed_texts(chunks)
        logger.info(
            "INDEXER | embeddings generated | filename=%r | document_id=%s | vectors=%d",
            filename,
            document_id,
            len(vectors),
        )

        for chunk_id, (chunk, vector) in enumerate(zip(chunks, vectors), start=1):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_id": chunk_id,
                        "text": chunk,
                        "collection": "default",
                        "created_at": created_at,
                        "page": None,
                        "source": filename,
                    },
                )
            )

        get_qdrant_client().upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
        logger.info(
            "INDEXER | Qdrant upsert complete | filename=%r | document_id=%s | points=%d",
            filename,
            document_id,
            len(points),
        )

    # Rebuild BM25 index in background to avoid blocking response
    threading.Thread(target=bm25_index.rebuild, daemon=True).start()
    logger.info("INDEXER | BM25 rebuild scheduled | filename=%r | document_id=%s", filename, document_id)

    return {
        "document_id": document_id,
        "indexed_chunks": len(points),
    }
