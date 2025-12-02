################################################################################
import os
import hashlib
################################################################################
from src.constants import network_security_constants
################################################################################

def validate_request(request):
    """
    Validate the incoming request for required headers and parameters.
    Returns an error message string if validation fails, otherwise None.
    """
    missing_headers = [
        header for header in network_security_constants.REQUIRED_HEADERS
        if header not in request.headers
    ]
    if missing_headers:
        return f"Missing required headers: {', '.join(missing_headers)}"
    
    ############################################################################
    # Check for suspicious headers
    ############################################################################
    found_suspicious = [
        header for header in network_security_constants.SUSPICIOUS_HEADERS
        if header in request.headers
    ]
    if found_suspicious:
        return f"Suspicious headers detected: {', '.join(found_suspicious)}"
    ############################################################################
    # Example validation: Check for a specific query parameter
    auth_header = request.headers.get("Authorization", None)

    if auth_header is None:
        return {"error": "Missing Authorization header"}, 401
    
    if auth_header.startwith("Api-Key "):
        api_key = auth_header.split(" ")[1]
        expected_api_key_hash = os.getenv("API_KEY_HASH")
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if api_key_hash != expected_api_key_hash:
            return {"error": "Invalid API key"}, 403

    if 'param' not in request.args:
        return "Missing required query parameter: param"

    # Additional validations can be added here

    return None