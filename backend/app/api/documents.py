import json

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool

from app.memory.store import memory_store
from app.services.document_service import (
    clear_all_documents,
    delete_document,
    delete_documents,
    list_documents,
)

router = APIRouter()


@router.get("/documents")
async def get_documents():
    return await run_in_threadpool(list_documents)


@router.delete("/documents/{document_id}")
async def remove_document(document_id: str):
    return await run_in_threadpool(delete_document, document_id)


@router.post("/documents/clear")
async def clear_documents(request: Request):
    """Clear uploaded documents and session chat memory (used when closing the app)."""
    raw_body = await request.body()
    payload: dict = {}
    if raw_body:
        try:
            parsed = json.loads(raw_body)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = {}

    session_id = payload.get("session_id")
    if isinstance(session_id, str) and session_id:
        memory_store.clear(session_id)

    document_ids = payload.get("document_ids")
    if isinstance(document_ids, list) and document_ids and not payload.get("clear_all"):
        return await run_in_threadpool(delete_documents, [str(doc_id) for doc_id in document_ids])

    return await run_in_threadpool(clear_all_documents)
