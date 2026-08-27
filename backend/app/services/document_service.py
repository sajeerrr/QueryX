from pathlib import Path

from app.rag.chunker import chunk_text
from app.utils.pdf import extract_text
from app.utils.text import clean_text
from app.rag.indexer import index_document


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def process_document(filename: str, data: bytes):

    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        f.write(data)

    text = clean_text(extract_text(str(filepath)))
    chunks = chunk_text(text)
    result = index_document(filename, chunks)

    return {
        "document_id": result["document_id"],
        "filename": filename,
        "chunk_count": len(chunks),
        "indexed_chunks": result["indexed_chunks"],
        "chunks": [
            {
                "id": i + 1,
                "text": chunk
            }
            for i, chunk in enumerate(chunks)
        ]
    }