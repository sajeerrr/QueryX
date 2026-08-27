from app.rag.pipeline.compression import compression_stage
from app.rag.pipeline.generation import generation_stage
from app.rag.pipeline.ranking import ranking_stage
from app.rag.pipeline.retrieval import retrieval_stage


class RAGPipeline:

    def run(self, question: str):

        rewritten, chunks = retrieval_stage.run(question)

        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the uploaded documents.",
                "sources": [],
            }

        chunks = ranking_stage.run(
            rewritten,
            chunks,
        )

        chunks = compression_stage.run(
            rewritten,
            chunks,
        )

        answer = generation_stage.run(
            question,
            chunks,
        )

        return {
            "answer": answer,
            "sources": [
                chunk.model_dump()
                for chunk in chunks
            ],
        }


pipeline = RAGPipeline()