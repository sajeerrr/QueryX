from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from app.schemas.document import UploadResponse
from app.services.document_service import process_document, process_document_stream
from app.core.logger import logger

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse
)
async def upload_pdf(
    file: UploadFile = File(...)
):
    logger.info("UPLOAD API | received regular upload | filename=%r | content_type=%r", file.filename, file.content_type)
    content = await file.read()
    logger.info("UPLOAD API | request body read | filename=%r | bytes=%d", file.filename, len(content))
    return await run_in_threadpool(
        process_document,
        file.filename,
        content
    )


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
