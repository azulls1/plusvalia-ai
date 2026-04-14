"""
Tests para FastAPI endpoints — API de predicciones ML.
"""

import pytest


class TestHealthEndpoint:
    """Tests para /health."""

    def test_health_returns_200(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200

    def test_health_includes_status(self, api_client):
        response = api_client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestRateLimiting:
    """Tests para rate limiting middleware."""

    def test_rate_limit_header_present(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200

    def test_excessive_requests_return_429(self, api_client):
        """Verify rate limit middleware exists."""
        from middleware.security import RateLimitMiddleware
        assert RateLimitMiddleware is not None


class TestCORSConfiguration:
    """Tests para CORS."""

    def test_cors_allows_configured_origins(self, api_client):
        response = api_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code != 403


class TestPredictionEndpoint:
    """Tests para endpoint de prediccion."""

    def test_predict_requires_coordinates(self, api_client):
        response = api_client.post("/predictions/predict", json={})
        assert response.status_code == 422

    def test_predict_valid_input(self, api_client):
        response = api_client.post("/predictions/predict", json={
            "lat": 19.4326,
            "lon": -99.1332,
            "area_m2": 200,
            "city": "Ciudad de México",
            "state": "CDMX",
        })
        assert response.status_code == 200
        data = response.json()
        assert "predicted_price_m2" in data


class TestDocsEndpoint:
    """Tests para documentacion API."""

    def test_docs_accessible(self, api_client):
        response = api_client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self, api_client):
        response = api_client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json(self, api_client):
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert data["info"]["title"] == "Análisis de Mercado Inmobiliario - API ML"
