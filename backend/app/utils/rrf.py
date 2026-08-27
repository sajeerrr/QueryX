from app.schemas.retrieval import RetrievedChunk


def reciprocal_rank_fusion(*rankings: list[RetrievedChunk], k: int = 60) -> list[RetrievedChunk]:

    scores = {}

    for ranking in rankings:

        for rank, chunk in enumerate(ranking):

            key = (
                chunk.document_id,
                chunk.chunk_id,
            )

            if key not in scores:

                scores[key] = {
                    "chunk": chunk,
                    "score": 0.0,
                }

            scores[key]["score"] += 1 / (k + rank + 1)

    merged = sorted(
        scores.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    return [
        item["chunk"]
        for item in merged
    ]