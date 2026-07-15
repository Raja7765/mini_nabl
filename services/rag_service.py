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


# ==========================================
# INITIAL SETUP & ENVIRONMENT CONFIGURATION
# ==========================================
load_dotenv()

# Verify API key presence
api_key = os.getenv("GOOGLE_API_KEY")
print("API key loaded successfully:", api_key is not None)


# ==========================================
# INITIALIZE EMBEDDING MODEL
# ==========================================
print("Initializing embedding model...")

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)

# Quick test vector validation
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
# RAG QUESTION ANSWERING FUNCTION
# ==========================================

def rewrite_question(user_question: str, conversation_history: str) -> str:
    # No previous conversation means no rewriting is needed
    if not conversation_history.strip():
        return user_question

    rewrite_prompt = f"""
You are a query rewriting assistant.

Use the previous conversation only to understand references
in the current question such as "it", "its", "this", "that",
"they", or similar follow-up references.

Rewrite the current question as a clear standalone question.

Do not answer the question.
Return only the rewritten question.

Previous Conversation:
{conversation_history}

Current Question:
{user_question}
"""

    response = llm.invoke(rewrite_prompt)

    rewritten_question = response.content

    print(f"Original Question: {user_question}")
    print(f"Rewritten Question: {rewritten_question}")

    return rewritten_question












def ask_question(
    user_question: str,
    session_id: str
) -> str:

    print(f"\nSession ID -> '{session_id}'")
    print(f"User Query Captured -> '{user_question}'")


    # ==========================================
    # STEP 1: GET PREVIOUS HISTORY FROM REDIS
    # ==========================================
    print("\nLoading previous conversation from Redis...")

    history = get_session_history(session_id)

    print(
        f"Previous conversation turns found: "
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
    # STEP 3: SIMILARITY SEARCH
    # ==========================================
    print(
        "\nExecuting mathematical "
        "vector similarity search..."
    )

    results = vector_store.similarity_search(
        user_question,
        k=3
    )


    # ==========================================
    # STEP 4: COMBINE RETRIEVED CHUNKS
    # ==========================================
    print(
        "\n--- CHROMADB RETRIEVED "
        "CHUNKS FOUND ---"
    )

    combined_context = ""

    for i, chunk in enumerate(results, 1):

        print(f"\n--- Chunk {i} ---")

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
    # STEP 5: CONSTRUCT RAG PROMPT
    # ==========================================
    print(
        "\nConstructing prompt and "
        "waking up Gemini LLM..."
    )

    prompt = f"""
You are an expert NABL assistant.

Use the previous conversation history to understand
follow-up questions and references such as:
"it", "its", "that", "this", and similar references.

Answer the user's question using ONLY the provided
NABL document context.

The previous conversation history is provided only
to help understand the meaning of the current question.

If the answer cannot be found in the retrieved
document context, say that the information is not
available in the provided document.

Previous Conversation:
{conversation_history}

Retrieved Document Context:
{combined_context}

Current Question:
{user_question}
"""


    # ==========================================
    # STEP 6: GENERATE FINAL ANSWER
    # ==========================================
    print(
        "\n--- GENERATING FINAL AI ANSWER ---"
    )

    final_response = llm.invoke(prompt)

    answer = final_response.content


    # ==========================================
    # STEP 7: SAVE CONVERSATION TO REDIS
    # ==========================================
    add_to_history(
        session_id=session_id,
        user_message=user_question,
        assistant_message=answer
    )

    print(
        f"Conversation saved to Redis "
        f"for session: {session_id}"
    )


    # ==========================================
    # STEP 8: RETURN FINAL ANSWER
    # ==========================================
    return answer