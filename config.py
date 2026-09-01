import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# ==========================================
# VECTOR STORE & EMBEDDING CONFIGURATION
# ==========================================
CHROMA_PERSIST_DIRECTORY = "./chroma_data"
COLLECTION_NAME = "nabl_documents"
EMBEDDING_MODEL_NAME = "gemini-embedding-001"
DOCUMENT_FOLDER = Path(r"C:\Users\rajas\OneDrive\ドキュメント\NABL_Documents")
BASE_DIR = Path(__file__).resolve().parent
TRAINING_FILE = BASE_DIR / "training.json"
METADATA_FILE = BASE_DIR / "metadata.json"
FAQ_FILE = BASE_DIR / "data" / "faqs.json"
# ==========================================
# INGESTION & TEXT SPLITTER CONFIGURATION
# ==========================================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 65
