"""
Modelo de ajuste estacional para zonas turisticas.
Captura variaciones de precio por temporada en destinos como Cancun, Los Cabos, PV.
"""

import math
import numpy as np
import pandas as pd
import joblib
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger

warnings.filterwarnings("ignore")

# ================================================================
# Constantes
# ================================================================

_MODELS_DIR = Path(__file__).parent / "models"

# Zonas turisticas de Mexico con coordenadas centrales y radio de influencia
TOURISM_ZONES: Dict[str, Dict[str, Any]] = {
    "Cancun": {
        "lat": 21.1619, "lon": -86.8515,
        "radius_km": 25.0,
        "tier": "premium",  # Zona de mayor impacto estacional
    },
    "Playa del Carmen": {
        "lat": 20.6296, "lon": -87.0739,
        "radius_km": 15.0,
        "tier": "premium",
    },
    "Tulum": {
        "lat": 20.2114, "lon": -87.4654,
        "radius_km": 15.0,
        "tier": "premium",
    },
    "Riviera Maya": {
        "lat": 20.5, "lon": -87.2,
        "radius_km": 40.0,
        "tier": "premium",
    },
    "Los Cabos": {
        "lat": 22.8905, "lon": -109.9167,
        "radius_km": 30.0,
        "tier": "premium",
    },
    "Puerto Vallarta": {
        "lat": 20.6534, "lon": -105.2253,
        "radius_km": 20.0,
        "tier": "high",
    },
    "Riviera Nayarit": {
        "lat": 20.8, "lon": -105.3,
        "radius_km": 30.0,
        "tier": "high",
    },
    "Acapulco": {
        "lat": 16.8531, "lon": -99.8237,
        "radius_km": 15.0,
        "tier": "medium",
    },
    "Mazatlan": {
        "lat": 23.2494, "lon": -106.4111,
        "radius_km": 15.0,
        "tier": "medium",
    },
    "Huatulco": {
        "lat": 15.7753, "lon": -96.1348,
        "radius_km": 10.0,
        "tier": "medium",
    },
    "Ixtapa Zihuatanejo": {
        "lat": 17.6603, "lon": -101.6051,
        "radius_km": 12.0,
        "tier": "medium",
    },
    "Merida": {
        "lat": 20.9674, "lon": -89.5926,
        "radius_km": 20.0,
        "tier": "low",  # Turismo cultural, menos estacional
    },
    "San Miguel de Allende": {
        "lat": 20.9144, "lon": -100.7452,
        "radius_km": 10.0,
        "tier": "low",
    },
    "Cozumel": {
        "lat": 20.4318, "lon": -86.9223,
        "radius_km": 15.0,
        "tier": "premium",
    },
}

# Definicion de temporadas para Mexico (turismo)
# Alta: Diciembre-Abril (invierno norteamericano + spring break)
# Media: Julio-Agosto (vacaciones de verano)
# Baja: Mayo-Junio, Septiembre-Noviembre
SEASON_MONTHS: Dict[str, List[int]] = {
    "alta": [12, 1, 2, 3, 4],
    "media": [7, 8],
    "baja": [5, 6, 9, 10, 11],
}

# Factores base de ajuste estacional por tier y temporada
# Estos se refinan con datos reales durante fit()
BASE_SEASONAL_FACTORS: Dict[str, Dict[str, float]] = {
    "premium": {
        "alta": 1.20,   # +20% en temporada alta
        "media": 1.08,  # +8% en verano
        "baja": 0.92,   # -8% en temporada baja
    },
    "high": {
        "alta": 1.15,   # +15%
        "media": 1.05,  # +5%
        "baja": 0.94,   # -6%
    },
    "medium": {
        "alta": 1.10,   # +10%
        "media": 1.03,  # +3%
        "baja": 0.96,   # -4%
    },
    "low": {
        "alta": 1.05,   # +5%
        "media": 1.02,  # +2%
        "baja": 0.98,   # -2%
    },
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia haversine entre dos puntos en km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


# ================================================================
# SeasonalAdjuster
# ================================================================

class SeasonalAdjuster:
    """Modelo de ajuste estacional para zonas turisticas de Mexico.

    Aprende patrones estacionales de precio a partir de datos historicos
    y aplica multiplicadores para ajustar predicciones segun la epoca del ano.

    Solo aplica ajustes a propiedades dentro del radio de zonas turisticas
    definidas. Propiedades fuera de zonas turisticas no se ajustan (factor = 1.0).

    Temporadas:
        - Alta (dic-abr): Invierno norteamericano, spring break, Semana Santa
        - Media (jul-ago): Vacaciones de verano mexicanas
        - Baja (may-jun, sep-nov): Temporada de lluvias/huracanes, baja demanda
    """

    def __init__(self):
        # Factores aprendidos por zona y mes
        # Estructura: {nombre_zona: {mes: factor}}
        self._zone_monthly_factors: Dict[str, Dict[int, float]] = {}

        # Factores base (se usan si no hay datos suficientes)
        self._base_factors = BASE_SEASONAL_FACTORS

        # Estadisticas de ajuste
        self._fit_stats: Dict[str, Any] = {}

        # Estado de entrenamiento
        self._is_fitted: bool = False

        # Minimo de muestras por zona/mes para confiar en el factor aprendido
        self._min_samples_per_month = 30

        # Ruta de persistencia
        self.model_path = _MODELS_DIR
        self.model_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Identificacion de zona turistica
    # ------------------------------------------------------------------

    def _find_nearest_zone(
        self, lat: float, lon: float,
    ) -> Optional[Tuple[str, Dict[str, Any], float]]:
        """Encuentra la zona turistica mas cercana si esta dentro del radio.

        Args:
            lat: Latitud de la propiedad
            lon: Longitud de la propiedad

        Returns:
            Tupla (nombre_zona, info_zona, distancia_km) o None si no esta en zona turistica
        """
        best_zone = None
        best_info = None
        best_distance = float("inf")

        for zone_name, zone_info in TOURISM_ZONES.items():
            dist = _haversine_km(lat, lon, zone_info["lat"], zone_info["lon"])
            if dist <= zone_info["radius_km"] and dist < best_distance:
                best_zone = zone_name
                best_info = zone_info
                best_distance = dist

        if best_zone is not None:
            return best_zone, best_info, best_distance
        return None

    def _is_in_tourism_zone(self, lat: float, lon: float) -> bool:
        """Verifica si una coordenada esta dentro de alguna zona turistica."""
        return self._find_nearest_zone(lat, lon) is not None

    # ------------------------------------------------------------------
    # Ajuste (fit)
    # ------------------------------------------------------------------

    def fit(
        self,
        df: pd.DataFrame,
        date_col: str = "collection_date",
        target_col: str = "price_m2",
    ) -> None:
        """Aprende patrones estacionales por zona turistica a partir de datos.

        Calcula el factor estacional como la relacion entre el precio promedio
        de cada mes y el precio promedio anual en cada zona.

        Args:
            df: DataFrame con datos historicos (necesita lat, lon, fecha, precio)
            date_col: Nombre de la columna de fecha
            target_col: Nombre de la columna de precio por m2
        """
        logger.info(f"=== SeasonalAdjuster fit con {len(df)} muestras ===")

        df_work = df.copy()

        # Validar columnas requeridas
        required_cols = ["lat", "lon", date_col]
        missing = [c for c in required_cols if c not in df_work.columns]
        if missing:
            logger.warning(
                f"Columnas faltantes para ajuste estacional: {missing}. "
                f"Se usaran factores base."
            )
            self._is_fitted = True
            return

        # Calcular target si no existe
        if target_col not in df_work.columns and "price_mxn" in df_work.columns:
            df_work[target_col] = df_work["price_mxn"] / df_work["area_m2"].replace(0, np.nan)

        if target_col not in df_work.columns:
            logger.warning(f"Columna '{target_col}' no encontrada. Usando factores base.")
            self._is_fitted = True
            return

        # Extraer mes de la fecha
        df_work["_month"] = pd.to_datetime(
            df_work[date_col], errors="coerce"
        ).dt.month

        # Filtrar datos validos
        df_work = df_work.dropna(subset=[target_col, "_month", "lat", "lon"])
        df_work = df_work[df_work[target_col] > 0]

        # Asignar zona turistica a cada propiedad
        def assign_zone(row):
            result = self._find_nearest_zone(row["lat"], row["lon"])
            if result:
                return result[0]  # nombre de la zona
            return None

        df_work["_zone"] = df_work.apply(assign_zone, axis=1)
        df_tourism = df_work[df_work["_zone"].notna()].copy()

        if len(df_tourism) == 0:
            logger.info(
                "No se encontraron propiedades en zonas turisticas. "
                "Se usaran factores base."
            )
            self._is_fitted = True
            return

        logger.info(
            f"Propiedades en zonas turisticas: {len(df_tourism)} "
            f"({len(df_tourism) / len(df) * 100:.1f}%)"
        )

        # Calcular factores por zona y mes
        zone_stats = {}
        for zone_name in df_tourism["_zone"].unique():
            df_zone = df_tourism[df_tourism["_zone"] == zone_name]
            zone_mean = df_zone[target_col].mean()

            if zone_mean <= 0:
                continue

            monthly_factors: Dict[int, float] = {}
            monthly_counts: Dict[int, int] = {}

            for month in range(1, 13):
                df_month = df_zone[df_zone["_month"] == month]
                monthly_counts[month] = len(df_month)

                if len(df_month) >= self._min_samples_per_month:
                    # Factor aprendido: precio mensual / precio promedio anual
                    month_mean = df_month[target_col].mean()
                    factor = month_mean / zone_mean
                    # Limitar factor a rango razonable [0.75, 1.35]
                    factor = max(0.75, min(1.35, factor))
                    monthly_factors[month] = round(factor, 4)
                else:
                    # Usar factor base para este tier
                    zone_tier = TOURISM_ZONES.get(zone_name, {}).get("tier", "medium")
                    season = self.get_season_info(month)
                    base_factor = self._base_factors.get(zone_tier, {}).get(season, 1.0)
                    monthly_factors[month] = round(base_factor, 4)

            self._zone_monthly_factors[zone_name] = monthly_factors
            zone_stats[zone_name] = {
                "n_samples": len(df_zone),
                "mean_price_m2": round(zone_mean, 2),
                "monthly_counts": monthly_counts,
                "months_learned": sum(
                    1 for m, c in monthly_counts.items()
                    if c >= self._min_samples_per_month
                ),
            }

        # Guardar estadisticas
        self._fit_stats = {
            "n_total": len(df),
            "n_tourism": len(df_tourism),
            "zones_fitted": list(self._zone_monthly_factors.keys()),
            "zone_stats": zone_stats,
            "fitted_at": datetime.now().isoformat(),
        }

        self._is_fitted = True

        logger.info(
            f"Ajuste estacional completado para {len(self._zone_monthly_factors)} zonas. "
            f"Zonas: {list(self._zone_monthly_factors.keys())}"
        )

    # ------------------------------------------------------------------
    # Factor estacional
    # ------------------------------------------------------------------

    def get_seasonal_factor(
        self, lat: float, lon: float, month: int,
    ) -> float:
        """Retorna el multiplicador estacional para una ubicacion y mes.

        Args:
            lat: Latitud de la propiedad
            lon: Longitud de la propiedad
            month: Mes del ano (1-12)

        Returns:
            Multiplicador estacional (ej: 1.15 = +15% en temporada alta).
            Retorna 1.0 si la propiedad no esta en zona turistica.
        """
        if month < 1 or month > 12:
            logger.warning(f"Mes invalido: {month}. Retornando factor 1.0")
            return 1.0

        # Buscar zona turistica
        zone_result = self._find_nearest_zone(lat, lon)
        if zone_result is None:
            return 1.0  # No es zona turistica, sin ajuste

        zone_name, zone_info, distance = zone_result

        # Buscar factor aprendido
        if zone_name in self._zone_monthly_factors:
            factor = self._zone_monthly_factors[zone_name].get(month, 1.0)
        else:
            # Usar factor base segun tier
            tier = zone_info.get("tier", "medium")
            season = self.get_season_info(month)
            factor = self._base_factors.get(tier, {}).get(season, 1.0)

        # Atenuar el factor segun distancia al centro
        # Propiedades mas lejanas del centro turistico tienen menos impacto estacional
        radius = zone_info.get("radius_km", 20.0)
        if radius > 0:
            distance_attenuation = 1.0 - (distance / radius) * 0.5
            # Factor se acerca a 1.0 conforme aumenta la distancia
            factor = 1.0 + (factor - 1.0) * max(0.5, distance_attenuation)

        return round(factor, 4)

    # ------------------------------------------------------------------
    # Ajuste de prediccion
    # ------------------------------------------------------------------

    def adjust_prediction(
        self,
        price_m2: float,
        lat: float,
        lon: float,
        month: int,
    ) -> float:
        """Aplica ajuste estacional a una prediccion de precio.

        Args:
            price_m2: Precio por m2 predicho (sin ajuste estacional)
            lat: Latitud de la propiedad
            lon: Longitud de la propiedad
            month: Mes para el que se quiere el precio ajustado

        Returns:
            Precio por m2 ajustado por temporada
        """
        factor = self.get_seasonal_factor(lat, lon, month)
        adjusted = price_m2 * factor

        if factor != 1.0:
            zone_result = self._find_nearest_zone(lat, lon)
            zone_name = zone_result[0] if zone_result else "desconocida"
            season = self.get_season_info(month)
            logger.debug(
                f"Ajuste estacional: {zone_name}, mes={month} ({season}), "
                f"factor={factor:.4f}, "
                f"${price_m2:,.0f} -> ${adjusted:,.0f}"
            )

        return round(adjusted, 2)

    # ------------------------------------------------------------------
    # Informacion de temporada
    # ------------------------------------------------------------------

    @staticmethod
    def get_season_info(month: int) -> str:
        """Retorna el nombre de la temporada para un mes dado.

        Args:
            month: Mes del ano (1-12)

        Returns:
            'alta', 'media', o 'baja'
        """
        for season_name, months in SEASON_MONTHS.items():
            if month in months:
                return season_name
        return "baja"  # Default

    def get_season_details(self, month: int) -> Dict[str, Any]:
        """Retorna informacion detallada de la temporada.

        Args:
            month: Mes del ano (1-12)

        Returns:
            dict con nombre de temporada, descripcion y meses incluidos
        """
        season = self.get_season_info(month)

        descriptions = {
            "alta": (
                "Temporada alta: invierno norteamericano, spring break y Semana Santa. "
                "Mayor demanda turistica y precios mas altos."
            ),
            "media": (
                "Temporada media: vacaciones de verano mexicanas. "
                "Demanda moderada, turismo nacional predomina."
            ),
            "baja": (
                "Temporada baja: epoca de lluvias y huracanes. "
                "Menor demanda turistica, mejores precios."
            ),
        }

        return {
            "temporada": season,
            "mes": month,
            "descripcion": descriptions.get(season, ""),
            "meses_temporada": SEASON_MONTHS.get(season, []),
        }

    # ------------------------------------------------------------------
    # Analisis completo por zona
    # ------------------------------------------------------------------

    def get_zone_analysis(
        self, lat: float, lon: float,
    ) -> Optional[Dict[str, Any]]:
        """Retorna analisis estacional completo para una ubicacion.

        Args:
            lat: Latitud
            lon: Longitud

        Returns:
            dict con informacion de zona, factores por mes, y recomendaciones.
            None si no esta en zona turistica.
        """
        zone_result = self._find_nearest_zone(lat, lon)
        if zone_result is None:
            return None

        zone_name, zone_info, distance = zone_result

        # Factores por mes
        monthly_analysis = {}
        for month in range(1, 13):
            factor = self.get_seasonal_factor(lat, lon, month)
            season = self.get_season_info(month)
            monthly_analysis[month] = {
                "factor": factor,
                "temporada": season,
                "impacto_pct": round((factor - 1.0) * 100, 2),
            }

        # Mejor y peor mes
        best_month = max(monthly_analysis, key=lambda m: monthly_analysis[m]["factor"])
        worst_month = min(monthly_analysis, key=lambda m: monthly_analysis[m]["factor"])

        # Variacion maxima
        max_factor = monthly_analysis[best_month]["factor"]
        min_factor = monthly_analysis[worst_month]["factor"]
        max_variation = round((max_factor / min_factor - 1) * 100, 2)

        return {
            "zona": zone_name,
            "tier": zone_info.get("tier", "medium"),
            "distancia_km": round(distance, 2),
            "factores_mensuales": monthly_analysis,
            "mejor_mes_venta": {
                "mes": best_month,
                "factor": max_factor,
                "temporada": self.get_season_info(best_month),
            },
            "mejor_mes_compra": {
                "mes": worst_month,
                "factor": min_factor,
                "temporada": self.get_season_info(worst_month),
            },
            "variacion_maxima_pct": max_variation,
            "recomendacion": (
                f"En {zone_name}, los precios varian hasta {max_variation}% entre "
                f"temporada alta y baja. El mejor mes para vender es "
                f"mes {best_month} ({self.get_season_info(best_month)}) y el mejor "
                f"para comprar es mes {worst_month} ({self.get_season_info(worst_month)})."
            ),
        }

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def save(self, path: Optional[Path] = None) -> Path:
        """Guarda el modelo estacional a disco."""
        save_dir = path or self.model_path
        save_dir.mkdir(parents=True, exist_ok=True)

        model_file = save_dir / "seasonal_adjuster.joblib"
        metadata = {
            "zone_monthly_factors": self._zone_monthly_factors,
            "fit_stats": self._fit_stats,
            "is_fitted": self._is_fitted,
            "min_samples_per_month": self._min_samples_per_month,
        }
        joblib.dump(metadata, model_file)
        logger.info(f"Modelo estacional guardado en: {model_file}")
        return model_file

    def load(self, path: Optional[Path] = None) -> bool:
        """Carga un modelo estacional previamente guardado."""
        load_dir = path or self.model_path
        model_file = load_dir / "seasonal_adjuster.joblib"

        if not model_file.exists():
            logger.warning(f"No se encontro modelo estacional en: {model_file}")
            return False

        try:
            metadata = joblib.load(model_file)
            self._zone_monthly_factors = metadata["zone_monthly_factors"]
            self._fit_stats = metadata.get("fit_stats", {})
            self._is_fitted = metadata.get("is_fitted", True)
            self._min_samples_per_month = metadata.get("min_samples_per_month", 30)
            logger.info(
                f"Modelo estacional cargado: "
                f"{len(self._zone_monthly_factors)} zonas"
            )
            return True
        except Exception as e:
            logger.error(f"Error cargando modelo estacional: {e}")
            return False
