from sentence_transformers import CrossEncoder
from app.schemas.retrieval import RetrievedChunk
from app.core.config import (
    HYBRID_TOP_K,
    RERANK_TOP_K,
    RERANK_THRESHOLD,
)


class Reranker:

    def __init__(self):

        self.model = CrossEncoder(
            "BAAI/bge-reranker-v2-m3"
        )

    def rerank(self, question: str, chunks: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:

        if not chunks:
            return []

        pairs = [

            (question, chunk.text)
            for chunk in chunks
        ]

        scores = self.model.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)

        chunks.sort(

            key=lambda x: x.score,
            reverse=True,
        )

        filtered = [
            chunk
            for chunk in chunks
            if chunk.score > RERANK_THRESHOLD
        ]

        return filtered[:top_k]

reranker = Reranker()