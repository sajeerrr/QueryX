class RankingStage:

    def run(self, chunks, top_k: int = 5):
        return chunks[:top_k]


ranking_stage = RankingStage()