"""
security.py — FastAPI Security Middleware

Provides production-grade security hardening for the Python ML API:
  1. Security response headers (OWASP recommended)
  2. Request ID generation (for tracing and debugging)
  3. Input size limits (prevent DoS via large payloads)
  4. Content-Type validation (reject unexpected content types)
  5. CORS hardening (restrict allowed origins)

OWASP references:
  - A01:2021 Broken Access Control
  - A04:2021 Insecure Design
  - A05:2021 Security Misconfiguration

Usage in main.py or app.py:
    from middleware.security import (
        SecurityHeadersMiddleware,
        RequestSizeLimitMiddleware,
        ContentTypeValidationMiddleware,
        generate_request_id
    )

    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_body_size=5 * 1024 * 1024)
    app.add_middleware(ContentTypeValidationMiddleware)
"""

import uuid
import time
import logging
from typing import Callable, Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# ================================================================
# Helper: Request ID Generation
# ================================================================

def generate_request_id() -> str:
    """Generate a unique request ID for tracing."""
    return str(uuid.uuid4())


# ================================================================
# Middleware 1: Security Headers
# ================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds OWASP-recommended security headers to every response.

    These headers protect against:
    - XSS (X-Content-Type-Options, X-XSS-Protection)
    - Clickjacking (X-Frame-Options)
    - MIME sniffing (X-Content-Type-Options)
    - Information disclosure (removal of server headers)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID for tracing
        request_id = generate_request_id()
        request.state.request_id = request_id

        # Log incoming request (no sensitive data)
        start_time = time.time()
        logger.info(
            "Request started | id=%s | method=%s | path=%s | client=%s",
            request_id,
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown"
        )

        # Process request
        response = await call_next(request)

        # Calculate request duration
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(self), payment=()"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # Add request ID to response for client-side tracing
        response.headers["X-Request-ID"] = request_id

        # Remove server identification header if present
        for header_name in ("Server", "X-Powered-By"):
            if header_name in response.headers:
                del response.headers[header_name]

        # Log response
        logger.info(
            "Request completed | id=%s | status=%s | duration=%sms",
            request_id,
            response.status_code,
            duration_ms
        )

        return response


# ================================================================
# Middleware 2: Request Body Size Limit
# ================================================================

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests with bodies exceeding the configured limit.

    Prevents:
    - DoS attacks via large payloads
    - Memory exhaustion from unbounded request bodies

    Default limit: 5 MB (suitable for CSV file uploads).
    """

    def __init__(self, app: ASGIApp, max_body_size: int = 5 * 1024 * 1024):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                length = int(content_length)
                if length > self.max_body_size:
                    max_mb = self.max_body_size / (1024 * 1024)
                    logger.warning(
                        "Request rejected: body too large | size=%s | max=%s | path=%s",
                        content_length,
                        self.max_body_size,
                        request.url.path
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Payload Too Large",
                            "message": f"El cuerpo de la solicitud excede el límite de {max_mb:.0f} MB.",
                            "max_size_bytes": self.max_body_size
                        }
                    )
            except ValueError:
                # Invalid Content-Length header
                logger.warning(
                    "Request rejected: invalid Content-Length header | value=%s",
                    content_length
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Bad Request",
                        "message": "Header Content-Length inválido."
                    }
                )

        return await call_next(request)


# ================================================================
# Middleware 3: Content-Type Validation
# ================================================================

class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates Content-Type headers on requests with bodies.

    Prevents:
    - Content type confusion attacks
    - Unexpected data format processing

    Allowed types are configurable. Defaults to JSON and multipart (for file uploads).
    """

    # HTTP methods that typically have request bodies
    BODY_METHODS: Set[str] = {"POST", "PUT", "PATCH"}

    # Allowed Content-Type prefixes
    ALLOWED_CONTENT_TYPES: Set[str] = {
        "application/json",
        "multipart/form-data",
        "application/x-www-form-urlencoded",
        "text/csv",
    }

    def __init__(
        self,
        app: ASGIApp,
        allowed_types: Optional[Set[str]] = None
    ):
        super().__init__(app)
        if allowed_types:
            self.ALLOWED_CONTENT_TYPES = allowed_types

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only validate Content-Type for methods that have bodies
        if request.method in self.BODY_METHODS:
            content_type = request.headers.get("content-type", "")

            if content_type:
                # Extract the base content type (before any ;charset= etc.)
                base_type = content_type.split(";")[0].strip().lower()

                if not any(
                    base_type.startswith(allowed)
                    for allowed in self.ALLOWED_CONTENT_TYPES
                ):
                    logger.warning(
                        "Request rejected: unsupported Content-Type | type=%s | path=%s",
                        content_type,
                        request.url.path
                    )
                    return JSONResponse(
                        status_code=415,
                        content={
                            "error": "Unsupported Media Type",
                            "message": f"Content-Type '{base_type}' no es soportado.",
                            "allowed_types": sorted(self.ALLOWED_CONTENT_TYPES)
                        }
                    )

        return await call_next(request)


# ================================================================
# Middleware 4: Rate Limiting (Server-Side)
# ================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting per client IP with path-based limits.

    Uses Redis sorted sets when available for distributed rate limiting
    across multiple workers/instances. Falls back to in-memory storage
    when Redis is unavailable.

    Default: 100 requests per minute per IP.
    Expensive endpoints (ML inference, training) have stricter limits.
    """

    # More restrictive limits for expensive endpoints (requests per window)
    ENDPOINT_LIMITS: dict[str, int] = {
        "/predictions/predict": 30,               # 30 predictions per minute
        "/predictions/explain": 10,                # 10 explanations per minute
        "/train": 1,                               # 1 training per minute
        "/predictions/drift-compute-baseline": 5,  # 5 baseline computations per minute
    }

    REDIS_PREFIX = "rate_limit:"

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # In-memory fallback store: { "ip:path": [timestamp1, timestamp2, ...] }
        self._requests: dict[str, list[float]] = {}

    def _get_limit_for_path(self, path: str) -> int:
        """Return the rate limit for a given path, falling back to global default."""
        for endpoint_path, limit in self.ENDPOINT_LIMITS.items():
            if path.rstrip("/") == endpoint_path.rstrip("/"):
                return limit
        return self.max_requests

    def _check_rate_limit_redis(self, rate_key: str, now: float, effective_limit: int) -> tuple[bool, int]:
        """Check rate limit using Redis sorted sets. Returns (is_limited, current_count)."""
        from middleware.redis_client import get_redis
        redis = get_redis()
        if not redis:
            return self._check_rate_limit_memory(rate_key, now, effective_limit)

        try:
            redis_key = f"{self.REDIS_PREFIX}{rate_key}"
            window_start = now - self.window_seconds

            pipe = redis.pipeline()
            # Remove entries outside the window
            pipe.zremrangebyscore(redis_key, "-inf", window_start)
            # Count entries in the current window
            pipe.zcount(redis_key, window_start, "+inf")
            # Add current request timestamp
            pipe.zadd(redis_key, {str(now): now})
            # Set TTL on the key to auto-cleanup
            pipe.expire(redis_key, self.window_seconds + 1)
            results = pipe.execute()

            current_count = results[1]  # zcount result

            if current_count >= effective_limit:
                # Remove the entry we just added since request is denied
                redis.zrem(redis_key, str(now))
                return True, current_count

            return False, current_count + 1
        except Exception:
            # Redis failed, fall back to in-memory
            return self._check_rate_limit_memory(rate_key, now, effective_limit)

    def _check_rate_limit_memory(self, rate_key: str, now: float, effective_limit: int) -> tuple[bool, int]:
        """Check rate limit using in-memory storage. Returns (is_limited, current_count)."""
        window_start = now - self.window_seconds

        if rate_key not in self._requests:
            self._requests[rate_key] = []

        # Remove old entries outside the window
        self._requests[rate_key] = [
            ts for ts in self._requests[rate_key]
            if ts > window_start
        ]

        current_count = len(self._requests[rate_key])

        if current_count >= effective_limit:
            return True, current_count

        # Record this request
        self._requests[rate_key].append(now)

        # Periodic cleanup to prevent memory leak
        if len(self._requests) > 10000:
            self._cleanup_stale_entries(window_start)

        return False, current_count + 1

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        path = request.url.path

        # Determine the effective limit for this path
        effective_limit = self._get_limit_for_path(path)

        # Use a composite key of IP + path for endpoint-specific limiting
        if effective_limit < self.max_requests:
            rate_key = f"{client_ip}:{path}"
        else:
            rate_key = client_ip

        # Check rate limit (tries Redis first, falls back to memory)
        is_limited, current_count = self._check_rate_limit_redis(rate_key, now, effective_limit)

        if is_limited:
            logger.warning(
                "Rate limit exceeded | ip=%s | path=%s | requests=%s | limit=%s | window=%ss",
                client_ip,
                path,
                current_count,
                effective_limit,
                self.window_seconds
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Demasiadas solicitudes. Intenta de nuevo más tarde.",
                    "retry_after_seconds": self.window_seconds
                },
                headers={
                    "Retry-After": str(self.window_seconds)
                }
            )

        return await call_next(request)

    def _cleanup_stale_entries(self, window_start: float) -> None:
        """Remove IPs with no requests in the current window (in-memory only)."""
        stale_ips = [
            ip for ip, timestamps in self._requests.items()
            if not timestamps or max(timestamps) < window_start
        ]
        for ip in stale_ips:
            del self._requests[ip]
