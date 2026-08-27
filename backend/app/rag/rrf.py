from app.schemas.retrieval import RetrievedChunk

def reciprocal_rank_fusion(*rankings, k=60):

    scores = {}

    for ranking in rankings:

        for rank, doc in enumerate(ranking):

            key = (
                doc.document_id,
                doc.chunk_id
            )

            scores.setdefault(key, {
                "score": 0,
                "doc": doc
            })

            scores[key]["score"] += (
                1 / (k + rank + 1)
            )

    return [
        item["doc"]

        for item in sorted(
            scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
    ]