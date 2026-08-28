from openai import OpenAI

from app.core.config import API_KEY, CHAT_MODEL

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def generate(prompt: str, system_prompt: str) -> str:
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    return response.choices[0].message.content.strip()


def generate_stream(
    prompt: str,
    system_prompt: str,
):
    """
    Stream the LLM response token by token.
    """

    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        stream=True,
    )

    for chunk in stream:

        if (
            chunk.choices
            and chunk.choices[0].delta.content
        ):

            yield chunk.choices[0].delta.content