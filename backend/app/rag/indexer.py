import sys
import threading
import uuid
from datetime import datetime, timezone

from qdrant_client.models import PointStruct

from app.core.config import COLLECTION_NAME
from app.core.logger import logger
from app.db.qdrant import get_qdrant_client
from app.rag.bm25_index import bm25_index
from app.rag.embeddings import embed_texts


class TerminalIndexingAnimation:
    """Show a compact live spinner in interactive terminals while indexing."""

    _terminal_lock = threading.Lock()
    _frames = ("|", "/", "-", "\\")

    def __init__(self, filename: str, chunk_count: int):
        self.filename = filename
        self.chunk_count = chunk_count
        self.message = "Generating embeddings"
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._owns_terminal = False

    def start(self) -> None:
        if not sys.stdout.isatty():
            return
        self._owns_terminal = self._terminal_lock.acquire(blocking=False)
        if not self._owns_terminal:
            return

        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def update(self, message: str) -> None:
        self.message = message

    def stop(self, outcome: str) -> None:
        if not self._owns_terminal:
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        sys.stdout.write("\r" + " " * 120 + "\r")
        sys.stdout.write(f"[INDEXING] {outcome} | {self.filename} | {self.chunk_count} chunks\n")
        sys.stdout.flush()
        self._terminal_lock.release()
        self._owns_terminal = False

    def _animate(self) -> None:
        frame_index = 0
        while not self._stop_event.is_set():
            frame = self._frames[frame_index % len(self._frames)]
            line = f"[INDEXING] {frame} {self.message} | {self.filename} | {self.chunk_count} chunks"
            sys.stdout.write("\r" + line[:118].ljust(118))
            sys.stdout.flush()
            frame_index += 1
            self._stop_event.wait(0.12)


def index_document(
    filename: str,
    chunks: list[str],
    document_id: str | None = None,
) -> dict:
    """Embed and upsert document chunks into Qdrant and schedule BM25 refresh."""
    document_id = document_id or str(uuid.uuid4())
    logger.info(
        "INDEXER | started | filename=%r | document_id=%s | chunks=%d",
        filename,
        document_id,
        len(chunks),
    )
    animation = TerminalIndexingAnimation(filename, len(chunks))
    animation.start()

    points = []
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        if chunks:
            vectors = embed_texts(chunks)
            logger.info(
                "INDEXER | embeddings generated | filename=%r | document_id=%s | vectors=%d",
                filename,
                document_id,
                len(vectors),
            )

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
                            "created_at": created_at,
                            "page": None,
                            "source": filename,
                        },
                    )
                )

            animation.update("Uploading vectors to Qdrant")
            get_qdrant_client().upsert(
                collection_name=COLLECTION_NAME,
                points=points,
            )
            logger.info(
                "INDEXER | Qdrant upsert complete | filename=%r | document_id=%s | points=%d",
                filename,
                document_id,
                len(points),
            )

        # Rebuild BM25 index in background to avoid blocking response
        threading.Thread(target=bm25_index.rebuild, daemon=True).start()
        logger.info("INDEXER | BM25 rebuild scheduled | filename=%r | document_id=%s", filename, document_id)
        animation.stop("Complete")
    except Exception:
        animation.stop("Failed")
        raise

    return {
        "document_id": document_id,
        "indexed_chunks": len(points),
    }
