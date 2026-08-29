from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from app.schemas.document import UploadResponse
from app.services.document_service import (
    process_document, process_document_stream, begin_processing,
    cancel_processing, finish_processing, DocumentProcessingCancelled,
)
from app.core.logger import logger

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse
)
async def upload_pdf(
    file: UploadFile = File(...),
    x_upload_id: str | None = Header(default=None),
):
    logger.info("UPLOAD API | received regular upload | filename=%r | content_type=%r", file.filename, file.content_type)
    content = await file.read()
    logger.info("UPLOAD API | request body read | filename=%r | bytes=%d", file.filename, len(content))
    cancel_event = begin_processing(x_upload_id)
    try:
        return await run_in_threadpool(process_document, file.filename, content, cancel_event)
    except DocumentProcessingCancelled:
        raise HTTPException(status_code=409, detail="Document processing was cancelled.")
    finally:
        finish_processing(x_upload_id)


@router.post("/upload/cancel/{upload_id}")
async def cancel_upload(upload_id: str):
    cancelled = cancel_processing(upload_id)
    logger.info("UPLOAD API | cancellation requested | upload_id=%s | found=%s", upload_id, cancelled)
    return {"cancelled": cancelled}


@router.post("/upload/stream")
async def upload_pdf_stream(
    file: UploadFile = File(...)
):
    logger.info("UPLOAD STREAM API | received upload | filename=%r | content_type=%r", file.filename, file.content_type)
    content = await file.read()
    logger.info("UPLOAD STREAM API | request body read | filename=%r | bytes=%d", file.filename, len(content))
    return StreamingResponse(
        process_document_stream(file.filename, content),
        media_type="application/x-ndjson"
    )
