from app.llm.groq import generate
from app.llm.prompt import build_prompt
from app.rag.retriever import retrieve


def ask_question(question: str):

    chunks = retrieve(question)

    prompt = build_prompt(
        question,
        chunks,
    )

    answer = generate(prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": chunks,
    }