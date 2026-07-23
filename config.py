import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# VECTOR STORE & EMBEDDING CONFIGURATION
# ==========================================
CHROMA_PERSIST_DIRECTORY = "./chroma_data"
COLLECTION_NAME = "nabl_documents"
EMBEDDING_MODEL_NAME = "gemini-embedding-001"
DATA_PATH = "./data/*.pdf"

# ==========================================
# INGESTION & TEXT SPLITTER CONFIGURATION
# ==========================================
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 65
