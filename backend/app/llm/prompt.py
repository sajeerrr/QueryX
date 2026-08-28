def build_prompt(
    question: str,
    history: list,
    chunks,
) -> str:
    """
    Build the final RAG prompt.
    """

    # -----------------------------
    # Conversation History
    # -----------------------------
    conversation = []

    for message in history:
        conversation.append(
            f"{message.role.capitalize()}: {message.content}"
        )

    conversation = "\n".join(conversation)

    # -----------------------------
    # Retrieved Context
    # -----------------------------
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

    # -----------------------------
    # Final Prompt
    # -----------------------------
    return f"""
Conversation History
====================

{conversation}

====================

Retrieved Context
====================

{context}

====================

Question

{question}

Instructions

- Use the conversation history only to understand follow-up questions.
- Answer ONLY using the retrieved context.
- Do NOT use outside knowledge.
- If the answer is not present in the retrieved context, reply:
  "I couldn't find this information in the uploaded documents."
- Be concise and accurate.
"""