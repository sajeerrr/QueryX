import threading
from openai import OpenAI

from app.core.config import CHAT_MODEL, GEMINI_API_KEY

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_client: OpenAI | None = None
_client_lock = threading.Lock()


def get_gemini_client() -> OpenAI:
    """Return a lazily initialized OpenAI-compatible Gemini API client."""
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY (or API_KEY) environment variable is not configured.")

        _client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_OPENAI_BASE_URL,
            max_retries=3,
            timeout=30.0,
        )
        return _client


def _build_messages(prompt: str, system_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]


def generate(prompt: str, system_prompt: str) -> str:
    """Generate a complete response from the configured Gemini chat model."""
    response = get_gemini_client().chat.completions.create(
        model=CHAT_MODEL,
        messages=_build_messages(prompt, system_prompt),
        temperature=0,
    )
    return (response.choices[0].message.content or "").strip()


def generate_stream(prompt: str, system_prompt: str):
    """Stream the Gemini LLM response token by token."""
    stream = get_gemini_client().chat.completions.create(
        model=CHAT_MODEL,
        messages=_build_messages(prompt, system_prompt),
        temperature=0,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
