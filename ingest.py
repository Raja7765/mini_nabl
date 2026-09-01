import os
import time
import re

from utils.document_utils import extract_document_name
from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    BATCH_SIZE,
    MAX_RETRIES,
    RETRY_WAIT_SECONDS,
)
from services.vector_store import VectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

print("Initializing Vector Store for ingestion...")
vector_store = VectorStore()


# ============================================================
# SINGLE PDF INGESTION
# ============================================================

def ingest_single_pdf(pdf_file):
    """
    Ingest a single PDF into ChromaDB.
    """
    print(f"\n" + "=" * 60)
    print(f"STARTING SINGLE PDF INGESTION: {pdf_file}")
    print("=" * 60)

    loader = PyPDFLoader(pdf_file)
    pages = loader.load()
    num_pages = len(pages)

    raw_document_name = extract_document_name(pdf_file)
    normalized_doc_id = str(raw_document_name).strip().upper().replace(" ", "")

    print(f"[INGEST] Document ID: {normalized_doc_id}")
    print(f"[INGEST] Number of pages: {num_pages}")

    # 1. Delete existing records before re-ingestion
    deleted_count = 0
    try:
        deleted_count = vector_store.delete_by_document(normalized_doc_id)
        print(f"[INGEST] Number of records deleted before re-ingestion: {deleted_count}")
    except Exception as e:
        print(f"[INGEST] Could not delete old data: {e}")

    # 2. Add document metadata to pages
    for page in pages:
        page.metadata["document"] = normalized_doc_id

    if pages:
        print(f"[INGEST] Sample Page 0 Metadata: {pages[0].metadata}")

    # 3. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(pages)
    num_chunks = len(chunks)

    # 4. Generate deterministic chunk IDs & check uniqueness
    chunk_ids = []
    seen_contents = set()
    duplicate_chunk_count = 0

    for idx, chunk in enumerate(chunks):
        chunk.metadata["document"] = normalized_doc_id
        page_num = chunk.metadata.get("page", 0)
        c_id = f"{normalized_doc_id}_p{page_num}_c{idx}"
        chunk_ids.append(c_id)

        content_key = (page_num, chunk.page_content.strip())
        if content_key in seen_contents:
            duplicate_chunk_count += 1
        else:
            seen_contents.add(content_key)

    unique_chunk_count = len(seen_contents)

    print(f"[INGEST] Number of chunks before insertion: {num_chunks}")
    print(f"[INGEST] Unique chunk count: {unique_chunk_count}")
    print(f"[INGEST] Duplicate chunk count: {duplicate_chunk_count}")

    if num_chunks > 0:
        sample_page = chunks[0].metadata.get("page", 0)
        print(f"[INGEST] Sample Chunk 0 -> Document ID: {normalized_doc_id}, Page: {sample_page}, Chunk ID: {chunk_ids[0]}")

    # 5. Store chunks in batches
    total_chunks = len(chunks)
    total_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE
    records_inserted = 0

    for i in range(total_batches):
        batch_num = i + 1
        start_idx = i * BATCH_SIZE
        end_idx = min((i + 1) * BATCH_SIZE, total_chunks)

        batch_chunks = chunks[start_idx:end_idx]
        batch_ids = chunk_ids[start_idx:end_idx]
        attempts = 0
        success = False

        while attempts < MAX_RETRIES and not success:
            try:
                vector_store.add_documents(batch_chunks, ids=batch_ids)
                success = True
                records_inserted += len(batch_chunks)
                print(f"[DEBUG] Batch {batch_num}/{total_batches} stored ({len(batch_chunks)} records).")
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    attempts += 1
                    if attempts < MAX_RETRIES:
                        print(f"Rate limit hit. Retrying in {RETRY_WAIT_SECONDS} seconds... (Attempt {attempts}/{MAX_RETRIES})")
                        time.sleep(RETRY_WAIT_SECONDS)
                    else:
                        print(f"Max retries reached for batch {batch_num}. Failing batch.")
                        raise
                else:
                    raise

        if batch_num < total_batches:
            time.sleep(RETRY_WAIT_SECONDS)

    print(f"[INGEST] Number of records inserted: {records_inserted}")
    print(f"Ingestion completed for {os.path.basename(pdf_file)}.")
    print("=" * 60 + "\n")
    return records_inserted


# ============================================================
# BULK PDF INGESTION
# ============================================================

def ingest_multiple_pdfs(pdf_files):
    """
    Ingest multiple PDF files into ChromaDB.
    If one PDF fails, the remaining PDFs will continue processing.
    """
    total_files = len(pdf_files)
    successful_files = []
    failed_files = []

    print("\n" + "=" * 70)
    print("STARTING BULK INGESTION")
    print("=" * 70)
    print(f"Total PDF files: {total_files}")

    # --------------------------------------------------------
    # Process each PDF
    # --------------------------------------------------------
    for index, pdf_file in enumerate(pdf_files, start=1):
        filename = os.path.basename(pdf_file)
        
        print("\n" + "-" * 70)
        print(f"[INGEST] Processing PDF {index}/{total_files}: {filename}")
        print("-" * 70)

        try:
            chunks_count = ingest_single_pdf(pdf_file)
            successful_files.append({
                "file": filename,
                "chunks": chunks_count
            })
            print(f"SUCCESS: {filename}")
        except Exception as e:
            print(f"FAILED: {filename}")
            print(f"Error: {e}")
            failed_files.append({
                "file": filename,
                "error": str(e)
            })
            continue

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("[INGEST] BULK INGESTION COMPLETED")
    print("=" * 70)
    print(f"[INGEST] Total files : {total_files}")
    print(f"[INGEST] Successful  : {len(successful_files)}")
    print(f"[INGEST] Failed      : {len(failed_files)}")
    print("=" * 70)

    return {
        "total_files": total_files,
        "successful_count": len(successful_files),
        "failed_count": len(failed_files),
        "successful_files": successful_files,
        "failed_files": failed_files
    }