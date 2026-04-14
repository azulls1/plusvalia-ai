"""
Data pipeline scheduler for geo-app.
Orchestrates: scraping -> validation -> training -> deployment.
Can be run via cron or manually.
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, MODELS_DIR
from ml_model.predictor import PlusvaliaPredictorModel
from ml_model.data_validator import DataValidator


async def run_pipeline(steps: list[str] = None):
    """Run the data pipeline."""
    all_steps = ["validate", "train", "evaluate", "register"]
    steps = steps or all_steps

    logger.info(f"Starting data pipeline: {steps}")
    results = {}

    if "validate" in steps:
        logger.info("Step 1: Validating training data...")
        validator = DataValidator()
        # Find latest CSV
        csvs = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if csvs:
            import pandas as pd
            df = pd.read_csv(csvs[0])
            report = validator.validate(df)
            results["validation"] = {
                "file": csvs[0].name,
                "quality_score": report.quality_score,
                "rows": len(df),
                "issues": len(report.issues),
            }
            logger.info(f"Validation: quality={report.quality_score}, issues={len(report.issues)}")
        else:
            logger.warning("No CSV files found in data directory")
            results["validation"] = {"error": "No data files found"}

    if "train" in steps:
        logger.info("Step 2: Training model...")
        model = PlusvaliaPredictorModel()
        try:
            model.train()
            results["training"] = {"status": "success"}
        except Exception as e:
            results["training"] = {"status": "error", "message": str(e)}
            logger.error(f"Training failed: {e}")

    if "evaluate" in steps:
        logger.info("Step 3: Evaluating model...")
        metrics_files = sorted(MODELS_DIR.glob("*.metrics.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if metrics_files:
            import json
            with open(metrics_files[0]) as f:
                metrics = json.load(f)
            results["evaluation"] = metrics
            logger.info(f"Latest metrics: R2={metrics.get('r2_score', 'N/A')}, MAE={metrics.get('mae', 'N/A')}")
        else:
            results["evaluation"] = {"status": "no metrics found"}

    if "register" in steps:
        logger.info("Step 4: Registering model...")
        from ml_model.model_registry import ModelRegistry
        registry = ModelRegistry(str(MODELS_DIR))
        registry.save_registry()
        results["registry"] = registry.get_registry()

    logger.info(f"Pipeline complete: {results}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Data pipeline for geo-app")
    parser.add_argument("--steps", nargs="+", choices=["validate", "train", "evaluate", "register"], default=None)
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.steps))
