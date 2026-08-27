from rank_bm25 import BM25Okapi

from app.db.qdrant import client
from app.core.config import COLLECTION_NAME
from app.schemas.retrieval import RetrievedChunk


class BM25Index:

    def __init__(self):

        self.index = None
        self.documents = []
        self.metadata = []

    def rebuild(self):

        print("Building BM25 index...")

        self.documents.clear()
        self.metadata.clear()

        offset = None

        while True:

            points, offset = client.scroll(

                collection_name=COLLECTION_NAME,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            for point in points:

                payload = point.payload

                self.documents.append(
                    payload["text"].lower().split()
                )

                self.metadata.append(

                    RetrievedChunk(

                        score=0.0,
                        document_id=payload["document_id"],
                        filename=payload["filename"],
                        chunk_id=payload["chunk_id"],
                        text=payload["text"],
                        page=payload.get("page"),
                        collection=payload.get("collection"),
                        source=payload.get("source"),
                    )
                )

            if offset is None:
                break

        if self.documents:

            self.index = BM25Okapi(self.documents)
            print(f"BM25 indexed {len(self.documents)} chunks")

        else:

            self.index = None
            print("BM25 empty")

    def search(self, query: str, limit: int = 10):

        if self.index is None:
            return []

        tokens = query.lower().split()
        scores = self.index.get_scores(tokens)
        ranked = sorted(

            zip(scores, self.metadata),
            key=lambda x: x[0],
            reverse=True,
        )

        results = []

        for score, chunk in ranked[:limit]:

            chunk.score = float(score)
            results.append(chunk)

        return results


bm25_index = BM25Index()