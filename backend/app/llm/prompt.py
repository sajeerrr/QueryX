def build_prompt(question: str, chunks: list[dict]) -> str:

    """
    Build the RAG prompt.
    """

    context = []

    for chunk in chunks:

        context.append(

            f"""
    Source: {chunk.filename}
    Chunk: {chunk.chunk_id}

    {chunk.text}
    """

        )

    context = "\n\n".join(context)

    return f"""
You are QueryX.

Answer ONLY using the provided context.

If the answer cannot be found, say:

"I couldn't find this information in the uploaded documents."

Never invent information.

========================

{context}

========================

Question:

{question}
"""