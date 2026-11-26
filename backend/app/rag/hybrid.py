from app.core.config import HYBRID_TOP_K
from app.rag.bm25_index import bm25_index
from app.rag.retriever import retrieve
from app.rag.rrf import reciprocal_rank_fusion
from app.schemas.retrieval import RetrievedChunk


def hybrid_search(
    question: str,
    limit: int = 5,
    document_ids: list[str] | None = None,
) -> list[RetrievedChunk]:
    """Combine dense vector retrieval and BM25 lexical retrieval using RRF."""
    candidate_limit = max(limit, HYBRID_TOP_K)

    dense_results = retrieve(
        question,
        limit=candidate_limit,
        document_ids=document_ids,
    )

    bm25_results = bm25_index.search(
        question,
        limit=candidate_limit,
        document_ids=document_ids,
    )

    fused = reciprocal_rank_fusion(dense_results, bm25_results)
    return fused[:limit]
