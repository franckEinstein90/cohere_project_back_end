"""Handler for deleting tools."""
import os
import shutil
from pathlib import Path
from flask import jsonify, current_app

from src.app_utils import DocumentLibraryDB


def _remove_directory(path: Path):
    """Remove a directory tree if it exists."""
    if path.exists():
        shutil.rmtree(path)


def handle_delete_tool(tool_id: str):
    """Delete a tool and associated resources."""
    db = DocumentLibraryDB()
    try:
        tool = db.tools.get(tool_id)
        if not tool:
            return jsonify({
                "error": "not_found",
                "message": "Tool not found",
            }), 404

        root_path = Path(current_app.root_path)

        library_dir = root_path / "libraries" / tool["name"]
        data_library_dir = root_path / "data" / "libraries" / tool_id

        vector_store_base = Path(os.getenv("VECTORSTORE_PATH", "vectorstore/"))
        if not vector_store_base.is_absolute():
            vector_store_base = root_path / vector_store_base
        vector_store_dir = vector_store_base / tool_id

        try:
            _remove_directory(library_dir)
            _remove_directory(data_library_dir)
            _remove_directory(vector_store_dir)
        except Exception as cleanup_error:
            current_app.logger.error(f"Failed to remove tool directories: {cleanup_error}")
            return jsonify({
                "error": "cleanup_failed",
                "message": "Failed to remove tool directories",
            }), 500

        db.tools.delete(tool_id)
        return jsonify({
            "status": "success",
            "message": "Tool and associated data deleted",
        }), 200
    except Exception as e:
        current_app.logger.exception("Unexpected error deleting tool")
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": str(e),
        }), 500
