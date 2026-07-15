import os
import glob
import time
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==========================================
# INITIAL SETUP & ENVIRONMENT CONFIGURATION
# ==========================================
load_dotenv()

# Verify API key presence
api_key = os.getenv("GOOGLE_API_KEY")
print("API key loaded successfully:", api_key is not None)

# Initialize the Embedding Model
print("Initializing embedding model...")
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

# ==========================================
# STEP 1: Load all PDF from data folder
# ==========================================
print("Step 1: Loading all PDFs...")

raw_documents = []
pdf_files = glob.glob("./data/*.pdf")

for pdf_file in pdf_files:
    print(f"Loading: {pdf_file}")
    loader = PyPDFLoader(pdf_file)
    pages = loader.load()
    raw_documents.extend(pages)

print(f"Total PDFs loaded: {len(pdf_files)}")
print(f"Total raw pages loaded: {len(raw_documents)}")

# ==========================================
# STEP 2: Split into chunks
# ==========================================
print("\nStep 2: Splitting full pages into smaller text chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(raw_documents)
print(f"Text splitting complete! Total chunks created: {len(chunks)}")

# ==========================================
# STEP 3 & 4: Initialize ChromaDB & Add Chunks in Batches
# ==========================================
print("\nSteps 3 & 4: Initializing ChromaDB and embedding chunks in batches...")

vector_store = Chroma(
    persist_directory="./chroma_data",
    embedding_function=embeddings,
    collection_name="nabl_documents"
)

batch_size = 50
total_chunks = len(chunks)
total_batches = (total_chunks + batch_size - 1) // batch_size

for i in range(total_batches):
    batch_num = i + 1
    start_idx = i * batch_size
    end_idx = min((i + 1) * batch_size, total_chunks)
    batch = chunks[start_idx:end_idx]
    
    print(f"\nProcessing Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
    
    attempts = 0
    max_retries = 3
    success = False
    
    while attempts < max_retries and not success:
        try:
            vector_store.add_documents(batch)
            print(f"Batch {batch_num} successfully stored.")
            success = True
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                attempts += 1
                if attempts < max_retries:
                    print(f"Rate limit hit! Retrying batch {batch_num} in 65 seconds (Attempt {attempts + 1}/{max_retries})...")
                    time.sleep(65)
                else:
                    print(f"Failed to store batch {batch_num} after {max_retries} attempts.")
                    raise
            else:
                raise
                
    if batch_num < total_batches:
        print("Waiting 65 seconds before the next batch to respect rate limits...")
        time.sleep(65)

print("\nVector database successfully initialized with chunks!")
