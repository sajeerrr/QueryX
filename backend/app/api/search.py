from fastapi import APIRouter, Query

from app.rag.retriever import retrieve
from app.schemas.search import SearchResponse

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(query: str = Query(..., min_length=2)):
    results = retrieve(query)
    return {
        "query": query,
        "matches": results,
        "total": len(results),
    }
