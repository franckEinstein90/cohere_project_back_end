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

def setup_security_middleware(app):
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