"""Tests for ml_model/bias_evaluator.py — Bias & fairness evaluation."""

import pytest
import numpy as np
import pandas as pd


@pytest.fixture
def sample_predictions():
    np.random.seed(42)
    n = 200
    cities = np.random.choice(["CDMX", "GDL", "MTY", "QRO"], n)
    actual = np.random.uniform(5000, 30000, n)
    predicted = actual * np.random.uniform(0.8, 1.2, n)
    return pd.DataFrame({
        "city": cities, "price_m2": actual, "predicted_price_m2": predicted,
        "area_m2": np.random.uniform(50, 500, n),
    })


class TestGeographicBias:
    def test_returns_dict_per_city(self, sample_predictions):
        from ml_model.bias_evaluator import BiasEvaluator
        evaluator = BiasEvaluator()
        result = evaluator.evaluate_geographic_bias(sample_predictions)
        assert isinstance(result, dict)
        assert "CDMX" in result

    def test_insufficient_data(self):
        from ml_model.bias_evaluator import BiasEvaluator
        evaluator = BiasEvaluator()
        small_df = pd.DataFrame({"city": ["A"], "price_m2": [100], "predicted_price_m2": [110]})
        result = evaluator.evaluate_geographic_bias(small_df)
        assert result["status"] == "insufficient_data"


class TestPriceRangeBias:
    def test_returns_brackets(self, sample_predictions):
        from ml_model.bias_evaluator import BiasEvaluator
        evaluator = BiasEvaluator()
        result = evaluator.evaluate_price_range_bias(sample_predictions)
        assert isinstance(result, dict)


class TestAreaBias:
    def test_returns_small_and_large(self, sample_predictions):
        from ml_model.bias_evaluator import BiasEvaluator
        evaluator = BiasEvaluator()
        result = evaluator.evaluate_area_bias(sample_predictions)
        assert "small_lots" in result
        assert "large_lots" in result


class TestFairnessScore:
    def test_perfect_fairness(self):
        from ml_model.bias_evaluator import BiasEvaluator
        evaluator = BiasEvaluator()
        score = evaluator.compute_fairness_score(
            {"A": 1.0, "B": 1.0}, {"low": 0.1, "high": 0.1}, {"small_lots": 0.1, "large_lots": 0.1}
        )
        assert score >= 90

    def test_biased_returns_low_score(self):
        from ml_model.bias_evaluator import BiasEvaluator
        evaluator = BiasEvaluator()
        score = evaluator.compute_fairness_score(
            {"A": 0.5, "B": 2.0}, {"low": 0.05, "high": 0.5}, {"small_lots": 0.05, "large_lots": 0.5}
        )
        assert score < 70


class TestFullEvaluation:
    def test_evaluate_returns_report(self, sample_predictions):
        from ml_model.bias_evaluator import BiasEvaluator
        evaluator = BiasEvaluator()
        report = evaluator.evaluate(sample_predictions)
        assert hasattr(report, "fairness_score")
        assert hasattr(report, "bias_detected")
        assert hasattr(report, "recommendations")
        assert 0 <= report.fairness_score <= 100
