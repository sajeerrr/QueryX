from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.rag.pipeline import pipeline
from app.schemas.chat import ChatRequest

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):
    return pipeline.run(
        session_id=request.session_id,
        question=request.question,
    )


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    return StreamingResponse(
        pipeline.run_stream(
            session_id=request.session_id,
            question=request.question,
        ),
        media_type="text/plain; charset=utf-8",
    )
