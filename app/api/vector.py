from fastapi import APIRouter
from app.services.qdrant_service import search_demo

router = APIRouter()

@router.get("/search-demo")
def search():
    
    results = search_demo()
    response=[]

    for item in results:
        response.append({
            "score":item.score,
            "text":item.payload["text"]
        })

    return response