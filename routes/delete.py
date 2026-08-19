import os

from fastapi import APIRouter, HTTPException

from services.training_service import (
    get_training_document,
    remove_training_document
)

from services.metadata_service import (
    remove_document_metadata
)

from services.vector_store import VectorStore


router = APIRouter()

vector_store = VectorStore()


@router.delete("/documents/{document_name}")
def delete_document(document_name: str):

    # ==========================================
    # STEP 1: GET DOCUMENT FROM TRAINING.JSON
    # ==========================================

    document = get_training_document(document_name)

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_name}' not found in training.json."
        )

    try:

        sanitized_filename = document.get(
            "sanitized_filename",
            document_name
        )

        # ==========================================
        # STEP 2: DELETE PHYSICAL PDF
        # ==========================================

        file_path = document.get("file_path")

        if file_path and os.path.exists(file_path):

            os.remove(file_path)

            print(
                f"[DELETE] PDF deleted: {file_path}"
            )

        else:

            print(
                f"[DELETE] PDF not found: {file_path}"
            )

        # ==========================================
        # STEP 3: DELETE CHROMADB VECTORS
        # ==========================================

        deleted_chunks = vector_store.delete_by_document(
            sanitized_filename
        )

        print(
            f"[DELETE] ChromaDB chunks deleted: "
            f"{deleted_chunks}"
        )

        # ==========================================
        # STEP 4: REMOVE FROM TRAINING.JSON
        # ==========================================

        training_removed = remove_training_document(
            sanitized_filename
        )

        # ==========================================
        # STEP 5: REMOVE FROM METADATA.JSON
        # ==========================================

        metadata_removed = remove_document_metadata(
            sanitized_filename
        )

        # ==========================================
        # RESPONSE
        # ==========================================

        return {
            "message": (
                f"Document '{document_name}' "
                f"deleted successfully."
            ),
            "deleted_document": sanitized_filename,
            "deleted_file_path": file_path,
            "chunks_deleted": deleted_chunks,
            "training_removed": training_removed,
            "metadata_removed": metadata_removed
        }

    except Exception as e:

        print(
            f"[DELETE] Error deleting "
            f"'{document_name}': {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )