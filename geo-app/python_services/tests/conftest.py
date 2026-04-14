"""
Configuracion global de pytest para python_services.

Sets up environment variables BEFORE any config import happens.
"""

import os
import sys

# ---- Set env vars BEFORE any project module is imported ----
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key-for-testing")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:4200")
os.environ.setdefault("MAX_REQUESTS_PER_HOUR", "100")
os.environ.setdefault("INEGI_API_TOKEN", "test-inegi-token")

# Agregar directorios al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml_model"))

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_env(monkeypatch):
    """Variables de entorno mock para tests."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key-for-testing")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:4200")
    monkeypatch.setenv("MAX_REQUESTS_PER_HOUR", "100")


@pytest.fixture
def sample_comparable():
    """Comparable inmobiliario de ejemplo."""
    return {
        "title": "Terreno en Col. Roma",
        "price_mxn": 3500000.0,
        "area_m2": 200.0,
        "lat": 19.4156,
        "lon": -99.1617,
        "city": "Ciudad de México",
        "state": "CDMX",
        "address": "Col. Roma Norte",
    }


def _make_mock_model():
    """Create a standard mock ML model."""
    mock_model = MagicMock()
    mock_model.price_model = MagicMock()
    mock_model.model_version = "1.0"
    mock_model.predict_price.return_value = {
        "predicted_price_m2": 15000.0,
        "predicted_total_price": 7500000.0,
        "plusvalia_score": 72.5,
        "growth_potential": "alto",
        "confidence": 85.0,
        "model_version": "1.0",
        "features_used": {
            "area_m2": 500,
            "distance_to_center": 5.0,
            "city": "Querétaro",
            "state": "Querétaro",
        },
    }
    return mock_model


def _make_mock_supabase():
    """Create a standard mock Supabase client."""
    mock_sb = MagicMock()

    # Mock insert result
    mock_insert_result = MagicMock()
    mock_insert_result.data = [{"id": 42}]
    mock_sb.table.return_value.insert.return_value.execute.return_value = mock_insert_result

    # Mock select result (for various query chains)
    mock_select_result = MagicMock()
    mock_select_result.data = [
        {
            "id": 1,
            "lat": 20.5,
            "lon": -100.3,
            "plusvalia_score": 70,
            "city": "Querétaro",
            "state": "Querétaro",
            "predicted_price_m2": 15000,
            "growth_potential": "alto",
        },
    ]

    # Support all query chain patterns
    t = mock_sb.table.return_value
    s = t.select.return_value
    s.execute.return_value = mock_select_result
    s.limit.return_value.execute.return_value = mock_select_result
    s.order.return_value.limit.return_value.execute.return_value = mock_select_result
    s.eq.return_value.execute.return_value = mock_select_result
    s.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_select_result
    s.eq.return_value.gte.return_value.limit.return_value.execute.return_value = mock_select_result
    s.gte.return_value.limit.return_value.execute.return_value = mock_select_result

    return mock_sb


@pytest.fixture
def mock_model():
    """Fixture providing a mock ML model."""
    return _make_mock_model()


@pytest.fixture
def mock_supabase():
    """Fixture providing a mock Supabase client."""
    return _make_mock_supabase()


@pytest.fixture
def api_client(mock_model, mock_supabase):
    """FastAPI TestClient with mocked deps — use for all API tests."""
    import api.deps as deps_module

    # Replace the lazy proxies with our mocks
    original_model = deps_module.model
    original_supabase = deps_module.supabase
    deps_module.model = mock_model
    deps_module.supabase = mock_supabase

    # Also patch the router-level references (they import from deps at module load)
    patches = [
        patch("api.routers.predictions.model", mock_model),
        patch("api.routers.predictions.supabase", mock_supabase),
        patch("api.routers.stats.model", mock_model),
        patch("api.routers.stats.supabase", mock_supabase),
        patch("api.routers.training.model", mock_model),
        patch("api.routers.training.supabase", mock_supabase),
    ]
    for p in patches:
        p.start()

    from api.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    yield client

    for p in patches:
        p.stop()
    deps_module.model = original_model
    deps_module.supabase = original_supabase
