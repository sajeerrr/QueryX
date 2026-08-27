from rag.embeddings import embed

vector = embed("Hello QueryX")

print(len(vector))