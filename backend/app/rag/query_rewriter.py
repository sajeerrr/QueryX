from app.llm.groq import generate


SYSTEM_PROMPT = """You rewrite user questions for semantic retrieval.

Requirements:
- Standalone
- Clear
- Grammatically complete
- Preserve the original meaning
- Do not answer it
- Return ONLY the rewritten question
"""


class QueryRewriter:

    def rewrite(self, question: str) -> str:

        rewritten = generate(
            prompt=question,
            system_prompt=SYSTEM_PROMPT,
        )

        return rewritten.strip()


query_rewriter = QueryRewriter()