"""
Enriquecimiento a nivel AGEB (Area Geoestadistica Basica) de INEGI.
Reemplaza promedios por ciudad con datos granulares por zona (~65K AGEBs urbanos).

Los AGEBs son la unidad censal basica de INEGI. Cada AGEB urbano contiene
entre 25 y 50 manzanas (~2,500 habitantes). Esto permite features
demograficos mucho mas precisos que los promedios municipales.

Fuentes de datos:
- Censo de Poblacion y Vivienda 2020 (INEGI)
- Indice de Marginacion 2020 (CONAPO)
- Encuesta Intercensal (INEGI)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger

try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOPANDAS_AVAILABLE = True
except ImportError:
    gpd = None
    Point = None
    GEOPANDAS_AVAILABLE = False
    logger.warning(
        "geopandas/shapely no instalados. Ejecuta: pip install geopandas shapely"
    )


# Columnas AGEB que generamos como features del modelo
AGEB_FEATURE_COLUMNS = [
    "ageb_population_density",
    "ageb_marginalization_index",
    "ageb_education_level",
    "ageb_income_proxy",
    "ageb_pct_internet",
    "ageb_pct_vacant_housing",
    "ageb_infrastructure_score",
]

# Mapeo de columnas del censo INEGI a nuestros features internos
# Las claves son nombres de columnas comunes en datos de INEGI
_INEGI_COLUMN_MAP = {
    # Poblacion total
    "POBTOT": "population_total",
    # Viviendas habitadas
    "VIVTOT": "housing_total",
    "VPH_INTER": "housing_with_internet",
    "VIVPAR_DES": "vacant_housing",
    "VIVPAR_HAB": "occupied_housing",
    # Educacion - grado promedio de escolaridad
    "GRAPROES": "avg_education_years",
    # Economicos
    "PEA": "economically_active_pop",
    "POCUPADA": "employed_pop",
    # Servicios basicos
    "VPH_AGUADV": "housing_piped_water",
    "VPH_DRENAJ": "housing_drainage",
    "VPH_C_ELEC": "housing_electricity",
}


def load_ageb_data(filepath: str) -> Optional[Any]:
    """Carga datos AGEB desde un shapefile, GeoJSON o CSV.

    Soporta multiples formatos de entrada:
    - Shapefile (.shp): formato nativo de INEGI
    - GeoJSON (.geojson): formato web
    - CSV (.csv): requiere columnas de geometria o lat/lon del centroide

    Parameters
    ----------
    filepath : str
        Ruta al archivo de datos AGEB.

    Returns
    -------
    gpd.GeoDataFrame o None
        GeoDataFrame con geometrias AGEB y datos censales,
        o None si falla la carga.
    """
    if not GEOPANDAS_AVAILABLE:
        logger.error("geopandas no disponible, no se pueden cargar datos AGEB")
        return None

    try:
        if filepath.endswith(".csv"):
            # Cargar CSV y crear geometria desde columnas
            df = pd.read_csv(filepath, dtype={"CVE_AGEB": str, "CVEGEO": str})

            # Intentar encontrar columna de geometria WKT
            if "geometry" in df.columns:
                from shapely import wkt
                df["geometry"] = df["geometry"].apply(wkt.loads)
                ageb_gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
            elif "lat" in df.columns and "lon" in df.columns:
                # Solo centroides - crear puntos (menos preciso para contenciones)
                geometry = [
                    Point(lon, lat)
                    for lat, lon in zip(df["lat"], df["lon"])
                ]
                ageb_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
                logger.warning(
                    "Datos AGEB cargados como puntos (centroides). "
                    "Para mejor precision, usar shapefile con poligonos."
                )
            else:
                logger.error(
                    "CSV de AGEB no contiene columna 'geometry' ni 'lat'/'lon'"
                )
                return None
        else:
            # Shapefile o GeoJSON - geopandas los lee directamente
            ageb_gdf = gpd.read_file(filepath)

        # Asegurar CRS correcto (INEGI usa EPSG:6372 pero convertimos a WGS84)
        if ageb_gdf.crs is not None and ageb_gdf.crs.to_epsg() != 4326:
            ageb_gdf = ageb_gdf.to_crs(epsg=4326)

        # Construir indice espacial si no existe
        if not ageb_gdf.sindex:
            logger.debug("Construyendo indice espacial para AGEBs...")

        logger.info(
            f"Datos AGEB cargados: {len(ageb_gdf)} registros desde {filepath}"
        )
        return ageb_gdf

    except Exception as e:
        logger.error(f"Error cargando datos AGEB desde {filepath}: {e}")
        return None


def find_ageb_for_point(
    lat: float,
    lon: float,
    ageb_gdf: Any,
) -> Dict[str, float]:
    """Encuentra el AGEB que contiene un punto dado.

    Usa el indice espacial R-tree de geopandas para busqueda eficiente.
    Si el punto no cae dentro de ningun AGEB, busca el AGEB mas cercano
    dentro de un radio de 1 km.

    Parameters
    ----------
    lat : float
        Latitud del punto.
    lon : float
        Longitud del punto.
    ageb_gdf : gpd.GeoDataFrame
        GeoDataFrame con poligonos AGEB.

    Returns
    -------
    dict
        Diccionario con datos del AGEB encontrado, o diccionario vacio
        si no se encuentra ningun AGEB cercano.
    """
    if not GEOPANDAS_AVAILABLE or ageb_gdf is None:
        return {}

    try:
        point = Point(lon, lat)  # Shapely usa (x=lon, y=lat)

        # Buscar candidatos usando el indice espacial (bounding box)
        possible_matches_idx = list(ageb_gdf.sindex.intersection(point.bounds))

        if possible_matches_idx:
            possible_matches = ageb_gdf.iloc[possible_matches_idx]
            # Verificar contencion real (no solo bounding box)
            precise_matches = possible_matches[
                possible_matches.geometry.contains(point)
            ]

            if len(precise_matches) > 0:
                # Tomar el primer match (normalmente solo hay uno)
                ageb_row = precise_matches.iloc[0]
                return ageb_row.to_dict()

        # Fallback: buscar AGEB mas cercano dentro de ~1 km
        # Aproximacion: 0.01 grados ~ 1.1 km
        buffer = point.buffer(0.01)
        nearby_idx = list(ageb_gdf.sindex.intersection(buffer.bounds))

        if nearby_idx:
            nearby = ageb_gdf.iloc[nearby_idx]
            distances = nearby.geometry.distance(point)
            closest_idx = distances.idxmin()
            return ageb_gdf.loc[closest_idx].to_dict()

        return {}

    except Exception as e:
        logger.debug(f"Error buscando AGEB para ({lat}, {lon}): {e}")
        return {}


def _extract_ageb_features(ageb_data: Dict) -> Dict[str, float]:
    """Extrae y calcula features normalizados de un registro AGEB.

    Convierte los datos crudos del censo en features utiles para el modelo.

    Parameters
    ----------
    ageb_data : dict
        Diccionario con datos crudos del AGEB.

    Returns
    -------
    dict
        Features calculados y normalizados.
    """
    features: Dict[str, float] = {}

    # Poblacion total y area para densidad
    pop_total = _safe_float(ageb_data.get("POBTOT", ageb_data.get("population_total")))
    area_km2 = _safe_float(ageb_data.get("area_km2"))

    # Densidad poblacional (habitantes por km2)
    if pop_total > 0 and area_km2 > 0:
        features["ageb_population_density"] = pop_total / area_km2
    elif pop_total > 0:
        # Estimacion: AGEB urbano promedio ~0.5 km2
        features["ageb_population_density"] = pop_total / 0.5
    else:
        features["ageb_population_density"] = 0.0

    # Indice de marginacion (CONAPO) - ya viene calculado
    marginalization = _safe_float(
        ageb_data.get("IM_2020", ageb_data.get("marginalization_index",
        ageb_data.get("ageb_marginalization_index")))
    )
    features["ageb_marginalization_index"] = marginalization

    # Nivel educativo - grado promedio de escolaridad
    education = _safe_float(
        ageb_data.get("GRAPROES", ageb_data.get("avg_education_years",
        ageb_data.get("ageb_education_level")))
    )
    features["ageb_education_level"] = education

    # Proxy de ingreso: basado en PEA y educacion
    # Si hay datos directos de ingreso, usarlos
    income = _safe_float(
        ageb_data.get("income_proxy", ageb_data.get("ageb_income_proxy"))
    )
    if income == 0.0 and pop_total > 0:
        pea = _safe_float(ageb_data.get("PEA", ageb_data.get("economically_active_pop")))
        employed = _safe_float(ageb_data.get("POCUPADA", ageb_data.get("employed_pop")))
        # Proxy: tasa de empleo * educacion como indicador relativo
        if pea > 0:
            employment_rate = employed / pea
            income = employment_rate * max(education, 1.0) * 1000.0
        else:
            income = education * 800.0
    features["ageb_income_proxy"] = income

    # Porcentaje de viviendas con internet
    housing_total = _safe_float(
        ageb_data.get("VIVPAR_HAB", ageb_data.get("occupied_housing",
        ageb_data.get("housing_total")))
    )
    housing_internet = _safe_float(
        ageb_data.get("VPH_INTER", ageb_data.get("housing_with_internet"))
    )
    if housing_total > 0:
        features["ageb_pct_internet"] = (housing_internet / housing_total) * 100.0
    else:
        features["ageb_pct_internet"] = 0.0

    # Porcentaje de viviendas desocupadas
    housing_all = _safe_float(
        ageb_data.get("VIVTOT", ageb_data.get("housing_total"))
    )
    vacant = _safe_float(
        ageb_data.get("VIVPAR_DES", ageb_data.get("vacant_housing"))
    )
    if housing_all > 0:
        features["ageb_pct_vacant_housing"] = (vacant / housing_all) * 100.0
    else:
        features["ageb_pct_vacant_housing"] = 0.0

    # Score de infraestructura: promedio ponderado de servicios basicos
    services = []
    for service_col, service_name in [
        ("VPH_AGUADV", "housing_piped_water"),
        ("VPH_DRENAJ", "housing_drainage"),
        ("VPH_C_ELEC", "housing_electricity"),
    ]:
        val = _safe_float(ageb_data.get(service_col, ageb_data.get(service_name)))
        if housing_total > 0 and val > 0:
            services.append(val / housing_total)

    if services:
        # Score 0-100 basado en cobertura promedio de servicios
        features["ageb_infrastructure_score"] = (sum(services) / len(services)) * 100.0
    else:
        features["ageb_infrastructure_score"] = 0.0

    return features


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convierte un valor a float de forma segura.

    Parameters
    ----------
    value : Any
        Valor a convertir.
    default : float
        Valor por defecto si la conversion falla.

    Returns
    -------
    float
    """
    if value is None:
        return default
    try:
        result = float(value)
        return result if not np.isnan(result) else default
    except (ValueError, TypeError):
        return default


def get_ageb_fallback(
    city: str,
    state: str,
    demographics_cache: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """Retorna valores fallback a nivel ciudad/estado cuando no hay AGEB.

    Busca primero por ciudad, luego por estado, y finalmente retorna
    valores promedio nacionales como ultimo recurso.

    Parameters
    ----------
    city : str
        Nombre de la ciudad.
    state : str
        Nombre del estado.
    demographics_cache : dict
        Cache con promedios demograficos por ciudad y estado.
        Estructura: {"ciudad_estado": {feature: valor}, ...}

    Returns
    -------
    dict
        Features demograficos de fallback.
    """
    # Promedios nacionales como ultimo recurso (basados en Censo 2020)
    national_defaults: Dict[str, float] = {
        "ageb_population_density": 5500.0,     # hab/km2 promedio urbano
        "ageb_marginalization_index": -0.5,     # ligeramente bajo (escala CONAPO)
        "ageb_education_level": 9.7,            # grado promedio nacional
        "ageb_income_proxy": 7000.0,            # proxy relativo
        "ageb_pct_internet": 52.0,              # porcentaje nacional 2020
        "ageb_pct_vacant_housing": 14.0,        # porcentaje nacional
        "ageb_infrastructure_score": 85.0,      # cobertura promedio urbana
    }

    # Intentar buscar por ciudad
    city_key = f"{city}_{state}".lower().strip()
    if city_key in demographics_cache:
        result = national_defaults.copy()
        result.update(demographics_cache[city_key])
        return result

    # Intentar buscar por estado
    state_key = state.lower().strip()
    if state_key in demographics_cache:
        result = national_defaults.copy()
        result.update(demographics_cache[state_key])
        return result

    return national_defaults


def enrich_with_ageb(
    df: pd.DataFrame,
    ageb_gdf: Any,
    demographics_cache: Optional[Dict[str, Dict[str, float]]] = None,
) -> pd.DataFrame:
    """Enriquece un DataFrame con features a nivel AGEB.

    Para cada propiedad, busca el AGEB correspondiente y extrae
    features demograficos del censo. Si no encuentra AGEB, usa
    valores de fallback por ciudad/estado.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con columnas 'lat', 'lon'. Opcionalmente 'city', 'state'.
    ageb_gdf : gpd.GeoDataFrame
        GeoDataFrame con poligonos y datos AGEB.
    demographics_cache : dict, optional
        Cache de promedios por ciudad/estado para fallback.

    Returns
    -------
    pd.DataFrame
        DataFrame con columnas AGEB agregadas:
        - ageb_population_density
        - ageb_marginalization_index
        - ageb_education_level
        - ageb_income_proxy
        - ageb_pct_internet
        - ageb_pct_vacant_housing
        - ageb_infrastructure_score
    """
    if demographics_cache is None:
        demographics_cache = {}

    if "lat" not in df.columns or "lon" not in df.columns:
        logger.warning("Columnas lat/lon no encontradas, omitiendo enriquecimiento AGEB")
        for col in AGEB_FEATURE_COLUMNS:
            df[col] = 0.0
        return df

    has_geo = GEOPANDAS_AVAILABLE and ageb_gdf is not None
    if not has_geo:
        logger.warning(
            "GeoDataFrame AGEB no disponible, usando fallback por ciudad/estado"
        )

    logger.info(f"Enriqueciendo {len(df)} registros con datos AGEB...")

    cities = df["city"].values if "city" in df.columns else [""] * len(df)
    states = df["state"].values if "state" in df.columns else [""] * len(df)

    all_features: List[Dict[str, float]] = []
    ageb_hits = 0
    fallback_hits = 0

    for i in range(len(df)):
        lat = df["lat"].iloc[i]
        lon = df["lon"].iloc[i]
        city = str(cities[i])
        state = str(states[i])

        features: Dict[str, float] = {}

        # Intentar buscar AGEB exacto
        if has_geo:
            ageb_data = find_ageb_for_point(lat, lon, ageb_gdf)
            if ageb_data:
                features = _extract_ageb_features(ageb_data)
                ageb_hits += 1

        # Fallback si no se encontro AGEB o faltan datos
        if not features or all(v == 0.0 for v in features.values()):
            features = get_ageb_fallback(city, state, demographics_cache)
            fallback_hits += 1

        all_features.append(features)

    # Agregar columnas al DataFrame
    feat_df = pd.DataFrame(all_features, index=df.index)
    for col in AGEB_FEATURE_COLUMNS:
        if col in feat_df.columns:
            df[col] = feat_df[col].fillna(0.0)
        else:
            df[col] = 0.0

    logger.info(
        f"Enriquecimiento AGEB completado: "
        f"{ageb_hits} con AGEB directo, {fallback_hits} con fallback"
    )

    return df
