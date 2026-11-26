import asyncio
import json
import threading
import uuid
from pathlib import Path
from time import perf_counter

from fastapi import HTTPException
from qdrant_client.http.models import FieldCondition, Filter, MatchAny, MatchValue

from app.core.config import COLLECTION_NAME
from app.core.logger import logger
from app.db.qdrant import get_qdrant_client
from app.rag.bm25_index import bm25_index
from app.rag.chunker import ChunkingCancelled, chunk_text
from app.rag.indexer import index_document
from app.utils.pdf import extract_text
from app.utils.text import clean_text

_processing_jobs: dict[str, threading.Event] = {}
_processing_jobs_lock = threading.Lock()


class DocumentProcessingCancelled(Exception):
    """Raised when an upload is cancelled mid-processing."""


def sanitize_filename(filename: str | None) -> str:
    """Strip any directory components from an uploaded filename."""
    clean_name = Path(filename or "document.pdf").name.strip()
    return clean_name or "document.pdf"


def list_documents() -> list[dict]:
    """Return one summary entry per indexed document across all Qdrant pages."""
    qdrant_client = get_qdrant_client()
    documents: dict[str, dict] = {}
    offset = None

    while True:
        points, offset = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            doc_id = payload["document_id"]
            if doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "filename": payload["filename"],
                    "chunks": 1,
                }
            else:
                documents[doc_id]["chunks"] += 1

        if offset is None:
            break

    return list(documents.values())


def delete_document(document_id: str, rebuild_bm25: bool = True) -> dict:
    """Delete a single document from Qdrant and refresh BM25."""
    qdrant_client = get_qdrant_client()
    doc_filter = Filter(
        must=[
            FieldCondition(
                key="document_id",
                match=MatchValue(value=document_id),
            )
        ]
    )

    qdrant_client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=doc_filter,
    )

    if rebuild_bm25:
        threading.Thread(target=bm25_index.rebuild, daemon=True).start()

    return {
        "deleted": True,
        "document_id": document_id,
    }


def delete_documents(document_ids: list[str], rebuild_bm25: bool = True) -> dict:
    """Delete multiple documents from Qdrant and refresh BM25."""
    unique_ids = [doc_id for doc_id in dict.fromkeys(document_ids) if doc_id]
    if not unique_ids:
        return {"deleted": 0}

    qdrant_client = get_qdrant_client()
    qdrant_client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=unique_ids),
                )
            ]
        ),
    )

    if rebuild_bm25:
        bm25_index.rebuild()

    logger.info("DOCUMENT | deleted %d session document(s) from Qdrant", len(unique_ids))
    return {"deleted": len(unique_ids)}


def clear_all_documents() -> dict:
    """Delete all points in the Qdrant collection and clear BM25."""
    qdrant_client = get_qdrant_client()
    qdrant_client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(),
    )
    bm25_index.clear()

    logger.info("DOCUMENT | cleared all documents from Qdrant and BM25")
    return {"cleared": True}


def _extract_and_clean(data: bytes) -> str:
    raw_text = extract_text(data)
    text = clean_text(raw_text)
    if not text.strip():
        raise ValueError("The uploaded PDF contains no extractable text.")
    return text


def _rollback_partial_document(filename: str, document_id: str | None) -> None:
    if not document_id:
        return
    try:
        delete_document(document_id, rebuild_bm25=False)
        logger.info("DOCUMENT | deleted partial document | filename=%r | document_id=%s", filename, document_id)
    except Exception:
        logger.exception("DOCUMENT | failed to delete partial document | filename=%r | document_id=%s", filename, document_id)


def begin_processing(upload_id: str | None) -> threading.Event | None:
    if not upload_id:
        return None
    event = threading.Event()
    with _processing_jobs_lock:
        _processing_jobs[upload_id] = event
    return event


def cancel_processing(upload_id: str) -> bool:
    with _processing_jobs_lock:
        event = _processing_jobs.get(upload_id)
    if not event:
        return False
    event.set()
    return True


def finish_processing(upload_id: str | None) -> None:
    if not upload_id:
        return
    with _processing_jobs_lock:
        _processing_jobs.pop(upload_id, None)


def process_document(
    filename: str,
    data: bytes,
    cancel_event: threading.Event | None = None,
) -> dict:
    started_at = perf_counter()
    safe_name = sanitize_filename(filename)
    logger.info("DOCUMENT | started regular processing | filename=%r | bytes=%d", safe_name, len(data))

    document_id = str(uuid.uuid4())

    def check_cancelled(document_id_for_cleanup: str | None = None) -> None:
        if cancel_event and cancel_event.is_set():
            logger.info("DOCUMENT | cancellation requested | filename=%r | document_id=%s", safe_name, document_id_for_cleanup)
            if document_id_for_cleanup:
                _rollback_partial_document(safe_name, document_id_for_cleanup)
            raise DocumentProcessingCancelled()

    check_cancelled(document_id)
    try:
        text = _extract_and_clean(data)
    except ValueError as e:
        logger.warning("DOCUMENT | PDF extraction failed | filename=%r | error=%s", safe_name, e)
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("DOCUMENT | text extracted | filename=%r | characters=%d", safe_name, len(text))

    logger.info("DOCUMENT | chunking started | filename=%r", safe_name)
    chunking_started_at = perf_counter()
    try:
        chunks = chunk_text(text, should_cancel=lambda: bool(cancel_event and cancel_event.is_set()))
    except ChunkingCancelled as exc:
        check_cancelled(document_id)
        raise DocumentProcessingCancelled() from exc
    logger.info("DOCUMENT | chunking finished | filename=%r | elapsed_seconds=%.2f", safe_name, perf_counter() - chunking_started_at)

    if not chunks:
        logger.warning("DOCUMENT | no chunks created | filename=%r", safe_name)
        raise HTTPException(status_code=400, detail="Could not extract text chunks from the document.")

    logger.info("DOCUMENT | chunks created | filename=%r | chunks=%d", safe_name, len(chunks))

    check_cancelled(document_id)
    logger.info("DOCUMENT | embedding and indexing started | filename=%r", safe_name)
    result = index_document(safe_name, chunks, document_id=document_id)
    logger.info(
        "DOCUMENT | indexing complete | filename=%r | document_id=%s | indexed_chunks=%d | elapsed_seconds=%.2f",
        safe_name,
        result["document_id"],
        result["indexed_chunks"],
        perf_counter() - started_at,
    )

    if cancel_event and cancel_event.is_set():
        logger.info("DOCUMENT | cancellation was requested after indexing started | filename=%r | document_id=%s", safe_name, document_id)
        _rollback_partial_document(safe_name, document_id)
        raise DocumentProcessingCancelled()

    return {
        "document_id": result["document_id"],
        "filename": safe_name,
        "chunk_count": len(chunks),
        "indexed_chunks": result["indexed_chunks"],
        "chunks": [
            {"id": i + 1, "text": chunk}
            for i, chunk in enumerate(chunks)
        ],
    }


async def process_document_stream(filename: str, data: bytes):
    """Asynchronously process a PDF in memory and yield NDJSON progress events."""
    started_at = perf_counter()
    safe_name = sanitize_filename(filename)
    logger.info("DOCUMENT STREAM | processing started | filename=%r | bytes=%d", safe_name, len(data))

    try:
        yield json.dumps({
            "stage": "extracting",
            "progress": 20,
            "message": f"Reading and extracting text from {safe_name}…",
        }) + "\n"
        await asyncio.sleep(0.05)

        try:
            text = _extract_and_clean(data)
        except ValueError as e:
            logger.warning("DOCUMENT STREAM | PDF extraction failed | filename=%r | error=%s", safe_name, e)
            yield json.dumps({"stage": "error", "message": str(e)}) + "\n"
            return

        logger.info("DOCUMENT STREAM | text extracted | filename=%r | characters=%d", safe_name, len(text))

        yield json.dumps({
            "stage": "chunking",
            "progress": 45,
            "message": "Splitting document into semantic paragraphs…",
        }) + "\n"
        await asyncio.sleep(0.05)

        logger.info("DOCUMENT STREAM | chunking started | filename=%r", safe_name)
        chunking_started_at = perf_counter()
        chunks = await asyncio.to_thread(chunk_text, text)
        logger.info("DOCUMENT STREAM | chunking finished | filename=%r | elapsed_seconds=%.2f", safe_name, perf_counter() - chunking_started_at)

        if not chunks:
            logger.warning("DOCUMENT STREAM | no chunks created | filename=%r", safe_name)
            yield json.dumps({"stage": "error", "message": "Could not extract text chunks from the document."}) + "\n"
            return

        logger.info("DOCUMENT STREAM | chunks created | filename=%r | chunks=%d", safe_name, len(chunks))

        yield json.dumps({
            "stage": "embedding",
            "progress": 70,
            "message": f"Generating vector embeddings for {len(chunks)} chunks…",
        }) + "\n"
        await asyncio.sleep(0.05)

        yield json.dumps({
            "stage": "indexing",
            "progress": 90,
            "message": "Generating embeddings and storing the document in the database…",
        }) + "\n"
        await asyncio.sleep(0.05)

        logger.info("DOCUMENT STREAM | embedding and Qdrant indexing started | filename=%r | chunks=%d", safe_name, len(chunks))
        result = await asyncio.to_thread(index_document, safe_name, chunks)
        logger.info(
            "DOCUMENT STREAM | indexing complete | filename=%r | document_id=%s | indexed_chunks=%d | elapsed_seconds=%.2f",
            safe_name,
            result["document_id"],
            result["indexed_chunks"],
            perf_counter() - started_at,
        )

        yield json.dumps({
            "stage": "complete",
            "progress": 100,
            "message": f"Indexed {result['indexed_chunks']} chunks successfully",
            "document_id": result["document_id"],
            "filename": safe_name,
            "indexed_chunks": result["indexed_chunks"],
        }) + "\n"

    except asyncio.CancelledError:
        logger.warning("DOCUMENT STREAM | client disconnected/cancelled | filename=%r", safe_name)
        raise
    except Exception as e:
        logger.exception("DOCUMENT STREAM | processing failed | filename=%r | error=%s", safe_name, e)
        yield json.dumps({"stage": "error", "message": f"Processing error: {str(e)}"}) + "\n"
