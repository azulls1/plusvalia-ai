# ================================================================
# FEATURES DE TURISMO - Puntuaciones de proximidad a zonas turisticas
# Calcula scores basados en distancia a hotspots turisticos de Mexico
# usando la formula de Haversine para distancias geodesicas
# ================================================================

import math
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List


# ================================================================
# Hotspots turisticos de Mexico
# Formato: nombre -> (latitud, longitud, radio_de_influencia_km)
# El radio define la zona de impacto directo en el precio del suelo
# ================================================================
TOURISM_HOTSPOTS: Dict[str, Tuple[float, float, int]] = {
    "cancun": (21.16, -86.85, 15),
    "playa_del_carmen": (20.63, -87.07, 10),
    "tulum": (20.21, -87.46, 8),
    "los_cabos": (22.89, -109.92, 12),
    "puerto_vallarta": (20.65, -105.23, 10),
    "isla_mujeres": (20.88, -86.87, 8),
    "acapulco": (16.86, -99.88, 10),
    "huatulco": (15.77, -96.13, 8),
    "ixtapa_zihuatanejo": (17.64, -101.55, 8),
    "mazatlan": (23.24, -106.44, 10),
    "cozumel": (20.43, -86.92, 8),
    "san_miguel_allende": (20.91, -100.74, 8),
    "valle_de_bravo": (19.19, -100.13, 6),
    "puebla_centro": (19.04, -98.20, 5),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en kilometros entre dos puntos (lat, lon)
    usando la formula de Haversine."""
    R = 6371.0  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def tourism_proximity_score(lat: float, lon: float) -> float:
    """Calcula un score de proximidad turistica entre 0 y 100.

    El score se basa en la distancia a todos los hotspots turisticos,
    ponderado por el radio de influencia de cada uno. Los hotspots
    mas cercanos y con mayor radio contribuyen mas al score final.

    Args:
        lat: Latitud del punto a evaluar
        lon: Longitud del punto a evaluar

    Returns:
        Score entre 0.0 (sin influencia turistica) y 100.0 (centro turistico)
    """
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return 0.0

    total_score = 0.0

    for _name, (h_lat, h_lon, radius_km) in TOURISM_HOTSPOTS.items():
        dist_km = _haversine_km(lat, lon, h_lat, h_lon)

        # Zona de impacto: hasta 3x el radio de influencia
        max_influence_km = radius_km * 3.0

        if dist_km >= max_influence_km:
            continue

        # Decaimiento exponencial: score maximo dentro del radio,
        # decae rapidamente fuera de el
        if dist_km <= radius_km:
            # Dentro del radio de influencia directa
            proximity = 1.0 - (dist_km / radius_km) * 0.3
        else:
            # Fuera del radio pero dentro de la zona de influencia extendida
            normalized_dist = (dist_km - radius_km) / (max_influence_km - radius_km)
            proximity = 0.7 * math.exp(-3.0 * normalized_dist)

        # Ponderar por el radio del hotspot (destinos mas grandes pesan mas)
        weight = radius_km / 15.0  # Normalizar contra el maximo (Cancun=15)
        contribution = proximity * weight * 100.0
        total_score = max(total_score, contribution)

    # Agregar bonificacion por multiples hotspots cercanos (efecto de corredor turistico)
    nearby_count = 0
    for _name, (h_lat, h_lon, radius_km) in TOURISM_HOTSPOTS.items():
        dist_km = _haversine_km(lat, lon, h_lat, h_lon)
        if dist_km <= radius_km * 2.0:
            nearby_count += 1

    if nearby_count > 1:
        # Bonificacion por corredor turistico (ej: Riviera Maya)
        corridor_bonus = min(15.0, (nearby_count - 1) * 5.0)
        total_score = min(100.0, total_score + corridor_bonus)

    return round(min(100.0, total_score), 2)


def is_tourism_zone(lat: float, lon: float) -> bool:
    """Determina si un punto esta dentro de alguna zona turistica.

    Un punto se considera en zona turistica si esta dentro del
    radio de influencia de al menos un hotspot.

    Args:
        lat: Latitud del punto
        lon: Longitud del punto

    Returns:
        True si el punto esta dentro de alguna zona turistica
    """
    for _name, (h_lat, h_lon, radius_km) in TOURISM_HOTSPOTS.items():
        dist_km = _haversine_km(lat, lon, h_lat, h_lon)
        if dist_km <= radius_km:
            return True
    return False


def nearest_tourism_hotspot(lat: float, lon: float) -> Tuple[str, float]:
    """Encuentra el hotspot turistico mas cercano y su distancia.

    Args:
        lat: Latitud del punto
        lon: Longitud del punto

    Returns:
        Tupla con (nombre_del_hotspot, distancia_en_km)
    """
    min_dist = float("inf")
    nearest_name = "none"

    for name, (h_lat, h_lon, _radius) in TOURISM_HOTSPOTS.items():
        dist_km = _haversine_km(lat, lon, h_lat, h_lon)
        if dist_km < min_dist:
            min_dist = dist_km
            nearest_name = name

    return nearest_name, round(min_dist, 2)


def add_tourism_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas de features turisticos a un DataFrame.

    Requiere que el DataFrame tenga columnas 'lat' y 'lon'.
    Agrega tres columnas nuevas:
        - tourism_score: Score de proximidad turistica (0-100)
        - is_tourism_zone: Booleano si esta en zona turistica
        - nearest_tourism_km: Distancia al hotspot mas cercano en km

    Args:
        df: DataFrame con columnas 'lat' y 'lon'

    Returns:
        DataFrame con las tres columnas de turismo agregadas
    """
    df = df.copy()

    # Verificar que existan las columnas necesarias
    if "lat" not in df.columns or "lon" not in df.columns:
        raise ValueError("El DataFrame debe contener columnas 'lat' y 'lon'")

    # Calcular scores de turismo para cada fila
    scores: List[float] = []
    zones: List[bool] = []
    distances: List[float] = []

    for _, row in df.iterrows():
        lat_val = float(row["lat"])
        lon_val = float(row["lon"])

        scores.append(tourism_proximity_score(lat_val, lon_val))
        zones.append(is_tourism_zone(lat_val, lon_val))
        _name, dist = nearest_tourism_hotspot(lat_val, lon_val)
        distances.append(dist)

    df["tourism_score"] = scores
    df["is_tourism_zone"] = zones
    df["nearest_tourism_km"] = distances

    return df
