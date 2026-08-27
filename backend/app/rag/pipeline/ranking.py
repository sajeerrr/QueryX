from app.core.config import RERANK_TOP_K
from app.rag.reranker import reranker


class RankingStage:

    def run(self, question, chunks):

        return reranker.rerank(
            question,
            chunks,
            top_k=RERANK_TOP_K,
        )


ranking_stage = RankingStage()