# ================================================================
# SPATIAL KNN FEATURE ENGINEERING
# Computes comparable-sales features using nearest-neighbor lookups
# ================================================================

import math
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
from scipy.spatial import KDTree
from loguru import logger
from datetime import datetime


# Approximate conversion: 1 degree latitude ~ 111 km in Mexico
_DEG_TO_KM_LAT = 111.0
# Longitude varies by latitude; at ~23 deg N (center of Mexico) ~ 102 km
_DEG_TO_KM_LON_DEFAULT = 102.0


# ================================================================
# Puntos de referencia geografica para features de distancia
# Coordenadas (lat, lon) de puntos representativos
# ================================================================

# Puntos costeros de Mexico (muestreo representativo)
COAST_POINTS: List[Tuple[float, float]] = [
    # Costa del Pacifico (norte a sur)
    (32.53, -117.12),   # Tijuana, BC
    (31.30, -113.53),   # Puerto Penasco, Son
    (27.92, -110.89),   # Los Mochis, Sin
    (23.24, -106.42),   # Mazatlan, Sin
    (20.65, -105.25),   # Puerto Vallarta, Jal
    (19.06, -104.32),   # Manzanillo, Col
    (17.63, -101.55),   # Acapulco, Gro
    (16.86, -99.88),    # Acapulco (este), Gro
    (15.67, -96.49),    # Huatulco, Oax
    (14.72, -92.44),    # Tapachula costa, Chis
    # Golfo de Mexico (norte a sur)
    (25.87, -97.50),    # Matamoros, Tam
    (22.20, -97.85),    # Tampico, Tam
    (19.80, -96.37),    # Tuxpan, Ver
    (19.20, -96.13),    # Veracruz, Ver
    (18.65, -95.20),    # Coatzacoalcos, Ver
    (18.50, -92.65),    # Ciudad del Carmen, Camp
    (21.17, -86.85),    # Cancun, QR
    (20.50, -87.37),    # Playa del Carmen, QR
    (20.97, -89.62),    # Progreso, Yuc
    # Mar de Cortes
    (24.14, -110.31),   # La Paz, BCS
    (22.89, -109.92),   # Cabo San Lucas, BCS
    (28.63, -111.88),   # Bahia de Kino, Son
    (30.85, -112.82),   # Puerto Libertad, Son
]

# Puntos de la frontera Mexico-EEUU (oeste a este)
BORDER_POINTS: List[Tuple[float, float]] = [
    (32.54, -117.04),   # Tijuana - San Ysidro
    (32.49, -116.62),   # Tecate
    (32.66, -115.50),   # Mexicali
    (32.38, -114.76),   # San Luis Rio Colorado
    (31.33, -110.94),   # Nogales
    (31.30, -109.54),   # Agua Prieta
    (31.74, -106.43),   # Ciudad Juarez
    (29.56, -104.41),   # Ojinaga
    (28.71, -100.52),   # Piedras Negras
    (27.48, -99.50),    # Nuevo Laredo
    (26.00, -98.23),    # Reynosa
    (25.87, -97.50),    # Matamoros
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in kilometers between two (lat, lon) points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


class SpatialFeatureEngine:
    """Builds spatial KNN features from a corpus of property transactions.

    At initialization (or via ``fit``), a KDTree is built from all known
    property coordinates.  At query time, features like *avg_price_m2_1km*
    are computed on-the-fly from the K nearest neighbours within the
    requested radii.

    Coordinates are stored in a Cartesian approximation (km offsets from
    a reference point) so that Euclidean KDTree distances approximate
    real-world distances.
    """

    def __init__(self):
        self._tree: Optional[KDTree] = None
        self._coords_km: Optional[np.ndarray] = None  # (N, 2)
        self._prices_m2: Optional[np.ndarray] = None
        self._timestamps: Optional[np.ndarray] = None  # ordinal days
        self._states: Optional[np.ndarray] = None
        self._cities: Optional[np.ndarray] = None
        self._ref_lat: float = 23.0  # center of Mexico
        self._ref_lon: float = -102.0

        # Fallback averages per city/state when no neighbours are found
        self._city_avg_price_m2: Dict[str, float] = {}
        self._state_avg_price_m2: Dict[str, float] = {}
        self._global_avg_price_m2: float = 5000.0

        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _to_km(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert (lat, lon) to approximate (x_km, y_km) relative to ref."""
        y = (lat - self._ref_lat) * _DEG_TO_KM_LAT
        x = (lon - self._ref_lon) * _DEG_TO_KM_LON_DEFAULT * math.cos(math.radians(lat))
        return x, y

    def _to_km_array(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        """Vectorised version returning (N, 2) array."""
        y = (lats - self._ref_lat) * _DEG_TO_KM_LAT
        x = (lons - self._ref_lon) * _DEG_TO_KM_LON_DEFAULT * np.cos(np.radians(lats))
        return np.column_stack([x, y])

    # ------------------------------------------------------------------
    # Fit (build the KDTree)
    # ------------------------------------------------------------------

    def fit(self, df: pd.DataFrame) -> "SpatialFeatureEngine":
        """Build the spatial index from training data.

        Parameters
        ----------
        df : DataFrame
            Must contain ``lat``, ``lon``, ``price_m2`` (or ``price_mxn`` +
            ``area_m2``).  Optionally ``collection_date``, ``city``, ``state``.
        """
        required = {"lat", "lon"}
        missing = required - set(df.columns)
        if missing:
            logger.warning(f"SpatialFeatureEngine.fit: missing columns {missing}; skipping")
            return self

        df_clean = df.dropna(subset=["lat", "lon"]).copy()

        # Ensure price_m2 exists
        if "price_m2" not in df_clean.columns:
            if "price_mxn" in df_clean.columns and "area_m2" in df_clean.columns:
                df_clean["price_m2"] = df_clean["price_mxn"] / df_clean["area_m2"].replace(0, np.nan)
                df_clean = df_clean.dropna(subset=["price_m2"])
            else:
                logger.warning("SpatialFeatureEngine.fit: no price data available; skipping")
                return self

        # Filter obviously bad coordinates (outside Mexico bounding box)
        mask = (
            (df_clean["lat"].between(14.0, 33.0)) &
            (df_clean["lon"].between(-118.0, -86.0)) &
            (df_clean["price_m2"] > 0)
        )
        df_clean = df_clean[mask].reset_index(drop=True)

        if len(df_clean) < 5:
            logger.warning(f"SpatialFeatureEngine.fit: only {len(df_clean)} valid rows; not enough")
            return self

        # Build arrays
        lats = df_clean["lat"].values.astype(np.float64)
        lons = df_clean["lon"].values.astype(np.float64)
        self._coords_km = self._to_km_array(lats, lons)
        self._prices_m2 = df_clean["price_m2"].values.astype(np.float64)

        # Timestamps (ordinal days for trend calculation)
        if "collection_date" in df_clean.columns:
            dates = pd.to_datetime(df_clean["collection_date"], errors="coerce")
            self._timestamps = dates.map(
                lambda d: d.toordinal() if pd.notna(d) else np.nan
            ).values.astype(np.float64)
        else:
            self._timestamps = np.full(len(df_clean), np.nan)

        # City / state for fallbacks
        self._cities = df_clean.get("city", pd.Series([""] * len(df_clean))).values
        self._states = df_clean.get("state", pd.Series([""] * len(df_clean))).values

        # Build KDTree
        self._tree = KDTree(self._coords_km)

        # Precompute fallback averages
        if "city" in df_clean.columns:
            self._city_avg_price_m2 = df_clean.groupby("city")["price_m2"].mean().to_dict()
        if "state" in df_clean.columns:
            self._state_avg_price_m2 = df_clean.groupby("state")["price_m2"].mean().to_dict()
        self._global_avg_price_m2 = float(df_clean["price_m2"].mean())

        self._is_fitted = True
        logger.info(
            f"SpatialFeatureEngine fitted with {len(df_clean)} properties "
            f"(KDTree built, global avg price/m2 = ${self._global_avg_price_m2:,.0f})"
        )
        return self

    # ------------------------------------------------------------------
    # Query features for a single point
    # ------------------------------------------------------------------

    def _fallback_price(self, city: str = "", state: str = "") -> float:
        """Return best available fallback average price/m2."""
        if city and city in self._city_avg_price_m2:
            return self._city_avg_price_m2[city]
        if state and state in self._state_avg_price_m2:
            return self._state_avg_price_m2[state]
        return self._global_avg_price_m2

    def compute_features(
        self,
        lat: float,
        lon: float,
        city: str = "",
        state: str = "",
        k_max: int = 50,
    ) -> Dict[str, float]:
        """Compute spatial KNN features for a single property location.

        Parameters
        ----------
        lat, lon : float
            Property coordinates.
        city, state : str
            Used for fallback averages when no neighbours are found.
        k_max : int
            Maximum neighbours to retrieve from KDTree (pre-filter by radius).

        Returns
        -------
        dict with keys:
            avg_price_m2_1km, avg_price_m2_5km, median_price_m2_5km,
            comparable_count_1km, comparable_count_5km, price_trend_5km,
            nearest_price_m2, nearest_distance_km
        """
        fallback = self._fallback_price(city, state)

        default_features = {
            "avg_price_m2_1km": fallback,
            "avg_price_m2_5km": fallback,
            "median_price_m2_5km": fallback,
            "comparable_count_1km": 0.0,
            "comparable_count_5km": 0.0,
            "price_trend_5km": 0.0,
            "nearest_price_m2": fallback,
            "nearest_distance_km": 10.0,
        }

        if not self._is_fitted or self._tree is None:
            return default_features

        # Query KDTree
        point_km = np.array(self._to_km(lat, lon)).reshape(1, 2)

        # Query at most k_max neighbours within 10 km (generous radius)
        k = min(k_max, len(self._prices_m2))
        distances, indices = self._tree.query(point_km, k=k)
        distances = distances.flatten()
        indices = indices.flatten()

        # Filter valid indices (KDTree may return inf for sparse regions)
        valid = (distances < 10.0) & (indices < len(self._prices_m2))
        distances = distances[valid]
        indices = indices[valid]

        if len(indices) == 0:
            return default_features

        prices = self._prices_m2[indices]
        timestamps = self._timestamps[indices] if self._timestamps is not None else None

        # 1 km radius
        mask_1km = distances <= 1.0
        prices_1km = prices[mask_1km]

        # 5 km radius
        mask_5km = distances <= 5.0
        prices_5km = prices[mask_5km]

        features = {}

        # avg_price_m2_1km
        features["avg_price_m2_1km"] = (
            float(np.mean(prices_1km)) if len(prices_1km) > 0 else fallback
        )

        # avg_price_m2_5km
        features["avg_price_m2_5km"] = (
            float(np.mean(prices_5km)) if len(prices_5km) > 0 else fallback
        )

        # median_price_m2_5km
        features["median_price_m2_5km"] = (
            float(np.median(prices_5km)) if len(prices_5km) > 0 else fallback
        )

        # comparable counts
        features["comparable_count_1km"] = float(len(prices_1km))
        features["comparable_count_5km"] = float(len(prices_5km))

        # price_trend_5km (slope of price vs time for 5km neighbours)
        features["price_trend_5km"] = 0.0
        if timestamps is not None and len(prices_5km) >= 3:
            ts_5km = timestamps[mask_5km]
            valid_ts = ~np.isnan(ts_5km)
            if valid_ts.sum() >= 3:
                t = ts_5km[valid_ts]
                p = prices_5km[valid_ts]
                # Normalise time to years
                t_years = (t - t.min()) / 365.25
                if t_years.max() > 0:
                    try:
                        slope = float(np.polyfit(t_years, p, 1)[0])
                        features["price_trend_5km"] = slope
                    except (np.linalg.LinAlgError, ValueError):
                        pass

        # Nearest neighbour info
        features["nearest_price_m2"] = float(prices[0])
        features["nearest_distance_km"] = float(distances[0])

        # ---- Features nuevos (v2) ----

        # Desviacion estandar de precios en 5km (volatilidad de precios local)
        if len(prices_5km) >= 2:
            features["price_std_5km"] = float(np.std(prices_5km, ddof=1))
        else:
            features["price_std_5km"] = 0.0

        # Ratio precio 1km / 5km (indicador de premium/descuento local)
        avg_1km = features["avg_price_m2_1km"]
        avg_5km = features["avg_price_m2_5km"]
        if avg_5km > 0:
            features["price_ratio_1km_5km"] = avg_1km / avg_5km
        else:
            features["price_ratio_1km_5km"] = 1.0

        # Precio ponderado por distancia inversa (IDW)
        if len(prices) > 0:
            # Evitar division por cero: distancia minima de 0.01 km
            safe_distances = np.maximum(distances[:len(prices)], 0.01)
            weights = 1.0 / safe_distances
            features["inverse_distance_weighted_price"] = float(
                np.average(prices, weights=weights)
            )
        else:
            features["inverse_distance_weighted_price"] = fallback

        # Percentil del precio dentro de la distribucion estatal
        features["price_percentile_in_state"] = self._compute_state_percentile(
            state, fallback
        )

        # Distancia a la costa mas cercana (km)
        features["distance_to_coast_km"] = self._min_distance_to_points(
            lat, lon, COAST_POINTS
        )

        # Distancia a la frontera EEUU mas cercana (km)
        features["distance_to_us_border_km"] = self._min_distance_to_points(
            lat, lon, BORDER_POINTS
        )

        # Distancia a la carretera principal mas cercana (placeholder)
        # Se enriquecera con datos de OSM/SCT en una fase posterior
        features["distance_to_nearest_highway_km"] = 0.0

        return features

    # ------------------------------------------------------------------
    # Helpers para features de distancia y percentiles
    # ------------------------------------------------------------------

    @staticmethod
    def _min_distance_to_points(
        lat: float, lon: float, reference_points: List[Tuple[float, float]]
    ) -> float:
        """Calcula la distancia minima en km a una lista de puntos de referencia.

        Parameters
        ----------
        lat, lon : float
            Coordenadas del punto de consulta.
        reference_points : list of (lat, lon)
            Lista de puntos de referencia (costa, frontera, etc.).

        Returns
        -------
        float
            Distancia en km al punto mas cercano. Retorna 9999.0 si no hay puntos.
        """
        if not reference_points:
            return 9999.0

        min_dist = float("inf")
        for ref_lat, ref_lon in reference_points:
            dist = _haversine_km(lat, lon, ref_lat, ref_lon)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def _compute_state_percentile(self, state: str, price_m2: float) -> float:
        """Calcula el percentil de un precio dentro de su distribucion estatal.

        Busca todas las propiedades del mismo estado en el corpus de
        entrenamiento y calcula en que percentil cae el precio dado.

        Parameters
        ----------
        state : str
            Nombre del estado.
        price_m2 : float
            Precio por m2 de la propiedad.

        Returns
        -------
        float
            Percentil (0-100). Retorna 50.0 si no hay datos del estado.
        """
        if not self._is_fitted or self._states is None:
            return 50.0

        # Filtrar precios del mismo estado
        state_mask = self._states == state
        if not np.any(state_mask):
            return 50.0

        state_prices = self._prices_m2[state_mask]
        if len(state_prices) < 2:
            return 50.0

        # Calcular percentil usando interpolacion lineal
        percentile = float(
            np.searchsorted(np.sort(state_prices), price_m2)
            / len(state_prices)
            * 100.0
        )
        return min(100.0, max(0.0, percentile))

    # ------------------------------------------------------------------
    # Batch: add spatial features to a whole DataFrame
    # ------------------------------------------------------------------

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add spatial features to every row of *df* (must have lat, lon).

        Modifies ``df`` in-place and returns it.
        """
        if not self._is_fitted:
            logger.warning("SpatialFeatureEngine not fitted; returning default features")
            for col in [
                "avg_price_m2_1km", "avg_price_m2_5km", "median_price_m2_5km",
                "comparable_count_1km", "comparable_count_5km", "price_trend_5km",
                "nearest_price_m2", "nearest_distance_km",
                "price_std_5km", "price_ratio_1km_5km",
                "inverse_distance_weighted_price",
                "price_percentile_in_state",
                "distance_to_coast_km", "distance_to_us_border_km",
                "distance_to_nearest_highway_km",
            ]:
                if "price" in col and "ratio" not in col and "percentile" not in col:
                    df[col] = self._global_avg_price_m2
                elif "ratio" in col:
                    df[col] = 1.0
                elif "percentile" in col:
                    df[col] = 50.0
                else:
                    df[col] = 0.0
            return df

        if "lat" not in df.columns or "lon" not in df.columns:
            logger.warning("SpatialFeatureEngine.transform: no lat/lon columns")
            return df

        logger.info(f"Computing spatial features for {len(df)} rows...")
        results = []
        cities = df["city"].values if "city" in df.columns else [""] * len(df)
        states = df["state"].values if "state" in df.columns else [""] * len(df)

        for i in range(len(df)):
            feat = self.compute_features(
                lat=df["lat"].iloc[i],
                lon=df["lon"].iloc[i],
                city=str(cities[i]),
                state=str(states[i]),
            )
            results.append(feat)

        feat_df = pd.DataFrame(results, index=df.index)
        for col in feat_df.columns:
            df[col] = feat_df[col]

        logger.info("Spatial features computed successfully")
        return df

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def get_state(self) -> dict:
        """Return serializable state for saving alongside the model."""
        if not self._is_fitted:
            return {"fitted": False}
        return {
            "fitted": True,
            "n_properties": len(self._prices_m2),
            "global_avg_price_m2": self._global_avg_price_m2,
            "city_avg_price_m2": self._city_avg_price_m2,
            "state_avg_price_m2": self._state_avg_price_m2,
            "coords_km": self._coords_km,
            "prices_m2": self._prices_m2,
            "timestamps": self._timestamps,
            "cities": self._cities,
            "states": self._states,
            "ref_lat": self._ref_lat,
            "ref_lon": self._ref_lon,
        }

    def load_state(self, state: dict) -> "SpatialFeatureEngine":
        """Restore from a previously saved state dict."""
        if not state.get("fitted", False):
            return self
        self._coords_km = state["coords_km"]
        self._prices_m2 = state["prices_m2"]
        self._timestamps = state.get("timestamps")
        self._cities = state.get("cities")
        self._states = state.get("states")
        self._ref_lat = state.get("ref_lat", 23.0)
        self._ref_lon = state.get("ref_lon", -102.0)
        self._global_avg_price_m2 = state.get("global_avg_price_m2", 5000.0)
        self._city_avg_price_m2 = state.get("city_avg_price_m2", {})
        self._state_avg_price_m2 = state.get("state_avg_price_m2", {})
        self._tree = KDTree(self._coords_km)
        self._is_fitted = True
        logger.info(f"SpatialFeatureEngine restored with {len(self._prices_m2)} properties")
        return self
