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

        results = self.chroma_db.similarity_search(
            query=query,
            k=k,
            filter=filter
        )

        return results

    def add_documents(self, documents):

        self.chroma_db.add_documents(documents)

    def delete_by_document(self, document_name):
        results = self.chroma_db.get(
            where={"document": document_name}
        )
        ids = results.get("ids", [])
        if ids:
            self.chroma_db.delete(ids=ids)
            print(f"Deleted existing document: {document_name}")

    def update_documents(self, ids, documents):

        self.chroma_db.update_documents(
            ids=ids,
            documents=documents
        )

    def delete_documents(self, ids):

        self.chroma_db.delete(ids=ids)

    def count(self):

        return self.chroma_db._collection.count()