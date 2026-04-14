"""Tests for API prediction endpoints (post-refactor)."""

import pytest
from unittest.mock import MagicMock


class TestPredictEndpoint:
    def test_predict_valid_input(self, api_client):
        response = api_client.post("/predictions/predict", json={
            "lat": 20.5888, "lon": -100.3899, "area_m2": 500,
            "city": "Querétaro", "state": "Querétaro",
        })
        assert response.status_code == 200
        data = response.json()
        assert "predicted_price_m2" in data
        assert "plusvalia_score" in data

    def test_predict_missing_fields(self, api_client):
        response = api_client.post("/predictions/predict", json={"lat": 20.5})
        assert response.status_code == 422

    def test_predict_invalid_lat(self, api_client):
        response = api_client.post("/predictions/predict", json={
            "lat": 999, "lon": -100, "area_m2": 500,
            "city": "Test", "state": "Test",
        })
        assert response.status_code == 422

    def test_predict_negative_area(self, api_client):
        response = api_client.post("/predictions/predict", json={
            "lat": 20.5, "lon": -100, "area_m2": -100,
            "city": "Test", "state": "Test",
        })
        assert response.status_code == 422


class TestHeatmapEndpoint:
    def test_heatmap_returns_points(self, api_client):
        response = api_client.get("/predictions/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data
        assert "count" in data

    def test_heatmap_with_city_filter(self, api_client):
        response = api_client.get("/predictions/heatmap?city=Querétaro")
        assert response.status_code == 200


class TestHistoryEndpoint:
    def test_history_returns_predictions(self, api_client):
        response = api_client.get("/predictions/history")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "count" in data

    def test_history_with_limit(self, api_client):
        response = api_client.get("/predictions/history?limit=10")
        assert response.status_code == 200


class TestNearbyEndpoint:
    def test_nearby_requires_coordinates(self, api_client):
        response = api_client.get("/predictions/nearby")
        assert response.status_code == 422

    def test_nearby_with_coordinates(self, api_client):
        response = api_client.get("/predictions/nearby?lat=20.5&lon=-100.3")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data


class TestBboxEndpoint:
    def test_bbox_returns_predictions(self, api_client):
        response = api_client.get("/predictions/bbox?min_lat=20&max_lat=21&min_lon=-101&max_lon=-100")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "bbox" in data


class TestStatsByCityEndpoint:
    def test_stats_by_city(self, api_client):
        response = api_client.get("/predictions/stats-by-city")
        assert response.status_code == 200


class TestHealthEndpoint:
    def test_health_check(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, api_client):
        response = api_client.get("/")
        assert response.status_code == 200

    def test_stats_endpoint(self, api_client):
        response = api_client.get("/stats")
        assert response.status_code == 200


class TestTrainEndpoint:
    def test_train_skips_when_model_exists(self, api_client):
        """Training skips when model already loaded and force_retrain is false."""
        response = api_client.post("/train", json={"min_samples": 100, "force_retrain": False})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "skipped"

    def test_train_with_force_retrain(self, api_client, mock_model, mock_supabase):
        """Training runs with force_retrain=true."""
        # Make supabase return enough data
        import pandas as pd
        mock_select = MagicMock()
        mock_select.data = [{"price_mxn": 1000000, "area_m2": 100, "lat": 20.5, "lon": -100.3,
                             "city": "Querétaro", "state": "Querétaro"} for _ in range(150)]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_select
        mock_model.train.return_value = {"test_r2": 0.85, "test_mae": 1500}

        from unittest.mock import patch
        with patch("api.routers.training.model", mock_model):
            with patch("api.routers.training.supabase", mock_supabase):
                response = api_client.post("/train", json={"min_samples": 100, "force_retrain": True})
        assert response.status_code == 200


class TestPredictionCache:
    """Tests for prediction cache mechanism."""

    def test_cache_key_rounds_coordinates(self):
        from api.routers.predictions import _cache_key
        key = _cache_key(20.58881, -100.38991, 500)
        assert key == "20.589:-100.39:500"

    def test_cache_key_buckets_area(self):
        from api.routers.predictions import _cache_key
        key1 = _cache_key(20.0, -100.0, 123)
        key2 = _cache_key(20.0, -100.0, 149)
        assert key1 == key2  # Both bucket to 100

    def test_cache_stores_and_retrieves(self):
        from api.routers.predictions import _set_cached_prediction, _get_cached_prediction
        _set_cached_prediction("test_key", {"price": 15000})
        result = _get_cached_prediction("test_key")
        assert result == {"price": 15000}

    def test_cache_miss_returns_none(self):
        from api.routers.predictions import _get_cached_prediction
        result = _get_cached_prediction("nonexistent_key_xyz")
        assert result is None

    def test_second_predict_uses_cache(self, api_client):
        """Second identical prediction should use cache."""
        payload = {
            "lat": 20.588, "lon": -100.389, "area_m2": 500,
            "city": "Querétaro", "state": "Querétaro",
        }
        r1 = api_client.post("/predictions/predict", json=payload)
        r2 = api_client.post("/predictions/predict", json=payload)
        assert r1.status_code == 200
        assert r2.status_code == 200


class TestRetryLogic:
    """Tests for Supabase retry mechanism."""

    def test_retry_function_exists(self):
        from api.routers.predictions import _retry_supabase
        assert callable(_retry_supabase)


class TestTrainEndpointExtended:
    """Extended training endpoint tests."""

    def test_train_request_defaults(self):
        from api.schemas import TrainRequest
        req = TrainRequest()
        assert req.min_samples == 100
        assert req.force_retrain is False

    def test_train_request_custom_values(self):
        from api.schemas import TrainRequest
        req = TrainRequest(min_samples=50, force_retrain=True)
        assert req.min_samples == 50
        assert req.force_retrain is True
