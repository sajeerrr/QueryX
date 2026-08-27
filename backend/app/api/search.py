from fastapi import APIRouter, Query
from app.services.search_service import search_documents
from app.schemas.search import SearchResponse


router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    query: str = Query(..., min_length=2)
):
    return search_documents(query)