from app.llm.groq import generate


SYSTEM_PROMPT = """Generate 3 different search queries for the user's question.

Requirements:
- Different wording
- Same meaning
- One query per line
- No numbering
- Do NOT answer the question
"""


class MultiQueryGenerator:

    def generate(self, question: str):

        response = generate(
            prompt=question,
            system_prompt=SYSTEM_PROMPT,
        )

        queries = [
            line.strip()
            for line in response.splitlines()
            if line.strip()
        ]

        return queries[:3]

multi_query = MultiQueryGenerator()