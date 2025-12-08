"""File processing utilities for library uploads."""
import json
import os
import logging
################################################################################
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_cohere import CohereEmbeddings
from werkzeug.datastructures import FileStorage
################################################################################
from src.schemas.class_DocumentMetadata import DocumentMetadata
################################################################################
from .chunk_file_content import chunk_file_content
################################################################################
from . import errors as FileErrors
from .read_uploaded_file import read_uploaded_file
################################################################################
logger = logging.getLogger(__name__)

def _validate_chunk_parameters(chunk_size: int, chunk_overlap: int) -> None:
    """Validate chunking parameters.
    
    Args:
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Token overlap between chunks
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
        raise ValueError("chunk_overlap must be a non-negative integer")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
        
    Raises:
        InvalidFileError: If filename is invalid
    """
    if not filename or not isinstance(filename, str):
        raise FileErrors.InvalidFileError("filename must be a non-empty string")
    
    # Remove directory paths
    sanitized = os.path.basename(filename)
    
    if not sanitized or sanitized in ('.', '..'):
        raise FileErrors.InvalidFileError(f"Invalid filename: {filename}")
    
    return sanitized





def prepare_metadata_for_storage(
    metadata_obj: Optional[DocumentMetadata],
    filename: str,
    tool_id: str,
    uploaded_by: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Prepare metadata dictionary for storage.
    
    Args:
        metadata_obj: Validated DocumentMetadata object
        filename: Name of the file
        tool_id: Tool identifier
        uploaded_by: Username or identifier of uploader
        
    Returns:
        Metadata dictionary with system fields, or None if no metadata
        
    Raises:
        MetadataError: If metadata preparation fails
    """
    if not metadata_obj:
        return None
    
    try:
        # Convert Pydantic model to dict
        meta_dict = metadata_obj.model_dump(exclude_none=False)
        
        # Add system fields
        meta_dict["uploaded_by"] = uploaded_by or "anonymous"
        meta_dict["filename"] = filename
        meta_dict["tool_id"] = tool_id
        meta_dict["saved_at"] = datetime.utcnow().isoformat() + "Z"
        
        return meta_dict
    except Exception as e:
        raise FileErrors.MetadataError(f"Failed to prepare metadata: {str(e)}")


def save_file_and_metadata(
    root_path: Path,
    tool_id: str,
    filename: str,
    content: str,
    metadata_dict: Optional[Dict[str, Any]] = None
) -> tuple[Path, Optional[Path]]:
    """Save file content and optional metadata to disk.
    
    Args:
        root_path: Application root path
        tool_id: Tool identifier
        filename: Sanitized filename
        content: File content
        metadata_dict: Optional metadata dictionary
        
    Returns:
        Tuple of (file_path, metadata_path)
        
    Raises:
        StorageError: If file or metadata cannot be saved
    """
    base_dir = root_path / "data" / "libraries" / tool_id
    
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise FileErrors.StorageError(f"Failed to create directory {base_dir}: {str(e)}")
    
    file_path = base_dir / filename
    metadata_path = None
    
    # Save file content
    try:
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except Exception as e:
        raise FileErrors.StorageError(f"Failed to save file {file_path}: {str(e)}")
    
    # Save metadata if provided
    if metadata_dict:
        metadata_path = base_dir / (filename + ".metadata.json")
        try:
            with open(metadata_path, "w", encoding="utf-8") as mh:
                json.dump(metadata_dict, mh, ensure_ascii=False, indent=2)
        except Exception as e:
            # Clean up the file if metadata save fails
            try:
                file_path.unlink()
            except:
                pass
            raise FileErrors.StorageError(f"Failed to save metadata {metadata_path}: {str(e)}")
    
    return file_path, metadata_path


def process_library_upload(
    root_path: Path,
    tool_id: str,
    uploaded_file: FileStorage,
    metadata_obj: Optional[DocumentMetadata],
    chunk_size: int,
    chunk_overlap: int,
    uploaded_by: Optional[str] = None
) -> Dict[str, Any]:
    
    try:
        document_chunks = chunk_file_content(
            uploaded_file=uploaded_file, 
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap)
    except Exception as e:
        raise FileErrors.FileProcessingError(f"Failed to chunk file content: {str(e)}")

    ############################################################################
    # Add metadata to each chunk
    ############################################################################
    for i, chunk in enumerate(document_chunks):
        chunk.metadata['chunk_index'] = i
        chunk.metadata['source_file'] = uploaded_file.filename

    ############################################################################
    # Initialize Cohere embeddings
    ############################################################################
    try:
        cohere_api_key = os.getenv("COHERE_API_KEY")
        embeddings = CohereEmbeddings(
            cohere_api_key=cohere_api_key,
            model="embed-english-v3.0",
        )
    except Exception as e:
        error_message = f"Failed to initialize Cohere embeddings: {str(e)}"
        logger.error(error_message)
        raise e 

    ############################################################################
    # Load or create vectorstore
    # There is a vectorstore for each tool_id
    ############################################################################
    vectorstore_path = os.getenv("VECTORSTORE_PATH", "vectorstore/") + tool_id + "/"
    if os.path.exists(vectorstore_path + "index.faiss"):
        vectorstore = FAISS.load_local(
            vectorstore_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        vectorstore.add_documents(document_chunks)
    else:
        os.makedirs(vectorstore_path, exist_ok=True) 
        vectorstore = FAISS.from_documents(
            document_chunks,
            embeddings
        )

    vectorstore.save_local(vectorstore_path)
    ############################################################################


    return {
        "status": "success",
    }
