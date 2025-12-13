"""Flask blueprint for library routes."""
from flask import Blueprint
################################################################################
from .library_routes import handle_list_libraries, add_library_file as handle_add_library_file
################################################################################
libraries_bp = Blueprint("libraries", __name__)


@libraries_bp.route("/<tool_id>/libraries", methods=["GET"])
def list_libraries(tool_id):
    """List document libraries for a given tool_id."""
    return handle_list_libraries(tool_id)


@libraries_bp.route("/<tool_id>/libraries", methods=["POST"])
def add_library_file(tool_id):
    """Add a library file for a given tool_id."""
    return handle_add_library_file(tool_id)
