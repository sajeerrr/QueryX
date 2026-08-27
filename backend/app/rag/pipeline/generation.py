from app.llm.groq import generate
from app.llm.prompt import build_prompt

ANSWER_SYSTEM_PROMPT = """
You are QueryX, a Retrieval-Augmented Generation assistant.

Answer ONLY using the provided document context.

Rules:
- Do not use outside knowledge.
- If the answer is not present in the context, reply:
  "I don't know."
- Be concise and accurate.
"""

class GenerationStage:

    def run(self, question, chunks):

        prompt = build_prompt(
            question,
            chunks,
        )

        return generate(
            prompt=prompt,
            system_prompt=ANSWER_SYSTEM_PROMPT,
        )

generation_stage = GenerationStage()