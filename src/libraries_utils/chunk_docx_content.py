import logging
import os
################################################################################
from langchain_text_splitters import RecursiveCharacterTextSplitter
from werkzeug.datastructures import FileStorage
from langchain_core.documents import Document
################################################################################
from src.schemas.class_ChunkConfig import ChunkConfig

def chunk_docx_content(
        uploaded_file: FileStorage, 
        chunk_config: ChunkConfig) -> list[Document]:
       # Placeholder implementation
    try:
        from .save_filestorage_to_temp_docx import save_filestorage_to_temp_docx
        docx_path = save_filestorage_to_temp_docx(uploaded_file)
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(docx_path)
        documents = loader.load()

        try:
            os.remove(docx_path)
        except Exception as e:
            logging.warning(f"Failed to remove temporary DOCX file: {str(e)}")
            pass
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_config.chunk_size,
            chunk_overlap=chunk_config.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_documents(documents)
        return chunks
    except Exception as e:
        logging.error(f"Error loading DOCX file: {str(e)}")
        raise 