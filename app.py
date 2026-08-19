from fastapi import FastAPI
from routes.upload import router as upload_router
from routes.chat import router as chat_router
from routes.delete import router as delete_router
from routes.update import router as update_router

# Create fastapi application
app = FastAPI()

# Include route routers
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(delete_router)
app.include_router(update_router)

# Test endpoints
@app.get("/")
def home():
    return {"message": "Mini NABL RAG API is running"}