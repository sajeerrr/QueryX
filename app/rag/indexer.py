import uuid

from qdrant_client.models import PointStruct

from app.core.config import COLLECTION_NAME
from app.db.qdrant import client
from app.rag.embeddings import embed_text


def index_document(
    filename: str,
    chunks: list[str]
):
    """
    Generate embeddings and store them in Qdrant.
    """

    points = []

    for chunk_id, chunk in enumerate(chunks, start=1):

        vector = embed_text(chunk)

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "filename": filename,
                    "chunk_id": chunk_id,
                    "text": chunk
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(points)