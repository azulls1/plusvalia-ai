"""
NDVI (Normalized Difference Vegetation Index) feature engineering.
Usa datos de Sentinel-2 o datos pre-computados para estimar verdor por zona.

El NDVI es un proxy fuerte de calidad de vecindario en mercados inmobiliarios
mexicanos. Zonas con mayor cobertura vegetal tienden a tener:
- Mayor valor por m2
- Menor densidad de construccion
- Mejor calidad de vida percibida

Valores NDVI:
- -1.0 a 0.0: Agua, nubes, superficies artificiales
- 0.0 a 0.2: Suelo desnudo, concreto denso
- 0.2 a 0.4: Vegetacion escasa, zonas semiurbanas
- 0.4 a 0.6: Vegetacion moderada, parques urbanos
- 0.6 a 1.0: Vegetacion densa, bosques
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger

try:
    import rasterio
    from rasterio.transform import rowcol
    RASTERIO_AVAILABLE = True
except ImportError:
    rasterio = None
    RASTERIO_AVAILABLE = False
    logger.warning("rasterio no instalado. Ejecuta: pip install rasterio")


# Umbrales para categorizar NDVI
_NDVI_THRESHOLDS = {
    "urban_dense": 0.15,     # Zonas urbanas densas (concreto, asfalto)
    "low_green": 0.25,       # Vegetacion baja, suburbano denso
    "moderate": 0.40,        # Vegetacion moderada, parques
    "high_green": 1.0,       # Vegetacion abundante, zonas residenciales verdes
}

# Radio por defecto para calculo de NDVI promedio (metros)
_DEFAULT_RADIUS_M = 500


def compute_ndvi_from_raster(
    lat: float,
    lon: float,
    raster_path: str,
    radius_m: int = _DEFAULT_RADIUS_M,
) -> float:
    """Extrae NDVI promedio de un GeoTIFF dentro de un radio dado.

    Lee una ventana del raster alrededor del punto especificado
    y calcula el promedio de los pixeles dentro del radio.

    Parameters
    ----------
    lat : float
        Latitud del punto central.
    lon : float
        Longitud del punto central.
    raster_path : str
        Ruta al archivo GeoTIFF con valores NDVI.
        El raster debe estar en CRS EPSG:4326 o compatible.
    radius_m : int
        Radio en metros para el calculo del promedio.

    Returns
    -------
    float
        Valor NDVI promedio dentro del radio. Retorna 0.0 si falla.
    """
    if not RASTERIO_AVAILABLE:
        logger.debug("rasterio no disponible, retornando NDVI por defecto")
        return 0.0

    try:
        with rasterio.open(raster_path) as src:
            # Convertir radio de metros a grados (aproximacion)
            # 1 grado de latitud ~ 111,320 metros
            radius_deg = radius_m / 111320.0

            # Definir bounding box del area de interes
            min_lon = lon - radius_deg / math.cos(math.radians(lat))
            max_lon = lon + radius_deg / math.cos(math.radians(lat))
            min_lat = lat - radius_deg
            max_lat = lat + radius_deg

            # Obtener filas/columnas del raster para la ventana
            try:
                row_min, col_min = rowcol(src.transform, min_lon, max_lat)
                row_max, col_max = rowcol(src.transform, max_lon, min_lat)
            except Exception:
                # Fallback: usar el pixel central
                row_center, col_center = rowcol(src.transform, lon, lat)
                row_min = max(0, row_center - 5)
                row_max = min(src.height, row_center + 5)
                col_min = max(0, col_center - 5)
                col_max = min(src.width, col_center + 5)

            # Asegurar limites validos
            row_min = max(0, min(row_min, row_max))
            row_max = min(src.height, max(row_min + 1, row_max))
            col_min = max(0, min(col_min, col_max))
            col_max = min(src.width, max(col_min + 1, col_max))

            # Leer ventana del raster (banda 1)
            window = rasterio.windows.Window.from_slices(
                (int(row_min), int(row_max)),
                (int(col_min), int(col_max)),
            )
            data = src.read(1, window=window)

            # Filtrar nodata y valores fuera de rango NDVI
            nodata = src.nodata
            if nodata is not None:
                valid_mask = (data != nodata) & (data >= -1.0) & (data <= 1.0)
            else:
                valid_mask = (data >= -1.0) & (data <= 1.0)

            valid_pixels = data[valid_mask]

            if len(valid_pixels) > 0:
                return float(np.mean(valid_pixels))
            else:
                return 0.0

    except Exception as e:
        logger.debug(f"Error leyendo NDVI raster para ({lat}, {lon}): {e}")
        return 0.0


def load_ndvi_lookup(filepath: str) -> Dict[str, float]:
    """Carga un lookup pre-computado de NDVI por celda H3.

    El lookup puede ser generado previamente procesando imagenes
    Sentinel-2 y promediando valores NDVI por celda hexagonal.

    Parameters
    ----------
    filepath : str
        Ruta al archivo CSV o JSON con el lookup.
        CSV esperado: columnas 'h3_index' y 'ndvi_mean'.
        JSON esperado: {h3_index: ndvi_value, ...}.

    Returns
    -------
    dict
        Diccionario {h3_index: ndvi_promedio}.
    """
    try:
        if filepath.endswith(".json"):
            import json
            with open(filepath, "r") as f:
                lookup = json.load(f)
            # Asegurar valores float
            lookup = {k: float(v) for k, v in lookup.items()}

        elif filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
            if "h3_index" in df.columns and "ndvi_mean" in df.columns:
                lookup = dict(zip(df["h3_index"], df["ndvi_mean"].astype(float)))
            elif "h3_index" in df.columns and "ndvi" in df.columns:
                lookup = dict(zip(df["h3_index"], df["ndvi"].astype(float)))
            else:
                logger.error(
                    f"CSV de NDVI debe contener 'h3_index' y 'ndvi_mean': {filepath}"
                )
                return {}
        else:
            logger.error(f"Formato no soportado para lookup NDVI: {filepath}")
            return {}

        logger.info(f"Lookup NDVI cargado: {len(lookup)} celdas desde {filepath}")
        return lookup

    except Exception as e:
        logger.error(f"Error cargando lookup NDVI desde {filepath}: {e}")
        return {}


def _classify_ndvi(ndvi_value: float) -> str:
    """Clasifica un valor NDVI en categoria descriptiva.

    Parameters
    ----------
    ndvi_value : float
        Valor NDVI (-1 a 1).

    Returns
    -------
    str
        Categoria: 'urban_dense', 'low_green', 'moderate' o 'high_green'.
    """
    if ndvi_value < _NDVI_THRESHOLDS["urban_dense"]:
        return "urban_dense"
    elif ndvi_value < _NDVI_THRESHOLDS["low_green"]:
        return "low_green"
    elif ndvi_value < _NDVI_THRESHOLDS["moderate"]:
        return "moderate"
    else:
        return "high_green"


def _ndvi_to_green_score(ndvi_value: float) -> float:
    """Convierte valor NDVI a score de verdor 0-100.

    Transformacion lineal donde:
    - NDVI <= 0.0 -> score 0
    - NDVI >= 0.6 -> score 100

    Parameters
    ----------
    ndvi_value : float
        Valor NDVI.

    Returns
    -------
    float
        Score de verdor entre 0 y 100.
    """
    # Mapeo lineal de [0, 0.6] a [0, 100]
    score = (ndvi_value / 0.6) * 100.0
    return max(0.0, min(100.0, score))


def add_ndvi_features(
    df: pd.DataFrame,
    ndvi_lookup: Optional[Dict[str, float]] = None,
    raster_path: Optional[str] = None,
    radius_m: int = _DEFAULT_RADIUS_M,
) -> pd.DataFrame:
    """Agrega features de vegetacion (NDVI) al DataFrame.

    Estrategia de datos en cascada:
    1. Si hay raster_path, extraer NDVI directo del GeoTIFF
    2. Si hay ndvi_lookup (por celda H3), usar el lookup
    3. Fallback: estimar desde datos OSM (parques/jardines)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con columnas 'lat' y 'lon'.
    ndvi_lookup : dict, optional
        Lookup pre-computado {h3_index: ndvi_value}.
    raster_path : str, optional
        Ruta al GeoTIFF con datos NDVI.
    radius_m : int
        Radio en metros para calculo de NDVI promedio.

    Returns
    -------
    pd.DataFrame
        DataFrame con columnas adicionales:
        - ndvi_500m: valor NDVI promedio dentro del radio
        - ndvi_category: clasificacion del verdor
        - green_space_score: score 0-100 derivado del NDVI
    """
    if "lat" not in df.columns or "lon" not in df.columns:
        logger.warning("Columnas lat/lon no encontradas, omitiendo features NDVI")
        df["ndvi_500m"] = 0.0
        df["ndvi_category"] = "urban_dense"
        df["green_space_score"] = 0.0
        return df

    logger.info(f"Calculando features NDVI para {len(df)} registros...")

    # Intentar importar h3 para lookup basado en celdas hexagonales
    h3_available = False
    try:
        import h3
        h3_available = True
    except ImportError:
        pass

    ndvi_values: List[float] = []
    source_counts = {"raster": 0, "lookup": 0, "fallback": 0}

    for i in range(len(df)):
        lat = df["lat"].iloc[i]
        lon = df["lon"].iloc[i]
        ndvi = None

        # Estrategia 1: Raster directo (mas preciso)
        if raster_path and RASTERIO_AVAILABLE:
            ndvi = compute_ndvi_from_raster(lat, lon, raster_path, radius_m)
            if ndvi != 0.0:
                source_counts["raster"] += 1
                ndvi_values.append(ndvi)
                continue

        # Estrategia 2: Lookup por celda H3
        if ndvi_lookup and h3_available:
            # Buscar en resoluciones de mayor a menor precision
            for res in [9, 7, 5]:
                try:
                    h3_idx = h3.latlng_to_cell(lat, lon, res)
                    if h3_idx in ndvi_lookup:
                        ndvi = ndvi_lookup[h3_idx]
                        source_counts["lookup"] += 1
                        break
                except Exception:
                    continue

        # Estrategia 3: Valor por defecto conservador
        if ndvi is None:
            ndvi = 0.20  # Valor urbano tipico mexicano
            source_counts["fallback"] += 1

        ndvi_values.append(ndvi)

    # Agregar columnas al DataFrame
    df["ndvi_500m"] = ndvi_values
    df["ndvi_category"] = df["ndvi_500m"].apply(_classify_ndvi)
    df["green_space_score"] = df["ndvi_500m"].apply(_ndvi_to_green_score)

    logger.info(
        f"Features NDVI generados. Fuentes: "
        f"raster={source_counts['raster']}, "
        f"lookup={source_counts['lookup']}, "
        f"fallback={source_counts['fallback']}"
    )

    return df


def estimate_ndvi_from_osm(
    lat: float,
    lon: float,
    amenities_df: pd.DataFrame,
    radius_km: float = 1.0,
) -> float:
    """Estima NDVI a partir de datos OSM cuando no hay satelite disponible.

    Cuenta parques, jardines y areas verdes cercanas como proxy
    del indice de vegetacion. Es una aproximacion burda pero util
    cuando no hay imagenes satelitales.

    Parameters
    ----------
    lat : float
        Latitud del punto.
    lon : float
        Longitud del punto.
    amenities_df : pd.DataFrame
        DataFrame con amenidades OSM. Debe contener:
        - 'lat', 'lon': coordenadas
        - 'type' o 'amenity': tipo de amenidad
        Tipos relevantes: 'park', 'garden', 'forest', 'meadow',
        'recreation_ground', 'nature_reserve'.
    radius_km : float
        Radio de busqueda en kilometros.

    Returns
    -------
    float
        Valor NDVI estimado (0.0 a 0.6).
    """
    if amenities_df is None or len(amenities_df) == 0:
        return 0.15  # Valor por defecto urbano

    if "lat" not in amenities_df.columns or "lon" not in amenities_df.columns:
        return 0.15

    # Tipos de amenidades que indican vegetacion
    green_types = {
        "park", "garden", "forest", "meadow",
        "recreation_ground", "nature_reserve",
        "grass", "village_green", "cemetery",
    }

    # Columna de tipo de amenidad
    type_col = "type" if "type" in amenities_df.columns else "amenity"
    if type_col not in amenities_df.columns:
        return 0.15

    # Filtrar solo amenidades verdes
    green_mask = amenities_df[type_col].str.lower().isin(green_types)
    green_df = amenities_df[green_mask]

    if len(green_df) == 0:
        return 0.10  # Sin espacios verdes detectados

    # Calcular distancias aproximadas (formula simplificada)
    # 1 grado lat ~ 111 km, 1 grado lon ~ 111 * cos(lat) km
    cos_lat = math.cos(math.radians(lat))
    dlat = (green_df["lat"].values - lat) * 111.0
    dlon = (green_df["lon"].values - lon) * 111.0 * cos_lat
    distances_km = np.sqrt(dlat ** 2 + dlon ** 2)

    # Contar espacios verdes dentro del radio
    nearby_count = int(np.sum(distances_km <= radius_km))

    # Convertir conteo a estimacion de NDVI
    # Heuristica calibrada para ciudades mexicanas:
    # 0 parques -> 0.10 (urbano denso)
    # 1-2 parques -> 0.20 (algo de verde)
    # 3-5 parques -> 0.30 (zona moderadamente verde)
    # 6+ parques -> 0.40+ (zona muy verde)
    if nearby_count == 0:
        estimated_ndvi = 0.10
    elif nearby_count <= 2:
        estimated_ndvi = 0.20
    elif nearby_count <= 5:
        estimated_ndvi = 0.30
    else:
        # Asintoticamente se acerca a 0.55 maximo
        estimated_ndvi = min(0.55, 0.30 + nearby_count * 0.025)

    return estimated_ndvi
