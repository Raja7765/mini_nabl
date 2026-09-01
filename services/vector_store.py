from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import (
    CHROMA_PERSIST_DIRECTORY,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
)


class VectorStore:

    def __init__(self):

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL_NAME
        )

        self.chroma_db = Chroma(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings,
            collection_name=COLLECTION_NAME
        )

    def search(
        self,
        query,
        k=3,
        filter=None
    ):

        print("\n[VECTOR SEARCH]")
        print(f"Query: {query}")
        print(f"Filter: {filter}")

        try:
            results = self.chroma_db.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
        except Exception as e:
            print(f"[VECTOR SEARCH ERROR] {e}")
            results = []

        print(f"[VECTOR SEARCH] Results found: {len(results)}")

        for i, result in enumerate(results, 1):
            print(f"\nResult {i}")
            print(f"Metadata: {result.metadata}")
            print(f"Content: {result.page_content[:300]}")

        return results or []

    def add_documents(self, documents, ids=None):

        print(
            f"[VECTOR] Starting add_documents: "
            f"{len(documents)} documents"
        )

        if ids:
            self.chroma_db.add_documents(documents, ids=ids)
        else:
            self.chroma_db.add_documents(documents)

        print(
            f"[VECTOR] Finished add_documents: "
            f"{len(documents)} documents"
        )

    def delete_by_document(self, document_name):

        results = self.chroma_db.get(
            where={
                "document": document_name
            }
        )

        ids = results.get("ids", [])

        if ids:

            self.chroma_db.delete(
                ids=ids
            )

            print(
                f"Deleted {len(ids)} existing records for document: "
                f"{document_name}"
            )
            return len(ids)

        return 0

    def update_documents(
        self,
        ids,
        documents
    ):

        self.chroma_db.update_documents(
            ids=ids,
            documents=documents
        )

    def delete_documents(self, ids):

        self.chroma_db.delete(
            ids=ids
        )

    def count_by_document(self, document_name):

        results = self.chroma_db.get(
            where={"[VECTOR]document": document_name}
        )

        return len(results.get("ids", []))