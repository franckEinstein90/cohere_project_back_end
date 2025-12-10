################################################################################
import json
from pathlib import Path
from typing import Optional, List
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
################################################################################
from src.schemas.class_DocumentMetadata import DocumentMetadata
from src.libraries_utils.file_processor import (
    process_library_upload,
    FileProcessingError,
    InvalidFileError,
    StorageError,
    MetadataError,
)
################################################################################
libraries_bp = Blueprint("libraries", __name__)



@libraries_bp.route("/<tool_id>/libraries", methods=["POST"])
def add_library_file(tool_id):
    """Add (save) a file for the given tool_id.

    Accepts multipart/form-data with:
      - file: the uploaded file (required)
      - metadata: JSON string with optional metadata object (optional)
      - chunk_size: integer, defaults to 500 tokens (optional)
      - chunk_overlap: integer, defaults to 50 tokens (optional)
      - uploaded_by: string, username/identifier (optional)

    Saves file to: data/libraries/<tool_id>/<filename>
    Returns 201 with saved path on success.
    """
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
    
    # Get chunk parameters from form data
    try:
        chunk_size = int(request.form.get('chunk_size', 500))
        chunk_overlap = int(request.form.get('chunk_overlap', 50))
    except (ValueError, TypeError) as e:
        return jsonify({
            "error": "invalid_parameters",
            "message": "chunk_size and chunk_overlap must be integers",
            "details": str(e)
        }), 400
    
    # Get optional uploaded_by field
    uploaded_by = request.form.get('uploaded_by')
    
    # Process the file upload
    try:
        result = process_library_upload(
            root_path=Path(current_app.root_path),
            tool_id=tool_id,
            uploaded_file=uploaded_file,
            metadata_obj=metadata_obj,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
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
    
 