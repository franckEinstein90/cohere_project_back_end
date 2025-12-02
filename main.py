################################################################################
import os
import uuid
from flask import Flask, jsonify, request, g, app
from datetime import datetime
################################################################################
from dotenv import load_dotenv
################################################################################
load_dotenv()
################################################################################
from src.app_utils import validate_request

def _setup_security_middleware(app):
    @app.before_request
    def before_request_func():
        # Example security check (e.g., API key validation)
        g.request_start_time = datetime.utcnow()

        # Generate or retrieve a request ID
        rid = request.headers.get("X-REQUEST-ID", None)
        if not rid:
            rid = str(uuid.uuid4())
            request.environ["X-REQUEST-ID"] = rid
        g.request_id = rid
        g.logger = app.logger
        app.logger.info(
            f"[{g.request_id}] {request.method} {request.path} started at {g.request_start_time}"
            f"from ({request.remote_addr})"
            f"UA: {request.headers.get('User-Agent', 'unknown')[:50]}"
        )
        validation_error = validate_request(request)
        if validation_error:
            return jsonify({"error": validation_error}), 400



def create_app():
    application = Flask(__name__)

    _setup_security_middleware(application)
    @application.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"status": "ok"}), 200

    return application

if __name__ == "__main__":
    application = create_app()
    # Development server entry point
    application.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("DEBUG", "true").lower() == "true",
        use_reloader=False,
    )
