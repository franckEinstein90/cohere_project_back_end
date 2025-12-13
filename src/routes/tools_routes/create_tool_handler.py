"""Handler for creating tools."""
from flask import request, jsonify, current_app
from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid
import json


class ToolConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tool name")
    description: Optional[str] = Field(None, max_length=500, description="Tool description")


def handle_create_tool():
    """
    Create a new tool with a unique tool_id and initialize its library directory.
    
    Expected JSON payload:
    {
        "name": "My Tool",
        "description": "Optional description"
    }
    """
    try:
        # Parse and validate request body
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                "error": "invalid_request",
                "message": "Request body must be JSON"
            }), 400
        
        tool_config = ToolConfig(**request_data)
        
    except ValidationError as e:
        return jsonify({
            "error": "validation_error",
            "message": "Request validation failed",
            "details": e.errors()
        }), 422
    except Exception as e:
        return jsonify({
            "error": "invalid_json",
            "message": "Failed to parse request body",
            "details": str(e)
        }), 400
    
    # Generate unique tool_id
    tool_id = str(uuid.uuid4())
    
    try:
        # Create library directory structure
        root_path = Path(current_app.root_path)
        library_path = root_path / "libraries" / tool_id
        library_path.mkdir(parents=True, exist_ok=False)
        
        # Create subdirectories for organization
        (library_path / "documents").mkdir(exist_ok=True)
        (library_path / "metadata").mkdir(exist_ok=True)
        (library_path / "embeddings").mkdir(exist_ok=True)
        
        # Create tool metadata file
        tool_metadata = {
            "tool_id": tool_id,
            "name": tool_config.name,
            "description": tool_config.description,
            "created_at": datetime.utcnow().isoformat(),
            "document_count": 0
        }
        
        metadata_file = library_path / "tool_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(tool_metadata, f, indent=2)
        
        current_app.logger.info(f"Created new tool: {tool_id} - {tool_config.name}")
        
        return jsonify({
            "status": "success",
            "tool_id": tool_id,
            "name": tool_config.name,
            "description": tool_config.description,
            "library_path": str(library_path),
            "created_at": tool_metadata["created_at"]
        }), 201
        
    except FileExistsError:
        # This should be extremely rare with UUIDs
        current_app.logger.error(f"Tool directory already exists: {tool_id}")
        return jsonify({
            "error": "tool_exists",
            "message": "Tool ID already exists. Please retry."
        }), 409
    except PermissionError as e:
        current_app.logger.error(f"Permission error creating tool directory: {str(e)}")
        return jsonify({
            "error": "permission_error",
            "message": "Failed to create tool directory due to permissions"
        }), 500
    except OSError as e:
        current_app.logger.error(f"OS error creating tool directory: {str(e)}")
        return jsonify({
            "error": "storage_error",
            "message": "Failed to create tool directory",
            "details": str(e)
        }), 500
    except Exception as e:
        current_app.logger.exception("Unexpected error creating tool")
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500
