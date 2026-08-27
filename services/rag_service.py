import json
from langchain_google_genai import ChatGoogleGenerativeAI

from services.vector_store import VectorStore
from services.redis_session import (
    get_session_history,
    add_to_history
)
from services.query_router import route_query


# ==========================================
# LOAD EXISTING CHROMADB
# ==========================================

print("Loading Existing VectorStore")
vector_store = VectorStore()


# ==========================================
# INITIALIZE GEMINI LLM
# ==========================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.3,
    streaming=True
)


# ==========================================
# QUERY REWRITING FUNCTION
# ==========================================

def rewrite_question(
    user_question: str,
    conversation_history: str
) -> str:
    if not conversation_history.strip():
        print("No previous conversation. Using original question for retrieval.")
        return user_question

    print("\nRewriting follow-up question using conversation history...")

    rewrite_prompt = f"""
You are a query rewriting assistant for an NABL document chatbot.

Use the previous conversation only to understand references
in the current question such as:
- it
- its
- this
- that
- they
- them
- the document
- the policy

Rewrite the current question as a clear standalone question.
Do not answer the question.
Do not add information that is not present in the conversation.
Return ONLY the rewritten question.

Previous Conversation:
{conversation_history}

Current Question:
{user_question}
"""

    try:
        response = llm.invoke(rewrite_prompt)
        rewritten_question = response.content

        if isinstance(rewritten_question, list) and rewritten_question:
            if isinstance(rewritten_question[0], dict) and "text" in rewritten_question[0]:
                rewritten_question = rewritten_question[0]["text"]
            else:
                rewritten_question = str(rewritten_question[0])

        rewritten_question = str(rewritten_question).strip()
        print(f"Original Question: {user_question}")
        print(f"Rewritten Question: {rewritten_question}")
        return rewritten_question or user_question

    except Exception as e:
        print(f"[REWRITE_ERROR] Failed to rewrite question: {e}")
        return user_question


# ==========================================
# STREAMING RAG FUNCTION
# ==========================================

def stream_answer(
    user_question: str,
    session_id: str
):
    print("\n" + "=" * 60)
    print("NEW STREAM CHAT REQUEST")
    print("=" * 60)
    print(f"Session ID -> '{session_id}'")
    print(f"User Query Captured -> '{user_question}'")

    # ==========================================
    # STEP 1: GET PREVIOUS HISTORY FROM REDIS
    # ==========================================
    print("\nStep 1: Loading previous conversation from Redis...")
    history = get_session_history(session_id) or []
    print(f"Previous conversation turns found: {len(history)}")

    # ==========================================
    # STEP 2: FORMAT CONVERSATION HISTORY
    # ==========================================
    conversation_history = ""
    for turn in history:
        user_msg = turn.get("user", "")
        assistant_msg = turn.get("assistant", "")
        conversation_history += f"\nUser: {user_msg}\nAssistant: {assistant_msg}\n"

    # ==========================================
    # STEP 3: REWRITE FOLLOW-UP QUESTION
    # ==========================================
    print("\nStep 2: Preparing standalone search question...")
    search_question = rewrite_question(user_question, conversation_history)

    # ==========================================
    # STEP 4: QUERY ROUTER
    # ==========================================
    print("\nStep 3: Sending question to Query Router...")
    router_result = route_query(search_question, conversation_history) or {}

    topic = router_result.get("topic", "General Query")
    intent = router_result.get("intent", "General Inquiry")
    target_document = router_result.get("target_document")

    print("\n--- ROUTER DECISION ---")
    print(f"Topic: {topic}")
    print(f"Intent: {intent}")
    print(f"Target Document: {target_document}")

    # ==========================================
    # STEP 5: CHROMADB SIMILARITY SEARCH
    # ==========================================
    print("\nStep 4: Executing mathematical vector similarity search...")
    print(f"Search Question: {search_question}")

    # Maintain document isolation: filter by target_document if specified
    search_filter = {"document": target_document} if target_document else None

    try:
        results = vector_store.search(
            query=search_question,
            k=3,
            filter=search_filter
        )
    except Exception as e:
        print(f"[VECTOR SEARCH] Search error: {e}")
        results = []

    # Ensure results is never None
    results = results or []
    print(f"[VECTOR SEARCH] Total Chunks Retrieved: {len(results)}")

    # ==========================================
    # STEP 6: COMBINE RETRIEVED CHUNKS & HANDLE EMPTY
    # ==========================================
    print("\n--- CHROMADB RETRIEVED CHUNKS FOUND ---")

    if not results:
        fallback_msg = "The information is not available in the provided NABL document."
        print(f"[RAG] No chunks retrieved for filter={search_filter}. Returning fallback message.")
        yield f"data: {fallback_msg}\n\n"
        yield "data: [DONE]\n\n"

        # Save turn to history
        try:
            add_to_history(
                session_id=session_id,
                user_message=user_question,
                assistant_message=fallback_msg
            )
        except Exception as e:
            print(f"[REDIS_ERROR] Failed to save conversation history: {e}")
        return

    combined_context = ""
    for i, chunk in enumerate(results, 1):
        metadata = getattr(chunk, "metadata", {})
        content = getattr(chunk, "page_content", str(chunk))

        print(f"\n--- Chunk {i} ---")
        print(f"Source Metadata: {metadata}")
        print(f"Content Context:\n{content}")
        print("-" * 50)

        combined_context += f"\n--- Chunk {i} ---\n{content}\n"

    # ==========================================
    # STEP 7: CONSTRUCT FINAL RAG PROMPT
    # ==========================================
    print("\nStep 5: Constructing final RAG prompt...")

    prompt = f"""
You are an expert NABL assistant.

Use the previous conversation history only to understand the context of the user's current question.

Answer the user's question using ONLY the provided NABL document context.
Do not use outside knowledge.

If the answer cannot be found in the retrieved document context, say:
"The information is not available in the provided document."

Router Information:
Topic: {topic}
Intent: {intent}
Target Document: {target_document}

Previous Conversation:
{conversation_history}

Retrieved NABL Document Context:
{combined_context}

Current User Question:
{user_question}
"""

    # ==========================================
    # STEP 8: STREAM FINAL ANSWER
    # ==========================================
    print("\nStep 6: Streaming AI answer...")
    complete_answer = ""

    try:
        for chunk in llm.stream(prompt):
            if not chunk or not chunk.content:
                continue

            text = chunk.content

            # Handle list response types safely
            if isinstance(text, list) and text:
                if isinstance(text[0], dict) and "text" in text[0]:
                    text = text[0]["text"]
                else:
                    text = str(text[0])

            text = str(text)
            complete_answer += text

            # SSE response chunk
            yield f"data: {text}\n\n"

    except Exception as e:
        error_msg = f"An error occurred while generating the response: {str(e)}"
        print(f"[STREAM_ERROR] {error_msg}")
        yield f"data: {error_msg}\n\n"
        complete_answer += error_msg

    # ==========================================
    # STEP 9: SAVE CONVERSATION TO REDIS
    # ==========================================
    print("\nStep 7: Saving conversation to Redis...")
    try:
        add_to_history(
            session_id=session_id,
            user_message=user_question,
            assistant_message=complete_answer
        )
        print(f"Conversation successfully saved for session: {session_id}")
    except Exception as e:
        print(f"[REDIS_ERROR] Failed to save conversation history: {e}")

    print("\nRAG request completed successfully.")
    print("=" * 60)

    # ==========================================
    # STEP 10: SEND DONE MARKER
    # ==========================================
    yield "data: [DONE]\n\n"