from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.rag_service import stream_answer

router = APIRouter()


# Request body structure 
class QuestionRequest(BaseModel):
    session_id: str
    question: str


# Chat Stream response endpoint
@router.post("/chat/stream")
def chat_stream(request: QuestionRequest):
    return StreamingResponse(
        stream_answer(
            request.question,
            request.session_id
        ),
        media_type="text/event-stream"
    )
