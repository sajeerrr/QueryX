from app.rag.retriever import retrieve
from app.rag.bm25_index import bm25_index
from app.utils.rrf import reciprocal_rank_fusion
from app.core.config import HYBRID_TOP_K


def hybrid_search(question: str, limit: int = 5):

    dense_results = retrieve(
        question,
        limit=HYBRID_TOP_K,
    )

    bm25_results = bm25_index.search(
        question,
        limit=HYBRID_TOP_K,
    )

    fused = reciprocal_rank_fusion(
        dense_results,
        bm25_results,
    )

    return fused[:limit]