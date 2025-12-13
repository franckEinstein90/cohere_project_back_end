"""Handler for updating existing tools."""
from flask import request, jsonify, current_app
from pydantic import ValidationError

from src.app_utils import DocumentLibraryDB
from src.schemas import ToolUpdate


def handle_update_tool(tool_id: str):
    """Update a tool's name and/or description."""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                "error": "invalid_request",
                "message": "Request body must be JSON",
            }), 400

        update_payload = ToolUpdate(**request_data)
    except ValidationError as e:
        current_app.logger.error(f"Validation error updating tool: {e.errors()}")
        return jsonify({
            "error": "validation_error",
            "message": "Request validation failed",
            "details": e.errors(),
        }), 422
    except Exception as e:
        current_app.logger.error(f"Exception parsing update payload: {str(e)}")
        return jsonify({
            "error": "invalid_json",
            "message": "Failed to parse request body",
            "details": str(e),
        }), 400

    db = DocumentLibraryDB()
    try:
        existing_tool = db.tools.get(tool_id)
        if not existing_tool:
            return jsonify({
                "error": "not_found",
                "message": "Tool not found",
            }), 404

        if update_payload.name:
            tool_with_name = db.tools.get_by_name(update_payload.name)
            if tool_with_name and tool_with_name.get("tool_id") != tool_id:
                return jsonify({
                    "error": "tool_exists",
                    "message": "A tool with that name already exists",
                }), 409

        db.tools.update(
            tool_id=tool_id,
            name=update_payload.name,
            description=update_payload.description,
        )

        updated_tool = db.tools.get(tool_id)
        return jsonify({
            "status": "success",
            "tool": updated_tool,
        }), 200
    except ValueError as e:
        current_app.logger.error(f"Update conflict: {str(e)}")
        return jsonify({
            "error": "conflict",
            "message": str(e),
        }), 409
    except Exception as e:
        current_app.logger.exception("Unexpected error updating tool")
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": str(e),
        }), 500
