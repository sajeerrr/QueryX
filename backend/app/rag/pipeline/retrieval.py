from app.core.config import HYBRID_TOP_K
from app.rag.hybrid import hybrid_search
from app.rag.multi_query import multi_query
from app.rag.query_rewriter import query_rewriter
from app.rag.rrf import reciprocal_rank_fusion


class RetrievalStage:

    def run(self, question: str):

        rewritten = query_rewriter.rewrite(question)

        queries = multi_query.generate(rewritten)

        if not queries:
            queries = [rewritten]

        chunks = []

        for query in queries:
            chunks.extend(
                hybrid_search(
                    query,
                    limit=HYBRID_TOP_K,
                )
            )

        chunks = reciprocal_rank_fusion(chunks)

        return rewritten, chunks


retrieval_stage = RetrievalStage()