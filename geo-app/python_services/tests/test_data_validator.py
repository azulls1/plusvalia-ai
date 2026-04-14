"""Tests for ml_model/data_validator.py — Data quality validation."""

import pytest
import numpy as np
import pandas as pd


@pytest.fixture
def valid_dataset():
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "price_mxn": np.random.uniform(500000, 5000000, n),
        "area_m2": np.random.uniform(50, 500, n),
        "lat": np.random.uniform(19.0, 21.0, n),
        "lon": np.random.uniform(-104.0, -99.0, n),
        "city": np.random.choice(["CDMX", "GDL", "MTY"], n),
        "state": np.random.choice(["CDMX", "Jalisco", "NL"], n),
    })


class TestDataValidation:
    def test_valid_data_passes(self, valid_dataset):
        from ml_model.data_validator import DataValidator
        validator = DataValidator()
        report = validator.validate(valid_dataset)
        assert report.is_valid is True
        assert report.quality_score >= 80

    def test_missing_columns_detected(self):
        from ml_model.data_validator import DataValidator
        validator = DataValidator()
        df = pd.DataFrame({"price_mxn": [100], "area_m2": [50]})
        report = validator.validate(df)
        assert report.is_valid is False
        assert any(i["type"] == "missing_columns" for i in report.issues)

    def test_null_values_detected(self, valid_dataset):
        from ml_model.data_validator import DataValidator
        validator = DataValidator()
        df = valid_dataset.copy()
        df.loc[0:20, "price_mxn"] = None
        report = validator.validate(df)
        assert any(i["type"] == "null_values" for i in report.issues)

    def test_out_of_range_lat(self, valid_dataset):
        from ml_model.data_validator import DataValidator
        validator = DataValidator()
        df = valid_dataset.copy()
        df.loc[0, "lat"] = 90.0  # Outside Mexico
        report = validator.validate(df)
        assert any(i["type"] == "out_of_range" for i in report.issues)

    def test_duplicates_detected(self, valid_dataset):
        from ml_model.data_validator import DataValidator
        validator = DataValidator()
        df = pd.concat([valid_dataset, valid_dataset.head(10)])
        report = validator.validate(df)
        assert any(i["type"] == "duplicates" for i in report.issues)

    def test_quality_score_range(self, valid_dataset):
        from ml_model.data_validator import DataValidator
        validator = DataValidator()
        report = validator.validate(valid_dataset)
        assert 0 <= report.quality_score <= 100

    def test_empty_dataframe(self):
        from ml_model.data_validator import DataValidator
        validator = DataValidator()
        df = pd.DataFrame()
        report = validator.validate(df)
        assert report.is_valid is False
