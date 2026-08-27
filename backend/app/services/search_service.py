from app.rag.retriever import retrieve


def search_documents(query: str):

    results = retrieve(query)

    return {
        "query": query,
        "matches": results,
        "total": len(results),
    }