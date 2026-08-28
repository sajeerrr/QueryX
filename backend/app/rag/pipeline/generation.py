from app.llm.groq import generate, generate_stream
from app.llm.prompt import build_prompt


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


class GenerationStage:

    def run(
        self,
        question: str,
        history: list,
        chunks,
    ):

        prompt = build_prompt(
            question=question,
            history=history,
            chunks=chunks,
        )

        return generate(
            prompt=prompt,
            system_prompt=ANSWER_SYSTEM_PROMPT,
        )

    def run_stream(
        self,
        question: str,
        history: list,
        chunks,
    ):

        prompt = build_prompt(
            question=question,
            history=history,
            chunks=chunks,
        )

        return generate_stream(
            prompt=prompt,
            system_prompt=ANSWER_SYSTEM_PROMPT,
        )


generation_stage = GenerationStage()