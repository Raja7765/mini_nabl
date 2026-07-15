from fastapi import FastAPI
from pydantic import BaseModel
from services.rag_service import ask_question


#Create fast api application
app = FastAPI()

#Request body structure 
class QuestionRequest(BaseModel):
    question: str


#Test endpoints
@app.get("/")
def home():
    return {"message": "Mini NABL RAG API is running"}

#Chat endpoint 
@app.post("/chat")
def chat(request: QuestionRequest):

    #Send user question to the RAG service 
    answer = ask_question(request.question)

    # Gemini response list format-la vandha text mattum extract pannum
    if isinstance(answer, list):
        answer = answer[0]["text"]


    #Return the response in JSON format
    return {
        "question": request.question,
        "answer": answer
    }