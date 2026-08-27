import re

from app.schemas.retrieval import RetrievedChunk


class ContextCompressor:

    def compress(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:

        keywords = {

            word.lower()
            for word in re.findall(r"\w+", question)
            if len(word) > 2
        }

        compressed = []

        for chunk in chunks:

            sentences = re.split(

                r'(?<=[.!?])\s+|\n',

                chunk.text,

            )

            selected = []

            for sentence in sentences:

                text = sentence.lower()

                if any(

                    keyword in text

                    for keyword in keywords

                ):

                    selected.append(sentence)

            if selected:

                chunk.text = "\n".join(selected)

            compressed.append(chunk)

        return compressed


compressor = ContextCompressor()