"""
Feature Enrichment Pipeline for geo-app ML model.
Computes real features from existing data and stores in enrichment tables.

Usage:
    python scripts/enrich_features.py [--limit 1000] [--city "Guadalajara"]
"""
import sys
import math
import time
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import pandas as pd
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client

# ==================== CONSTANTS ====================

# City center coordinates for distance calculation
CITY_CENTERS = {
    "Ciudad de México": (19.4326, -99.1332),
    "Guadalajara": (20.6597, -103.3496),
    "Monterrey": (25.6866, -100.3161),
    "Puebla": (19.0414, -98.2063),
    "Querétaro": (20.5888, -100.3899),
    "Mérida": (20.9674, -89.5926),
    "Cancún": (21.1619, -86.8515),
    "Tijuana": (32.5149, -117.0382),
    "León": (21.1221, -101.6839),
    "Aguascalientes": (21.8818, -102.2916),
    "San Luis Potosí": (22.1565, -100.9855),
    "Chihuahua": (28.6353, -106.0889),
    "Morelia": (19.7060, -101.1950),
    "Hermosillo": (29.0729, -110.9559),
    "Saltillo": (25.4232, -100.9924),
    "Villahermosa": (17.9894, -92.9475),
    "Tuxtla Gutiérrez": (16.7516, -93.1152),
    "Oaxaca": (17.0732, -96.7266),
    "Veracruz": (19.1738, -96.1342),
    "Toluca": (19.2826, -99.6557),
    "Cuernavaca": (18.9242, -99.2216),
    "Pachuca": (20.1011, -98.7591),
    "Playa del Carmen": (20.6296, -87.0739),
    "Tulum": (20.2114, -87.4654),
    "Los Cabos": (22.8905, -109.9167),
    "Puerto Vallarta": (20.6534, -105.2253),
    "Mazatlán": (23.2494, -106.4111),
    "Acapulco": (16.8531, -99.8237),
    "Zapopan": (20.7230, -103.3843),
    "Naucalpan": (19.4784, -99.2397),
    "Tlalnepantla": (19.5370, -99.1949),
    "Ecatepec": (19.6015, -99.0520),
    # Distrito Federal boroughs
    "Benito Juárez": (19.3718, -99.1590),
    "Miguel Hidalgo": (19.4148, -99.1925),
    "Cuauhtémoc": (19.4285, -99.1428),
    "Coyoacán": (19.3467, -99.1617),
    "Alvaro Obregón": (19.3579, -99.2067),
    "Tlalpan": (19.2847, -99.1683),
    "Iztapalapa": (19.3558, -99.0592),
    "Gustavo A. Madero": (19.4748, -99.1139),
    "Azcapotzalco": (19.4869, -99.1843),
    "Iztacalco": (19.3954, -99.0974),
    "Venustiano Carranza": (19.4409, -99.1069),
    "Tláhuac": (19.2867, -99.0046),
    "Xochimilco": (19.2620, -99.1036),
    "Milpa Alta": (19.1925, -99.0230),
    "La Magdalena Contreras": (19.3227, -99.2437),
    "Cuajimalpa de Morelos": (19.3557, -99.2988),
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points."""
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


def get_city_center(city, state, lat, lon):
    """Get city center coordinates, fallback to property coords."""
    if city in CITY_CENTERS:
        return CITY_CENTERS[city]
    # Try state capital
    for c, coords in CITY_CENTERS.items():
        if state and state.lower() in c.lower():
            return coords
    return (lat, lon)  # fallback


def compute_amenity_features(comparable, amenities_df):
    """Compute amenity counts and distances for a single comparable."""
    c_lat, c_lon = comparable["lat"], comparable["lon"]

    # Category mapping
    category_map = {
        "school": ["school", "university", "college", "kindergarten"],
        "hospital": ["hospital", "clinic", "doctors", "pharmacy", "dentist"],
        "restaurant": ["restaurant", "cafe", "fast_food", "bar", "food_court"],
        "supermarket": ["supermarket", "convenience", "marketplace", "grocery"],
        "bank": ["bank", "atm", "bureau_de_change"],
        "park": ["park", "garden", "playground", "nature_reserve", "recreation_ground"],
        "transport": ["bus_station", "bus_stop", "taxi", "fuel", "parking"],
        "commercial": ["shop", "mall", "department_store", "commercial"],
    }

    counts = {
        "total_500m": 0,
        "total_1km": 0,
        "total_2km": 0,
        "total_5km": 0,
        "schools_1km": 0,
        "hospitals_1km": 0,
        "restaurants_1km": 0,
        "supermarkets_1km": 0,
        "banks_1km": 0,
        "parks_1km": 0,
        "transport_1km": 0,
        "commercial_1km": 0,
        "nearest_school_m": 99999,
        "nearest_hospital_m": 99999,
        "nearest_supermarket_m": 99999,
        "nearest_park_m": 99999,
        "nearest_transport_m": 99999,
    }

    for _, amenity in amenities_df.iterrows():
        dist_km = haversine_km(c_lat, c_lon, amenity["lat"], amenity["lon"])
        dist_m = dist_km * 1000
        a_type = str(amenity.get("amenity_type", "")).lower()

        # Count by radius
        if dist_km <= 0.5:
            counts["total_500m"] += 1
        if dist_km <= 1.0:
            counts["total_1km"] += 1
        if dist_km <= 2.0:
            counts["total_2km"] += 1
        if dist_km <= 5.0:
            counts["total_5km"] += 1

        # Count by category at 1km
        if dist_km <= 1.0:
            cat_key_map = {
                'school': 'schools_1km', 'hospital': 'hospitals_1km',
                'restaurant': 'restaurants_1km', 'supermarket': 'supermarkets_1km',
                'bank': 'banks_1km', 'park': 'parks_1km',
                'transport': 'transport_1km', 'commercial': 'commercial_1km',
            }
            for cat, keywords in category_map.items():
                if any(k in a_type for k in keywords):
                    key = cat_key_map.get(cat)
                    if key and key in counts:
                        counts[key] += 1
                    break

        # Nearest distances
        for cat, keywords in category_map.items():
            if any(k in a_type for k in keywords):
                key = f"nearest_{cat}_m"
                if key in counts and dist_m < counts[key]:
                    counts[key] = dist_m

    # Walkability score (0-100)
    walk_score = min(
        100,
        (
            min(counts["total_500m"], 20) * 2  # max 40 points from nearby amenities
            + (
                100
                if counts["nearest_school_m"] < 1000
                else 50 if counts["nearest_school_m"] < 2000 else 0
            )
            * 0.15
            + (
                100
                if counts["nearest_hospital_m"] < 2000
                else 50 if counts["nearest_hospital_m"] < 5000 else 0
            )
            * 0.1
            + (
                100
                if counts["nearest_supermarket_m"] < 500
                else 50 if counts["nearest_supermarket_m"] < 1000 else 0
            )
            * 0.15
            + (
                100
                if counts["nearest_transport_m"] < 500
                else 50 if counts["nearest_transport_m"] < 1000 else 0
            )
            * 0.1
            + (
                100
                if counts["nearest_park_m"] < 500
                else 50 if counts["nearest_park_m"] < 1000 else 0
            )
            * 0.1
        ),
    )
    counts["walkability_score"] = round(walk_score, 1)

    # Cap nearest distances
    for k in counts:
        if k.startswith("nearest_") and counts[k] == 99999:
            counts[k] = None

    return counts


def enrich_batch(supabase, comparables_batch, amenities_df):
    """Enrich a batch of comparables and upsert to Supabase."""
    amenity_records = []
    distance_records = []

    for _, comp in comparables_batch.iterrows():
        comp_id = comp["id"]

        # 1. Amenity counts
        counts = compute_amenity_features(comp, amenities_df)
        counts["comparable_id"] = comp_id
        counts["computed_at"] = datetime.now().isoformat()
        amenity_records.append(counts)

        # 2. Distance features
        center = get_city_center(
            comp.get("city", ""), comp.get("state", ""), comp["lat"], comp["lon"]
        )
        dist_center = haversine_km(comp["lat"], comp["lon"], center[0], center[1])

        distance_records.append(
            {
                "comparable_id": comp_id,
                "distance_to_center_km": round(dist_center, 2),
                "computed_at": datetime.now().isoformat(),
            }
        )

    # Upsert to Supabase
    if amenity_records:
        try:
            supabase.table("iainmobiliaria_amenity_counts").upsert(
                amenity_records, on_conflict="comparable_id"
            ).execute()
        except Exception as e:
            logger.error(f"Error upserting amenity counts: {e}")

    if distance_records:
        try:
            supabase.table("iainmobiliaria_distance_features").upsert(
                distance_records, on_conflict="comparable_id"
            ).execute()
        except Exception as e:
            logger.error(f"Error upserting distance features: {e}")

    return len(amenity_records)


def main():
    parser = argparse.ArgumentParser(description="Enrich comparable features")
    parser.add_argument(
        "--limit", type=int, default=5000, help="Max comparables to process"
    )
    parser.add_argument("--city", type=str, default=None, help="Filter by city")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    args = parser.parse_args()

    logger.info(f"Starting enrichment pipeline (limit={args.limit}, city={args.city})")

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Load amenities (all at once - they're the reference data)
    logger.info("Loading amenities...")
    amenities_result = (
        sb.table("iainmobiliaria_amenities")
        .select("id,name,amenity_type,lat,lon")
        .execute()
    )
    amenities_df = (
        pd.DataFrame(amenities_result.data) if amenities_result.data else pd.DataFrame()
    )
    logger.info(f"Loaded {len(amenities_df)} amenities")

    # Load comparables in batches
    query = sb.table("iainmobiliaria_comparables").select(
        "id,lat,lon,city,state,price_mxn,area_m2"
    )
    if args.city:
        query = query.eq("city", args.city)
    query = query.limit(args.limit)

    comparables_result = query.execute()
    comparables_df = pd.DataFrame(comparables_result.data)
    logger.info(f"Processing {len(comparables_df)} comparables")

    # Process in batches
    total_enriched = 0
    start = time.time()

    for i in range(0, len(comparables_df), args.batch_size):
        batch = comparables_df.iloc[i : i + args.batch_size]
        enriched = enrich_batch(sb, batch, amenities_df)
        total_enriched += enriched

        elapsed = time.time() - start
        rate = total_enriched / elapsed if elapsed > 0 else 0
        logger.info(
            f"Enriched {total_enriched}/{len(comparables_df)} ({rate:.0f}/s)"
        )

    logger.info(
        f"Pipeline complete: {total_enriched} comparables enriched in {time.time()-start:.0f}s"
    )


if __name__ == "__main__":
    main()
