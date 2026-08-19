import json
import re
from pathlib import Path
from datetime import datetime

from pypdf import PdfReader

from config import TRAINING_FILE, METADATA_FILE


# ==========================================
# TRAINING.JSON
# ==========================================

def load_training_data():
    """
    Load training.json.

    training.json is the document registry.
    This service only reads it when needed.
    """

    if not TRAINING_FILE.exists():
        return {
            "documents": []
        }

    with open(
        TRAINING_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read().strip()

    if not content:
        return {
            "documents": []
        }

    return json.loads(content)


# ==========================================
# METADATA.JSON
# ==========================================

def create_metadata_file():
    """
    Create metadata.json if it does not exist.
    """

    if METADATA_FILE.exists():
        return

    initial_data = {
        "documents": []
    }

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            initial_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"[METADATA] Created: {METADATA_FILE}"
    )


def load_metadata():
    """
    Load metadata.json.
    """

    create_metadata_file()

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read().strip()

    if not content:
        return {
            "documents": []
        }

    return json.loads(content)


def save_metadata(data):
    """
    Save data to metadata.json.
    """

    print(
        f"[METADATA] Writing to: {METADATA_FILE}"
    )

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"[METADATA] metadata.json saved successfully"
    )


# ==========================================
# FIRST PAGE EXTRACTION
# ==========================================

def extract_first_page_text(pdf_path: str) -> str:
    """
    Extract text only from the first page.
    """

    print(
        f"[METADATA] Reading first page: {pdf_path}"
    )

    reader = PdfReader(pdf_path)

    if not reader.pages:
        return ""

    text = reader.pages[0].extract_text() or ""

    print(
        f"[METADATA] First page extracted "
        f"({len(text)} characters)"
    )

    return text


# ==========================================
# FIELD EXTRACTION
# ==========================================

def extract_field(text: str, pattern: str):
    """
    Extract a field using regex.
    """

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1).strip()

    # Treat empty / placeholder values as None
    if value.upper() in {
        "--",
        "-",
        "N/A",
        "NA",
        ""
    }:
        return None

    return value


# ==========================================
# DOCUMENT ID
# ==========================================

def extract_document_id(text: str):
    """
    Extract NABL document ID.

    Examples:
        NABL 133
        NABL-133
        NABL133
        NABL133A
    """

    match = re.search(
        r"\bNABL\s*[-.]?\s*(\d+[A-Z]?)\b",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    return f"NABL{match.group(1).upper()}"


# ==========================================
# TITLE
# ==========================================

def extract_title(lines):
    """
    Extract document title from first page.
    """

    for index, line in enumerate(lines):

        upper_line = line.upper()

        if "NATIONAL ACCREDITATION BOARD" in upper_line:

            # Look at following lines for title
            for candidate in lines[index + 1:index + 8]:

                upper_candidate = candidate.upper()

                # Ignore metadata fields
                if (
                    "ISSUE NO" in upper_candidate
                    or "ISSUE DATE" in upper_candidate
                    or "AMENDMENT NO" in upper_candidate
                    or "AMENDMENT DATE" in upper_candidate
                ):
                    continue

                # Ignore organisation name
                if "QUALITY COUNCIL OF INDIA" in upper_candidate:
                    continue

                if not candidate.strip():
                    continue

                return candidate.strip()

    return None


# ==========================================
# EXTRACT PDF METADATA
# ==========================================

def extract_pdf_metadata(pdf_path: str):
    """
    Extract metadata from the first page
    of a single PDF.
    """

    text = extract_first_page_text(pdf_path)

    if not text.strip():

        raise ValueError(
            f"No text found on first page: {pdf_path}"
        )

    # Normalize text
    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # --------------------------------------
    # DOCUMENT ID
    # --------------------------------------

    document_id = extract_document_id(text)

    if not document_id:

        raise ValueError(
            f"NABL document ID not found "
            f"in first page: {pdf_path}"
        )

    # --------------------------------------
    # ISSUE NUMBER
    # --------------------------------------

    issue_no = extract_field(
        text,
        r"ISSUE\s*NO\.?\s*:\s*([^\n]+)"
    )

    # --------------------------------------
    # ISSUE DATE
    # --------------------------------------

    issue_date = extract_field(
        text,
        r"ISSUE\s*DATE\s*:\s*([^\n]+)"
    )

    # --------------------------------------
    # AMENDMENT NUMBER
    # --------------------------------------

    amendment_no = extract_field(
        text,
        r"AMENDMENT\s*NO\.?\s*:\s*([^\n]+)"
    )

    # --------------------------------------
    # AMENDMENT DATE
    # --------------------------------------

    amendment_date = extract_field(
        text,
        r"AMENDMENT\s*DATE\s*:\s*([^\n]+)"
    )

    # --------------------------------------
    # TITLE
    # --------------------------------------

    title = extract_title(lines)

    # --------------------------------------
    # FINAL METADATA
    # --------------------------------------

    metadata = {
        "document_id": document_id,
        "title": title,
        "issue_no": issue_no,
        "issue_date": issue_date,
        "amendment_no": amendment_no,
        "amendment_date": amendment_date,
        "source_file": Path(pdf_path).name,
        "extracted_from": "first_page",
        "updated_at": datetime.now().isoformat()
    }

    return metadata


# ==========================================
# GENERATE / UPDATE METADATA FOR ONE PDF
# ==========================================

def generate_metadata_for_pdf(pdf_path: str):
    """
    Extract first-page metadata from one PDF
    and add/update it in metadata.json.
    """

    print(
        f"[METADATA] Processing: {pdf_path}"
    )

    # --------------------------------------
    # 1. Extract metadata from PDF
    # --------------------------------------

    metadata = extract_pdf_metadata(
        pdf_path
    )

    print(
        f"[METADATA] Extracted data: {metadata}"
    )

    document_id = metadata.get(
        "document_id"
    )

    if not document_id:

        raise ValueError(
            f"Document ID not found: {pdf_path}"
        )

    # --------------------------------------
    # 2. Load existing metadata.json
    # --------------------------------------

    data = load_metadata()

    documents = data.get(
        "documents",
        []
    )

    # --------------------------------------
    # 3. Remove old version
    # --------------------------------------

    documents = [
        document
        for document in documents
        if document.get("document_id") != document_id
    ]

    # --------------------------------------
    # 4. Add latest metadata
    # --------------------------------------

    documents.append(
        metadata
    )

    data["documents"] = documents

    # --------------------------------------
    # 5. Save metadata.json
    # --------------------------------------

    save_metadata(
        data
    )

    print(
        f"[METADATA] Successfully updated: "
        f"{document_id}"
    )

    return metadata


# ==========================================
# GET DOCUMENT METADATA
# ==========================================

def get_document_metadata(document_id: str):
    """
    Get metadata using document ID.
    """

    data = load_metadata()

    for document in data.get(
        "documents",
        []
    ):

        if document.get(
            "document_id"
        ) == document_id:

            return document

    return None


# ==========================================
# REMOVE DOCUMENT METADATA
# ==========================================

def remove_document_metadata(document_id: str):
    """
    Remove document metadata from metadata.json.
    """

    data = load_metadata()

    documents = data.get(
        "documents",
        []
    )

    updated_documents = [
        document
        for document in documents
        if document.get(
            "document_id"
        ) != document_id
    ]

    removed = (
        len(updated_documents)
        != len(documents)
    )

    data["documents"] = updated_documents

    save_metadata(
        data
    )

    if removed:

        print(
            f"[METADATA] Removed: "
            f"{document_id}"
        )

    else:

        print(
            f"[METADATA] Document not found: "
            f"{document_id}"
        )

    return removed