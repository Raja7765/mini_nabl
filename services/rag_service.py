import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma


# ==========================================
# INITIAL SETUP & ENVIRONMENT CONFIGURATION
# ==========================================
load_dotenv()

# Verify API key presence
api_key = os.getenv("GOOGLE_API_KEY")
print("API key loaded successfully:", api_key is not None)

# Initialize the Embedding Model (Translates text to float arrays)
print("Initializing embedding model...")
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

# Quick test vector validation
test_vector = embeddings.embed_query("Hello")
print("Embedding engine verified! Vector dimension length:", len(test_vector))
print("-" * 50)


# ==========================================
# LOAD EXISTING VECTOR STORE
# ==========================================
print("Loading existing ChromaDB...")
vector_store = Chroma(
    persist_directory="./chroma_data",
    embedding_function=embeddings,
    collection_name="nabl_documents"
)


# ==========================================
# STEP 5: Initialize LLM
# ==========================================
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.3)


def ask_question(user_question: str) -> str:
    print(f"\nUser Query Captured -> '{user_question}'")
    
    # ==========================================
    # STEP 6: Similarity search
    # ==========================================
    print("\nExecuting mathematical vector similarity search...")
    # Note: we are returning the top 3 highest-scoring paragraph chunks
    results = vector_store.similarity_search(user_question, k=3)

    # ==========================================
    # STEP 7: Retrieved chunks
    # ==========================================
    print("\n--- CHROMADB RETRIEVED CHUNKS FOUND ---")
    combined_context = ""

    for i, chunk in enumerate(results, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Source Metadata: {chunk.metadata}")
        print(f"Content Context:\n{chunk.page_content}")
        print("-" * 50)
        
        combined_context += f"\n--- Chunk {i} ---\n{chunk.page_content}\n"

    # ==========================================
    # STEP 8: Construct prompt
    # ==========================================
    print("\nConstructing prompt and waking up Gemini LLM...")
    prompt = f"""
You are an expert NABL assistant. Answer the user's question using ONLY the provided context.
If the answer cannot be found in the retrieved context, say that the information is not available in the provided document.

Context: {combined_context}
Question: {user_question}
"""

    # ==========================================
    # STEP 9: Final answer
    # ==========================================
    print("\n--- GENERATING FINAL AI ANSWER ---")
    final_response = llm.invoke(prompt)
    return final_response.content
