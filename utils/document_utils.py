import os
import re

def extract_document_name(file_name):
    raw_document_name = os.path.splitext(
        os.path.basename(file_name)
    )[0]

    cleaned_name = raw_document_name.replace(" ", "")

    cleaned_name = re.sub(
        r"docs?$",
        "",
        cleaned_name,
        flags=re.IGNORECASE
    )

    # CORRECTED REGEX: Removed [A-Z]? so it only captures digits
    match = re.search(
        r"NABL[\s\-]?(\d+)",
        cleaned_name,
        re.IGNORECASE
    )

    if match:
        # No need for .upper() here since it's only digits now
        return f"NABL{match.group(1)}"

    return cleaned_name.split("_")[0].upper()