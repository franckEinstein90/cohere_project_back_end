"""Handler for creating tools."""
from flask import request, jsonify, current_app
from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
################################################################################
from src.schemas import ToolConfig
from src.tools_utils import create_tool

def handle_create_tool():
    """
    Create a new tool with a unique tool_id and initialize its library directory.
    
    Expected JSON payload:
    {
        "name": "My Tool",
        "description": "Optional description"
    }
    """
    current_app.logger.info("=== handle_create_tool called ===")
    try:
        # Parse and validate request body
        request_data = request.get_json()
        current_app.logger.info(f"Request data: {request_data}")
        if not request_data:
            return jsonify({
                "error": "invalid_request",
                "message": "Request body must be JSON"
            }), 400
        
        tool_config = ToolConfig(**request_data)
        current_app.logger.info(f"Tool config created: {tool_config}")
        
    except ValidationError as e:
        current_app.logger.error(f"Validation error: {e.errors()}")
        return jsonify({
            "error": "validation_error",
            "message": "Request validation failed",
            "details": e.errors()
        }), 422
    except Exception as e:
        current_app.logger.error(f"Exception parsing request: {str(e)}")
        return jsonify({
            "error": "invalid_json",
            "message": "Failed to parse request body",
            "details": str(e)
        }), 400
    
    # Generate unique tool_id
    
    try:
        current_app.logger.info("Calling create_tool...")
        result = create_tool(tool_config = tool_config)
        current_app.logger.info(f"create_tool returned: {result}")
        return jsonify(result), 201
        
    except FileExistsError:
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
