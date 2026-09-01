import os
from pathlib import Path
from fastapi import APIRouter, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from config import DOCUMENT_FOLDER
from ingest import ingest_single_pdf
from services.training_service import add_training_document
from utils.document_utils import extract_document_name
from services.metadata_service import generate_metadata_for_pdf
from services.validation_service import (
    validate_filename,
    validate_pdf_extension,
    validate_pdf_content,
)

router = APIRouter()


@router.put("/documents/update")
async def update_document(file: UploadFile = File(...)):

    DOCUMENT_FOLDER.mkdir(parents=True, exist_ok=True)

    filename = file.filename or ""

    try:
        # 1. Validate filename
        validate_filename(filename)

        # 2. Validate PDF extension
        validate_pdf_extension(filename)

        # 3. Read file
        content = await file.read()

        # 4. Validate PDF content
        validate_pdf_content(content)

        # 5. Save updated PDF to DOCUMENT_FOLDER
        file_path = DOCUMENT_FOLDER / filename

        print(f"[UPDATE] Saving updated file to: {file_path}")

        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Update metadata
        metadata = await run_in_threadpool(generate_metadata_for_pdf, str(file_path))

        # 6. Extract document name
        sanitized_filename = extract_document_name(filename)

        # 7. Update metadata
        add_training_document(
            original_filename=filename,
            sanitized_filename=sanitized_filename,
            file_path=str(file_path),
            mimetype=file.content_type,
        )

        # 8. Re-ingest document
        # ingest_single_pdf() already deletes old chunks
        # for this document before adding new chunks.
        chunks_added = await run_in_threadpool(
            ingest_single_pdf,
            str(file_path),
        )

        return {
            "success": True,
            "message": f"Document updated successfully: {filename}",
            "filename": filename,
            "chunks_added": chunks_added,
        }

    except ValueError as e:
        return {
            "success": False,
            "message": str(e),
            "filename": filename,
            "chunks_added": 0,
        }

    except Exception as e:
        print(f"[UPDATE] Error updating {filename}: {e}")

        return {
            "success": False,
            "message": "Failed to update document",
            "filename": filename,
            "chunks_added": 0,
        }

    finally:
        await file.close()