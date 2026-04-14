"""End-to-end pipeline tests — verify full request flows."""

import pytest


class TestPredictPipeline:
    """E2E: predict → verify response structure → check DB insert."""

    def test_full_predict_flow(self, api_client):
        response = api_client.post("/predictions/predict", json={
            "lat": 20.6597, "lon": -103.3496, "area_m2": 500,
            "city": "Guadalajara", "state": "Jalisco",
        })
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "predicted_price_m2" in data
        assert "predicted_total_price" in data
        assert "plusvalia_score" in data
        assert "growth_potential" in data
        assert "confidence" in data
        assert "model_version" in data
        assert "features_used" in data
        assert "prediction_id" in data
        assert "timestamp" in data

        # Verify values are reasonable
        assert data["predicted_price_m2"] > 0
        assert data["predicted_total_price"] > 0
        assert 0 <= data["plusvalia_score"] <= 100
        assert data["growth_potential"] in ("bajo", "medio", "alto", "muy_alto")
        assert 0 <= data["confidence"] <= 100

    def test_predict_without_save(self, api_client):
        response = api_client.post("/predictions/predict?save_to_db=false", json={
            "lat": 20.6597, "lon": -103.3496, "area_m2": 500,
            "city": "Guadalajara", "state": "Jalisco",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["prediction_id"] is None


class TestHeatmapPipeline:
    """E2E: heatmap endpoint → verify response format."""

    def test_heatmap_response_format(self, api_client):
        response = api_client.get("/predictions/heatmap")
        assert response.status_code == 200
        data = response.json()

        assert "points" in data
        assert "count" in data
        assert isinstance(data["points"], list)
        assert data["count"] >= 0

        if data["points"]:
            point = data["points"][0]
            assert len(point) == 3  # [lat, lon, intensity]
            assert isinstance(point[0], (int, float))
            assert isinstance(point[1], (int, float))
            assert 0 <= point[2] <= 1


class TestHealthPipeline:
    """E2E: health → verify all subsystems."""

    def test_health_all_subsystems(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "model_loaded" in data
        assert "model_version" in data
        assert "api_version" in data
        assert "timestamp" in data
