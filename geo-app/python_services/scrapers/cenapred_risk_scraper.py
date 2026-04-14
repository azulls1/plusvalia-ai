"""
Scraper de datos de riesgo del CENAPRED - Atlas Nacional de Riesgos.

Fuente: https://www.atlasnacionalderiesgos.gob.mx/ y datos.gob.mx
Datos: zonas de riesgo sísmico (A/B/C/D), inundación, deslizamiento

La zonificación sísmica de México está definida por el CFE (Comisión Federal
de Electricidad) y el Manual de Diseño Sísmico. Se clasifica en cuatro zonas:
  - Zona A: Baja sismicidad (Yucatán, Chihuahua norte, Coahuila, NL, Tamaulipas)
  - Zona B: Moderada (Durango, Aguascalientes, partes de Jalisco, SLP, Veracruz)
  - Zona C: Alta (partes de Jalisco, Michoacán, Puebla, Oaxaca interior, CDMX)
  - Zona D: Muy alta (costa del Pacífico de Jalisco a Chiapas, Guerrero, Oaxaca costa)

Este scraper implementa la clasificación usando polígonos simplificados
basados en la zonificación oficial del CFE.
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from config import DATA_DIR

# ── Paths ────────────────────────────────────────────────────────────────────

OUTPUT_FILE = DATA_DIR / "cenapred_zonas_riesgo.csv"

# ── Zonificación sísmica de México (CFE) ────────────────────────────────────
#
# Clasificación por estado/región basada en el Manual de Diseño por Sismo
# de la Comisión Federal de Electricidad (CFE-2015).
# Para estados con zonas mixtas, se usan coordenadas de referencia.
#
# Formato: {estado: zona_default} para estados completamente en una zona,
# y polígonos de refinamiento para estados que cruzan varias zonas.

# Estados completamente en una zona sísmica
STATE_SEISMIC_ZONE: Dict[str, str] = {
    # Zona A — Baja sismicidad
    "Yucatán": "A",
    "Quintana Roo": "A",
    "Campeche": "A",
    "Nuevo León": "A",
    "Tamaulipas": "A",
    "Coahuila": "A",
    "Tabasco": "A",
    # Zona B — Moderada
    "Aguascalientes": "B",
    "Durango": "B",
    "Zacatecas": "B",
    "San Luis Potosí": "B",
    "Guanajuato": "B",
    "Querétaro": "B",
    "Hidalgo": "B",
    "Tlaxcala": "B",
    "Nayarit": "B",
    "Sinaloa": "B",
    # Zona C — Alta
    "Ciudad de México": "C",
    "México": "C",
    "Puebla": "C",
    "Morelos": "C",
    "Baja California": "C",
    "Baja California Sur": "C",
    "Sonora": "C",
    # Zona D — Muy alta (costa del Pacífico)
    "Guerrero": "D",
    "Chiapas": "D",
}

# Estados con zonas mixtas — se evalúan por latitud/longitud
# Formato: lista de (lat_min, lat_max, lon_min, lon_max, zona)
# Los rectángulos se evalúan en orden; el primero que contenga el punto gana.
MIXED_ZONE_STATES: Dict[str, List[Tuple[float, float, float, float, str]]] = {
    "Jalisco": [
        # Costa del Pacífico → Zona D
        (19.0, 21.0, -106.0, -104.5, "D"),
        # Zona metropolitana de Guadalajara → Zona C
        (20.4, 21.0, -104.5, -103.0, "C"),
        # Resto del estado → Zona B
        (19.0, 23.0, -106.0, -101.0, "B"),
    ],
    "Michoacán": [
        # Costa del Pacífico → Zona D
        (17.5, 19.0, -104.0, -101.0, "D"),
        # Interior → Zona C
        (19.0, 20.5, -104.0, -100.0, "C"),
        # Norte del estado → Zona B
        (20.0, 21.0, -104.0, -100.0, "B"),
    ],
    "Oaxaca": [
        # Costa del Pacífico → Zona D
        (15.0, 16.5, -99.0, -95.5, "D"),
        # Sierra y valles centrales → Zona C
        (16.5, 18.5, -98.5, -95.5, "C"),
        # Istmo → Zona C
        (15.5, 17.5, -95.5, -94.0, "C"),
    ],
    "Colima": [
        # Todo Colima es zona C-D; costa → D
        (18.5, 19.2, -104.8, -103.5, "D"),
        # Interior → Zona C
        (19.0, 19.8, -104.5, -103.3, "C"),
    ],
    "Veracruz": [
        # Sur (cerca de Oaxaca/Chiapas) → Zona C
        (16.5, 18.5, -97.0, -94.5, "C"),
        # Centro y norte → Zona B
        (18.5, 23.0, -98.5, -96.0, "B"),
        # Resto → Zona A
        (20.5, 23.0, -98.0, -96.5, "A"),
    ],
    "Chihuahua": [
        # Sierra Madre Occidental (suroeste) → Zona B
        (25.5, 29.0, -109.0, -107.0, "B"),
        # Resto → Zona A
        (25.5, 32.0, -109.0, -103.5, "A"),
    ],
}

# ── Zonas de inundación por estado (datos simplificados CENAPRED) ───────────
#
# Nivel de riesgo de inundación promedio por estado.
# Fuente: Atlas Nacional de Riesgos — mapas de susceptibilidad a inundaciones.
# Valores: 'alto', 'medio', 'bajo', 'nulo'

STATE_FLOOD_RISK: Dict[str, str] = {
    "Tabasco": "alto",
    "Veracruz": "alto",
    "Chiapas": "medio",
    "Campeche": "medio",
    "Quintana Roo": "medio",
    "Yucatán": "medio",
    "Tamaulipas": "medio",
    "Sinaloa": "medio",
    "Nayarit": "medio",
    "Jalisco": "medio",
    "Guerrero": "medio",
    "Oaxaca": "medio",
    "Puebla": "medio",
    "Hidalgo": "medio",
    "San Luis Potosí": "medio",
    "Ciudad de México": "medio",
    "México": "medio",
    "Michoacán": "medio",
    "Colima": "medio",
    "Morelos": "bajo",
    "Tlaxcala": "bajo",
    "Querétaro": "bajo",
    "Guanajuato": "bajo",
    "Aguascalientes": "bajo",
    "Zacatecas": "bajo",
    "Durango": "bajo",
    "Chihuahua": "bajo",
    "Sonora": "bajo",
    "Baja California": "bajo",
    "Baja California Sur": "bajo",
    "Coahuila": "bajo",
    "Nuevo León": "bajo",
    "Monterrey": "bajo",
}

# Zonas costeras con alto riesgo de inundación (lat, lon, radio_km)
FLOOD_HIGH_RISK_ZONES: List[Tuple[float, float, float]] = [
    # Planicie costera de Tabasco
    (18.0, -92.9, 80),
    # Planicie costera de Veracruz (zona Coatzacoalcos)
    (18.1, -94.4, 50),
    # Zona de Villahermosa
    (17.99, -92.93, 40),
    # Desembocadura del Pánuco (Tamaulipas)
    (22.2, -97.8, 30),
    # Costa de Nayarit (marismas)
    (21.5, -105.2, 25),
    # Valle de México (zona lacustre)
    (19.4, -99.1, 15),
]

# ── Zonas de deslizamiento (simplificado) ───────────────────────────────────

# Regiones montañosas con alto riesgo de deslizamiento
# (lat_centro, lon_centro, radio_km, nivel)
LANDSLIDE_ZONES: List[Tuple[float, float, float, str]] = [
    # Sierra Norte de Puebla
    (20.0, -97.5, 50, "alto"),
    # Sierra de Guerrero
    (17.5, -99.5, 60, "alto"),
    # Sierra Madre del Sur (Oaxaca)
    (16.5, -96.5, 50, "alto"),
    # Sierra Madre Occidental (Chihuahua-Sinaloa)
    (26.0, -107.5, 80, "medio"),
    # Eje Neovolcánico
    (19.3, -99.7, 40, "medio"),
    # Sierra de Chiapas
    (16.0, -92.5, 60, "alto"),
    # Barrancas de Monterrey
    (25.6, -100.3, 20, "medio"),
    # Sierra Madre Oriental (Hidalgo-Veracruz)
    (20.5, -98.0, 50, "medio"),
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia haversine en kilómetros entre dos puntos."""
    R = 6371.0  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _get_state_from_coords(lat: float, lon: float) -> str:
    """
    Estima el estado mexicano a partir de coordenadas.
    Usa un mapeo simplificado de bounding boxes por estado.
    """
    # Bounding boxes aproximados de estados mexicanos (lat_min, lat_max, lon_min, lon_max)
    STATE_BOUNDS: Dict[str, Tuple[float, float, float, float]] = {
        "Aguascalientes": (21.7, 22.5, -103.0, -102.0),
        "Baja California": (28.0, 32.8, -117.5, -114.5),
        "Baja California Sur": (22.8, 28.0, -115.0, -109.0),
        "Campeche": (17.8, 20.0, -92.5, -89.0),
        "Chiapas": (14.5, 17.6, -94.2, -90.4),
        "Chihuahua": (25.5, 32.0, -109.1, -103.3),
        "Ciudad de México": (19.1, 19.6, -99.4, -98.9),
        "Coahuila": (24.5, 29.9, -104.0, -99.8),
        "Colima": (18.6, 19.6, -104.8, -103.4),
        "Durango": (22.3, 26.8, -107.2, -103.4),
        "Guanajuato": (20.0, 21.9, -102.1, -99.6),
        "Guerrero": (16.3, 18.9, -102.2, -98.0),
        "Hidalgo": (19.6, 21.4, -99.9, -97.9),
        "Jalisco": (18.9, 22.8, -105.7, -101.5),
        "México": (18.4, 20.3, -100.6, -98.6),
        "Michoacán": (17.9, 20.4, -103.7, -100.0),
        "Morelos": (18.3, 19.1, -99.5, -98.6),
        "Nayarit": (20.6, 23.1, -105.8, -103.7),
        "Nuevo León": (23.2, 27.9, -101.2, -98.4),
        "Oaxaca": (15.4, 18.7, -98.7, -93.9),
        "Puebla": (17.8, 20.6, -98.9, -96.7),
        "Querétaro": (20.0, 21.7, -100.6, -99.0),
        "Quintana Roo": (18.5, 21.6, -89.5, -86.7),
        "San Luis Potosí": (21.2, 24.3, -102.3, -98.3),
        "Sinaloa": (22.5, 27.0, -109.5, -105.3),
        "Sonora": (26.3, 32.5, -115.1, -108.5),
        "Tabasco": (17.2, 18.7, -94.2, -91.0),
        "Tamaulipas": (22.2, 27.7, -100.2, -97.1),
        "Tlaxcala": (19.1, 19.7, -98.7, -97.6),
        "Veracruz": (17.1, 22.5, -98.7, -93.6),
        "Yucatán": (19.6, 21.7, -91.0, -87.5),
        "Zacatecas": (21.0, 25.1, -104.4, -101.7),
    }

    best_state = ""
    best_dist = float("inf")

    for state, (lat_min, lat_max, lon_min, lon_max) in STATE_BOUNDS.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            # Punto dentro del bounding box → distancia al centro
            center_lat = (lat_min + lat_max) / 2
            center_lon = (lon_min + lon_max) / 2
            dist = _haversine_km(lat, lon, center_lat, center_lon)
            if dist < best_dist:
                best_dist = dist
                best_state = state

    return best_state


def get_seismic_zone(lat: float, lon: float) -> str:
    """
    Retorna la zona sísmica (A/B/C/D) basada en la zonificación del CFE.

    Args:
        lat: Latitud del punto
        lon: Longitud del punto

    Returns:
        'A' (baja), 'B' (moderada), 'C' (alta), o 'D' (muy alta)
    """
    state = _get_state_from_coords(lat, lon)

    if not state:
        logger.debug(f"No se pudo determinar estado para ({lat}, {lon})")
        return "B"  # Valor por defecto conservador

    # Verificar si el estado tiene zona fija
    if state in STATE_SEISMIC_ZONE:
        return STATE_SEISMIC_ZONE[state]

    # Verificar estados con zonas mixtas
    if state in MIXED_ZONE_STATES:
        for lat_min, lat_max, lon_min, lon_max, zone in MIXED_ZONE_STATES[state]:
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return zone
        # Si no cae en ningún rectángulo, usar el último definido (más conservador)
        return MIXED_ZONE_STATES[state][-1][-1]

    # Fallback basado en distancia a la costa del Pacífico
    # Puntos más cercanos al Pacífico tienden a zona C/D
    pacific_lon = -105.0
    if lon < pacific_lon and lat < 22.0:
        return "C"

    return "B"


def get_flood_risk(lat: float, lon: float) -> str:
    """
    Retorna el nivel de riesgo de inundación para una coordenada.

    Args:
        lat: Latitud del punto
        lon: Longitud del punto

    Returns:
        'alto', 'medio', 'bajo', o 'nulo'
    """
    # Primero verificar zonas de alto riesgo conocidas
    for zone_lat, zone_lon, radius_km in FLOOD_HIGH_RISK_ZONES:
        dist = _haversine_km(lat, lon, zone_lat, zone_lon)
        if dist <= radius_km:
            return "alto"

    # Verificar por estado
    state = _get_state_from_coords(lat, lon)
    if state in STATE_FLOOD_RISK:
        return STATE_FLOOD_RISK[state]

    # Verificar proximidad a la costa (zonas costeras tienen mayor riesgo)
    # Línea de costa simplificada: si altitud estimada es baja y cerca del mar
    # Usamos como proxy la distancia a puntos costeros conocidos
    coastal_points = [
        (23.2, -106.4),  # Mazatlán
        (20.6, -105.2),  # Puerto Vallarta
        (19.1, -104.3),  # Manzanillo
        (16.8, -99.8),   # Acapulco
        (15.7, -96.1),   # Huatulco
        (19.2, -96.1),   # Veracruz
        (18.5, -88.3),   # Chetumal
        (21.2, -86.8),   # Cancún
    ]
    for clat, clon in coastal_points:
        if _haversine_km(lat, lon, clat, clon) < 20:
            return "medio"

    return "bajo"


def _get_landslide_risk(lat: float, lon: float) -> str:
    """
    Retorna el nivel de riesgo de deslizamiento para una coordenada.

    Returns:
        'alto', 'medio', 'bajo'
    """
    for zone_lat, zone_lon, radius_km, nivel in LANDSLIDE_ZONES:
        dist = _haversine_km(lat, lon, zone_lat, zone_lon)
        if dist <= radius_km:
            return nivel
    return "bajo"


def get_risk_score(lat: float, lon: float) -> float:
    """
    Calcula un puntaje combinado de riesgo de 0 a 100 (100 = más seguro).

    Componentes:
    - Riesgo sísmico (40% del peso)
    - Riesgo de inundación (35% del peso)
    - Riesgo de deslizamiento (25% del peso)

    Args:
        lat: Latitud del punto
        lon: Longitud del punto

    Returns:
        Puntaje de 0.0 a 100.0 donde 100 es más seguro
    """
    # Puntaje sísmico (zona A=100, B=75, C=45, D=15)
    seismic_scores = {"A": 100, "B": 75, "C": 45, "D": 15}
    seismic_zone = get_seismic_zone(lat, lon)
    seismic_score = seismic_scores.get(seismic_zone, 50)

    # Puntaje de inundación
    flood_scores = {"nulo": 100, "bajo": 80, "medio": 45, "alto": 10}
    flood_level = get_flood_risk(lat, lon)
    flood_score = flood_scores.get(flood_level, 50)

    # Puntaje de deslizamiento
    landslide_scores = {"bajo": 100, "medio": 55, "alto": 15}
    landslide_level = _get_landslide_risk(lat, lon)
    landslide_score = landslide_scores.get(landslide_level, 50)

    # Puntaje combinado ponderado
    combined = (
        seismic_score * 0.40
        + flood_score * 0.35
        + landslide_score * 0.25
    )

    return round(combined, 2)


def add_risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columnas de riesgo al DataFrame.

    Requiere columnas 'lat' y 'lon' en el DataFrame.
    Agrega: seismic_zone, flood_risk, landslide_risk, risk_score

    Args:
        df: DataFrame con columnas lat y lon

    Returns:
        DataFrame con columnas de riesgo agregadas
    """
    if df.empty:
        logger.warning("DataFrame vacío, no se agregan features de riesgo")
        return df

    df = df.copy()

    if "lat" not in df.columns or "lon" not in df.columns:
        logger.error("DataFrame no tiene columnas 'lat' y 'lon'")
        return df

    logger.info(f"Calculando features de riesgo para {len(df)} registros...")

    seismic_zones = []
    flood_risks = []
    landslide_risks = []
    risk_scores = []

    for _, row in df.iterrows():
        lat = row.get("lat")
        lon = row.get("lon")

        if pd.isna(lat) or pd.isna(lon):
            seismic_zones.append(None)
            flood_risks.append(None)
            landslide_risks.append(None)
            risk_scores.append(None)
            continue

        seismic_zones.append(get_seismic_zone(lat, lon))
        flood_risks.append(get_flood_risk(lat, lon))
        landslide_risks.append(_get_landslide_risk(lat, lon))
        risk_scores.append(get_risk_score(lat, lon))

    df["seismic_zone"] = seismic_zones
    df["flood_risk"] = flood_risks
    df["landslide_risk"] = landslide_risks
    df["risk_score"] = risk_scores

    # Estadísticas
    zone_counts = df["seismic_zone"].value_counts()
    logger.info(f"Distribución de zonas sísmicas:\n{zone_counts.to_string()}")

    flood_counts = df["flood_risk"].value_counts()
    logger.info(f"Distribución de riesgo de inundación:\n{flood_counts.to_string()}")

    avg_score = df["risk_score"].mean()
    logger.info(f"Puntaje de riesgo promedio: {avg_score:.1f}/100")

    return df


def _generate_reference_data() -> pd.DataFrame:
    """
    Genera un CSV de referencia con datos de riesgo para ciudades principales.
    Útil para validación y como lookup rápido.
    """
    # Ciudades principales de México con coordenadas
    cities = [
        ("Guadalajara", "Jalisco", 20.6597, -103.3496),
        ("Zapopan", "Jalisco", 20.7167, -103.4000),
        ("Tlaquepaque", "Jalisco", 20.6400, -103.3100),
        ("Tonalá", "Jalisco", 20.6250, -103.2333),
        ("Tlajomulco", "Jalisco", 20.4740, -103.4410),
        ("Ciudad de México", "Ciudad de México", 19.4326, -99.1332),
        ("Monterrey", "Nuevo León", 25.6866, -100.3161),
        ("Puebla", "Puebla", 19.0414, -98.2063),
        ("Cancún", "Quintana Roo", 21.1619, -86.8515),
        ("Mérida", "Yucatán", 20.9674, -89.5926),
        ("Tijuana", "Baja California", 32.5149, -117.0382),
        ("Querétaro", "Querétaro", 20.5888, -100.3899),
        ("León", "Guanajuato", 21.1250, -101.6860),
        ("Acapulco", "Guerrero", 16.8531, -99.8237),
        ("Oaxaca", "Oaxaca", 17.0732, -96.7266),
        ("Veracruz", "Veracruz", 19.2026, -96.1533),
        ("Villahermosa", "Tabasco", 17.9892, -92.9475),
        ("Tuxtla Gutiérrez", "Chiapas", 16.7528, -93.1152),
        ("Hermosillo", "Sonora", 29.0729, -110.9559),
        ("Chihuahua", "Chihuahua", 28.6353, -106.0889),
        ("Culiacán", "Sinaloa", 24.8049, -107.3940),
        ("Morelia", "Michoacán", 19.7060, -101.1950),
        ("Saltillo", "Coahuila", 25.4232, -100.9925),
        ("Aguascalientes", "Aguascalientes", 21.8818, -102.2916),
        ("Cuernavaca", "Morelos", 18.9186, -99.2342),
        ("San Luis Potosí", "San Luis Potosí", 22.1565, -100.9855),
        ("Toluca", "México", 19.2826, -99.6557),
        ("Durango", "Durango", 24.0277, -104.6532),
        ("Zacatecas", "Zacatecas", 22.7709, -102.5833),
        ("Pachuca", "Hidalgo", 20.1011, -98.7591),
        ("Colima", "Colima", 19.2433, -103.7247),
        ("Tepic", "Nayarit", 21.5010, -104.8943),
    ]

    rows = []
    for city, state, lat, lon in cities:
        rows.append({
            "city": city,
            "state": state,
            "lat": lat,
            "lon": lon,
            "seismic_zone": get_seismic_zone(lat, lon),
            "flood_risk": get_flood_risk(lat, lon),
            "landslide_risk": _get_landslide_risk(lat, lon),
            "risk_score": get_risk_score(lat, lon),
            "generated_at": datetime.now().isoformat(),
        })

    df = pd.DataFrame(rows)
    return df


def main():
    """Genera datos de referencia de riesgo y los guarda en CSV."""
    logger.info("=" * 70)
    logger.info("CENAPRED - ATLAS NACIONAL DE RIESGOS")
    logger.info("Generando datos de zonificación de riesgo para ciudades principales")
    logger.info("=" * 70)

    df = _generate_reference_data()

    if df.empty:
        logger.warning("No se generaron datos de referencia")
        return

    # Guardar CSV
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    logger.info(f"Guardado: {OUTPUT_FILE} ({len(df)} registros)")

    # Reporte
    logger.info("\n" + "=" * 60)
    logger.info("REPORTE DE ZONIFICACION DE RIESGO")
    logger.info("=" * 60)

    logger.info("\nDistribución de zonas sísmicas:")
    for zone in ["A", "B", "C", "D"]:
        count = len(df[df["seismic_zone"] == zone])
        cities_in_zone = df[df["seismic_zone"] == zone]["city"].tolist()
        logger.info(f"  Zona {zone}: {count} ciudades — {', '.join(cities_in_zone[:5])}")

    logger.info("\nDistribución de riesgo de inundación:")
    for level in ["alto", "medio", "bajo", "nulo"]:
        count = len(df[df["flood_risk"] == level])
        if count > 0:
            logger.info(f"  {level.upper()}: {count} ciudades")

    logger.info(f"\nPuntaje promedio de seguridad: {df['risk_score'].mean():.1f}/100")
    logger.info(f"Ciudad más segura: {df.loc[df['risk_score'].idxmax(), 'city']} "
                f"({df['risk_score'].max():.1f})")
    logger.info(f"Ciudad con más riesgo: {df.loc[df['risk_score'].idxmin(), 'city']} "
                f"({df['risk_score'].min():.1f})")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    main()
