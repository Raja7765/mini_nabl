import json
from datetime import datetime

from config import TRAINING_FILE


# ==========================================
# CREATE TRAINING FILE
# ==========================================

def create_training_file():
    """Create training.json if it does not exist."""

    if TRAINING_FILE.exists():
        return

    initial_data = {
        "documents": []
    }

    with open(TRAINING_FILE, "w", encoding="utf-8") as file:
        json.dump(
            initial_data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ==========================================
# LOAD TRAINING DATA
# ==========================================

def load_training_data():
    """Load document registry from training.json."""

    create_training_file()

    with open(TRAINING_FILE, "r", encoding="utf-8") as file:
        content = file.read().strip()

    # Handle empty training.json safely
    if not content:
        return {
            "documents": []
        }

    return json.loads(content)


# ==========================================
# SAVE TRAINING DATA
# ==========================================

def save_training_data(data):
    """Save document registry to training.json."""

    with open(TRAINING_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ==========================================
# ADD / UPDATE DOCUMENT
# ==========================================

def add_training_document(
    original_filename,
    sanitized_filename,
    file_path,
    mimetype
):
    """
    Add a document to training.json.

    If the same sanitized filename already exists,
    replace the old entry instead of creating a duplicate.
    """

    data = load_training_data()

    new_document = {
        "original_filename": original_filename,
        "sanitized_filename": sanitized_filename,
        "file_path": str(file_path),
        "mimetype": mimetype or "application/pdf",
        "uploaded_at": datetime.now().isoformat()
    }

    documents = data.get("documents", [])

    # Remove existing document with same ID
    documents = [
        document
        for document in documents
        if document.get("sanitized_filename") != sanitized_filename
    ]

    # Add latest version
    documents.append(new_document)

    data["documents"] = documents

    save_training_data(data)

    print(
        f"Added/updated: {sanitized_filename}"
    )


# ==========================================
# GET DOCUMENT
# ==========================================

def get_training_document(sanitized_filename):
    """
    Get one document from training.json
    using its sanitized document ID.
    """

    data = load_training_data()

    for document in data.get("documents", []):

        if document.get("sanitized_filename") == sanitized_filename:
            return document

    return None


# ==========================================
# GET ALL DOCUMENTS
# ==========================================

def get_all_training_documents():
    """Return all documents from training.json."""

    data = load_training_data()

    return data.get("documents", [])


# ==========================================
# REMOVE DOCUMENT
# ==========================================

def remove_training_document(sanitized_filename):
    """
    Remove a document from training.json
    using its sanitized document ID.
    """

    data = load_training_data()

    documents = data.get("documents", [])

    updated_documents = [
        document
        for document in documents
        if document.get("sanitized_filename") != sanitized_filename
    ]

    removed = len(updated_documents) != len(documents)

    data["documents"] = updated_documents

    save_training_data(data)

    if removed:
        print(
            f"Removed: {sanitized_filename}"
        )
    else:
        print(
            f"Document not found: {sanitized_filename}"
        )

    return removed