import json
from langchain_google_genai import ChatGoogleGenerativeAI


# ==========================================
# INITIALIZE ROUTER LLM
# ==========================================
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
    "target_document": "NABL163 or null"
}}
"""

    response = router_llm.invoke(prompt)

    response_text = response.content

    # Some Gemini responses may return content as a list
    if isinstance(response_text, list):
        response_text = response_text[0]["text"]

    # Remove Markdown JSON code blocks if returned
    cleaned_response = (
        response_text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        router_result = json.loads(cleaned_response)

    except json.JSONDecodeError:

        print(
            "Router JSON parsing failed. "
            "Using fallback result."
        )

        router_result = {
            "topic": "General Query",
            "intent": "General Inquiry",
            "target_document": None
        }

    print("Router Result:")
    print(router_result)

    print("--- QUERY ROUTER COMPLETED ---")

    return router_result