from pathlib import Path
from fastapi import HTTPException

from app.rag.chunker import chunk_text, ChunkingCancelled
from app.utils.pdf import extract_text
from app.utils.text import clean_text
from app.rag.indexer import index_document
from app.services.document_manager import delete_document
from app.core.config import UPLOAD_DIR
from app.core.logger import logger

import threading
import uuid
from time import perf_counter

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logger.info("DOCUMENT STORAGE | upload directory=%s", UPLOAD_DIR)

_processing_jobs: dict[str, threading.Event] = {}
_processing_jobs_lock = threading.Lock()


class DocumentProcessingCancelled(Exception):
    pass


def _rollback_partial_document(filename: str, document_id: str | None, filepath: Path | None = None):
    if not document_id:
        return
    try:
        delete_document(document_id)
        logger.info("DOCUMENT | deleted partial document | filename=%r | document_id=%s", filename, document_id)
    except Exception:
        logger.exception("DOCUMENT | failed to delete partial document | filename=%r | document_id=%s", filename, document_id)

    if filepath is not None:
        try:
            filepath.unlink(missing_ok=True)
            logger.info("DOCUMENT | removed cancelled upload file | path=%s", filepath)
        except OSError:
            logger.warning("DOCUMENT | could not remove cancelled upload | path=%s", filepath)


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


def finish_processing(upload_id: str | None):
    if not upload_id:
        return
    with _processing_jobs_lock:
        _processing_jobs.pop(upload_id, None)


import json
import asyncio

def process_document(filename: str, data: bytes, cancel_event: threading.Event | None = None):
    started_at = perf_counter()
    logger.info("DOCUMENT | started regular processing | filename=%r | bytes=%d", filename, len(data))

    filepath = UPLOAD_DIR / filename
    document_id = str(uuid.uuid4())

    def check_cancelled(document_id_for_cleanup: str | None = None):
        if cancel_event and cancel_event.is_set():
            logger.info("DOCUMENT | cancellation requested | filename=%r | document_id=%s", filename, document_id_for_cleanup)
            if document_id_for_cleanup:
                _rollback_partial_document(filename, document_id_for_cleanup, filepath)
            else:
                try:
                    filepath.unlink(missing_ok=True)
                except OSError:
                    logger.warning("DOCUMENT | could not remove cancelled upload | path=%s", filepath)
            raise DocumentProcessingCancelled()

    try:
        with open(filepath, "wb") as f:
            f.write(data)
        logger.info("DOCUMENT | file saved | filename=%r | path=%s", filename, filepath)
    except Exception:
        logger.exception("DOCUMENT | failed to save upload | filename=%r | path=%s", filename, filepath)

    check_cancelled(document_id)
    try:
        raw_text = extract_text(data)
    except ValueError as e:
        logger.warning("DOCUMENT | PDF extraction failed | filename=%r | error=%s", filename, e)
        raise HTTPException(status_code=400, detail=str(e))

    check_cancelled(document_id)
    text = clean_text(raw_text)
    if not text.strip():
        logger.warning("DOCUMENT | no extractable text | filename=%r", filename)
        raise HTTPException(status_code=400, detail="The uploaded PDF contains no extractable text.")

    logger.info("DOCUMENT | text extracted | filename=%r | characters=%d", filename, len(text))

    logger.info("DOCUMENT | chunking started | filename=%r", filename)
    chunking_started_at = perf_counter()
    try:
        chunks = chunk_text(text, should_cancel=lambda: bool(cancel_event and cancel_event.is_set()))
    except ChunkingCancelled as exc:
        check_cancelled(document_id)
        raise DocumentProcessingCancelled() from exc
    logger.info("DOCUMENT | chunking finished | filename=%r | elapsed_seconds=%.2f", filename, perf_counter() - chunking_started_at)
    if not chunks:
        logger.warning("DOCUMENT | no chunks created | filename=%r", filename)
        raise HTTPException(status_code=400, detail="Could not extract text chunks from the document.")

    logger.info("DOCUMENT | chunks created | filename=%r | chunks=%d", filename, len(chunks))

    check_cancelled(document_id)
    logger.info("DOCUMENT | embedding and indexing started | filename=%r", filename)
    result = index_document(filename, chunks, document_id=document_id)
    logger.info("DOCUMENT | indexing complete | filename=%r | document_id=%s | indexed_chunks=%d | elapsed_seconds=%.2f", filename, result["document_id"], result["indexed_chunks"], perf_counter() - started_at)

    if cancel_event and cancel_event.is_set():
        logger.info("DOCUMENT | cancellation was requested after indexing started | filename=%r | document_id=%s", filename, document_id)
        _rollback_partial_document(filename, document_id, filepath)
        raise DocumentProcessingCancelled()

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


async def process_document_stream(filename: str, data: bytes):
    """
    Asynchronously processes a PDF and yields real-time JSON events with progress percentage and status.
    """
    started_at = perf_counter()
    logger.info("DOCUMENT STREAM | processing started | filename=%r | bytes=%d", filename, len(data))
    try:
        # Stage 1: Extract text
        yield json.dumps({
            "stage": "extracting",
            "progress": 20,
            "message": f"Reading and extracting text from {filename}…"
        }) + "\n"
        await asyncio.sleep(0.05)

        filepath = UPLOAD_DIR / filename
        try:
            with open(filepath, "wb") as f:
                f.write(data)
            logger.info("DOCUMENT STREAM | file saved | filename=%r | path=%s", filename, filepath)
        except Exception:
            logger.exception("DOCUMENT STREAM | failed to save upload | filename=%r | path=%s", filename, filepath)

        try:
            raw_text = extract_text(data)
        except ValueError as e:
            logger.warning("DOCUMENT STREAM | PDF extraction failed | filename=%r | error=%s", filename, e)
            yield json.dumps({"stage": "error", "message": str(e)}) + "\n"
            return

        text = clean_text(raw_text)
        if not text.strip():
            logger.warning("DOCUMENT STREAM | no extractable text | filename=%r", filename)
            yield json.dumps({"stage": "error", "message": "The uploaded PDF contains no extractable text."}) + "\n"
            return

        logger.info("DOCUMENT STREAM | text extracted | filename=%r | characters=%d", filename, len(text))

        # Stage 2: Chunking
        yield json.dumps({
            "stage": "chunking",
            "progress": 45,
            "message": "Splitting document into semantic paragraphs…"
        }) + "\n"
        await asyncio.sleep(0.05)

        logger.info("DOCUMENT STREAM | chunking started | filename=%r", filename)
        chunking_started_at = perf_counter()
        # Keep CPU work off the async response loop so progress events and
        # health/document requests remain responsive during large PDFs.
        chunks = await asyncio.to_thread(chunk_text, text)
        logger.info("DOCUMENT STREAM | chunking finished | filename=%r | elapsed_seconds=%.2f", filename, perf_counter() - chunking_started_at)
        if not chunks:
            logger.warning("DOCUMENT STREAM | no chunks created | filename=%r", filename)
            yield json.dumps({"stage": "error", "message": "Could not extract text chunks from the document."}) + "\n"
            return

        logger.info("DOCUMENT STREAM | chunks created | filename=%r | chunks=%d", filename, len(chunks))

        # Stage 3: Embedding
        yield json.dumps({
            "stage": "embedding",
            "progress": 70,
            "message": f"Generating vector embeddings for {len(chunks)} chunks…"
        }) + "\n"
        await asyncio.sleep(0.05)

        # Stage 4: Indexing in Qdrant & BM25. Emit this *before* the blocking
        # operation so the client remains visibly processing until it completes.
        yield json.dumps({
            "stage": "indexing",
            "progress": 90,
            "message": "Generating embeddings and storing the document in the database…"
        }) + "\n"
        await asyncio.sleep(0.05)

        logger.info("DOCUMENT STREAM | embedding and Qdrant indexing started | filename=%r | chunks=%d", filename, len(chunks))
        result = await asyncio.to_thread(index_document, filename, chunks)
        logger.info("DOCUMENT STREAM | indexing complete | filename=%r | document_id=%s | indexed_chunks=%d | elapsed_seconds=%.2f", filename, result["document_id"], result["indexed_chunks"], perf_counter() - started_at)

        # Stage 5: Complete
        yield json.dumps({
            "stage": "complete",
            "progress": 100,
            "message": f"Indexed {result['indexed_chunks']} chunks successfully",
            "document_id": result["document_id"],
            "filename": filename,
            "indexed_chunks": result["indexed_chunks"]
        }) + "\n"

    except asyncio.CancelledError:
        # This means the browser closed the stream before indexing completed.
        logger.warning("DOCUMENT STREAM | client disconnected/cancelled | filename=%r", filename)
        raise
    except Exception as e:
        logger.exception("DOCUMENT STREAM | processing failed | filename=%r | error=%s", filename, e)
        yield json.dumps({"stage": "error", "message": f"Processing error: {str(e)}"}) + "\n"
