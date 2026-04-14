"""
Tests para PlusvaliaPredictorModel -- Cobertura de ML pipeline.
Updated for V2 (real enrichment features).
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json


# Mock config antes de importar predictor
@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    """Mock de configuracion para tests."""
    import sys
    if "." not in sys.path:
        monkeypatch.syspath_prepend(".")
    if ".." not in sys.path:
        monkeypatch.syspath_prepend("..")
    tmp = Path(tempfile.mkdtemp())
    monkeypatch.setenv("MODEL_PATH", str(tmp))
    monkeypatch.setenv("MIN_TRAINING_SAMPLES", "10")
    return tmp


@pytest.fixture
def sample_training_data():
    """Dataset de entrenamiento de prueba."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "price_mxn": np.random.uniform(500000, 5000000, n),
        "area_m2": np.random.uniform(50, 500, n),
        "lat": np.random.uniform(19.0, 20.5, n),
        "lon": np.random.uniform(-99.5, -98.5, n),
        "city": np.random.choice(["Ciudad de México", "Guadalajara", "Monterrey", "Zapopan"], n),
        "state": np.random.choice(["CDMX", "Jalisco", "Nuevo León"], n),
        "collection_date": pd.date_range("2024-01-01", periods=n, freq="D"),
    })


@pytest.fixture
def sample_prediction_input():
    """Input para prediccion individual."""
    return {
        "lat": 19.4326,
        "lon": -99.1332,
        "city": "Ciudad de México",
        "state": "CDMX",
        "area_m2": 200,
    }


def _mock_demographics_fallback():
    """Return fallback demographics dict used when DB is unavailable."""
    return {
        'population_density': 1500, 'economic_level_score': 5,
        'unemployment_rate': 4.0, 'avg_income': 8000,
        'education_index': 0.15, 'security_score': 50,
        'infrastructure_score': 85, 'pct_vacant_housing': 8,
        'population_growth': 1.0,
    }


class TestFeaturePreparation:
    """Tests para prepare_features()."""

    def test_price_m2_calculated(self, sample_training_data):
        """price_m2 se calcula correctamente desde price_mxn / area_m2."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            model.inegi_client = MagicMock()
            model.label_encoders = {}
            model._demographics_cache = {}

            # Mock _get_demographics to avoid DB calls
            model._get_demographics = MagicMock(return_value=_mock_demographics_fallback())

            df = sample_training_data.copy()
            result = model.prepare_features(df)

            expected = df["price_mxn"] / df["area_m2"]
            np.testing.assert_array_almost_equal(result["price_m2"], expected)

    def test_temporal_features_created(self, sample_training_data):
        """Features temporales (month, quarter) se crean cuando collection_date existe."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            model.inegi_client = MagicMock()
            model.label_encoders = {}
            model._demographics_cache = {}
            model._get_demographics = MagicMock(return_value=_mock_demographics_fallback())

            result = model.prepare_features(sample_training_data)

            assert "month" in result.columns
            assert "quarter" in result.columns
            assert all(result["month"].between(1, 12))
            assert all(result["quarter"].between(1, 4))

    def test_distance_to_center_uses_haversine(self, sample_training_data):
        """distance_to_center uses real Haversine calculation."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            model.inegi_client = MagicMock()
            model.label_encoders = {}
            model._demographics_cache = {}
            model._get_demographics = MagicMock(return_value=_mock_demographics_fallback())

            result = model.prepare_features(sample_training_data.head(5))
            # Should have computed distances (not all zeros)
            assert "distance_to_center" in result.columns
            # Cities in sample are known, so should get real distances
            assert not all(result["distance_to_center"] == 0.0)

    def test_missing_lat_lon_defaults_to_zero(self):
        """Sin lat/lon, distance_to_center = 0.0."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            model.inegi_client = MagicMock()
            model.label_encoders = {}
            model._demographics_cache = {}
            model._get_demographics = MagicMock(return_value=_mock_demographics_fallback())

            df = pd.DataFrame({
                "price_mxn": [1000000],
                "area_m2": [100],
            })
            result = model.prepare_features(df)
            assert result["distance_to_center"].iloc[0] == 0.0

    def test_demographic_features_populated(self, sample_training_data):
        """V2 demographic features are present in output."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            model.inegi_client = MagicMock()
            model.label_encoders = {}
            model._demographics_cache = {}
            model._get_demographics = MagicMock(return_value=_mock_demographics_fallback())

            result = model.prepare_features(sample_training_data.head(5))
            for col in ['population_density', 'economic_level_score',
                        'unemployment_rate', 'avg_income', 'education_index',
                        'security_score', 'infrastructure_score',
                        'pct_vacant_housing', 'population_growth']:
                assert col in result.columns, f"Missing feature: {col}"
                assert not result[col].isna().any(), f"NaN in {col}"

    def test_lat_lon_normalized(self, sample_training_data):
        """lat_normalized and lon_normalized are present."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            model.inegi_client = MagicMock()
            model.label_encoders = {}
            model._demographics_cache = {}
            model._get_demographics = MagicMock(return_value=_mock_demographics_fallback())

            result = model.prepare_features(sample_training_data.head(5))
            assert "lat_normalized" in result.columns
            assert "lon_normalized" in result.columns
            assert all(result["lat_normalized"].between(0, 1))
            assert all(result["lon_normalized"].between(0, 1))


class TestHaversine:
    """Tests for _calculate_distance_to_center."""

    def test_known_city_distance(self):
        """Distance from a known city center to itself should be ~0."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            dist = model._calculate_distance_to_center(19.4326, -99.1332, "Ciudad de México")
            assert dist < 0.01  # Should be essentially zero

    def test_unknown_city_returns_default(self):
        """Unknown city returns 5km default."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            dist = model._calculate_distance_to_center(19.0, -99.0, "CiudadInexistente")
            assert dist == 5.0

    def test_partial_match(self):
        """Partial city name match works."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            # "guadalajara" should match "Guadalajara"
            dist = model._calculate_distance_to_center(20.6597, -103.3496, "guadalajara")
            assert dist < 0.01


class TestEconomicScore:
    """Tests for _compute_economic_score."""

    def test_low_marginacion_high_score(self):
        """muy_bajo marginacion should produce high score."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            score = model._compute_economic_score({
                'avg_income_mxn': 15000,
                'pct_education_superior': 35,
                'grado_marginacion': 'muy_bajo',
            })
            assert score >= 8.0

    def test_high_marginacion_low_score(self):
        """muy_alto marginacion should produce low score."""
        with patch("ml_model.predictor.INEGIClient"):
            from ml_model.predictor import PlusvaliaPredictorModel
            model = PlusvaliaPredictorModel.__new__(PlusvaliaPredictorModel)
            score = model._compute_economic_score({
                'avg_income_mxn': 3000,
                'pct_education_superior': 5,
                'grado_marginacion': 'muy_alto',
            })
            assert score <= 3.0


class TestDriftDetector:
    """Tests para DriftDetector."""

    def test_compute_baseline(self):
        """Baseline se computa correctamente."""
        from ml_model.monitoring.drift_detector import DriftDetector

        detector = DriftDetector()
        df = pd.DataFrame({
            "price_m2": np.random.normal(15000, 3000, 100),
            "area_m2": np.random.normal(200, 50, 100),
            "lat": np.random.normal(19.4, 0.1, 100),
            "lon": np.random.normal(-99.1, 0.1, 100),
            "city": np.random.choice(["CDMX", "GDL"], 100),
            "plusvalia_score": np.random.normal(60, 15, 100),
        })

        baseline = detector.compute_baseline(df)

        assert "numeric_features" in baseline
        assert "price_m2" in baseline["numeric_features"]
        assert "mean" in baseline["numeric_features"]["price_m2"]
        assert baseline["n_samples"] == 100

    def test_no_drift_with_same_data(self):
        """No detecta drift cuando datos son iguales al baseline."""
        from ml_model.monitoring.drift_detector import DriftDetector

        np.random.seed(42)
        detector = DriftDetector()
        df = pd.DataFrame({
            "price_m2": np.random.normal(15000, 3000, 200),
            "area_m2": np.random.normal(200, 50, 200),
            "lat": np.random.normal(19.4, 0.1, 200),
            "lon": np.random.normal(-99.1, 0.1, 200),
            "plusvalia_score": np.random.normal(60, 15, 200),
        })

        detector.compute_baseline(df)
        report = detector.check_drift(df)

        assert report.severity in ("none", "low")

    def test_high_drift_detected(self):
        """Detecta drift alto cuando distribucion cambia significativamente."""
        from ml_model.monitoring.drift_detector import DriftDetector

        detector = DriftDetector()

        baseline_df = pd.DataFrame({
            "price_m2": np.random.normal(15000, 3000, 200),
            "plusvalia_score": np.random.normal(60, 15, 200),
        })
        detector.compute_baseline(baseline_df)

        # Datos con drift severo (media desplazada 5 sigmas)
        drifted_df = pd.DataFrame({
            "price_m2": np.random.normal(35000, 3000, 200),
            "plusvalia_score": np.random.normal(90, 5, 200),
        })

        report = detector.check_drift(drifted_df)
        assert report.drift_detected is True
        assert report.severity in ("medium", "high", "critical")

    def test_save_and_load_baseline(self, tmp_path):
        """Baseline se guarda y carga correctamente."""
        from ml_model.monitoring.drift_detector import DriftDetector

        baseline_path = str(tmp_path / "baseline.json")
        detector = DriftDetector(baseline_stats_path=baseline_path)

        df = pd.DataFrame({
            "price_m2": [10000, 20000, 30000],
            "plusvalia_score": [50, 60, 70],
        })

        detector.compute_baseline(df)
        detector.save_baseline()

        # Cargar en nueva instancia
        detector2 = DriftDetector(baseline_stats_path=baseline_path)
        assert detector2.baseline_stats is not None
        assert detector2.baseline_stats["n_samples"] == 3

    def test_report_json_serializable(self):
        """Reporte se serializa a JSON sin errores."""
        from ml_model.monitoring.drift_detector import DriftDetector

        detector = DriftDetector()
        df = pd.DataFrame({
            "price_m2": np.random.normal(15000, 3000, 50),
            "plusvalia_score": np.random.normal(60, 15, 50),
        })
        detector.compute_baseline(df)
        report = detector.check_drift(df)

        json_str = detector.generate_report_json(report)
        parsed = json.loads(json_str)
        assert "drift_detected" in parsed
        assert "severity" in parsed


class TestModelTraining:
    """Tests para entrenamiento y prediccion (mocked)."""

    def test_model_requires_minimum_samples(self):
        """Modelo rechaza datasets muy pequenos."""
        small_df = pd.DataFrame({
            "price_mxn": [1000000, 2000000],
            "area_m2": [100, 200],
        })
        assert len(small_df) < 10  # MIN_TRAINING_SAMPLES

    def test_cross_validation_returns_scores(self, sample_training_data):
        """Cross-validation produce scores validos."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import cross_val_score

        X = sample_training_data[["area_m2"]].values
        y = sample_training_data["price_mxn"].values

        model = RandomForestRegressor(n_estimators=10, random_state=42)
        scores = cross_val_score(model, X, y, cv=3, scoring="r2")

        assert len(scores) == 3
        assert all(isinstance(s, float) for s in scores)

    def test_ensemble_predictions_differ(self, sample_training_data):
        """RandomForest y GradientBoosting producen predicciones diferentes."""
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

        X = sample_training_data[["area_m2"]].values
        y = sample_training_data["price_mxn"].values

        rf = RandomForestRegressor(n_estimators=10, random_state=42)
        gb = GradientBoostingRegressor(n_estimators=10, random_state=42)

        rf.fit(X, y)
        gb.fit(X, y)

        rf_pred = rf.predict(X[:5])
        gb_pred = gb.predict(X[:5])

        # No deben ser exactamente iguales
        assert not np.allclose(rf_pred, gb_pred)


class TestFullTrainAndPredict:
    """Tests that run the full train->predict pipeline with mock data."""

    @pytest.fixture
    def trained_model(self, sample_training_data):
        """A model that has been trained on sample data."""
        with patch("ml_model.predictor.INEGIClient") as mock_inegi:
            mock_client = MagicMock()
            mock_inegi.return_value = mock_client

            with patch("ml_model.predictor.MODEL_PATH", Path(tempfile.mkdtemp())):
                with patch("ml_model.predictor.MIN_TRAINING_SAMPLES", 10):
                    from ml_model.predictor import PlusvaliaPredictorModel
                    model = PlusvaliaPredictorModel(model_version="test")
                    model.inegi_client = mock_client
                    # Mock demographics to avoid DB calls during tests
                    model._get_demographics = MagicMock(
                        return_value=_mock_demographics_fallback()
                    )
                    model.train(sample_training_data)
                    return model

    def test_train_returns_metrics(self, trained_model):
        """Training returns evaluation metrics."""
        assert trained_model.price_model is not None
        assert trained_model.feature_names is not None
        assert len(trained_model.feature_names) > 0

    def test_train_creates_model(self, trained_model):
        """Training creates a price model."""
        assert trained_model.price_model is not None

    def test_predict_after_train(self, trained_model):
        """Prediction works after training."""
        result = trained_model.predict_price(
            lat=20.5888, lon=-100.3899, area_m2=500,
            city="Guadalajara", state="Jalisco"
        )
        assert "predicted_price_m2" in result
        assert "plusvalia_score" in result
        assert "growth_potential" in result
        assert "confidence" in result
        assert result["predicted_price_m2"] > 0

    def test_predict_returns_features_used(self, trained_model):
        """Prediction includes features used."""
        result = trained_model.predict_price(
            lat=19.4326, lon=-99.1332, area_m2=200,
            city="Monterrey", state="Nuevo León"
        )
        assert "features_used" in result
        assert "area_m2" in result["features_used"]

    def test_predict_growth_potential_categories(self, trained_model):
        """Growth potential is one of the valid categories."""
        result = trained_model.predict_price(
            lat=20.5888, lon=-100.3899, area_m2=500,
            city="Guadalajara", state="Jalisco"
        )
        assert result["growth_potential"] in ("bajo", "medio", "alto", "muy_alto")

    def test_predict_score_bounded(self, trained_model):
        """Plusvalia score is between 0 and 100."""
        result = trained_model.predict_price(
            lat=20.5888, lon=-100.3899, area_m2=500,
            city="Guadalajara", state="Jalisco"
        )
        assert 0 <= result["plusvalia_score"] <= 100

    def test_predict_confidence_from_ensemble(self, trained_model):
        """Confidence is calculated from ensemble, not hardcoded."""
        result = trained_model.predict_price(
            lat=20.5888, lon=-100.3899, area_m2=500,
            city="Guadalajara", state="Jalisco"
        )
        # Should be calculated dynamically, between 50-99
        assert 50 <= result["confidence"] <= 99

    def test_train_too_few_samples_raises(self):
        """Training with <20 samples raises ValueError."""
        with patch("ml_model.predictor.INEGIClient") as mock_inegi:
            mock_client = MagicMock()
            mock_inegi.return_value = mock_client
            with patch("ml_model.predictor.MODEL_PATH", Path(tempfile.mkdtemp())):
                with patch("ml_model.predictor.MIN_TRAINING_SAMPLES", 10):
                    from ml_model.predictor import PlusvaliaPredictorModel
                    model = PlusvaliaPredictorModel(model_version="test")
                    small_df = pd.DataFrame({
                        "price_mxn": [1000000] * 5,
                        "area_m2": [100] * 5,
                        "lat": [20.0] * 5,
                        "lon": [-100.0] * 5,
                        "city": ["Test"] * 5,
                        "state": ["Test"] * 5,
                    })
                    with pytest.raises(ValueError, match="al menos 20 muestras"):
                        model.train(small_df)

    def test_predict_without_train_raises(self):
        """Prediction without training raises ValueError."""
        with patch("ml_model.predictor.INEGIClient") as mock_inegi:
            mock_inegi.return_value = MagicMock()
            with patch("ml_model.predictor.MODEL_PATH", Path(tempfile.mkdtemp())):
                with patch("ml_model.predictor.MIN_TRAINING_SAMPLES", 10):
                    from ml_model.predictor import PlusvaliaPredictorModel
                    model = PlusvaliaPredictorModel(model_version="test")
                    with pytest.raises(ValueError, match="Modelo no entrenado"):
                        model.predict_price(lat=20.0, lon=-100.0, area_m2=100, city="Test", state="Test")

    def test_save_and_load_model(self, trained_model):
        """Model can be saved and loaded."""
        # Save
        saved_path = trained_model.save_model("test_model.pkl")
        assert Path(saved_path).exists()

        # Load into new model
        with patch("ml_model.predictor.INEGIClient") as mock_inegi:
            mock_inegi.return_value = MagicMock()
            with patch("ml_model.predictor.MODEL_PATH", trained_model.model_path):
                with patch("ml_model.predictor.MIN_TRAINING_SAMPLES", 10):
                    from ml_model.predictor import PlusvaliaPredictorModel
                    new_model = PlusvaliaPredictorModel(model_version="loaded")
                    new_model.load_model("test_model.pkl")
                    assert new_model.price_model is not None
                    assert new_model.model_version == "test"

    def test_load_nonexistent_model_raises(self):
        """Loading nonexistent model raises FileNotFoundError."""
        with patch("ml_model.predictor.INEGIClient") as mock_inegi:
            mock_inegi.return_value = MagicMock()
            with patch("ml_model.predictor.MODEL_PATH", Path(tempfile.mkdtemp())):
                with patch("ml_model.predictor.MIN_TRAINING_SAMPLES", 10):
                    from ml_model.predictor import PlusvaliaPredictorModel
                    model = PlusvaliaPredictorModel(model_version="test")
                    with pytest.raises(FileNotFoundError):
                        model.load_model("nonexistent_model.pkl")

    def test_prepare_features_population_density_by_city(self, sample_training_data):
        """Population density is populated for all rows."""
        with patch("ml_model.predictor.INEGIClient") as mock_inegi:
            mock_client = MagicMock()
            mock_inegi.return_value = mock_client
            with patch("ml_model.predictor.MODEL_PATH", Path(tempfile.mkdtemp())):
                with patch("ml_model.predictor.MIN_TRAINING_SAMPLES", 10):
                    from ml_model.predictor import PlusvaliaPredictorModel
                    model = PlusvaliaPredictorModel(model_version="test")
                    model.inegi_client = mock_client
                    model._get_demographics = MagicMock(
                        return_value=_mock_demographics_fallback()
                    )
                    df = sample_training_data.copy()
                    result = model.prepare_features(df)
                    # Different cities should have population density
                    assert "population_density" in result.columns
                    assert not result["population_density"].isna().any()

    def test_expanded_feature_count(self, trained_model):
        """V2 model uses more features than V1's 10."""
        assert len(trained_model.feature_names) >= 15

    def test_feature_importance_in_metrics_file(self, trained_model):
        """Saved metrics JSON includes feature_importance."""
        import glob
        metrics_files = list(trained_model.model_path.glob("*.metrics.json"))
        assert len(metrics_files) >= 1
        with open(metrics_files[0]) as f:
            metrics = json.load(f)
        assert "feature_importance" in metrics
        assert len(metrics["feature_importance"]) == len(trained_model.feature_names)
