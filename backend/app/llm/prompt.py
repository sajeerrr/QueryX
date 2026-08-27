def build_prompt(
    question: str,
    contexts: list[dict],
) -> str:
    """
    Build the RAG prompt.
    """

    context = "\n\n".join(
        [
            f"[Chunk {c['chunk_id']}]\n{c['text']}"
            for c in contexts
        ]
    )

    return f"""
Answer the question ONLY using the supplied context.

Context:

{context}

Question:

{question}

Answer:
"""