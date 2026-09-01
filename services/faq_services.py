import json

from config import FAQ_FILE


# ==========================================
# CREATE FAQ FILE
# ==========================================

def create_faq_file():
    """Create faqs.json if it does not exist."""

    if FAQ_FILE.exists():
        return

    FAQ_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        FAQ_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "faqs": []
            },
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"[FAQ] Created: {FAQ_FILE}")


# ==========================================
# LOAD FAQ DATA
# ==========================================

def load_faq_data():
    """Load FAQ data from faqs.json."""

    create_faq_file()

    with open(
        FAQ_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read().strip()

    if not content:
        return {
            "faqs": []
        }

    return json.loads(content)


# ==========================================
# SAVE FAQ DATA
# ==========================================

def save_faq_data(data):
    """Save FAQ data to faqs.json."""

    with open(
        FAQ_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("[FAQ] faqs.json saved successfully")


# ==========================================
# ADD FAQ
# ==========================================

def add_faq(
    question,
    answer,
    document,
    page=None,
    intent_name=None
):
    """
    Add a FAQ entry.

    If the same question already exists
    for the same document, update it.
    """

    data = load_faq_data()

    faqs = data.get("faqs", [])

    new_faq = {
        "question": question,
        "answer": answer,
        "document": document,
        "page": page,
        "intent_name": intent_name
    }

    # Remove existing same question + document
    faqs = [
        faq
        for faq in faqs
        if not (
            faq.get("question", "").strip().lower()
            == question.strip().lower()
            and faq.get("document") == document
        )
    ]

    # Add latest FAQ
    faqs.append(new_faq)

    data["faqs"] = faqs

    save_faq_data(data)

    print(
        f"[FAQ] Added/updated: "
        f"{document} -> {question}"
    )


# ==========================================
# GET ALL FAQS
# ==========================================

def get_all_faqs():
    """Return all FAQ entries."""

    data = load_faq_data()

    return data.get(
        "faqs",
        []
    )


# ==========================================
# GET FAQS FOR DOCUMENT
# ==========================================

def get_faqs_by_document(document):
    """Return FAQs belonging to one document."""

    faqs = get_all_faqs()

    return [
        faq
        for faq in faqs
        if faq.get("document") == document
    ]
# ==========================================
# FIND FAQ
# ==========================================

def find_faq(question: str):
    """
    Find an FAQ using exact question matching.

    Returns:
        FAQ dictionary if found
        None if not found
    """

    faqs = get_all_faqs()

    normalized_question = (
        question
        .strip()
        .lower()
    )

    for faq in faqs:

        faq_question = (
            faq.get("question", "")
            .strip()
            .lower()
        )

        if faq_question == normalized_question:
            print(
                f"[FAQ] Match found: "
                f"{faq.get('intent_name')}"
            )

            return faq

    print(
        f"[FAQ] No match found for: {question}"
    )

    return None    