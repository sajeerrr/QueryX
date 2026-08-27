from app.rag.pipeline import pipeline


def ask_question(question: str):

    response = pipeline.run(question)

    return {
        "question": question,
        "answer": response["answer"],
        "sources": response["sources"]
    }