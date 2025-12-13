"""Handler for listing libraries."""
from flask import jsonify, current_app
from src.app_utils.database_manager import DocumentLibraryDB


def handle_list_libraries(tool_id):
    """List document libraries for a given tool_id."""
    current_app.logger.info(f"Listing libraries for tool_id={tool_id}")
    
    try:
        db = DocumentLibraryDB()
        libraries = db.documents.get_by_tool(tool_id)
        return jsonify({
            "tool_id": tool_id,
            "libraries": libraries
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error listing libraries for tool_id={tool_id}: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500
