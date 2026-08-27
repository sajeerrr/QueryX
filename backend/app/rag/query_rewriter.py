from app.llm.groq import generate


SYSTEM_PROMPT = """
Rewrite the user's question so it is:

- Standalone
- Clear
- Grammatically complete
- Preserve the original meaning
- Do not answer it
- Return ONLY the rewritten question
"""


class QueryRewriter:

    def rewrite(self, question: str) -> str:

        prompt = f"""
{SYSTEM_PROMPT}

Question:

{question}
"""

        rewritten = generate(
            prompt,
            system_prompt="""
You rewrite user questions for semantic retrieval.

Return ONLY the rewritten query.

Do not answer the question.
"""
        )

        return rewritten.strip()


query_rewriter = QueryRewriter()