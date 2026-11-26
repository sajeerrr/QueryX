import threading
from openai import OpenAI

from app.core.config import API_KEY, CHAT_MODEL

_client: OpenAI | None = None
_client_lock = threading.Lock()


def _get_client() -> OpenAI:
    """Return a lazily initialized OpenAI-compatible Groq client."""
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        if not API_KEY:
            raise RuntimeError("API_KEY (or GROQ_API_KEY) environment variable is not configured.")

        _client = OpenAI(
            api_key=API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        return _client


def _build_messages(prompt: str, system_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]


def generate(prompt: str, system_prompt: str) -> str:
    """Generate a complete response from the configured Groq chat model."""
    response = _get_client().chat.completions.create(
        model=CHAT_MODEL,
        messages=_build_messages(prompt, system_prompt),
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def generate_stream(prompt: str, system_prompt: str):
    """Stream the LLM response token by token."""
    stream = _get_client().chat.completions.create(
        model=CHAT_MODEL,
        messages=_build_messages(prompt, system_prompt),
        temperature=0,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
