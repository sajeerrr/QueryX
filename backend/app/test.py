from app.rag.bm25_index import bm25_index

print(
    bm25_index.search(
        "AI agent security",
        3
    )
)