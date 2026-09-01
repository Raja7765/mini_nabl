import os
import io
from typing import Optional
from pypdf import PdfReader

def validate_filename(filename: Optional[str]) -> None:
    if not filename:
        raise ValueError("[VALIDATION] Filename is missing.")

def validate_pdf_extension(filename: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("[VALIDATION] Only PDF files are allowed.")

def validate_pdf_content(content: bytes) -> None:
    """
    Validates the PDF in-memory. 
    Checks for 0 bytes, corrupted files, and completely blank pages.
    """
    # 1. Check for literal 0-byte files
    if not content or len(content) == 0:
        raise ValueError("Uploaded PDF is empty (0 bytes).")
        
    try:
        # 2. Load the PDF into memory (no disk saving required yet)
        pdf_stream = io.BytesIO(content)
        reader = PdfReader(pdf_stream)
        
        # 3. Check if it actually has pages
        if len(reader.pages) == 0:
            raise ValueError("[VALIDATION] The PDF contains no pages.")
            
        # 4. Check if the pages actually contain text
        text_found = False
        for page in reader.pages:
            if page.extract_text().strip():
                text_found = True
                break
                
        if not text_found:
            raise ValueError("[VALIDATION] The PDF is completely blank and contains no text.")
            
    except ValueError:
        # Re-raise the ValueErrors we explicitly threw above
        raise
    except Exception:
        # If PyPDF crashes while reading, it's heavily corrupted
        raise ValueError("Invalid or corrupted PDF file.")