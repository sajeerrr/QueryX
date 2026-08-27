from app.llm.groq import generate


SYSTEM_PROMPT = """
Generate 3 different search queries.

Requirements:

- Different wording
- Same meaning
- One query per line
- No numbering
"""


class MultiQueryGenerator:

    def generate(self, question: str):

        prompt = f"""
{SYSTEM_PROMPT}

Question:

{question}
"""
        response = generate(
            prompt,
            system_prompt="""
Generate multiple search queries.

Return one query per line.

Do NOT answer the question.
"""
        )

        queries = [
            line.strip()
            for line in response.splitlines()
            if line.strip()
        ]

        return queries[:3]

multi_query = MultiQueryGenerator()