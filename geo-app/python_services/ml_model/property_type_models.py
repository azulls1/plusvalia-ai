"""
Modelos especializados por tipo de propiedad.
Entrena modelos separados para residencial, comercial, terreno, etc.
Mejora precision al capturar dinamicas de mercado diferentes por segmento.
"""

import numpy as np
import pandas as pd
import joblib
import json
import yaml
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from loguru import logger
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

try:
    from xgboost import XGBRegressor
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False

try:
    import lightgbm as lgb
    _HAS_LIGHTGBM = True
except ImportError:
    _HAS_LIGHTGBM = False

from sklearn.ensemble import RandomForestRegressor

warnings.filterwarnings("ignore")

# ================================================================
# Constantes
# ================================================================

_CONFIG_PATH = Path(__file__).parent / "model_config.yaml"
_MODELS_DIR = Path(__file__).parent / "models" / "property_types"

# Minimo de muestras para entrenar modelo especializado
MIN_SAMPLES_PER_TYPE = 200

# Clasificacion de tipos de propiedad
# Mapea terminos del scraper a categorias normalizadas
PROPERTY_TYPE_MAPPING: Dict[str, str] = {
    # Residencial
    "casa": "residencial",
    "house": "residencial",
    "departamento": "residencial",
    "apartment": "residencial",
    "condominio": "residencial",
    "condo": "residencial",
    "townhouse": "residencial",
    "duplex": "residencial",
    "penthouse": "residencial",
    "residencia": "residencial",
    "residencial": "residencial",
    # Comercial
    "oficina": "comercial",
    "office": "comercial",
    "local": "comercial",
    "local_comercial": "comercial",
    "retail": "comercial",
    "comercial": "comercial",
    "mixed": "comercial",
    "uso_mixto": "comercial",
    "plaza_comercial": "comercial",
    # Terreno
    "terreno": "terreno",
    "land": "terreno",
    "lote": "terreno",
    "parcela": "terreno",
    "predio": "terreno",
    "terreno_habitacional": "terreno",
    "terreno_comercial": "terreno",
    # Industrial
    "bodega": "industrial",
    "warehouse": "industrial",
    "nave_industrial": "industrial",
    "factory": "industrial",
    "fabrica": "industrial",
    "industrial": "industrial",
    "parque_industrial": "industrial",
    # Turistico
    "hotel": "turistico",
    "vacation_rental": "turistico",
    "villa": "turistico",
    "cabana": "turistico",
    "resort": "turistico",
    "turistico": "turistico",
    "airbnb": "turistico",
}

# Zonas turisticas conocidas (para reclasificar propiedades cercanas)
TOURISM_HOTSPOTS: Dict[str, tuple] = {
    "Cancun": (21.1619, -86.8515),
    "Playa del Carmen": (20.6296, -87.0739),
    "Tulum": (20.2114, -87.4654),
    "Los Cabos": (22.8905, -109.9167),
    "Puerto Vallarta": (20.6534, -105.2253),
    "Riviera Maya": (20.5, -87.2),
    "Acapulco": (16.8531, -99.8237),
    "Mazatlan": (23.2494, -106.4111),
    "Huatulco": (15.7753, -96.1348),
    "Ixtapa": (17.6603, -101.6051),
}

TOURISM_RADIUS_KM = 30.0  # Radio para considerar propiedad como turistica


def _load_config() -> dict:
    """Carga configuracion desde YAML."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia haversine entre dos puntos en km."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def _is_near_tourism_hotspot(lat: float, lon: float) -> bool:
    """Verifica si una coordenada esta dentro del radio turistico."""
    for _name, (hlat, hlon) in TOURISM_HOTSPOTS.items():
        if _haversine_km(lat, lon, hlat, hlon) <= TOURISM_RADIUS_KM:
            return True
    return False


def normalize_property_type(
    raw_type: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> str:
    """Normaliza un tipo de propiedad crudo a categoria estandar.

    Si la propiedad esta cerca de zona turistica y su tipo no es
    claramente industrial/comercial, la reclasifica como 'turistico'.

    Args:
        raw_type: Tipo de propiedad como viene del scraper
        lat: Latitud (opcional, para deteccion turistica)
        lon: Longitud (opcional, para deteccion turistica)

    Returns:
        Tipo normalizado: 'residencial', 'comercial', 'terreno', 'industrial', 'turistico'
    """
    if not raw_type or pd.isna(raw_type):
        return "desconocido"

    # Normalizar texto
    clean = raw_type.strip().lower().replace(" ", "_").replace("-", "_")

    # Buscar en mapping
    normalized = PROPERTY_TYPE_MAPPING.get(clean, "desconocido")

    # Si es residencial y esta cerca de zona turistica, reclasificar
    if normalized in ("residencial", "desconocido") and lat is not None and lon is not None:
        if _is_near_tourism_hotspot(lat, lon):
            normalized = "turistico"

    return normalized


# ================================================================
# PropertyTypeModelManager
# ================================================================

class PropertyTypeModelManager:
    """Gestor de modelos especializados por tipo de propiedad.

    Entrena un modelo separado para cada tipo de propiedad con suficientes
    muestras, y mantiene un modelo global como fallback.

    Tipos soportados:
        - residencial: casas, departamentos, condominios
        - comercial: oficinas, locales, uso mixto
        - terreno: lotes, parcelas sin desarrollo
        - industrial: bodegas, naves industriales
        - turistico: hoteles, rentas vacacionales (cerca de zona turistica)

    Si un tipo tiene menos de MIN_SAMPLES_PER_TYPE muestras, se usa el modelo global.
    """

    def __init__(
        self,
        base_model_class: str = "xgboost",
        min_samples: int = MIN_SAMPLES_PER_TYPE,
    ):
        """Inicializa el gestor de modelos por tipo.

        Args:
            base_model_class: Tipo de modelo base ('xgboost', 'lightgbm', 'randomforest')
            min_samples: Minimo de muestras para entrenar modelo especializado
        """
        self.base_model_class = base_model_class
        self.min_samples = min_samples

        # Modelos por tipo
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.label_encoders: Dict[str, Dict[str, LabelEncoder]] = {}

        # Modelo global (fallback)
        self.global_model: Optional[Any] = None
        self.global_scaler = StandardScaler()
        self.global_label_encoders: Dict[str, LabelEncoder] = {}

        # Feature names compartidos
        self.feature_names: List[str] = []

        # Metricas por tipo
        self._metrics: Dict[str, Dict] = {}

        # Estado de entrenamiento
        self._trained_types: List[str] = []

        # Ruta de modelos
        self.model_path = _MODELS_DIR
        self.model_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Creacion de modelo base
    # ------------------------------------------------------------------

    def _create_model(self, n_samples: int = 1000) -> Any:
        """Crea una instancia del modelo base con parametros ajustados al tamano.

        Ajusta la complejidad del modelo segun el numero de muestras disponibles.
        """
        # Ajustar complejidad segun cantidad de datos
        if n_samples > 5000:
            n_estimators = 500
            max_depth = 8
        elif n_samples > 1000:
            n_estimators = 300
            max_depth = 6
        else:
            n_estimators = 200
            max_depth = 5

        if self.base_model_class == "xgboost":
            if not _HAS_XGBOOST:
                raise ImportError("XGBoost no instalado")
            return XGBRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1,
                verbosity=0,
            )
        elif self.base_model_class == "lightgbm":
            if not _HAS_LIGHTGBM:
                raise ImportError("LightGBM no instalado")
            return lgb.LGBMRegressor(
                n_estimators=n_estimators,
                num_leaves=min(63, 2 ** max_depth - 1),
                learning_rate=0.05,
                feature_fraction=0.8,
                bagging_fraction=0.8,
                bagging_freq=5,
                verbose=-1,
                random_state=42,
                n_jobs=-1,
            )
        elif self.base_model_class == "randomforest":
            return RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1,
            )
        else:
            raise ValueError(f"Tipo de modelo no soportado: {self.base_model_class}")

    # ------------------------------------------------------------------
    # Preparacion de features
    # ------------------------------------------------------------------

    def _prepare_features(
        self,
        df: pd.DataFrame,
        label_encs: Dict[str, LabelEncoder],
        fit: bool = False,
    ) -> tuple:
        """Prepara features numericos y categoricos.

        Returns:
            (X DataFrame, feature_names list)
        """
        df_f = df.copy()

        # Features derivados
        if "area_m2" in df_f.columns:
            df_f["log_area"] = np.log1p(df_f["area_m2"])
            df_f["is_large_lot"] = (df_f["area_m2"] > df_f["area_m2"].median()).astype(int)

        if "lat" in df_f.columns and "lon" in df_f.columns:
            df_f["lat_normalized"] = (df_f["lat"] - 14) / (33 - 14)
            df_f["lon_normalized"] = (df_f["lon"] - (-118)) / ((-86) - (-118))

        if "collection_date" in df_f.columns:
            dates = pd.to_datetime(df_f["collection_date"], errors="coerce")
            df_f["month"] = dates.dt.month.fillna(6).astype(int)
            df_f["quarter"] = dates.dt.quarter.fillna(2).astype(int)

        # Interacciones
        if "area_m2" in df_f.columns and "avg_income" in df_f.columns:
            df_f["area_x_income"] = df_f["area_m2"] * df_f["avg_income"]
        if "distance_to_center" in df_f.columns and "population_density" in df_f.columns:
            df_f["distance_x_density"] = df_f["distance_to_center"] * df_f["population_density"]

        # Categoricos
        for col in ["city", "state"]:
            if col in df_f.columns:
                if fit or col not in label_encs:
                    label_encs[col] = LabelEncoder()
                    df_f[f"{col}_encoded"] = label_encs[col].fit_transform(
                        df_f[col].astype(str)
                    )
                else:
                    known = set(label_encs[col].classes_)
                    safe = df_f[col].astype(str).apply(
                        lambda v: v if v in known else label_encs[col].classes_[0]
                    )
                    df_f[f"{col}_encoded"] = label_encs[col].transform(safe)

        # Seleccionar columnas de features
        candidate_cols = [
            "area_m2", "log_area", "is_large_lot",
            "lat_normalized", "lon_normalized",
            "distance_to_center",
            "population_density", "economic_level_score",
            "unemployment_rate", "avg_income", "education_index",
            "security_score", "infrastructure_score",
            "pct_vacant_housing", "population_growth",
            "median_age", "homicide_rate_per_100k", "pct_internet", "pea_pct",
            "month", "quarter",
            "area_x_income", "distance_x_density",
            "city_encoded", "state_encoded",
        ]
        feature_cols = [c for c in candidate_cols if c in df_f.columns]

        return df_f[feature_cols].fillna(0), feature_cols

    # ------------------------------------------------------------------
    # Entrenamiento
    # ------------------------------------------------------------------

    def train_all(
        self,
        df: pd.DataFrame,
        target_col: str = "price_m2",
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """Entrena modelos separados por tipo de propiedad.

        1. Clasifica cada propiedad por tipo
        2. Entrena modelo global con todos los datos
        3. Para cada tipo con suficientes muestras, entrena modelo especializado
        4. Calcula metricas comparativas

        Args:
            df: DataFrame con datos de propiedades
            target_col: Columna objetivo (precio por m2)
            test_size: Fraccion para test set

        Returns:
            dict con metricas por tipo y resumen general
        """
        logger.info(f"=== PropertyTypeModelManager entrenamiento con {len(df)} muestras ===")

        df_work = df.copy()

        # Calcular target si no existe
        if "price_m2" not in df_work.columns and "price_mxn" in df_work.columns:
            df_work["price_m2"] = df_work["price_mxn"] / df_work["area_m2"].replace(0, np.nan)

        df_work = df_work.dropna(subset=[target_col])
        df_work = df_work[df_work[target_col] > 0]

        # Clasificar propiedades por tipo
        if "property_type" in df_work.columns:
            df_work["property_type_normalized"] = df_work.apply(
                lambda r: normalize_property_type(
                    r.get("property_type", ""),
                    r.get("lat"),
                    r.get("lon"),
                ),
                axis=1,
            )
        else:
            # Si no hay columna de tipo, todas son "desconocido"
            df_work["property_type_normalized"] = "desconocido"
            logger.warning(
                "No se encontro columna 'property_type'. "
                "Usando modelo global para todo."
            )

        # Distribucion de tipos
        type_counts = df_work["property_type_normalized"].value_counts()
        logger.info(f"Distribucion de tipos de propiedad:\n{type_counts.to_string()}")

        # Log-transform del target
        df_work["log_target"] = np.log1p(df_work[target_col])

        # ---- 1. Modelo global (fallback) ----
        logger.info("Entrenando modelo GLOBAL (fallback)...")
        X_global, feature_cols = self._prepare_features(
            df_work, self.global_label_encoders, fit=True,
        )
        self.feature_names = feature_cols
        y_global = df_work["log_target"]

        X_global_scaled = pd.DataFrame(
            self.global_scaler.fit_transform(X_global),
            columns=feature_cols, index=X_global.index,
        )

        X_train_g, X_test_g, y_train_g, y_test_g = train_test_split(
            X_global_scaled, y_global, test_size=test_size, random_state=42,
        )

        self.global_model = self._create_model(n_samples=len(df_work))
        self.global_model.fit(X_train_g, y_train_g)

        # Metricas del modelo global
        y_pred_g = np.expm1(self.global_model.predict(X_test_g))
        y_test_g_orig = np.expm1(y_test_g)
        self._metrics["global"] = {
            "r2": float(r2_score(y_test_g_orig, y_pred_g)),
            "mae": float(mean_absolute_error(y_test_g_orig, y_pred_g)),
            "rmse": float(np.sqrt(mean_squared_error(y_test_g_orig, y_pred_g))),
            "n_train": len(X_train_g),
            "n_test": len(X_test_g),
        }
        logger.info(
            f"  Global: R2={self._metrics['global']['r2']:.4f}, "
            f"MAE=${self._metrics['global']['mae']:,.0f}"
        )

        # ---- 2. Modelos por tipo ----
        valid_types = [
            "residencial", "comercial", "terreno", "industrial", "turistico",
        ]

        for ptype in valid_types:
            mask = df_work["property_type_normalized"] == ptype
            n_samples = mask.sum()

            if n_samples < self.min_samples:
                logger.info(
                    f"  Tipo '{ptype}': {n_samples} muestras "
                    f"(< {self.min_samples}). Usando modelo global como fallback."
                )
                self._metrics[ptype] = {
                    "r2": None,
                    "mae": None,
                    "rmse": None,
                    "n_samples": n_samples,
                    "model": "global_fallback",
                }
                continue

            logger.info(f"  Entrenando modelo para '{ptype}' ({n_samples} muestras)...")

            df_type = df_work[mask].copy()

            # Preparar features para este tipo
            type_label_encs: Dict[str, LabelEncoder] = {}
            X_type, type_feature_cols = self._prepare_features(
                df_type, type_label_encs, fit=True,
            )
            y_type = df_type["log_target"]

            # Escalar
            type_scaler = StandardScaler()
            X_type_scaled = pd.DataFrame(
                type_scaler.fit_transform(X_type),
                columns=type_feature_cols, index=X_type.index,
            )

            # Split
            X_train_t, X_test_t, y_train_t, y_test_t = train_test_split(
                X_type_scaled, y_type, test_size=test_size, random_state=42,
            )

            # Entrenar modelo especializado
            model_t = self._create_model(n_samples=n_samples)
            model_t.fit(X_train_t, y_train_t)

            # Guardar modelo y preprocesadores
            self.models[ptype] = model_t
            self.scalers[ptype] = type_scaler
            self.label_encoders[ptype] = type_label_encs
            self._trained_types.append(ptype)

            # Metricas
            y_pred_t = np.expm1(model_t.predict(X_test_t))
            y_test_t_orig = np.expm1(y_test_t)
            self._metrics[ptype] = {
                "r2": float(r2_score(y_test_t_orig, y_pred_t)),
                "mae": float(mean_absolute_error(y_test_t_orig, y_pred_t)),
                "rmse": float(np.sqrt(mean_squared_error(y_test_t_orig, y_pred_t))),
                "n_train": len(X_train_t),
                "n_test": len(X_test_t),
                "n_samples": n_samples,
                "model": "especializado",
            }
            logger.info(
                f"    R2={self._metrics[ptype]['r2']:.4f}, "
                f"MAE=${self._metrics[ptype]['mae']:,.0f}"
            )

        # Resumen
        summary = {
            "total_samples": len(df_work),
            "types_distribution": type_counts.to_dict(),
            "trained_types": self._trained_types,
            "fallback_types": [
                t for t in valid_types if t not in self._trained_types
            ],
            "metrics": self._metrics,
            "base_model_class": self.base_model_class,
            "min_samples_threshold": self.min_samples,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Entrenamiento completado: {len(self._trained_types)} modelos "
            f"especializados + 1 global"
        )

        return summary

    # ------------------------------------------------------------------
    # Prediccion
    # ------------------------------------------------------------------

    def predict(
        self,
        features: Dict[str, Any],
        property_type: str = "desconocido",
    ) -> Dict[str, Any]:
        """Predice precio por m2 ruteando al modelo correcto segun tipo.

        Args:
            features: dict con features de la propiedad
            property_type: Tipo de propiedad (se normaliza automaticamente)

        Returns:
            dict con prediccion, tipo de modelo usado, e intervalo
        """
        if self.global_model is None:
            raise RuntimeError("Modelos no entrenados. Ejecutar train_all() primero.")

        # Normalizar tipo
        ptype = normalize_property_type(
            property_type,
            features.get("lat"),
            features.get("lon"),
        )

        # Seleccionar modelo
        if ptype in self.models:
            model = self.models[ptype]
            scaler = self.scalers[ptype]
            label_encs = self.label_encoders[ptype]
            model_used = f"especializado_{ptype}"
            logger.debug(f"Usando modelo especializado para '{ptype}'")
        else:
            model = self.global_model
            scaler = self.global_scaler
            label_encs = self.global_label_encoders
            model_used = "global_fallback"
            logger.debug(f"Tipo '{ptype}' sin modelo especializado, usando global")

        # Preparar features
        df_input = pd.DataFrame([features])
        X_input, _ = self._prepare_features(df_input, label_encs, fit=False)

        # Asegurar que las columnas coincidan con el modelo
        for col in self.feature_names:
            if col not in X_input.columns:
                X_input[col] = 0
        X_input = X_input[self.feature_names].fillna(0)

        # Escalar
        X_scaled = pd.DataFrame(
            scaler.transform(X_input), columns=self.feature_names,
        )

        # Predecir (log-space)
        y_pred_log = model.predict(X_scaled)[0]
        price_m2 = float(np.expm1(y_pred_log))
        price_m2 = max(100.0, price_m2)

        # Calcular intervalo basado en RMSE del tipo correspondiente
        type_metrics = self._metrics.get(ptype, self._metrics.get("global", {}))
        rmse = type_metrics.get("rmse", price_m2 * 0.15)
        if rmse is None:
            rmse = price_m2 * 0.15

        ci_lower = max(100.0, price_m2 - 1.96 * rmse)
        ci_upper = price_m2 + 1.96 * rmse

        return {
            "price_m2": round(price_m2, 2),
            "property_type": ptype,
            "model_used": model_used,
            "ci_lower": round(ci_lower, 2),
            "ci_upper": round(ci_upper, 2),
            "confidence": round(min(0.95, max(0.3, 1.0 - (rmse / max(price_m2, 1.0)))), 3),
        }

    # ------------------------------------------------------------------
    # Metricas
    # ------------------------------------------------------------------

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas por tipo de propiedad y comparativa con global.

        Returns:
            dict con metricas por tipo, incluyendo mejora vs modelo global
        """
        if not self._metrics:
            return {"error": "No hay metricas. Ejecutar train_all() primero."}

        global_r2 = self._metrics.get("global", {}).get("r2", 0)
        global_mae = self._metrics.get("global", {}).get("mae", 0)

        result = {}
        for ptype, metrics in self._metrics.items():
            entry = dict(metrics)

            # Calcular mejora vs global (solo para modelos especializados)
            if ptype != "global" and metrics.get("r2") is not None:
                entry["r2_improvement_vs_global"] = round(
                    metrics["r2"] - global_r2, 4
                )
                if global_mae > 0:
                    entry["mae_improvement_pct"] = round(
                        (global_mae - metrics["mae"]) / global_mae * 100, 2
                    )

            result[ptype] = entry

        return result

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def save_models(self, path: Optional[Path] = None) -> Path:
        """Guarda todos los modelos a disco."""
        save_dir = path or self.model_path
        save_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "global_model": self.global_model,
            "global_scaler": self.global_scaler,
            "global_label_encoders": self.global_label_encoders,
            "models": self.models,
            "scalers": self.scalers,
            "label_encoders": self.label_encoders,
            "feature_names": self.feature_names,
            "metrics": self._metrics,
            "trained_types": self._trained_types,
            "base_model_class": self.base_model_class,
            "min_samples": self.min_samples,
        }

        model_file = save_dir / "property_type_models.joblib"
        joblib.dump(metadata, model_file)
        logger.info(f"Modelos por tipo guardados en: {model_file}")
        return model_file

    def load_models(self, path: Optional[Path] = None) -> bool:
        """Carga modelos previamente guardados."""
        load_dir = path or self.model_path
        model_file = load_dir / "property_type_models.joblib"

        if not model_file.exists():
            logger.warning(f"No se encontraron modelos en: {model_file}")
            return False

        try:
            metadata = joblib.load(model_file)
            self.global_model = metadata["global_model"]
            self.global_scaler = metadata["global_scaler"]
            self.global_label_encoders = metadata["global_label_encoders"]
            self.models = metadata["models"]
            self.scalers = metadata["scalers"]
            self.label_encoders = metadata["label_encoders"]
            self.feature_names = metadata["feature_names"]
            self._metrics = metadata["metrics"]
            self._trained_types = metadata["trained_types"]
            self.base_model_class = metadata.get("base_model_class", "xgboost")
            self.min_samples = metadata.get("min_samples", MIN_SAMPLES_PER_TYPE)
            logger.info(
                f"Modelos por tipo cargados: {len(self._trained_types)} especializados + global"
            )
            return True
        except Exception as e:
            logger.error(f"Error cargando modelos por tipo: {e}")
            return False
