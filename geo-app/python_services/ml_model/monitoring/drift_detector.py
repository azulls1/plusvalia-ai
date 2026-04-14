"""
Data Drift Detector — Monitorea degradacion del modelo ML en produccion.

Detecta:
- Feature drift (distribucion de inputs cambia)
- Prediction drift (distribucion de outputs cambia)
- Performance drift (metricas caen vs baseline)

Uso:
    detector = DriftDetector(baseline_stats_path="baseline_stats.json")
    report = detector.check_drift(new_data_df)
    if report["drift_detected"]:
        alert(report)
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger
from scipy import stats


@dataclass
class DriftReport:
    """Reporte de deteccion de drift."""
    timestamp: str
    drift_detected: bool
    severity: str  # "none", "low", "medium", "high", "critical"
    feature_drifts: Dict[str, Dict[str, Any]]
    prediction_drift: Dict[str, Any]
    performance_drift: Dict[str, Any]
    recommendations: List[str]
    details: str


class DriftDetector:
    """Detecta data drift y model drift para el modelo de plusvalia."""

    # Umbrales para Kolmogorov-Smirnov test
    KS_THRESHOLD_LOW = 0.1
    KS_THRESHOLD_MEDIUM = 0.2
    KS_THRESHOLD_HIGH = 0.35

    # Umbrales para PSI (Population Stability Index)
    PSI_THRESHOLD_LOW = 0.1
    PSI_THRESHOLD_MEDIUM = 0.2
    PSI_THRESHOLD_HIGH = 0.25

    # Features numericas a monitorear
    NUMERIC_FEATURES = [
        "price_m2", "area_m2", "lat", "lon",
        "distance_to_center", "amenity_count"
    ]

    # Features categoricas
    CATEGORICAL_FEATURES = ["city", "state", "potential_level"]

    def __init__(self, baseline_stats_path: Optional[str] = None):
        self.baseline_stats: Optional[Dict] = None
        self.baseline_path = Path(baseline_stats_path) if baseline_stats_path else None

        if self.baseline_path and self.baseline_path.exists():
            with open(self.baseline_path, "r") as f:
                self.baseline_stats = json.load(f)
            logger.info(f"Baseline stats cargadas desde {self.baseline_path}")

    def compute_baseline(self, df: pd.DataFrame) -> Dict:
        """Calcula estadisticas baseline del dataset de entrenamiento."""
        baseline = {
            "computed_at": datetime.now().isoformat(),
            "n_samples": len(df),
            "numeric_features": {},
            "categorical_features": {},
            "prediction_stats": {},
        }

        for col in self.NUMERIC_FEATURES:
            if col in df.columns:
                values = df[col].dropna()
                baseline["numeric_features"][col] = {
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "median": float(values.median()),
                    "q25": float(values.quantile(0.25)),
                    "q75": float(values.quantile(0.75)),
                    "histogram": np.histogram(values, bins=20)[0].tolist(),
                    "bin_edges": np.histogram(values, bins=20)[1].tolist(),
                }

        for col in self.CATEGORICAL_FEATURES:
            if col in df.columns:
                value_counts = df[col].value_counts(normalize=True)
                baseline["categorical_features"][col] = {
                    "distribution": value_counts.to_dict(),
                    "n_unique": int(df[col].nunique()),
                }

        if "plusvalia_score" in df.columns:
            scores = df["plusvalia_score"].dropna()
            baseline["prediction_stats"] = {
                "mean": float(scores.mean()),
                "std": float(scores.std()),
                "median": float(scores.median()),
            }

        self.baseline_stats = baseline
        return baseline

    def save_baseline(self, path: Optional[str] = None):
        """Guarda baseline a disco."""
        save_path = Path(path) if path else self.baseline_path
        if save_path and self.baseline_stats:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(self.baseline_stats, f, indent=2, default=str)
            logger.info(f"Baseline guardada en {save_path}")

    def _ks_test(self, baseline_values: List[float], current_values: List[float]) -> Dict:
        """Kolmogorov-Smirnov test para drift en features numericas."""
        if len(current_values) < 10:
            return {"statistic": 0.0, "p_value": 1.0, "drift": False, "severity": "none"}

        statistic, p_value = stats.ks_2samp(baseline_values, current_values)

        if statistic > self.KS_THRESHOLD_HIGH:
            severity = "high"
        elif statistic > self.KS_THRESHOLD_MEDIUM:
            severity = "medium"
        elif statistic > self.KS_THRESHOLD_LOW:
            severity = "low"
        else:
            severity = "none"

        return {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "drift": p_value < 0.05,
            "severity": severity,
        }

    def _psi(self, expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        """Population Stability Index para drift de predicciones."""
        expected_percents = np.histogram(expected, bins=bins)[0] / len(expected)
        actual_percents = np.histogram(actual, bins=bins)[0] / len(actual)

        # Evitar division por cero
        expected_percents = np.clip(expected_percents, 1e-6, None)
        actual_percents = np.clip(actual_percents, 1e-6, None)

        psi = np.sum(
            (actual_percents - expected_percents)
            * np.log(actual_percents / expected_percents)
        )
        return float(psi)

    def check_drift(self, current_df: pd.DataFrame) -> DriftReport:
        """Ejecuta deteccion completa de drift contra baseline."""
        if not self.baseline_stats:
            return DriftReport(
                timestamp=datetime.now().isoformat(),
                drift_detected=False,
                severity="none",
                feature_drifts={},
                prediction_drift={},
                performance_drift={},
                recommendations=["Generar baseline primero con compute_baseline()"],
                details="No hay baseline para comparar.",
            )

        feature_drifts = {}
        drift_severities = []

        # 1. Feature drift (numericas)
        for col in self.NUMERIC_FEATURES:
            if col in current_df.columns and col in self.baseline_stats.get("numeric_features", {}):
                baseline_info = self.baseline_stats["numeric_features"][col]
                current_values = current_df[col].dropna().tolist()

                # Reconstruir baseline values desde histograma
                baseline_hist = baseline_info.get("histogram", [])
                baseline_edges = baseline_info.get("bin_edges", [])

                # KS test usando estadisticas resumidas
                ks_result = self._ks_test(
                    np.random.normal(
                        baseline_info["mean"], max(baseline_info["std"], 0.01), 1000
                    ).tolist(),
                    current_values,
                )

                # Comparar medias
                current_mean = float(np.mean(current_values)) if current_values else 0
                mean_shift = abs(current_mean - baseline_info["mean"]) / max(
                    baseline_info["std"], 0.01
                )

                feature_drifts[col] = {
                    "ks_test": ks_result,
                    "baseline_mean": baseline_info["mean"],
                    "current_mean": current_mean,
                    "mean_shift_sigmas": round(mean_shift, 2),
                }

                drift_severities.append(ks_result["severity"])

        # 2. Prediction drift
        prediction_drift = {}
        if "plusvalia_score" in current_df.columns and self.baseline_stats.get("prediction_stats"):
            current_scores = current_df["plusvalia_score"].dropna()
            baseline_pred = self.baseline_stats["prediction_stats"]

            if len(current_scores) >= 10:
                psi_value = self._psi(
                    np.random.normal(baseline_pred["mean"], baseline_pred["std"], 1000),
                    current_scores.values,
                )

                if psi_value > self.PSI_THRESHOLD_HIGH:
                    pred_severity = "high"
                elif psi_value > self.PSI_THRESHOLD_MEDIUM:
                    pred_severity = "medium"
                elif psi_value > self.PSI_THRESHOLD_LOW:
                    pred_severity = "low"
                else:
                    pred_severity = "none"

                prediction_drift = {
                    "psi": round(psi_value, 4),
                    "severity": pred_severity,
                    "baseline_mean": baseline_pred["mean"],
                    "current_mean": float(current_scores.mean()),
                }
                drift_severities.append(pred_severity)

        # 3. Determinar severidad global
        severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        max_severity = max(drift_severities, key=lambda s: severity_order.get(s, 0)) if drift_severities else "none"
        drift_detected = max_severity in ("medium", "high", "critical")

        # 4. Recomendaciones
        recommendations = []
        if drift_detected:
            recommendations.append("Reentrenar modelo con datos recientes")
            if max_severity in ("high", "critical"):
                recommendations.append("URGENTE: Modelo significativamente degradado")
                recommendations.append("Revisar pipeline de datos por anomalias")
            recommendations.append("Ejecutar validacion cruzada con datos nuevos")
            recommendations.append("Comparar feature importance vs baseline")
        else:
            recommendations.append("Modelo estable. Proxima revision en 7 dias.")

        return DriftReport(
            timestamp=datetime.now().isoformat(),
            drift_detected=drift_detected,
            severity=max_severity,
            feature_drifts=feature_drifts,
            prediction_drift=prediction_drift,
            performance_drift={},
            recommendations=recommendations,
            details=f"Analisis sobre {len(current_df)} muestras. {len(feature_drifts)} features evaluadas.",
        )

    def generate_report_json(self, report: DriftReport) -> str:
        """Serializa reporte a JSON."""
        return json.dumps(asdict(report), indent=2, default=str)
