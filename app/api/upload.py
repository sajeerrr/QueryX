from fastapi import APIRouter, UploadFile, File
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

    return process_document(
        file.filename,
        await file.read()
    )