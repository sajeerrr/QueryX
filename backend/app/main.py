from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from app.services.qdrant_service import create_collection

from app.api.search import router as search_router
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.rag.bm25_index import bm25_index


app = FastAPI(
    title="QueryX",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(search_router, prefix="/api", tags=["Search"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])


@app.on_event("startup")
async def startup():
    create_collection()
    bm25_index.rebuild()


@app.get("/")
async def root():
    return {
        "message": "Production RAG API"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }