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