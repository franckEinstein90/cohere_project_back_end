"""File processing utilities for library uploads."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.schemas.class_DocumentMetadata import DocumentMetadata


class FileProcessingError(Exception):
    """Base exception for file processing errors."""
    pass


class InvalidFileError(FileProcessingError):
    """Raised when file validation fails."""
    pass


class StorageError(FileProcessingError):
    """Raised when file storage operations fail."""
    pass


class MetadataError(FileProcessingError):
    """Raised when metadata processing fails."""
    pass


def validate_chunk_parameters(chunk_size: int, chunk_overlap: int) -> None:
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
        raise InvalidFileError("filename must be a non-empty string")
    
    # Remove directory paths
    sanitized = os.path.basename(filename)
    
    if not sanitized or sanitized in ('.', '..'):
        raise InvalidFileError(f"Invalid filename: {filename}")
    
    return sanitized


def read_uploaded_file(uploaded_file) -> tuple[str, str]:
    """Read and decode uploaded file content.
    
    Args:
        uploaded_file: Flask file object from request.files
        
    Returns:
        Tuple of (filename, content)
        
    Raises:
        InvalidFileError: If file cannot be read or decoded
    """
    if not uploaded_file or not uploaded_file.filename:
        raise InvalidFileError("No file selected")
    
    filename = uploaded_file.filename
    
    try:
        content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError as e:
        raise InvalidFileError(f"File must be UTF-8 encoded text: {str(e)}")
    except Exception as e:
        raise InvalidFileError(f"Failed to read file: {str(e)}")
    
    return filename, content


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
        raise MetadataError(f"Failed to prepare metadata: {str(e)}")


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
        raise StorageError(f"Failed to create directory {base_dir}: {str(e)}")
    
    file_path = base_dir / filename
    metadata_path = None
    
    # Save file content
    try:
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except Exception as e:
        raise StorageError(f"Failed to save file {file_path}: {str(e)}")
    
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
            raise StorageError(f"Failed to save metadata {metadata_path}: {str(e)}")
    
    return file_path, metadata_path


def process_library_upload(
    root_path: Path,
    tool_id: str,
    uploaded_file,
    metadata_obj: Optional[DocumentMetadata],
    chunk_size: int,
    chunk_overlap: int,
    uploaded_by: Optional[str] = None
) -> Dict[str, Any]:
    """Process a library file upload.
    
    This is the main entry point that coordinates all file processing steps:
    1. Read and validate the uploaded file
    2. Sanitize the filename
    3. Prepare metadata for storage
    4. Save file and metadata to disk
    
    Args:
        root_path: Application root path
        tool_id: Tool identifier
        uploaded_file: Flask file object
        metadata_obj: Validated DocumentMetadata object or None
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Token overlap between chunks
        uploaded_by: Username or identifier of uploader
        
    Returns:
        Dictionary with processing results including paths and metadata
        
    Raises:
        FileProcessingError: If any step fails (with specific subclass)
    """
    # Validate chunk parameters
    validate_chunk_parameters(chunk_size, chunk_overlap)
    
    # Read uploaded file
    filename, content = read_uploaded_file(uploaded_file)
    
    # Sanitize filename
    sanitized_filename = sanitize_filename(filename)
    
    # Prepare metadata
    metadata_dict = prepare_metadata_for_storage(
        metadata_obj,
        sanitized_filename,
        tool_id,
        uploaded_by
    )
    
    # Save file and metadata
    file_path, metadata_path = save_file_and_metadata(
        root_path,
        tool_id,
        sanitized_filename,
        content,
        metadata_dict
    )
    
    return {
        "filename": sanitized_filename,
        "content": content,
        "file_path": file_path,
        "metadata_path": metadata_path,
        "metadata_dict": metadata_dict,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }
