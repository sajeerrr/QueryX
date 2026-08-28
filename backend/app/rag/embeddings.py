from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"

model = SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """
    Generate a normalized embedding for a text chunk.
    """
    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate normalized embeddings for a list of text chunks in batches.
    """
    if not texts:
        return []
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False
    )
    return embeddings.tolist()