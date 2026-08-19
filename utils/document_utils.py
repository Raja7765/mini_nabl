import os
import re

def extract_document_name(file_name):
    raw_document_name = os.path.splitext(
        os.path.basename(file_name)
    )[0]

    cleaned_name = raw_document_name.replace(" ", "")

    cleaned_name = re.sub(
        r"doc$",
        "",
        cleaned_name,
        flags=re.IGNORECASE
    )

    match = re.match(
        r"NABL[\s\-]?(\d+)",
        cleaned_name,
        re.IGNORECASE
    )

    if match:
        return f"NABL{match.group(1)}"

    return cleaned_name.split("_")[0]