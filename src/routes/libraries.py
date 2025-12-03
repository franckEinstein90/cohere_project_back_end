import os
import json
from pathlib import Path
from typing import Optional
from flask import Blueprint, request, jsonify, current_app

libraries_bp = Blueprint("libraries", __name__)


@libraries_bp.route("/<tool_id>/libraries", methods=["POST"])
def add_library_file(tool_id):
    """Add (save) a file for the given tool_id.

    Expects JSON body:
      {
        "filename": "example.txt",
        "content": "file content as string"
      }

    Saves file to: data/libraries/<tool_id>/<filename>
    Returns 201 with saved path on success.
    """
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON payload"}), 400

    filename = payload.get("filename")
    content = payload.get("content")
    metadata: Optional[dict] = payload.get("metadata")

    if not filename or not isinstance(filename, str):
        return jsonify({"error": "filename is required and must be a string"}), 400
    if content is None or not isinstance(content, str):
        return jsonify({"error": "content is required and must be a string"}), 400

    # metadata is optional; if provided it should be a dict
    if metadata is not None and not isinstance(metadata, dict):
        return jsonify({"error": "metadata must be an object/dictionary if provided"}), 400

    # sanitize filename a little (avoid absolute paths)
    filename = os.path.basename(filename)

    base_dir = Path(current_app.root_path) / "data" / "libraries" / tool_id
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        file_path = base_dir / filename
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)

        # If metadata was provided, save a sidecar JSON file alongside the saved file.
        if metadata:
            meta_path = base_dir / (filename + ".metadata.json")
            # enrich metadata with some auto fields if not present
            meta_to_write = dict(metadata)  # copy
            meta_to_write.setdefault("uploaded_by", payload.get("uploaded_by", "anonymous"))
            meta_to_write.setdefault("filename", filename)
            meta_to_write.setdefault("tool_id", tool_id)
            meta_to_write.setdefault("saved_at", None)
            # set saved_at now as ISO timestamp
            from datetime import datetime

            meta_to_write["saved_at"] = datetime.utcnow().isoformat() + "Z"

            with open(meta_path, "w", encoding="utf-8") as mh:
                json.dump(meta_to_write, mh, ensure_ascii=False, indent=2)

    except Exception as exc:
        current_app.logger.exception("Failed to save library file or metadata")
        return jsonify({"error": "failed_to_save", "details": str(exc)}), 500

    return (
        jsonify({
            "status": "created",
            "path": str(file_path.relative_to(current_app.root_path)),
            "metadata_path": str((base_dir / (filename + ".metadata.json")).relative_to(current_app.root_path)) if metadata else None,
        }),
        201,
    )
