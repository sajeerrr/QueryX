from app.memory.manager import memory_manager

from app.rag.pipeline.compression import compression_stage
from app.rag.pipeline.generation import generation_stage
from app.rag.pipeline.ranking import ranking_stage
from app.rag.pipeline.retrieval import retrieval_stage


class RAGPipeline:

    def run(
        self,
        session_id: str,
        question: str,
    ):

        history = memory_manager.history(session_id)

        chunks = retrieval_stage.run(question)

        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the uploaded documents.",
                "sources": [],
            }

        chunks = ranking_stage.run(chunks)

        chunks = compression_stage.run(chunks)

        answer = generation_stage.run(
            question=question,
            history=history,
            chunks=chunks,
        )

        memory_manager.add_user(session_id, question)
        memory_manager.add_assistant(session_id, answer)

        return {
            "answer": answer,
            "sources": [
                chunk.model_dump()
                for chunk in chunks
            ],
        }

    def run_stream(
        self,
        session_id: str,
        question: str,
    ):

        history = memory_manager.history(session_id)

        chunks = retrieval_stage.run(question)

        if not chunks:
            yield "I couldn't find relevant information in the uploaded documents."
            return

        chunks = ranking_stage.run(chunks)

        chunks = compression_stage.run(chunks)

        stream = generation_stage.run_stream(
            question=question,
            history=history,
            chunks=chunks,
        )

        answer_tokens = []

        for token in stream:
            answer_tokens.append(token)
            yield token

        answer = "".join(answer_tokens)

        memory_manager.add_user(session_id, question)
        memory_manager.add_assistant(session_id, answer)


pipeline = RAGPipeline()