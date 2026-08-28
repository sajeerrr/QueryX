from app.core.config import HYBRID_TOP_K, ENABLE_MULTI_QUERY
from app.rag.hybrid import hybrid_search
from app.rag.multi_query import multi_query
from app.rag.query_rewriter import query_rewriter
from app.rag.rrf import reciprocal_rank_fusion
from app.core.logger import logger


class RetrievalStage:

    def run(self, question: str):

        rewritten = query_rewriter.rewrite(question)

        # Multi-query is optional - can be disabled for speed
        if ENABLE_MULTI_QUERY:
            queries = multi_query.generate(rewritten)
            if not queries:
                queries = [rewritten]
        else:
            queries = [rewritten]

        chunks = []

        for query in queries:
            chunks.extend(
                hybrid_search(
                    query,
                    limit=HYBRID_TOP_K,
                )
            )

        # Only fuse if we have multiple queries
        if len(queries) > 1:
            chunks = reciprocal_rank_fusion(chunks)

        return rewritten, chunks


retrieval_stage = RetrievalStage()