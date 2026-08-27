from rank_bm25 import BM25Okapi


class BM25Retriever:

    def __init__(self):
        self.documents = []
        self.metadata = []
        self.bm25 = None

    def build(self, chunks):

        self.documents = [
            chunk["text"].split()
            for chunk in chunks
        ]

        self.metadata = chunks
        self.bm25 = BM25Okapi(self.documents)

    def search(
        self,
        query: str,
        limit: int = 10
    ):

        if self.bm25 is None:
            return []

        scores = self.bm25.get_scores(query.split())

        ranked = sorted(
            zip(scores, self.metadata),
            reverse=True,
            key=lambda x: x[0]
        )

        return [
            item[1]
            for item in ranked[:limit]
        ]


bm25 = BM25Retriever()