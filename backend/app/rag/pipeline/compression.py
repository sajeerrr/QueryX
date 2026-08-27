from app.rag.compressor import compressor


class CompressionStage:

    def run(self, question, chunks):

        return compressor.compress(
            question,
            chunks,
        )


compression_stage = CompressionStage()