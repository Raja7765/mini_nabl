import os
from dotenv import load_dotenv

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)
from langchain_chroma import Chroma

from services.redis_session import (
    get_session_history,
    add_to_history
)

from services.query_router import route_query


# ==========================================
# INITIAL SETUP & ENVIRONMENT CONFIGURATION
# ==========================================
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

print(
    "API key loaded successfully:",
    api_key is not None
)


# ==========================================
# INITIALIZE EMBEDDING MODEL
# ==========================================
print("Initializing embedding model...")

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)

# Quick test to verify embedding model
test_vector = embeddings.embed_query("Hello")

print(
    "Embedding engine verified! "
    f"Vector dimension length: {len(test_vector)}"
)

print("-" * 50)


# ==========================================
# LOAD EXISTING CHROMADB
# ==========================================
print("Loading existing ChromaDB...")

vector_store = Chroma(
    persist_directory="./chroma_data",
    embedding_function=embeddings,
    collection_name="nabl_documents"
)


# ==========================================
# INITIALIZE GEMINI LLM
# ==========================================
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.3
)


# ==========================================
# QUERY REWRITING FUNCTION
# ==========================================
def rewrite_question(
    user_question: str,
    conversation_history: str
) -> str:

    # If there is no previous conversation,
    # rewriting is not required
    if not conversation_history.strip():
        print(
            "No previous conversation. "
            "Using original question for retrieval."
        )

        return user_question

    print(
        "\nRewriting follow-up question "
        "using conversation history..."
    )

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

    response = llm.invoke(rewrite_prompt)

    rewritten_question = response.content

    # Handle multimodal/list response if returned
    if isinstance(rewritten_question, list):
        rewritten_question = rewritten_question[0]["text"]

    rewritten_question = rewritten_question.strip()

    print(
        f"Original Question: "
        f"{user_question}"
    )

    print(
        f"Rewritten Question: "
        f"{rewritten_question}"
    )

    return rewritten_question


# ==========================================
# MAIN RAG QUESTION ANSWERING FUNCTION
# ==========================================
def ask_question(
    user_question: str,
    session_id: str
) -> str:

    print("\n" + "=" * 60)
    print("NEW CHAT REQUEST")
    print("=" * 60)

    print(
        f"Session ID -> "
        f"'{session_id}'"
    )

    print(
        f"User Query Captured -> "
        f"'{user_question}'"
    )


    # ==========================================
    # STEP 1: GET PREVIOUS HISTORY FROM REDIS
    # ==========================================
    print(
        "\nStep 1: Loading previous "
        "conversation from Redis..."
    )

    history = get_session_history(
        session_id
    )

    print(
        "Previous conversation turns found: "
        f"{len(history)}"
    )


    # ==========================================
    # STEP 2: FORMAT CONVERSATION HISTORY
    # ==========================================
    conversation_history = ""

    for turn in history:

        conversation_history += (
            f"\nUser: {turn['user']}\n"
            f"Assistant: {turn['assistant']}\n"
        )


    # ==========================================
    # STEP 3: REWRITE FOLLOW-UP QUESTION
    # ==========================================
    print(
        "\nStep 2: Preparing standalone "
        "search question..."
    )

    search_question = rewrite_question(
        user_question,
        conversation_history
    )


    # ==========================================
    # STEP 4: QUERY ROUTER
    # ==========================================
    print(
        "\nStep 3: Sending question "
        "to Query Router..."
    )

    router_result = route_query(
        search_question,
        conversation_history
    )

    topic = router_result.get(
        "topic",
        "General Query"
    )

    intent = router_result.get(
        "intent",
        "General Inquiry"
    )

    target_document = router_result.get(
        "target_document"
    )

    print("\n--- ROUTER DECISION ---")

    print(
        f"Topic: "
        f"{topic}"
    )

    print(
        f"Intent: "
        f"{intent}"
    )

    print(
        f"Target Document: "
        f"{target_document}"
    )


    # ==========================================
    # STEP 5: CHROMADB SIMILARITY SEARCH
    # ==========================================
    print(
        "\nStep 4: Executing mathematical "
        "vector similarity search..."
    )

    print(
        f"Search Question: "
        f"{search_question}"
    )

    # For now the router identifies the target
    # document, but retrieval still searches
    # across the full ChromaDB collection.
    #
    # Document filtering will be added
    # in the next step.
    results = vector_store.similarity_search(
        search_question,
        k=3
    )


    # ==========================================
    # STEP 6: COMBINE RETRIEVED CHUNKS
    # ==========================================
    print(
        "\n--- CHROMADB RETRIEVED "
        "CHUNKS FOUND ---"
    )

    combined_context = ""

    for i, chunk in enumerate(
        results,
        1
    ):

        print(
            f"\n--- Chunk {i} ---"
        )

        print(
            f"Source Metadata: "
            f"{chunk.metadata}"
        )

        print(
            f"Content Context:\n"
            f"{chunk.page_content}"
        )

        print("-" * 50)

        combined_context += (
            f"\n--- Chunk {i} ---\n"
            f"{chunk.page_content}\n"
        )


    # ==========================================
    # STEP 7: CONSTRUCT FINAL RAG PROMPT
    # ==========================================
    print(
        "\nStep 5: Constructing final "
        "RAG prompt..."
    )

    prompt = f"""
You are an expert NABL assistant.

Use the previous conversation history only to understand
the context of the user's current question.

Answer the user's question using ONLY the provided
NABL document context.

Do not use outside knowledge.

If the answer cannot be found in the retrieved document
context, say that the information is not available in
the provided document.

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
    # STEP 8: GENERATE FINAL ANSWER
    # ==========================================
    print(
        "\nStep 6: Generating final "
        "AI answer..."
    )

    final_response = llm.invoke(
        prompt
    )

    answer = final_response.content

    # Handle list response if returned
    if isinstance(answer, list):
        answer = answer[0]["text"]


    # ==========================================
    # STEP 9: SAVE CONVERSATION TO REDIS
    # ==========================================
    print(
        "\nStep 7: Saving conversation "
        "to Redis..."
    )

    add_to_history(
        session_id=session_id,
        user_message=user_question,
        assistant_message=answer
    )

    print(
        "Conversation successfully saved "
        f"for session: {session_id}"
    )


    # ==========================================
    # STEP 10: RETURN FINAL ANSWER
    # ==========================================
    print(
        "\nRAG request completed successfully."
    )

    print("=" * 60)

    return answer