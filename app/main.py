from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.qdrant_service import create_collection, insert_demo_data
from app.api.vector import router as vector_router


app = FastAPI(
    title="Production RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    vector_router,
    prefix="/api"
)

@app.on_event("startup")
def startup():

    create_collection()
    insert_demo_data()


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