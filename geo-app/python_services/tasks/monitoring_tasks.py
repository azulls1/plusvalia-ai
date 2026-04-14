"""Monitoring and maintenance tasks."""
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from celery_app import app


@app.task(name="tasks.monitoring_tasks.check_drift")
def check_drift():
    """Periodic drift detection check."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        import pandas as pd
        import redis as redis_lib
        from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        from supabase import create_client

        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        result = (
            sb.table("iainmobiliaria_predictions")
            .select("*")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )

        if not result.data or len(result.data) < 50:
            return {"status": "insufficient_data", "count": len(result.data or [])}

        from ml_model.monitoring.drift_detector import DriftDetector
        detector = DriftDetector()

        # Load baseline from Redis or file
        r = redis_lib.from_url("redis://localhost:6379/0")
        baseline = r.get("drift_baseline")
        if baseline:
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                f.write(baseline.decode())
                detector.load_baseline(f.name)
        else:
            baseline_path = (
                Path(__file__).parent.parent
                / "ml_model"
                / "monitoring"
                / "baseline_stats.json"
            )
            if baseline_path.exists():
                detector.load_baseline(str(baseline_path))
            else:
                return {"status": "no_baseline"}

        df = pd.DataFrame(result.data)
        report = detector.check_drift(df)

        # Store latest report in Redis
        report_data = {
            "severity": (
                str(report.severity) if hasattr(report, "severity") else "unknown"
            ),
            "checked_at": datetime.now().isoformat(),
            "n_records": len(df),
        }
        r.set("drift_report:latest", json.dumps(report_data), ex=86400)

        logger.info(f"[Celery] Drift check: severity={report_data['severity']}")
        return report_data
    except Exception as e:
        logger.error(f"[Celery] Drift check failed: {e}")
        return {"status": "error", "message": str(e)}


@app.task(name="tasks.monitoring_tasks.compute_baseline")
def compute_baseline():
    """Recompute drift baseline from current data."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        import pandas as pd
        import redis as redis_lib
        from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        from supabase import create_client
        from ml_model.monitoring.drift_detector import DriftDetector

        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        result = (
            sb.table("iainmobiliaria_predictions")
            .select("*")
            .limit(2000)
            .execute()
        )

        if not result.data or len(result.data) < 50:
            return {"status": "insufficient_data"}

        df = pd.DataFrame(result.data)
        detector = DriftDetector()
        detector.compute_baseline(df)

        # Save to file and Redis
        baseline_path = (
            Path(__file__).parent.parent
            / "ml_model"
            / "monitoring"
            / "baseline_stats.json"
        )
        detector.save_baseline(str(baseline_path))

        r = redis_lib.from_url("redis://localhost:6379/0")
        with open(baseline_path) as f:
            r.set("drift_baseline", f.read(), ex=86400 * 30)

        return {"status": "ok", "records": len(df)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.task(name="tasks.monitoring_tasks.cleanup_cache")
def cleanup_cache():
    """Clean expired cache entries from Redis."""
    try:
        import redis as redis_lib
        r = redis_lib.from_url("redis://localhost:6379/0")

        # Redis handles TTL automatically, but we can clean old drift reports
        keys = r.keys("drift_report:*")
        deleted = 0
        for key in keys:
            if key != b"drift_report:latest":
                ttl = r.ttl(key)
                if ttl == -1:  # No TTL set
                    r.expire(key, 86400 * 7)  # Set 7-day TTL
                    deleted += 1

        return {"status": "ok", "keys_updated": deleted}
    except Exception as e:
        return {"status": "error", "message": str(e)}
