from app.core.config import COLLECTION_NAME
from app.db.qdrant import client
from app.rag.embeddings import embed_text


def retrieve(
    query: str,
    limit: int = 5,
):
    """
    Search Qdrant for the most relevant chunks.
    """

    query_vector = embed_text(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
    )

    return [
        {
            "score": point.score,
            "chunk_id": point.payload["chunk_id"],
            "filename": point.payload["filename"],
            "text": point.payload["text"],
        }
        for point in results.points
    ]