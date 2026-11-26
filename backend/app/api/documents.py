from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.services.document_service import delete_document, list_documents

router = APIRouter()


@router.get("/documents")
async def get_documents():
    return await run_in_threadpool(list_documents)


@router.delete("/documents/{document_id}")
async def remove_document(document_id: str):
    return await run_in_threadpool(delete_document, document_id)
