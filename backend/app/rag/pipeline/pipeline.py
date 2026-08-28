from app.memory.manager import memory_manager

from app.rag.pipeline.compression import compression_stage
from app.rag.pipeline.generation import generation_stage
from app.rag.pipeline.ranking import ranking_stage
from app.rag.pipeline.retrieval import retrieval_stage


class RAGPipeline:

    def run(self, session_id: str, question: str):

        # Get recent conversation history
        history = memory_manager.history(session_id)

        # Retrieve relevant document chunks
        rewritten, chunks = retrieval_stage.run(question)

        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the uploaded documents.",
                "sources": [],
            }

        # Rerank retrieved chunks
        chunks = ranking_stage.run(
            rewritten,
            chunks,
        )

        # Compress context
        chunks = compression_stage.run(
            rewritten,
            chunks,
        )

        # Generate answer using conversation history
        answer = generation_stage.run(
            question=question,
            history=history,
            chunks=chunks,
        )

        # Save conversation
        memory_manager.add_user(
            session_id=session_id,
            message=question,
        )

        memory_manager.add_assistant(
            session_id=session_id,
            message=answer,
        )

        return {
            "answer": answer,
            "sources": [
                chunk.model_dump()
                for chunk in chunks
            ],
        }


pipeline = RAGPipeline()