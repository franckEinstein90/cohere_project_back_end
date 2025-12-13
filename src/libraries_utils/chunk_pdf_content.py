import tempfile
import logging
import os
from typing import List
################################################################################
from werkzeug.datastructures import FileStorage
from langchain_core.documents import Document
################################################################################
from src.schemas.class_ChunkConfig import ChunkConfig
from .errors import FileProcessingError


def chunk_pdf_content(
        uploaded_file: FileStorage, 
        chunk_config: ChunkConfig
    ) -> List[Document]:
    """Chunk PDF content using PyPDFLoader and a text splitter.

    Heavy optional dependencies are imported inside the function to avoid
    causing import-time errors when the module is loaded. If the optional
    dependencies are missing, a FileProcessingError is raised with a
    helpful message.
    """
    try:
        # Import optional heavy deps at runtime
        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except Exception as e:
            raise FileProcessingError(
                "Missing optional dependencies for PDF chunking: " + str(e)
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            uploaded_file.save(temp_pdf)
            tmp_path = temp_pdf.name

            # Some versions of PyPDFLoader do not accept `page_delimiter` or
            # `mode` as constructor kwargs. Try the preferred constructor
            # first, then fall back to a simpler call if needed.
            try:
                loader = PyPDFLoader(
                    tmp_path,
                    mode="single",
                    page_delimiter="\n----------------------END OF PAGE----------------------\n",
                )
            except TypeError:
                # Older/newer versions may not accept those kwargs — try simple
                # constructor and let the loader default to built-in behavior.
                try:
                    loader = PyPDFLoader(tmp_path)
                except Exception as e:
                    raise FileProcessingError(
                        "PyPDFLoader constructor failed; check installed "
                        "langchain_community version and API compatibility: "
                        + str(e)
                    )

            # Prefer `load()` if available, otherwise `load_and_split()` or similar
            if hasattr(loader, "load"):
                documents = loader.load()
            elif hasattr(loader, "load_and_split"):
                documents = loader.load_and_split()
            else:
                raise FileProcessingError(
                    "PyPDFLoader does not provide a recognized loading method (load/load_and_split)"
                )
            try:
                os.remove(tmp_path)
            except Exception:
                logging.exception("Failed to delete temporary file %s", tmp_path)

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_config.chunk_size,
                chunk_overlap=chunk_config.chunk_overlap,
                separators=["\n\n", "\n", " ", ""],
            )
            return splitter.split_documents(documents)

    except FileProcessingError:
        raise
    except Exception as e:
        raise FileProcessingError(f"Failed to chunk PDF content: {str(e)}")