"""Handler for adding library files."""
import json
from pathlib import Path
from typing import Optional
from flask import request, jsonify, current_app
from pydantic import ValidationError
from src.schemas import DocumentMetadata, ChunkConfig
from src.libraries_utils.file_processor import process_library_upload
from src.libraries_utils.errors import (
    FileProcessingError,
    InvalidFileError,
    StorageError,
    MetadataError,
)


def handle_add_library_file(tool_id):
    """Handle adding a library file for a given tool_id."""
    # Validate request has file upload
    if 'file' not in request.files:
        return jsonify({"error": "no_file", "message": "No file part in the request"}), 400

    uploaded_file = request.files['file']
    
    # Parse optional metadata from form data
    metadata_obj: Optional[DocumentMetadata] = None
    metadata_str = request.form.get('metadata')
    
    if metadata_str:
        try:
            metadata_json = json.loads(metadata_str)
            metadata_obj = DocumentMetadata(**metadata_json)
        except json.JSONDecodeError as e:
            return jsonify({
                "error": "invalid_json",
                "message": "metadata must be valid JSON string",
                "details": str(e)
            }), 400
        except ValidationError as e:
            return jsonify({
                "error": "metadata_validation_error",
                "message": "Metadata validation failed",
                "details": e.errors()
            }), 422
    
    # Get chunk parameters from form data or use defaults
    chunk_config: ChunkConfig
    chunk_config_str = request.form.get('chunk_config')
    if chunk_config_str:
        try:
            chunk_config_json = json.loads(chunk_config_str)
            chunk_config = ChunkConfig(**chunk_config_json)
        except json.JSONDecodeError as e:
            return jsonify({
                "error": "invalid_json",
                "message": "chunk_config must be valid JSON string",
                "details": str(e)
            }), 400
        except ValidationError as e:
            return jsonify({
                "error": "chunk_config_validation_error",
                "message": "ChunkConfig validation failed",
                "details": e.errors()
            }), 422
    else:
        # Create default chunk config if not provided
        chunk_config = ChunkConfig(chunk_size=1000, chunk_overlap=500)
    
    # Get optional uploaded_by field
    uploaded_by = request.form.get('uploaded_by')
    
    # Process the file upload
    try:
        result = process_library_upload(
            root_path=Path(current_app.root_path),
            tool_id=tool_id,
            uploaded_file=uploaded_file,
            metadata_obj=metadata_obj,
            chunk_config=chunk_config,
            uploaded_by=uploaded_by
        )
        return jsonify({
            "status": "success",
            "file_path": str(result.get("file_path")),
            "metadata_path": str(result.get("metadata_path")) if result.get("metadata_path") else None,
            "num_chunks": result.get("num_chunks"),
        }), 201
    except InvalidFileError as e:
        current_app.logger.warning(f"Invalid file upload: {str(e)}")
        return jsonify({
            "error": "invalid_file",
            "message": str(e)
        }), 400
    except MetadataError as e:
        current_app.logger.error(f"Metadata processing error: {str(e)}")
        return jsonify({
            "error": "metadata_error",
            "message": str(e)
        }), 500
    except StorageError as e:
        current_app.logger.error(f"Storage error: {str(e)}")
        return jsonify({
            "error": "storage_error",
            "message": str(e)
        }), 500
    except FileProcessingError as e:
        current_app.logger.error(f"File processing error: {str(e)}")
        return jsonify({
            "error": "processing_error",
            "message": str(e)
        }), 500
    except Exception as e:
        current_app.logger.exception("Unexpected error during file upload")
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500
