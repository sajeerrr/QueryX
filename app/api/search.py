from fastapi import APIRouter
from app.rag.retriever import retrieve


router = APIRouter()


@router.get("/search")
def search(query: str):

    return retrieve(query)