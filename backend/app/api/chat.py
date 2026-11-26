from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.logger import logger
from app.rag.pipeline import pipeline
from app.schemas.chat import ChatRequest

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        return pipeline.run(
            session_id=request.session_id,
            question=request.question,
        )
    except Exception as exc:
        logger.exception("CHAT API | request failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    def event_stream():
        try:
            yield from pipeline.run_stream(
                session_id=request.session_id,
                question=request.question,
            )
        except Exception as exc:
            logger.exception("CHAT STREAM API | stream failed: %s", exc)
            yield f"\n[Error: {exc}]"

    return StreamingResponse(
        event_stream(),
        media_type="text/plain; charset=utf-8",
    )
