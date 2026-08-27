from typing import List

from fastapi import APIRouter, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from ingest import ingest_single_pdf
from config import DOCUMENT_FOLDER
from ingest import ingest_multiple_pdfs
from services.training_service import add_training_document
from services.metadata_service import generate_metadata_for_pdf

from utils.document_utils import extract_document_name

from services.validation_service import (
    validate_filename,
    validate_pdf_extension,
    validate_pdf_content,
)


router = APIRouter()


@router.post("/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...)
):
    """
    Upload one or more PDF documents.

    Flow:
    1. Validate PDF
    2. Save PDF to DOCUMENT_FOLDER
    3. Update training.json
    4. Extract first-page metadata
    5. Update metadata.json
    6. Ingest document into ChromaDB
    """

    DOCUMENT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    uploaded_files = []
    failed_files = []

    for file in files:

        filename = file.filename or ""

        try:
            # ==========================================
            # 1. VALIDATE FILENAME
            # ==========================================

            validate_filename(filename)

            # ==========================================
            # 2. VALIDATE PDF EXTENSION
            # ==========================================

            validate_pdf_extension(filename)

            # ==========================================
            # 3. READ FILE INTO MEMORY
            # ==========================================

            content = await file.read()

            # ==========================================
            # 4. VALIDATE PDF CONTENT
            # ==========================================

            validate_pdf_content(content)

            # ==========================================
            # 5. SAVE PDF TO DOCUMENT FOLDER
            # ==========================================

            file_path = DOCUMENT_FOLDER / filename

            print(
                f"[UPLOAD] DOCUMENT_FOLDER: "
                f"{DOCUMENT_FOLDER}"
            )

            print(
                f"[UPLOAD] Saving PDF to: "
                f"{file_path}"
            )

            with open(file_path, "wb") as buffer:
                buffer.write(content)

            print(
                f"[UPLOAD] PDF saved successfully: "
                f"{filename}"
            )

            # ==========================================
            # 6. EXTRACT DOCUMENT ID
            # ==========================================

            sanitized_filename = extract_document_name(
                filename
            )

            print(
                f"[UPLOAD] Document ID: "
                f"{sanitized_filename}"
            )

            # ==========================================
            # 7. UPDATE TRAINING.JSON
            # ==========================================

            add_training_document(
                original_filename=filename,
                sanitized_filename=sanitized_filename,
                file_path=str(file_path),
                mimetype=file.content_type or "application/pdf",
            )

            print(
                "[UPLOAD] training.json updated"
            )

            # ==========================================
            # 8. EXTRACT FIRST-PAGE METADATA
            # ==========================================

            try:

                metadata = generate_metadata_for_pdf(
                    str(file_path)
                )

                print(
                    "[UPLOAD] metadata.json updated"
                )

                print(
                    f"[UPLOAD] Extracted metadata: "
                    f"{metadata}"
                )

            except Exception as metadata_error:

                # Metadata failure should not stop
                # the actual PDF upload.
                print(
                    "[UPLOAD] Metadata extraction failed: "
                    f"{metadata_error}"
                )

            # ==========================================
            # 9. INGEST INTO CHROMADB
            # ==========================================

            print(
                f"[UPLOAD] Starting ChromaDB ingestion: "
                f"{filename}"
            )

            await run_in_threadpool(
                ingest_single_pdf,
                str(file_path)
            )

            print(
                f"[UPLOAD] ChromaDB ingestion completed: "
                f"{filename}"
            )

            # ==========================================
            # 10. SUCCESS
            # ==========================================

            uploaded_files.append(filename)

        # ==============================================
        # VALIDATION ERROR
        # ==============================================

        except ValueError as val_err:

            print(
                f"[UPLOAD] Validation failed for "
                f"{filename}: {val_err}"
            )

            failed_files.append({
                "filename": filename,
                "error": str(val_err)
            })

        # ==============================================
        # UNEXPECTED ERROR
        # ==============================================

        except Exception as e:

            print(
                f"[UPLOAD] Error processing "
                f"{filename}: {e}"
            )

            failed_files.append({
                "filename": filename,
                "error": str(e)
            })

        # ==============================================
        # CLOSE UPLOAD FILE
        # ==============================================

        finally:

            try:
                await file.close()
            except Exception:
                pass

    # ==============================================
    # FINAL RESPONSE
    # ==============================================

    return {
        "message": "Upload process completed",
        "total_files": len(files),
        "successful_count": len(uploaded_files),
        "failed_count": len(failed_files),
        "successful_documents": uploaded_files,
        "failed_documents": failed_files,
    }