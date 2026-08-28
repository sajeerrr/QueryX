from app.core.config import RERANK_TOP_K, ENABLE_RERANKING
from app.rag.reranker import reranker
from app.core.logger import logger


class RankingStage:

    def run(self, question, chunks):

        # Reranking is optional - can be disabled for speed
        if not ENABLE_RERANKING:
            logger.debug("Reranking disabled, returning top chunks")
            return chunks[:RERANK_TOP_K]

        return reranker.rerank(
            question,
            chunks,
            top_k=RERANK_TOP_K,
        )


ranking_stage = RankingStage()