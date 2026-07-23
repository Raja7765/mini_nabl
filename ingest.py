import os
import glob
import time
import re
from dotenv import load_dotenv

from services.vector_store import VectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==========================================
# INITIAL SETUP & ENVIRONMENT CONFIGURATION
# ==========================================
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print("API key loaded successfully:", api_key is not None)

print("Initializing Vector Store...")
vector_store = VectorStore()


def ingest_single_pdf(pdf_file):
    """
    Ingest a single PDF into ChromaDB
    """

    print(f"\nLoading: {pdf_file}")

    loader = PyPDFLoader(pdf_file)
    pages = loader.load()

    # Extract document name
    raw_document_name = os.path.splitext(
        os.path.basename(pdf_file)
    )[0]

    cleaned_name = raw_document_name.replace(" ", "")

    match = re.match(r"^(NABL\d+[A-Z]?)", cleaned_name, re.IGNORECASE)

    if match:
        document_name = match.group(1).upper()
    else:
        document_name = cleaned_name.split("_")[0]

    # Add metadata
    for page in pages:
        page.metadata["document"] = document_name

    print(f"Loaded {len(pages)} pages")
    print("Metadata:", pages[0].metadata)

    # Split
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_documents(pages)

    print(f"Created {len(chunks)} chunks")

    # Store in batches
    batch_size = 50
    total_chunks = len(chunks)
    total_batches = (total_chunks + batch_size - 1) // batch_size

    for i in range(total_batches):

        batch_num = i + 1
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, total_chunks)

        batch = chunks[start_idx:end_idx]

        attempts = 0
        max_retries = 3
        success = False

        while attempts < max_retries and not success:

            try:
                vector_store.add_documents(batch)
                success = True
                print(f"Batch {batch_num}/{total_batches} stored.")

            except Exception as e:

                error_msg = str(e)

                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:

                    attempts += 1

                    if attempts < max_retries:

                        print(
                            f"Rate limit hit. Retrying in 65 seconds..."
                        )

                        time.sleep(65)

                    else:
                        raise

                else:
                    raise

        if batch_num < total_batches:
            time.sleep(65)

    print(f"{os.path.basename(pdf_file)} ingestion completed.")

    return len(chunks)


if __name__ == "__main__":

    print("Step 1: Loading all PDFs...")

    pdf_files = glob.glob("./data/*.pdf")

    total_chunks = 0

    for pdf_file in pdf_files:
        total_chunks += ingest_single_pdf(pdf_file)

    print("\n===================================")
    print(f"Total PDFs : {len(pdf_files)}")
    print(f"Total Chunks : {total_chunks}")
    print("Vector database successfully initialized!")