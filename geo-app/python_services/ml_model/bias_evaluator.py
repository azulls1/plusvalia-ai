"""
Bias & Fairness Evaluator — Evaluates model predictions for geographic and economic bias.

Checks:
- Geographic bias: Predictions should not systematically favor/penalize specific regions
- Price range bias: Model accuracy should be consistent across price brackets
- Area bias: Model should perform equally well for small and large lots
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class BiasReport:
    """Report of bias evaluation results."""
    timestamp: str
    bias_detected: bool
    geographic_bias: Dict[str, float]
    price_range_bias: Dict[str, float]
    area_bias: Dict[str, float]
    fairness_score: float  # 0-100, higher is fairer
    recommendations: List[str]


class BiasEvaluator:
    """Evaluates ML model predictions for systematic bias."""

    # Maximum acceptable relative error difference between groups
    MAX_RELATIVE_ERROR_DIFF = 0.3  # 30%

    def evaluate_geographic_bias(
        self, df: pd.DataFrame, prediction_col: str = "predicted_price_m2",
        actual_col: str = "price_m2", group_col: str = "city"
    ) -> Dict[str, float]:
        """Check if prediction errors differ significantly across geographic regions."""
        if actual_col not in df.columns or prediction_col not in df.columns:
            return {"status": "insufficient_data"}

        df = df.dropna(subset=[prediction_col, actual_col, group_col])
        if len(df) < 20:
            return {"status": "insufficient_data"}

        df["abs_error"] = abs(df[prediction_col] - df[actual_col])
        df["rel_error"] = df["abs_error"] / df[actual_col].clip(lower=1)

        group_errors = df.groupby(group_col)["rel_error"].mean().to_dict()
        overall_error = df["rel_error"].mean()

        bias_scores = {}
        for group, error in group_errors.items():
            bias_scores[str(group)] = round(error / max(overall_error, 0.001), 3)

        return bias_scores

    def evaluate_price_range_bias(
        self, df: pd.DataFrame, prediction_col: str = "predicted_price_m2",
        actual_col: str = "price_m2"
    ) -> Dict[str, float]:
        """Check if model accuracy varies across price brackets."""
        if actual_col not in df.columns or prediction_col not in df.columns:
            return {"status": "insufficient_data"}

        df = df.dropna(subset=[prediction_col, actual_col])
        if len(df) < 20:
            return {"status": "insufficient_data"}

        df["abs_error"] = abs(df[prediction_col] - df[actual_col])
        df["rel_error"] = df["abs_error"] / df[actual_col].clip(lower=1)

        # Create price brackets
        brackets = pd.qcut(df[actual_col], q=4, labels=["low", "medium", "high", "premium"], duplicates="drop")
        df["bracket"] = brackets

        return df.groupby("bracket")["rel_error"].mean().round(4).to_dict()

    def evaluate_area_bias(
        self, df: pd.DataFrame, prediction_col: str = "predicted_price_m2",
        actual_col: str = "price_m2", area_col: str = "area_m2"
    ) -> Dict[str, float]:
        """Check if model accuracy varies by lot size."""
        required = [prediction_col, actual_col, area_col]
        if not all(c in df.columns for c in required):
            return {"status": "insufficient_data"}

        df = df.dropna(subset=required)
        if len(df) < 20:
            return {"status": "insufficient_data"}

        df["abs_error"] = abs(df[prediction_col] - df[actual_col])
        df["rel_error"] = df["abs_error"] / df[actual_col].clip(lower=1)

        median_area = df[area_col].median()
        small = df[df[area_col] <= median_area]["rel_error"].mean()
        large = df[df[area_col] > median_area]["rel_error"].mean()

        return {"small_lots": round(float(small), 4), "large_lots": round(float(large), 4)}

    def compute_fairness_score(
        self, geographic: Dict, price_range: Dict, area: Dict
    ) -> float:
        """Compute overall fairness score (0-100)."""
        scores = []

        # Geographic fairness
        if "status" not in geographic:
            values = list(geographic.values())
            if values:
                spread = max(values) - min(values)
                scores.append(max(0, 100 - spread * 100))

        # Price range fairness
        if "status" not in price_range:
            values = list(price_range.values())
            if values:
                spread = max(values) - min(values)
                scores.append(max(0, 100 - spread * 200))

        # Area fairness
        if "status" not in area:
            small = area.get("small_lots", 0)
            large = area.get("large_lots", 0)
            diff = abs(small - large)
            scores.append(max(0, 100 - diff * 200))

        return round(np.mean(scores), 1) if scores else 50.0

    def evaluate(self, df: pd.DataFrame) -> BiasReport:
        """Run full bias evaluation."""
        from datetime import datetime

        geo = self.evaluate_geographic_bias(df)
        price = self.evaluate_price_range_bias(df)
        area = self.evaluate_area_bias(df)
        fairness = self.compute_fairness_score(geo, price, area)

        recommendations = []
        if fairness < 70:
            recommendations.append("Model shows significant bias — consider rebalancing training data")
        if fairness < 85:
            recommendations.append("Review feature importance for proxy variables that correlate with protected attributes")
        if "status" in geo:
            recommendations.append("Need more data for geographic bias evaluation")

        return BiasReport(
            timestamp=datetime.now().isoformat(),
            bias_detected=fairness < 70,
            geographic_bias=geo,
            price_range_bias=price,
            area_bias=area,
            fairness_score=fairness,
            recommendations=recommendations if recommendations else ["Model passes fairness checks"],
        )
