"""Flask blueprint for tools routes."""
from flask import Blueprint

from src.app_utils import DocumentLibraryDB
################################################################################
from .tools_routes import handle_create_tool, handle_update_tool, handle_delete_tool
################################################################################


tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/tools", methods=["POST"])
def create_tool():
    """Create a new tool with a unique tool_id and initialize its library directory."""
    return handle_create_tool()


@tools_bp.route("/tools", methods=["GET"])
def list_tools():
    """List all active tools."""
    try:
        db = DocumentLibraryDB()
        tools = db.tools.get_all()
        return {"tools": tools}, 200
    except Exception as e:
        return {"error": "internal_server_error", "message": str(e)}, 500


@tools_bp.route("/tools/<tool_id>", methods=["PATCH"])
def update_tool(tool_id: str):
    """Update an existing tool's metadata."""
    return handle_update_tool(tool_id)


@tools_bp.route("/tools/<tool_id>", methods=["DELETE"])
def delete_tool(tool_id: str):
    """Delete an existing tool and its associated resources."""
    return handle_delete_tool(tool_id)
