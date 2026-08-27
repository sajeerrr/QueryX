from fastapi import APIRouter
from pydantic import BaseModel
from app.services.rag_service import ask_question

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(
    request: ChatRequest,
):

    return ask_question(
        request.question
    )