import os
from typing import List
from fastapi import APIRouter, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from ingest import ingest_single_pdf

# 1. We changed this import to match your new validation service!
from services.validation_service import (
    validate_filename,
    validate_pdf_extension,
    validate_pdf_content, 
)

router = APIRouter()

@router.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):

    os.makedirs("data", exist_ok=True)

    uploaded_files = []
    failed_files = []

    for file in files:
        filename = file.filename or ""

        try:
            # Validate filename
            validate_filename(filename)

            # Validate PDF extension
            validate_pdf_extension(filename)

            # READ & VALIDATE IN MEMORY
            content = await file.read()
            
            # 2. We use the new single function here!
            validate_pdf_content(content) 

            # SAVE TO DISK (Only happens if the validation above passes)
            file_path = os.path.join("data", filename)
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # INGEST
            await run_in_threadpool(ingest_single_pdf, file_path)

            uploaded_files.append(filename)

        except ValueError as val_err:
            failed_files.append({
                "filename": filename,
                "error": str(val_err)
            })

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            failed_files.append({
                "filename": filename,
                "error": str(e)
            })

    return {
        "message": "Upload process completed",
        "total_files": len(files),
        "successful_count": len(uploaded_files),
        "failed_count": len(failed_files),
        "successful_documents": uploaded_files,
        "failed_documents": failed_files
    }