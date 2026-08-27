from fastapi import APIRouter

from app.services.document_manager import list_documents, delete_document

router = APIRouter()


@router.get("/documents")
def get_documents():

    return list_documents()


@router.delete("/documents/{document_id}")
def remove_document(document_id: str):

    return delete_document(document_id)