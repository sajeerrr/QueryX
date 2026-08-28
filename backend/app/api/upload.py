from fastapi import APIRouter, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from app.schemas.document import UploadResponse
from app.services.document_service import process_document

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse
)
async def upload_pdf(
    file: UploadFile = File(...)
):
    content = await file.read()
    return await run_in_threadpool(
        process_document,
        file.filename,
        content
    )