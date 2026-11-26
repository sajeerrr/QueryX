from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.upload import router as upload_router
from app.core.config import EPHEMERAL_DOCUMENTS
from app.core.logger import logger
from app.db.qdrant import ensure_collection
from app.rag.bm25_index import bm25_index
from app.services.document_service import clear_all_documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_collection()
    if EPHEMERAL_DOCUMENTS:
        clear_all_documents()
    else:
        bm25_index.rebuild()
    try:
        yield
    finally:
        if EPHEMERAL_DOCUMENTS:
            try:
                clear_all_documents()
            except Exception as exc:
                logger.warning("SHUTDOWN | failed to clear ephemeral documents: %s", exc)


app = FastAPI(
    title="QueryX",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(search_router, prefix="/api", tags=["Search"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])


@app.get("/")
async def root():
    return {"message": "Production RAG API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
