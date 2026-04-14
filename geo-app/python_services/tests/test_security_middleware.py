"""Tests for middleware/security.py — security headers, rate limit, size limit."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from middleware.security import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    ContentTypeValidationMiddleware,
    RateLimitMiddleware,
    generate_request_id,
)


def homepage(request):
    return PlainTextResponse("ok")


def create_app(*middlewares):
    app = Starlette(routes=[Route("/", homepage), Route("/post", homepage, methods=["POST"])])
    for mw_cls, kwargs in reversed(middlewares):
        app.add_middleware(mw_cls, **kwargs)
    return app


class TestGenerateRequestId:
    def test_returns_string(self):
        rid = generate_request_id()
        assert isinstance(rid, str)
        assert len(rid) == 36  # UUID format

    def test_unique_ids(self):
        ids = {generate_request_id() for _ in range(100)}
        assert len(ids) == 100


class TestSecurityHeadersMiddleware:
    @pytest.fixture
    def client(self):
        app = create_app((SecurityHeadersMiddleware, {}))
        return TestClient(app)

    def test_x_content_type_options(self, client):
        r = client.get("/")
        assert r.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options(self, client):
        r = client.get("/")
        assert r.headers["X-Frame-Options"] == "DENY"

    def test_strict_transport_security(self, client):
        r = client.get("/")
        assert "max-age=" in r.headers["Strict-Transport-Security"]

    def test_request_id_in_response(self, client):
        r = client.get("/")
        assert "X-Request-ID" in r.headers

    def test_server_header_removed(self, client):
        r = client.get("/")
        assert "Server" not in r.headers

    def test_cache_control(self, client):
        r = client.get("/")
        assert "no-store" in r.headers.get("Cache-Control", "")


class TestRequestSizeLimitMiddleware:
    @pytest.fixture
    def client(self):
        app = create_app((RequestSizeLimitMiddleware, {"max_body_size": 100}))
        return TestClient(app)

    def test_small_body_allowed(self, client):
        r = client.post("/post", content=b"small", headers={"Content-Length": "5"})
        assert r.status_code == 200

    def test_large_body_rejected(self, client):
        r = client.post("/post", content=b"x" * 200, headers={"Content-Length": "200"})
        assert r.status_code == 413

    def test_invalid_content_length(self, client):
        r = client.post("/post", content=b"x", headers={"Content-Length": "not-a-number"})
        assert r.status_code == 400


class TestContentTypeValidationMiddleware:
    @pytest.fixture
    def client(self):
        app = create_app((ContentTypeValidationMiddleware, {}))
        return TestClient(app)

    def test_json_allowed(self, client):
        r = client.post("/post", content=b'{"a":1}', headers={"Content-Type": "application/json"})
        assert r.status_code == 200

    def test_unsupported_type_rejected(self, client):
        r = client.post("/post", content=b"data", headers={"Content-Type": "text/plain"})
        assert r.status_code == 415

    def test_get_without_content_type_ok(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_multipart_allowed(self, client):
        r = client.post(
            "/post",
            content=b"data",
            headers={"Content-Type": "multipart/form-data; boundary=abc"},
        )
        assert r.status_code == 200


class TestRateLimitMiddleware:
    def test_under_limit_passes(self):
        app = create_app((RateLimitMiddleware, {"max_requests": 5, "window_seconds": 60}))
        client = TestClient(app)
        for _ in range(5):
            r = client.get("/")
            assert r.status_code == 200

    def test_over_limit_returns_429(self):
        app = create_app((RateLimitMiddleware, {"max_requests": 3, "window_seconds": 60}))
        client = TestClient(app)
        for _ in range(3):
            client.get("/")
        r = client.get("/")
        assert r.status_code == 429

    def test_429_includes_retry_after(self):
        app = create_app((RateLimitMiddleware, {"max_requests": 1, "window_seconds": 30}))
        client = TestClient(app)
        client.get("/")
        r = client.get("/")
        assert r.headers.get("Retry-After") == "30"
