from app.core.config import EMBEDDING_DIM, EMBEDDING_MODEL
from app.llm.gemini import get_gemini_client

_BATCH_SIZE = 64


def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a single query or chunk using Gemini."""
    response = get_gemini_client().embeddings.create(
        input=text,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIM,
    )
    return list(response.data[0].embedding)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for a list of text chunks in batches using Gemini."""
    if not texts:
        return []

    client = get_gemini_client()
    vectors: list[list[float]] = []

    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start:start + _BATCH_SIZE]
        response = client.embeddings.create(
            input=batch,
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIM,
        )
        ordered = (
            sorted(response.data, key=lambda item: item.index)
            if all(item.index is not None for item in response.data)
            else response.data
        )
        vectors.extend(list(item.embedding) for item in ordered)

    return vectors
