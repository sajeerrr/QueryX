from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.config import COLLECTION_NAME
from app.db.qdrant import get_qdrant_client
from app.rag.embeddings import embed_text
from app.schemas.retrieval import RetrievedChunk


def build_filter(document_ids: list[str] | None = None) -> Filter | None:
    """Build a Qdrant filter restricting results to specific document IDs."""
    if not document_ids:
        return None

    return Filter(
        should=[
            FieldCondition(
                key="document_id",
                match=MatchValue(value=doc_id),
            )
            for doc_id in document_ids
        ]
    )


def retrieve(
    query: str,
    limit: int = 5,
    document_ids: list[str] | None = None,
) -> list[RetrievedChunk]:
    """Search Qdrant for the most semantically relevant chunks."""
    query_vector = embed_text(query)
    search_filter = build_filter(document_ids)
    results = get_qdrant_client().query_points(
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
            source=point.payload.get("source"),
        )
        for point in results.points
    ]
