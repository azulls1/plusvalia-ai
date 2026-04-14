"""Tests for integrations/inegi_client.py — INEGI API client."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def inegi_client(mock_env):
    """Create INEGIClient instance with mocked config."""
    with patch("integrations.inegi_client.INEGI_API_TOKEN", "test-token"):
        with patch("integrations.inegi_client.INEGI_BASE_URL", "https://fake-inegi.example.com/"):
            from integrations.inegi_client import INEGIClient
            return INEGIClient(api_token="test-token")


class TestStateCode:
    def test_queretaro(self, inegi_client):
        assert inegi_client.get_state_code("Querétaro") == "22"

    def test_cdmx(self, inegi_client):
        assert inegi_client.get_state_code("Ciudad de México") == "09"

    def test_jalisco(self, inegi_client):
        assert inegi_client.get_state_code("Jalisco") == "14"

    def test_unknown_state(self, inegi_client):
        assert inegi_client.get_state_code("Atlantida") is None

    def test_case_insensitive(self, inegi_client):
        assert inegi_client.get_state_code("querétaro") == "22"


class TestDistanceToCenter:
    def test_queretaro_center(self, inegi_client):
        """Distance from Querétaro center to itself should be ~0."""
        distance = inegi_client.get_distance_to_center(20.5888, -100.3899, "Querétaro")
        assert distance < 0.1  # less than 100m

    def test_known_distance(self, inegi_client):
        """Distance between known cities should be reasonable."""
        distance = inegi_client.get_distance_to_center(19.4326, -99.1332, "Guadalajara")
        assert 400 < distance < 600  # ~540km CDMX to GDL

    def test_unknown_city_returns_default(self, inegi_client):
        """Unknown city returns default 5.0 km."""
        distance = inegi_client.get_distance_to_center(20.0, -100.0, "CiudadInventada")
        assert distance == 5.0


class TestEnrichWithDemographics:
    def test_adds_columns(self, inegi_client):
        df = pd.DataFrame({"lat": [19.4], "lon": [-99.1], "city": ["CDMX"]})
        result = inegi_client.enrich_with_demographics(df)
        assert "population_density" in result.columns
        assert "economic_level" in result.columns
        assert "avg_schooling_years" in result.columns

    def test_preserves_original_data(self, inegi_client):
        df = pd.DataFrame({"lat": [19.4], "lon": [-99.1], "city": ["CDMX"]})
        result = inegi_client.enrich_with_demographics(df)
        assert result["city"].iloc[0] == "CDMX"


class TestEconomicLevel:
    def test_high_income_municipality(self, inegi_client):
        level = inegi_client._estimate_economic_level("22014")
        assert level == "alto"

    def test_default_municipality(self, inegi_client):
        level = inegi_client._estimate_economic_level("99999")
        assert level == "medio"


class TestFetchPopulationData:
    def test_api_error_returns_empty_df(self, inegi_client):
        """API failure returns empty DataFrame."""
        import requests
        with patch.object(inegi_client.session, "get", side_effect=requests.RequestException("Network error")):
            result = inegi_client.fetch_population_data("22")
            assert isinstance(result, pd.DataFrame)
            assert result.empty

    def test_successful_response(self, inegi_client):
        """Successful API response is parsed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Series": [{
                "INDICADOR": "1002000001",
                "REGION": "22",
                "OBSERVATIONS": [
                    {"TIME_PERIOD": "2020", "OBS_VALUE": "2368467"}
                ]
            }]
        }
        mock_response.raise_for_status = MagicMock()
        with patch.object(inegi_client.session, "get", return_value=mock_response):
            result = inegi_client.fetch_population_data("22")
            assert not result.empty
            assert "year" in result.columns


class TestLoadAgebs:
    """Tests for AGEB shapefile loading."""

    def test_no_geopandas_returns_empty(self, inegi_client):
        """Without geopandas, returns empty DataFrame."""
        import integrations.inegi_client as mod
        original = mod.HAS_GEOPANDAS
        mod.HAS_GEOPANDAS = False
        result = inegi_client.load_agebs_shapefile("/fake/path.shp")
        assert isinstance(result, pd.DataFrame)
        assert result.empty
        mod.HAS_GEOPANDAS = original


class TestFetchEconomicIndicators:
    def test_returns_dict(self, inegi_client):
        result = inegi_client.fetch_economic_indicators("22014")
        assert isinstance(result, dict)
        assert "municipality_code" in result
        assert result["municipality_code"] == "22014"

    def test_economic_level_included(self, inegi_client):
        result = inegi_client.fetch_economic_indicators("22014")
        assert "economic_level" in result
        assert result["economic_level"] == "alto"
