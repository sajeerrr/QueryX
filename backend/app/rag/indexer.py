import uuid
import threading
from datetime import datetime

from qdrant_client.models import PointStruct

from app.core.config import COLLECTION_NAME
from app.db.qdrant import client
from app.rag.embeddings import embed_texts
from app.rag.bm25_index import bm25_index


def index_document(filename: str, chunks: list[str]):

    document_id = str(uuid.uuid4())

    points = []

    if chunks:
        vectors = embed_texts(chunks)

        for chunk_id, (chunk, vector) in enumerate(zip(chunks, vectors), start=1):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_id": chunk_id,
                        "text": chunk,
                        "collection": "default",
                        "created_at": datetime.utcnow().isoformat(),
                        "page": None,
                        "source": filename
                    }
                )
            )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

    # Rebuild BM25 index in background to avoid blocking response
    threading.Thread(target=bm25_index.rebuild, daemon=True).start()

    return {
        "document_id": document_id,
        "indexed_chunks": len(points)
    }