"""
H3 Hexagonal Feature Engineering para geo-app.
Reemplaza lat/lon normalizadas con H3 target-encoded features.

Utiliza el sistema de indexado hexagonal H3 de Uber para crear
representaciones espaciales de alta calidad. El target encoding
con suavizado bayesiano evita overfitting en celdas con pocas muestras.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from loguru import logger

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False
    logger.warning("h3 no instalado. Ejecuta: pip install h3")


# Suavizado global por defecto para target encoding bayesiano
_DEFAULT_SMOOTHING = 10
# Muestras minimas por celda antes de usar resolucion padre
_MIN_SAMPLES_PER_CELL = 5


def latlng_to_h3(lat: float, lon: float, resolution: int = 9) -> str:
    """Convierte coordenadas (lat, lon) a un indice H3 hexagonal.

    Parameters
    ----------
    lat : float
        Latitud en grados decimales.
    lon : float
        Longitud en grados decimales.
    resolution : int
        Resolucion H3 (0-15). Por defecto 9 (~0.1 km2).
        Resoluciones comunes para inmobiliario:
        - 7: regional (~5.16 km2)
        - 9: vecindario (~0.1 km2)
        - 11: manzana (~0.001 km2)

    Returns
    -------
    str
        Indice H3 como string hexadecimal, o cadena vacia si falla.
    """
    if not H3_AVAILABLE:
        return ""

    try:
        return h3.latlng_to_cell(lat, lon, resolution)
    except Exception as e:
        logger.debug(f"Error convirtiendo ({lat}, {lon}) a H3 res={resolution}: {e}")
        return ""


def _target_encode_column(
    values: pd.Series,
    target: pd.Series,
    smoothing: int = _DEFAULT_SMOOTHING,
) -> pd.Series:
    """Target encoding bayesiano con suavizado aditivo.

    Aplica la formula:
        encoded = (n_cell * mean_cell + smoothing * global_mean) / (n_cell + smoothing)

    Esto regulariza celdas con pocas muestras hacia la media global.

    Parameters
    ----------
    values : pd.Series
        Serie con los indices H3 (o cualquier categorica).
    target : pd.Series
        Serie con la variable objetivo (precio_m2).
    smoothing : int
        Factor de suavizado. Mayor = mas conservador.

    Returns
    -------
    pd.Series
        Valores target-encoded.
    """
    global_mean = target.mean()

    # Estadisticas por grupo
    stats = target.groupby(values).agg(["mean", "count"])
    stats.columns = ["mean_cell", "n_cell"]

    # Formula de suavizado bayesiano
    stats["encoded"] = (
        (stats["n_cell"] * stats["mean_cell"] + smoothing * global_mean)
        / (stats["n_cell"] + smoothing)
    )

    # Mapear de vuelta
    encoded = values.map(stats["encoded"])
    # Rellenar valores no encontrados con la media global
    encoded = encoded.fillna(global_mean)

    return encoded


def add_h3_features(
    df: pd.DataFrame,
    target_col: str = "price_m2",
    smoothing: int = _DEFAULT_SMOOTHING,
) -> pd.DataFrame:
    """Agrega features H3 hexagonales al DataFrame.

    Genera indices H3 a dos resoluciones (regional y vecindario),
    aplica target encoding con suavizado, y cuenta vecinos por celda.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con columnas 'lat', 'lon' y target_col.
    target_col : str
        Columna objetivo para target encoding.
    smoothing : int
        Factor de suavizado para target encoding.

    Returns
    -------
    pd.DataFrame
        DataFrame con columnas adicionales:
        - h3_res7_encoded: target encoding a nivel regional (~5 km2)
        - h3_res9_encoded: target encoding a nivel vecindario (~0.1 km2)
        - h3_neighbor_count_res9: propiedades en la misma celda H3 res9
    """
    if not H3_AVAILABLE:
        logger.warning("h3 no disponible, retornando features por defecto")
        df["h3_res7_encoded"] = df[target_col].mean() if target_col in df.columns else 0.0
        df["h3_res9_encoded"] = df[target_col].mean() if target_col in df.columns else 0.0
        df["h3_neighbor_count_res9"] = 0.0
        return df

    if "lat" not in df.columns or "lon" not in df.columns:
        logger.warning("Columnas lat/lon no encontradas, omitiendo features H3")
        return df

    if target_col not in df.columns:
        logger.warning(f"Columna objetivo '{target_col}' no encontrada")
        return df

    logger.info(f"Generando features H3 para {len(df)} registros...")

    # Generar indices H3 a dos resoluciones
    df["_h3_res7"] = df.apply(
        lambda row: latlng_to_h3(row["lat"], row["lon"], resolution=7), axis=1
    )
    df["_h3_res9"] = df.apply(
        lambda row: latlng_to_h3(row["lat"], row["lon"], resolution=9), axis=1
    )

    # Contar propiedades por celda res9 para detectar celdas con pocas muestras
    cell_counts_res9 = df["_h3_res9"].value_counts()
    cell_counts_res7 = df["_h3_res7"].value_counts()

    # Fallback: si una celda res9 tiene < _MIN_SAMPLES_PER_CELL, usar la celda padre (res7)
    # Para target encoding, esto se maneja con el suavizado bayesiano,
    # pero tambien creamos un flag para celdas con datos escasos
    sparse_mask = df["_h3_res9"].map(cell_counts_res9) < _MIN_SAMPLES_PER_CELL

    # Target encoding res7 (regional)
    df["h3_res7_encoded"] = _target_encode_column(
        df["_h3_res7"], df[target_col], smoothing=smoothing
    )

    # Target encoding res9 (vecindario)
    # Para celdas con pocas muestras, usamos el encoding de res7 como fallback
    h3_res9_encoded = _target_encode_column(
        df["_h3_res9"], df[target_col], smoothing=smoothing
    )

    # En celdas sparse, mezclar con el encoding de res7 para mayor estabilidad
    df["h3_res9_encoded"] = np.where(
        sparse_mask,
        (h3_res9_encoded + df["h3_res7_encoded"]) / 2.0,
        h3_res9_encoded,
    )

    # Conteo de vecinos en la misma celda H3 res9 (excluyendo la propiedad misma)
    df["h3_neighbor_count_res9"] = (
        df["_h3_res9"].map(cell_counts_res9).fillna(0).astype(float) - 1.0
    ).clip(lower=0.0)

    # Limpiar columnas temporales
    df.drop(columns=["_h3_res7", "_h3_res9"], inplace=True)

    logger.info(
        f"Features H3 generados. "
        f"Celdas res7: {cell_counts_res7.shape[0]}, "
        f"Celdas res9: {cell_counts_res9.shape[0]}, "
        f"Celdas sparse res9: {sparse_mask.sum()}"
    )

    return df


def build_h3_lookup(
    df: pd.DataFrame,
    target_col: str = "price_m2",
    smoothing: int = _DEFAULT_SMOOTHING,
) -> Dict[str, Dict]:
    """Pre-computa target encodings H3 para usar en inferencia.

    Construye un diccionario con las estadisticas de encoding
    por celda H3, que puede ser serializado y cargado para
    prediccion sin necesidad del DataFrame completo.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame de entrenamiento con 'lat', 'lon' y target_col.
    target_col : str
        Columna objetivo.
    smoothing : int
        Factor de suavizado.

    Returns
    -------
    dict
        Diccionario con estructura:
        {
            "global_mean": float,
            "smoothing": int,
            "res7": {h3_index: {"mean": float, "count": int, "encoded": float}},
            "res9": {h3_index: {"mean": float, "count": int, "encoded": float}},
        }
    """
    if not H3_AVAILABLE:
        logger.warning("h3 no disponible, retornando lookup vacio")
        return {"global_mean": 0.0, "smoothing": smoothing, "res7": {}, "res9": {}}

    if target_col not in df.columns:
        logger.warning(f"Columna '{target_col}' no encontrada en DataFrame")
        return {"global_mean": 0.0, "smoothing": smoothing, "res7": {}, "res9": {}}

    global_mean = float(df[target_col].mean())

    # Generar indices H3
    h3_res7 = df.apply(
        lambda row: latlng_to_h3(row["lat"], row["lon"], resolution=7), axis=1
    )
    h3_res9 = df.apply(
        lambda row: latlng_to_h3(row["lat"], row["lon"], resolution=9), axis=1
    )

    lookup: Dict[str, Dict] = {
        "global_mean": global_mean,
        "smoothing": smoothing,
        "res7": {},
        "res9": {},
    }

    # Construir lookup para cada resolucion
    for res_name, h3_series in [("res7", h3_res7), ("res9", h3_res9)]:
        stats = df[target_col].groupby(h3_series).agg(["mean", "count"])
        for h3_idx, row in stats.iterrows():
            n = int(row["count"])
            mean_cell = float(row["mean"])
            encoded = (n * mean_cell + smoothing * global_mean) / (n + smoothing)
            lookup[res_name][h3_idx] = {
                "mean": mean_cell,
                "count": n,
                "encoded": encoded,
            }

    logger.info(
        f"H3 lookup construido: {len(lookup['res7'])} celdas res7, "
        f"{len(lookup['res9'])} celdas res9"
    )

    return lookup


def apply_h3_lookup(
    df: pd.DataFrame,
    lookup: Dict[str, Dict],
) -> pd.DataFrame:
    """Aplica un lookup H3 pre-computado a nuevos datos para inferencia.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con columnas 'lat' y 'lon'.
    lookup : dict
        Diccionario generado por build_h3_lookup().

    Returns
    -------
    pd.DataFrame
        DataFrame con columnas h3_res7_encoded, h3_res9_encoded,
        h3_neighbor_count_res9 agregadas.
    """
    if not H3_AVAILABLE or not lookup.get("res7"):
        global_mean = lookup.get("global_mean", 0.0)
        df["h3_res7_encoded"] = global_mean
        df["h3_res9_encoded"] = global_mean
        df["h3_neighbor_count_res9"] = 0.0
        return df

    global_mean = lookup["global_mean"]
    smoothing = lookup.get("smoothing", _DEFAULT_SMOOTHING)
    res7_lookup = lookup["res7"]
    res9_lookup = lookup["res9"]

    h3_res7_encoded = []
    h3_res9_encoded = []
    h3_neighbor_counts = []

    for _, row in df.iterrows():
        lat, lon = row.get("lat", 0.0), row.get("lon", 0.0)

        # Obtener indices H3
        idx_res7 = latlng_to_h3(lat, lon, resolution=7)
        idx_res9 = latlng_to_h3(lat, lon, resolution=9)

        # Encoding res7
        if idx_res7 in res7_lookup:
            enc_res7 = res7_lookup[idx_res7]["encoded"]
        else:
            enc_res7 = global_mean
        h3_res7_encoded.append(enc_res7)

        # Encoding res9 con fallback a res7
        if idx_res9 in res9_lookup:
            info_res9 = res9_lookup[idx_res9]
            enc_res9 = info_res9["encoded"]
            count = info_res9["count"]

            # Si la celda res9 tiene pocas muestras, promediar con res7
            if count < _MIN_SAMPLES_PER_CELL:
                enc_res9 = (enc_res9 + enc_res7) / 2.0
        else:
            # Celda nunca vista: usar encoding de res7
            enc_res9 = enc_res7
            count = 0

        h3_res9_encoded.append(enc_res9)
        h3_neighbor_counts.append(max(0.0, float(count) - 1.0))

    df["h3_res7_encoded"] = h3_res7_encoded
    df["h3_res9_encoded"] = h3_res9_encoded
    df["h3_neighbor_count_res9"] = h3_neighbor_counts

    logger.info(f"H3 lookup aplicado a {len(df)} registros")

    return df
