from app.rag.pipeline.pipeline import pipeline


def ask_question(session_id: str, question: str):

    response = pipeline.run(session_id=session_id, question=question)

    return {
        "question": question,
        "answer": response["answer"],
        "sources": response["sources"]
    }