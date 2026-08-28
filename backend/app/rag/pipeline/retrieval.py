from app.rag.hybrid import hybrid_search


class RetrievalStage:

    def run(self, question: str):

        chunks = hybrid_search(
            question,
            limit=5,
        )

        return chunks


retrieval_stage = RetrievalStage()