################################################################################
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
################################################################################
from src.schemas.query import QueryRequest
################################################################################
query_bp = Blueprint("query", __name__)
################################################################################


@query_bp.route("/<tool_id>/query", methods=["POST"])
def query_tool(tool_id):
    #tools can be: system, playbooks.
    current_app.logger.info(f"Received query for tool_id={tool_id}")

    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        body = QueryRequest(**payload)
    except ValidationError as exc:
        # Return a 422 Unprocessable Entity with pydantic validation details
        return jsonify({"error": "validation_error", "details": exc.errors()}), 422

    # If the tool is `system`, expect additional `system` information and
    # delegate processing to the system_query processor.
    if tool_id == "system":
        from src.system_query.class_SystemDescription import SystemDescription
        from src.system_query.processor import process_system_tool

        system_payload = payload.get("system")
        if system_payload is None:
            return jsonify({
                "error": "validation_error",
                "details": [{"loc": ["system"], "msg": "Field required", "type": "missing"}]
            }), 422

        try:
            system_desc = SystemDescription.from_dict(system_payload)
        except Exception as exc:
            # Normalize validation error
            return jsonify({"error": "validation_error", "details": str(exc)}), 422

        # Delegate to the system processor for actual work
        # Pass the optional conversation history along if provided
        conv = None
        if getattr(body, "conversation", None):
            # model already validated conversation items
            conv = [t.model_dump() for t in body.conversation]

        result = process_system_tool(system_desc, body.user_prompt, conv)

        return jsonify({
            "tool_id": tool_id,
            "status": "processed",
            "result": result,
            "conversation": conv
        }), 200

    # Default handling for non-system tools: echo the prompt
    response = {
        "tool_id": tool_id,
        "received": {"user_prompt": body.user_prompt},
        "status": "queued",
        "conversation": [t.model_dump() for t in body.conversation] if getattr(body, "conversation", None) else None,
    }

    return jsonify(response), 200
