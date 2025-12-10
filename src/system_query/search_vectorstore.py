import os
################################################################################
from flask import logging
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_cohere import CohereEmbeddings
################################################################################

def search_system_vectorstore(
    query: str,
    top_k: int = 5
) -> list[Document]:

    try:
        cohere_api_key = os.getenv("COHERE_API_KEY")
        embeddings = CohereEmbeddings(
            cohere_api_key=cohere_api_key,
            model="embed-english-v3.0",
        )
        vectorstore_path = os.getenv("VECTORSTORE_PATH", "vectorstore/system/") 
        vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        search_results = vectorstore.similarity_search_with_score(query, k=top_k)
        return search_results
    except Exception as e:
        error_message = f"Failed to search vectorstore: {str(e)}"
        logging.error(error_message)
        raise e
