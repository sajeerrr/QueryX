from app.llm.groq import generate
from app.llm.prompt import build_prompt

from app.rag.hybrid import hybrid_search


class RAGPipeline:

    def run(self, question: str):

        chunks = hybrid_search(question)

        if not chunks:

            return {
                "answer":
                "I couldn't find relevant information in the uploaded documents.",
                "sources":[]
            }

        prompt = build_prompt(

            question=question,
            contexts=chunks,
        )

        answer = generate(prompt)

        return {

            "answer":answer,
            "sources":[
                chunk.model_dump()
                for chunk in chunks
            ]
        }

pipeline = RAGPipeline()