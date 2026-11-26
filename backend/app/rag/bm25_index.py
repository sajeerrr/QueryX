import threading
from rank_bm25 import BM25Okapi

from app.core.config import COLLECTION_NAME
from app.core.logger import logger
from app.db.qdrant import get_qdrant_client
from app.schemas.retrieval import RetrievedChunk


class BM25Index:
    """Thread-safe in-memory BM25 lexical index backed by Qdrant payloads."""

    def __init__(self):
        self._lock = threading.RLock()
        self.index: BM25Okapi | None = None
        self.documents: list[list[str]] = []
        self.metadata: list[RetrievedChunk] = []

    def rebuild(self) -> None:
        """Rebuild the BM25 index from all points currently stored in Qdrant."""
        logger.info("Building BM25 index...")
        qdrant_client = get_qdrant_client()

        documents: list[list[str]] = []
        metadata: list[RetrievedChunk] = []
        offset = None

        while True:
            points, offset = qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            for point in points:
                payload = point.payload or {}
                text = payload.get("text", "")
                documents.append(text.lower().split())
                metadata.append(
                    RetrievedChunk(
                        score=0.0,
                        document_id=payload["document_id"],
                        filename=payload["filename"],
                        chunk_id=payload["chunk_id"],
                        text=text,
                        page=payload.get("page"),
                        collection=payload.get("collection"),
                        source=payload.get("source"),
                    )
                )

            if offset is None:
                break

        new_index = BM25Okapi(documents) if documents else None
        with self._lock:
            self.documents = documents
            self.metadata = metadata
            self.index = new_index

        if documents:
            logger.info("BM25 indexed %d chunks", len(documents))
        else:
            logger.warning("BM25 index is empty")

    def clear(self) -> None:
        """Clear the in-memory BM25 index."""
        with self._lock:
            self.documents = []
            self.metadata = []
            self.index = None
        logger.info("BM25 index cleared")

    def search(
        self,
        query: str,
        limit: int = 10,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return top BM25 matches without mutating stored chunk metadata."""
        with self._lock:
            index = self.index
            documents = self.documents
            metadata = self.metadata

        if index is None or not metadata:
            return []

        tokens = query.lower().split()
        if not tokens:
            return []

        token_set = set(tokens)
        scores = index.get_scores(tokens)
        allowed_ids = set(document_ids) if document_ids else None

        candidates = [
            (float(score), chunk)
            for score, doc_tokens, chunk in zip(scores, documents, metadata)
            if (allowed_ids is None or chunk.document_id in allowed_ids)
            and (score > 0 or bool(token_set.intersection(doc_tokens)))
        ]
        candidates.sort(key=lambda item: item[0], reverse=True)

        return [
            chunk.model_copy(update={"score": score})
            for score, chunk in candidates[:limit]
        ]


bm25_index = BM25Index()
