"""Feature enrichment tasks."""
import math
import time
from pathlib import Path
from datetime import datetime
from loguru import logger
from celery_app import app


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


@app.task(name="tasks.enrichment_tasks.enrich_batch", bind=True, max_retries=3, queue="enrichment")
def enrich_batch(self, comparable_ids: list):
    """Enrich a batch of comparables with amenity features."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        import pandas as pd
        from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        from supabase import create_client

        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

        # Fetch comparables
        result = (
            sb.table("iainmobiliaria_comparables")
            .select("id,lat,lon,city,state")
            .in_("id", comparable_ids)
            .execute()
        )
        if not result.data:
            return {"status": "no_data", "ids": comparable_ids}

        comparables = pd.DataFrame(result.data)

        # Fetch nearby amenities (within bounding box)
        min_lat = comparables["lat"].min() - 0.05
        max_lat = comparables["lat"].max() + 0.05
        min_lon = comparables["lon"].min() - 0.05
        max_lon = comparables["lon"].max() + 0.05

        amenities_result = (
            sb.table("iainmobiliaria_amenities")
            .select("id,name,amenity_type,lat,lon")
            .gte("lat", min_lat)
            .lte("lat", max_lat)
            .gte("lon", min_lon)
            .lte("lon", max_lon)
            .execute()
        )

        amenities_df = (
            pd.DataFrame(amenities_result.data)
            if amenities_result.data
            else pd.DataFrame()
        )

        enriched = 0
        for _, comp in comparables.iterrows():
            # Count amenities at different radii
            counts = {
                "comparable_id": comp["id"],
                "total_500m": 0,
                "total_1km": 0,
                "total_2km": 0,
                "schools_1km": 0,
                "hospitals_1km": 0,
                "parks_1km": 0,
                "transport_1km": 0,
                "restaurants_1km": 0,
                "computed_at": datetime.now().isoformat(),
            }

            for _, am in amenities_df.iterrows():
                d = haversine_km(comp["lat"], comp["lon"], am["lat"], am["lon"])
                if d <= 0.5:
                    counts["total_500m"] += 1
                if d <= 1.0:
                    counts["total_1km"] += 1
                    t = str(am.get("amenity_type", "")).lower()
                    if "school" in t:
                        counts["schools_1km"] += 1
                    elif "hospital" in t or "clinic" in t:
                        counts["hospitals_1km"] += 1
                    elif "park" in t:
                        counts["parks_1km"] += 1
                    elif "bus" in t or "station" in t:
                        counts["transport_1km"] += 1
                    elif "restaurant" in t:
                        counts["restaurants_1km"] += 1
                if d <= 2.0:
                    counts["total_2km"] += 1

            counts["walkability_score"] = min(
                100, counts["total_500m"] * 3 + counts["total_1km"]
            )
            enriched += 1

        return {"status": "success", "enriched": enriched}
    except Exception as exc:
        logger.error(f"[Celery] Enrichment failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(name="tasks.enrichment_tasks.enrich_all", queue="enrichment")
def enrich_all(batch_size=100, limit=5000):
    """Orchestrate enrichment of all comparables."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from celery import group
    from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
    from supabase import create_client

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    result = (
        sb.table("iainmobiliaria_comparables").select("id").limit(limit).execute()
    )

    if not result.data:
        return {"status": "no_data"}

    ids = [r["id"] for r in result.data]
    batches = [ids[i : i + batch_size] for i in range(0, len(ids), batch_size)]

    job = group(enrich_batch.s(batch) for batch in batches)
    result = job.apply_async()

    return {"status": "dispatched", "total_ids": len(ids), "batches": len(batches)}
