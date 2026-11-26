from app.llm.gemini import generate, generate_stream
from app.llm.prompt import build_prompt
from app.memory import memory_manager
from app.rag.hybrid import hybrid_search

ANSWER_SYSTEM_PROMPT = """
You are QueryX, a Retrieval-Augmented Generation assistant.

Answer ONLY using the provided document context.

Rules:
- Use the conversation history only to understand follow-up questions.
- Use the retrieved document context as the source of truth.
- Do not use outside knowledge.
- If the answer is not present in the context, reply:
  "I couldn't find this information in the uploaded documents."
- Be concise and accurate.
"""


class RAGPipeline:
    """End-to-end Retrieval-Augmented Generation pipeline."""

    def run(self, session_id: str, question: str) -> dict:
        history = memory_manager.history(session_id)
        chunks = hybrid_search(question, limit=5)

        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the uploaded documents.",
                "sources": [],
            }

        prompt = build_prompt(question=question, history=history, chunks=chunks)
        answer = generate(prompt=prompt, system_prompt=ANSWER_SYSTEM_PROMPT)

        memory_manager.add_user(session_id, question)
        memory_manager.add_assistant(session_id, answer)

        return {
            "answer": answer,
            "sources": [chunk.model_dump() for chunk in chunks],
        }

    def run_stream(self, session_id: str, question: str):
        history = memory_manager.history(session_id)
        chunks = hybrid_search(question, limit=5)

        if not chunks:
            yield "I couldn't find relevant information in the uploaded documents."
            return

        prompt = build_prompt(question=question, history=history, chunks=chunks)
        stream = generate_stream(prompt=prompt, system_prompt=ANSWER_SYSTEM_PROMPT)

        answer_tokens = []
        for token in stream:
            answer_tokens.append(token)
            yield token

        answer = "".join(answer_tokens)
        memory_manager.add_user(session_id, question)
        memory_manager.add_assistant(session_id, answer)


pipeline = RAGPipeline()
