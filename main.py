################################################################################
import os
from flask import Flask, jsonify
################################################################################
from dotenv import load_dotenv
################################################################################
load_dotenv()
################################################################################
from src.app_utils.database_manager import DocumentLibraryDB
from src.app_utils import setup_security_middleware 
################################################################################

def _ensure_database_exists(db_path: str = "document_library.db") -> bool:
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
    setup_security_middleware(application)

    db_path = os.getenv("DOCUMENT_DB_PATH", "document_library.db")
    
    if _ensure_database_exists(db_path):
        application.logger.info(f"Created document library database at {db_path}")
    else:
        application.logger.info(f"Document library database already exists at {db_path}")

    # Register route blueprints
    try:
        # lazy import to avoid circular imports during config-time
        from src.routes.query import query_bp
        application.register_blueprint(query_bp, url_prefix="/api/v1")

        from src.routes.tools import tools_bp
        application.register_blueprint(tools_bp, url_prefix="/api/v1")

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
