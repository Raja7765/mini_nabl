from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import shutil
from ingest import ingest_single_pdf
from services.vector_store import VectorStore
from services.rag_service import stream_answer

# Create fastapi application
app = FastAPI()

# Create a vector instance 
vector_store = VectorStore()

# Request body structure 
class QuestionRequest(BaseModel):
    session_id: str
    question: str


# Test endpoints
@app.get("/")
def home():
    return {"message": "Mini NABL RAG API is running"}


# Document upload api
@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chunks = ingest_single_pdf(file_path)

    return {
        "message": "Document uploaded successfully",
        "filename": file.filename,
        "chunks": chunks
    }


# Chat Stream response endpoint
@app.post("/chat/stream")
def chat_stream(request: QuestionRequest):
    return StreamingResponse(
        stream_answer(
            request.question,
            request.session_id
        ),
        media_type="text/event-stream"
    )