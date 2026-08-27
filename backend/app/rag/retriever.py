from app.core.config import COLLECTION_NAME
from app.db.qdrant import client
from app.rag.embeddings import embed_text
from app.rag.filters import build_filter
from app.schemas.retrieval import RetrievedChunk


def retrieve(query: str, limit: int = 5, document_ids: list[str] | None = None):

    """
    Search Qdrant for the most relevant chunks.
    """

    query_vector = embed_text(query)
    search_filter = build_filter(document_ids)
    results = client.query_points(

        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=search_filter,
        limit=limit,
        with_payload=True,
    )

    return [
        RetrievedChunk(
            score=point.score,
            document_id=point.payload["document_id"],
            filename=point.payload["filename"],
            chunk_id=point.payload["chunk_id"],
            text=point.payload["text"],
            page=point.payload.get("page"),
            collection=point.payload.get("collection"),
            source=point.payload.get("source")
        )
        for point in results.points
    ]