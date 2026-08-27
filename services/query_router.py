import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI


# ==========================================
# INITIALIZE ROUTER LLM
# ==========================================
# Using 2.5-flash as it is highly stable for fast JSON routing
router_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", 
    temperature=0
)


# ==========================================
# QUERY ROUTER
# ==========================================
def route_query(
    user_question: str,
    conversation_history: str = ""
) -> dict:

    print("\n--- QUERY ROUTER STARTED ---")

    prompt = f"""
You are a query router for an NABL document assistant.

Analyze the user's current question and previous conversation.

Classify the query into the following fields:

1. topic:
   A short description of the topic.

2. intent:
   Choose exactly one:
   - Accreditation Process
   - Standards & Compliance
   - Document Request
   - Application Status
   - General Inquiry
   - Other

3. target_document:
   If the user explicitly mentions a NABL document number,
   return that document code.

   Examples:
   NABL 163 -> NABL163
   NABL 100A -> NABL100A

   If no specific document can be identified,
   return null.

Return ONLY valid JSON.

Previous Conversation:
{conversation_history}

Current Question:
{user_question}

Expected JSON format:
{{
    "topic": "short topic",
    "intent": "one intent category",
    "target_document": "NABL163"
}}
"""

    try:
        response = router_llm.invoke(prompt)
        response_text = response.content

        # Some Gemini responses may return content as a list
        if isinstance(response_text, list) and response_text:
            if isinstance(response_text[0], dict) and "text" in response_text[0]:
                response_text = response_text[0]["text"]
            else:
                response_text = str(response_text[0])

        # Remove Markdown JSON code blocks if returned
        cleaned_response = (
            str(response_text)
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        
        router_result = json.loads(cleaned_response)

    except (json.JSONDecodeError, Exception) as e:
        print(f"Router JSON parsing failed: {e}. Using fallback result.")
        router_result = {
            "topic": "General Query",
            "intent": "General Inquiry",
            "target_document": None
        }

    # --------------------------------------------------------
    # SANITATION BLOCK: Bulletproof the Target Document
    # --------------------------------------------------------
    target_doc = router_result.get("target_document")

    # Catch string "null", "None", or empty strings
    if target_doc in ["null", "None", "", None]:
        router_result["target_document"] = None
        
    elif isinstance(target_doc, str):
        # Force standard NABL document ID format (e.g., "NABL- 134 " -> "NABL134", "NABL 100A" -> "NABL100A")
        match = re.search(r"NABL[\s\-]?(\d+[A-Z]?)", target_doc, re.IGNORECASE)
        if match:
            router_result["target_document"] = f"NABL{match.group(1).upper()}"
        else:
            clean_doc = target_doc.upper().replace(" ", "").replace("-", "")
            router_result["target_document"] = clean_doc

    print("Router Result:")
    print(router_result)
    print("--- QUERY ROUTER COMPLETED ---")

    return router_result