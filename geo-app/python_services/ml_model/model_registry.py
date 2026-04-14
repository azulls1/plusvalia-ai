"""
Simple file-based model registry for tracking model versions and metrics.
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger


@dataclass
class ModelVersion:
    version: str
    path: str
    created_at: str
    r2_score: float = 0.0
    mae: float = 0.0
    mse: float = 0.0
    n_samples: int = 0
    n_features: int = 0
    is_active: bool = False


class ModelRegistry:
    """Tracks all model versions and their metrics."""

    def __init__(self, models_dir: str = None):
        self.models_dir = Path(models_dir or "ml_model/models")
        self.registry_path = self.models_dir / "registry.json"

    def scan_models(self) -> list[ModelVersion]:
        """Scan model directory and build registry from .pkl + .metrics.json files."""
        versions = []

        for pkl_path in sorted(self.models_dir.glob("*.pkl")):
            metrics_path = pkl_path.with_suffix(".metrics.json")
            metrics = {}
            if metrics_path.exists():
                with open(metrics_path) as f:
                    metrics = json.load(f)

            version = ModelVersion(
                version=metrics.get("version", pkl_path.stem),
                path=str(pkl_path),
                created_at=metrics.get("trained_at", "unknown"),
                r2_score=metrics.get("r2_score", 0.0),
                mae=metrics.get("mae", 0.0),
                mse=metrics.get("mse", 0.0),
                n_samples=metrics.get("n_samples", 0),
                n_features=metrics.get("n_features", 0),
            )
            versions.append(version)

        return versions

    def get_best_model(self) -> ModelVersion | None:
        """Get model with highest R2 score."""
        versions = self.scan_models()
        if not versions:
            return None
        scored = [v for v in versions if v.r2_score > 0]
        if scored:
            return max(scored, key=lambda v: v.r2_score)
        return versions[-1]  # latest if no metrics

    def get_registry(self) -> dict:
        """Get full registry as dict."""
        versions = self.scan_models()
        return {
            "total_models": len(versions),
            "latest": asdict(versions[-1]) if versions else None,
            "best": asdict(self.get_best_model()) if versions else None,
            "versions": [asdict(v) for v in versions],
        }

    def save_registry(self):
        """Persist registry to JSON."""
        registry = self.get_registry()
        with open(self.registry_path, "w") as f:
            json.dump(registry, f, indent=2)
        logger.info(f"Registry saved with {registry['total_models']} models")
