from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class VectorStore:

    def __init__(self):

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001"
        )

        self.chroma_db = Chroma(
            persist_directory="./chroma_data",
            embedding_function=self.embeddings,
            collection_name="nabl_documents"
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

    def update_documents(self, ids, documents):

        self.chroma_db.update_documents(
            ids=ids,
            documents=documents
        )

    def delete_documents(self, ids):

        self.chroma_db.delete(ids=ids)

    def count(self):

        return self.chroma_db._collection.count()