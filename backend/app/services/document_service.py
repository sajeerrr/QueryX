from pathlib import Path
from fastapi import HTTPException

from app.rag.chunker import chunk_text
from app.utils.pdf import extract_text
from app.utils.text import clean_text
from app.rag.indexer import index_document

# Absolute path to uploads directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def process_document(filename: str, data: bytes):

    filepath = UPLOAD_DIR / filename
    try:
        with open(filepath, "wb") as f:
            f.write(data)
    except Exception:
        pass

    try:
        raw_text = extract_text(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    text = clean_text(raw_text)
    if not text.strip():
        raise HTTPException(status_code=400, detail="The uploaded PDF contains no extractable text.")

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract text chunks from the document.")

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