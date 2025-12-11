################################################################################
import os
import threading
import uuid
from collections import defaultdict, deque
from datetime import datetime

from flask import Flask, jsonify, request, g, app
################################################################################
from dotenv import load_dotenv
################################################################################
load_dotenv()
################################################################################
from src.app_utils import validate_request
from src.app_utils.database_manager import DocumentLibraryDB
################################################################################

def _setup_security_middleware(app):
    allowed_methods = {"GET", "POST"}
    request_buckets = defaultdict(deque)
    bucket_lock = threading.Lock()
    rate_limit_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", 120))
    suspicious_header_max_length = int(os.getenv("SUSPICIOUS_HEADER_MAX_LENGTH", 2048))

    def _detect_suspicious_headers(headers):
        suspicious_reasons = []
        for header, value in headers.items():
            if any(char in header for char in ("\n", "\r")) or any(
                char in value for char in ("\n", "\r")
            ):
                suspicious_reasons.append(f"header {header} contains control characters")
            if len(value) > suspicious_header_max_length:
                suspicious_reasons.append(f"header {header} exceeds maximum length")
        return suspicious_reasons

    @app.before_request
    def before_request_func():
        g.request_start_time = datetime.utcnow()

        # Generate or retrieve a request ID
        rid = request.headers.get("X-REQUEST-ID", None)
        if not rid:
            rid = str(uuid.uuid4())
            request.environ["X-REQUEST-ID"] = rid
        g.request_id = rid
        g.logger = app.logger

        if request.method not in allowed_methods:
            app.logger.warning(
                "[%s] Blocked method %s on %s", g.request_id, request.method, request.path
            )
            return (
                jsonify(
                    {
                        "error": "Method not allowed",
                        "allowed_methods": sorted(allowed_methods),
                    }
                ),
                405,
            )

        suspicious_reasons = _detect_suspicious_headers(request.headers)
        if suspicious_reasons:
            app.logger.warning(
                "[%s] Suspicious headers detected: %s", g.request_id, "; ".join(suspicious_reasons)
            )
            return (
                jsonify({"error": "Suspicious headers detected", "details": suspicious_reasons}),
                400,
            )

        requester = request.remote_addr or "unknown"
        now_ts = datetime.utcnow().timestamp()
        with bucket_lock:
            bucket = request_buckets[requester]
            cutoff = now_ts - 60
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            bucket.append(now_ts)
            if len(bucket) > rate_limit_per_minute:
                app.logger.warning(
                    "[%s] Rate limit exceeded for %s (%s req/min)",
                    g.request_id,
                    requester,
                    rate_limit_per_minute,
                )
                return (
                    jsonify(
                        {
                            "error": "Too Many Requests",
                            "retry_after_seconds": 60,
                            "rate_limit_per_minute": rate_limit_per_minute,
                        }
                    ),
                    429,
                )

        app.logger.info(
            f"[{g.request_id}] {request.method} {request.path} started at {g.request_start_time}"
            f" from ({request.remote_addr})"
            f" UA: {request.headers.get('User-Agent', 'unknown')[:50]}"
        )

    @app.after_request
    def after_request_func(response):
        request_id = getattr(g, "request_id", "unknown")
        start_time = getattr(g, "request_start_time", None)
        if start_time is not None:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            app.logger.info(
                "[%s] %s %s completed with %s in %.2fms",
                request_id,
                request.method,
                request.path,
                response.status_code,
                duration_ms,
            )
        return response

    @app.teardown_request
    def teardown_request_func(error=None):
        if error:
            request_id = getattr(g, "request_id", "unknown")
            app.logger.exception(
                "[%s] Unhandled exception during request processing", request_id
            )

def ensure_database_exists(db_path: str = "document_library.db") -> bool:
    """Ensure the database exists, creating it if necessary.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        bool: True if database was created, False if it already existed
    """
    import os
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Creating...")
        db = DocumentLibraryDB(db_path)
        db.create_database()
        return True
    return False

def create_app():
    
    application = Flask(__name__)
    _setup_security_middleware(application)

    db_path = os.getenv("DOCUMENT_DB_PATH", "document_library.db")
    
    if ensure_database_exists(db_path):
        application.logger.info(f"Created document library database at {db_path}")
    else:
        application.logger.info(f"Document library database already exists at {db_path}")

    # Register route blueprints
    try:
        # lazy import to avoid circular imports during config-time
        from src.routes.query import query_bp
        application.register_blueprint(query_bp, url_prefix="/api/v1")
        # register libraries blueprint
        from src.routes.libraries import libraries_bp
        application.register_blueprint(libraries_bp, url_prefix="/api/v1")
    except Exception as e:
        # Log full exception so import-time errors are visible in logs
        application.logger.exception("Could not register route blueprints")

    # Log registered blueprints and available routes for easier debugging
    try:
        application.logger.info("Registered blueprints: %s", list(application.blueprints.keys()))
        for rule in application.url_map.iter_rules():
            application.logger.debug("Route: %s -> %s", rule.rule, rule.endpoint)
    except Exception:
        # If logging of routes fails, don't let it crash the app
        application.logger.exception("Failed to list registered routes")

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
