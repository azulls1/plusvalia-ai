"""ML model training tasks."""
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from celery_app import app


@app.task(name="tasks.training_tasks.train_model", bind=True, max_retries=2, queue="ml")
def train_model(self, force_retrain=False):
    """Train or retrain the ML model. Returns metrics dict."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        logger.info(f"[Celery] Starting model training (force={force_retrain})")
        import pandas as pd
        from ml_model.predictor import PlusvaliaPredictorModel
        from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        from supabase import create_client

        # Fetch training data from Supabase
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        result = sb.table("iainmobiliaria_comparables").select("*").limit(50000).execute()

        if not result.data or len(result.data) < 50:
            return {"status": "error", "message": f"Insufficient data: {len(result.data or [])} records"}

        df = pd.DataFrame(result.data)
        df = df.dropna(subset=["lat", "lon", "price_mxn", "area_m2", "city", "state"])

        if "price_m2" not in df.columns:
            df["price_m2"] = df["price_mxn"] / df["area_m2"]

        df = df[(df["price_m2"] > 500) & (df["price_m2"] < 200000)]

        model = PlusvaliaPredictorModel()
        metrics = model.train(df=df, target_col="price_m2")

        logger.info(f"[Celery] Training complete: R²={metrics.get('r2_score', 'N/A')}")
        return {
            "status": "success",
            "trained_at": datetime.now().isoformat(),
            "records_used": len(df),
            **metrics
        }
    except Exception as exc:
        logger.error(f"[Celery] Training failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@app.task(name="tasks.training_tasks.generate_predictions", bind=True, queue="ml")
def generate_predictions(self, limit=5000):
    """Generate predictions for comparables and store in DB."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        import pandas as pd
        from ml_model.predictor import PlusvaliaPredictorModel
        from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        from supabase import create_client

        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        model = PlusvaliaPredictorModel()

        # Find latest model
        models_dir = Path(__file__).parent.parent / "ml_model" / "models"
        latest = sorted(models_dir.glob("plusvalia_model_v2*.pkl"))
        if not latest:
            latest = sorted(models_dir.glob("*.pkl"))
        if not latest:
            return {"status": "error", "message": "No model found"}

        model.load_model(latest[-1].name)

        # Fetch comparables
        result = sb.table("iainmobiliaria_comparables").select("lat,lon,area_m2,city,state").limit(limit).execute()
        df = pd.DataFrame(result.data)

        # Sample 3 per city
        sampled = df.groupby("city", group_keys=False).apply(
            lambda x: x.sample(min(len(x), 3), random_state=42)
        ).reset_index(drop=True)

        predictions = []
        for _, row in sampled.iterrows():
            try:
                r = model.predict_price(
                    lat=row["lat"],
                    lon=row["lon"],
                    area_m2=row["area_m2"],
                    city=str(row["city"]),
                    state=str(row["state"]),
                )
                if r and r.get("predicted_price_m2"):
                    predictions.append({
                        "lat": round(float(row["lat"]), 6),
                        "lon": round(float(row["lon"]), 6),
                        "city": str(row["city"])[:100],
                        "state": str(row["state"])[:100],
                        "predicted_price_m2": round(float(r["predicted_price_m2"]), 2),
                        "plusvalia_score": round(float(r.get("plusvalia_score", 50)), 1),
                        "growth_potential": str(r.get("growth_potential", "medio")),
                        "model_version": "v2.0_celery",
                        "model_confidence": round(float(r.get("confidence", 70)), 1),
                    })
            except Exception:
                pass

        # Upload
        if predictions:
            for i in range(0, len(predictions), 200):
                batch = predictions[i:i + 200]
                sb.table("iainmobiliaria_predictions").insert(batch).execute()

        return {"status": "success", "predictions_count": len(predictions)}
    except Exception as exc:
        logger.error(f"[Celery] Prediction generation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
