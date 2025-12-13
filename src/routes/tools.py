"""Flask blueprint for tools routes."""
from flask import Blueprint
################################################################################
from .tools_routes import handle_create_tool
################################################################################
tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/tools", methods=["POST"])
def create_tool():
    """Create a new tool with a unique tool_id and initialize its library directory."""
    return handle_create_tool()