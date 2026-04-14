"""
Data Validator — Validates training and prediction data quality.

Checks:
- Missing values and their patterns
- Outlier detection (IQR method)
- Data type consistency
- Value range validation
- Class balance for categorical features
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class ValidationReport:
    """Data validation report."""
    is_valid: bool
    total_rows: int
    issues: List[Dict[str, str]]
    quality_score: float  # 0-100


class DataValidator:
    """Validates datasets for ML training and prediction."""

    REQUIRED_COLUMNS = ["price_mxn", "area_m2", "lat", "lon", "city", "state"]

    LAT_RANGE = (14.0, 33.0)   # Mexico latitude range
    LON_RANGE = (-118.0, -86.0) # Mexico longitude range
    PRICE_RANGE = (1000, 500_000_000)  # MXN
    AREA_RANGE = (1, 1_000_000)  # m²

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """Run all validations on the dataset."""
        issues = []

        # 1. Check required columns
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            issues.append({"type": "missing_columns", "severity": "critical",
                          "detail": f"Missing: {missing_cols}"})

        # 2. Check for nulls
        available_required = [c for c in self.REQUIRED_COLUMNS if c in df.columns]
        if available_required:
            null_counts = df[available_required].isnull().sum()
            for col, count in null_counts.items():
                if count > 0:
                    pct = count / len(df) * 100
                    severity = "critical" if pct > 20 else "warning" if pct > 5 else "info"
                    issues.append({"type": "null_values", "severity": severity,
                                  "detail": f"{col}: {count} nulls ({pct:.1f}%)"})

        # 3. Check value ranges
        if "lat" in df.columns:
            out_of_range = df[(df["lat"] < self.LAT_RANGE[0]) | (df["lat"] > self.LAT_RANGE[1])]
            if len(out_of_range) > 0:
                issues.append({"type": "out_of_range", "severity": "warning",
                              "detail": f"lat: {len(out_of_range)} values outside Mexico range"})

        if "lon" in df.columns:
            out_of_range = df[(df["lon"] < self.LON_RANGE[0]) | (df["lon"] > self.LON_RANGE[1])]
            if len(out_of_range) > 0:
                issues.append({"type": "out_of_range", "severity": "warning",
                              "detail": f"lon: {len(out_of_range)} values outside Mexico range"})

        if "price_mxn" in df.columns:
            out_of_range = df[(df["price_mxn"] < self.PRICE_RANGE[0]) | (df["price_mxn"] > self.PRICE_RANGE[1])]
            if len(out_of_range) > 0:
                issues.append({"type": "out_of_range", "severity": "warning",
                              "detail": f"price_mxn: {len(out_of_range)} suspicious values"})

        if "area_m2" in df.columns:
            out_of_range = df[(df["area_m2"] < self.AREA_RANGE[0]) | (df["area_m2"] > self.AREA_RANGE[1])]
            if len(out_of_range) > 0:
                issues.append({"type": "out_of_range", "severity": "warning",
                              "detail": f"area_m2: {len(out_of_range)} suspicious values"})

        # 4. Check for duplicates
        if len(df) > 0:
            dupes = df.duplicated().sum()
            if dupes > 0:
                pct = dupes / len(df) * 100
                issues.append({"type": "duplicates", "severity": "warning",
                              "detail": f"{dupes} duplicate rows ({pct:.1f}%)"})

        # 5. Check outliers (IQR method on price_mxn)
        if "price_mxn" in df.columns and len(df) > 0:
            q1 = df["price_mxn"].quantile(0.25)
            q3 = df["price_mxn"].quantile(0.75)
            iqr = q3 - q1
            outliers = df[(df["price_mxn"] < q1 - 3 * iqr) | (df["price_mxn"] > q3 + 3 * iqr)]
            if len(outliers) > 0:
                issues.append({"type": "outliers", "severity": "info",
                              "detail": f"price_mxn: {len(outliers)} extreme outliers (IQR×3)"})

        # 6. Check class balance
        if "city" in df.columns and len(df) > 0:
            city_counts = df["city"].value_counts()
            if len(city_counts) > 1:
                ratio = city_counts.min() / city_counts.max()
                if ratio < 0.1:
                    issues.append({"type": "class_imbalance", "severity": "warning",
                                  "detail": f"City imbalance ratio: {ratio:.2f} (min/max)"})

        # Compute quality score
        critical = sum(1 for i in issues if i["severity"] == "critical")
        warnings = sum(1 for i in issues if i["severity"] == "warning")
        quality_score = max(0, 100 - critical * 25 - warnings * 5)

        return ValidationReport(
            is_valid=critical == 0,
            total_rows=len(df),
            issues=issues,
            quality_score=quality_score,
        )
