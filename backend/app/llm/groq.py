from openai import OpenAI

# from app.core.config import settings
from app.core.config import API_KEY, CHAT_MODEL


client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def generate(prompt: str) -> str:
    """
    Generate an answer using Groq.
    """

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are QueryX, a retrieval augmented AI assistant. "
                    "Answer ONLY using the provided context. "
                    "If the answer isn't present, say you don't know."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
    )

    return response.choices[0].message.content