from fastapi import UploadFile, File
import os
import shutil
from ingest import ingest_single_pdf
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.vector_store import VectorStore
from fastapi import FastAPI
from pydantic import BaseModel
from services.rag_service import ask_question


#Create fast api application
app = FastAPI()

#Create a vector instance 
vector_store = VectorStore()

#Request body structure 
class QuestionRequest(BaseModel):
    session_id: str
    question: str


#Test endpoints
@app.get("/")
def home():
    return {"message": "Mini NABL RAG API is running"}

#Chat endpoint 
@app.post("/chat")
def chat(request: QuestionRequest):
    

    #Send user question to the RAG service 
    answer = ask_question(request.question,request.session_id)

    # Gemini response list format-la vandha text mattum extract pannum
    if isinstance(answer, list):
        answer = answer[0]["text"]


    #Return the response in JSON format
    return {
        "question": request.question,
        "session_id":request.session_id,
        "answer": answer
    }

#Document upload api
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