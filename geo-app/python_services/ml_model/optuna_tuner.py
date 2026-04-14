"""
Optimizacion de hiperparametros con Optuna para geo-app.
Soporta XGBoost, LightGBM, y RandomForest.
"""

import json
import numpy as np
import pandas as pd
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from loguru import logger
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler, LabelEncoder

try:
    import optuna
    from optuna.samplers import TPESampler
    _HAS_OPTUNA = True
except ImportError:
    _HAS_OPTUNA = False
    logger.warning("Optuna no instalado; OptunaModelTuner no funcionara")

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
_MODELS_DIR = Path(__file__).parent / "models"
_RESULTS_DIR = Path(__file__).parent / "tuning_results"

# Tipos de modelo soportados
SUPPORTED_MODELS = ["xgboost", "lightgbm", "randomforest"]


# ================================================================
# OptunaModelTuner
# ================================================================

class OptunaModelTuner:
    """Optimizador de hiperparametros usando Optuna con validacion cruzada.

    Soporta tres tipos de modelo:
        - xgboost: Gradient boosting con XGBoost
        - lightgbm: Gradient boosting con LightGBM
        - randomforest: Random Forest de scikit-learn

    Usa TPE (Tree-structured Parzen Estimator) como sampler por defecto.
    El target se transforma con log1p para mejor distribucion.
    """

    def __init__(
        self,
        model_type: str = "xgboost",
        n_trials: int = 100,
        cv_folds: int = 5,
        random_state: int = 42,
        timeout: Optional[int] = None,
    ):
        """Inicializa el tuner.

        Args:
            model_type: Tipo de modelo ('xgboost', 'lightgbm', 'randomforest')
            n_trials: Numero de trials de optimizacion
            cv_folds: Numero de folds para cross-validation
            random_state: Semilla para reproducibilidad
            timeout: Timeout en segundos (None = sin limite)
        """
        if not _HAS_OPTUNA:
            raise ImportError("Optuna es requerido. Instalar: pip install optuna")

        if model_type not in SUPPORTED_MODELS:
            raise ValueError(
                f"Tipo de modelo '{model_type}' no soportado. "
                f"Opciones: {SUPPORTED_MODELS}"
            )

        self.model_type = model_type
        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.timeout = timeout

        # Resultados
        self.study: Optional[optuna.Study] = None
        self.best_params: Dict[str, Any] = {}
        self.best_model: Optional[Any] = None
        self.best_score: float = 0.0

        # Preprocesamiento
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []

        # Datos preparados (se establecen en tune())
        self._X: Optional[np.ndarray] = None
        self._y: Optional[np.ndarray] = None

        # Historial
        self._optimization_history: List[Dict] = []

        # Directorio de resultados
        _RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Espacios de busqueda por modelo
    # ------------------------------------------------------------------

    def _suggest_xgboost_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Espacio de busqueda para hiperparametros de XGBoost."""
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 10.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 10.0),
            # Parametros fijos
            "random_state": self.random_state,
            "n_jobs": -1,
            "verbosity": 0,
        }

    def _suggest_lightgbm_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Espacio de busqueda para hiperparametros de LightGBM."""
        return {
            "num_leaves": trial.suggest_int("num_leaves", 15, 127),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
            "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 5, 100),
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
            "max_depth": trial.suggest_int("max_depth", -1, 12),
            "bagging_freq": trial.suggest_int("bagging_freq", 1, 7),
            # Parametros fijos
            "objective": "regression",
            "metric": "mae",
            "boosting_type": "gbdt",
            "verbose": -1,
            "random_state": self.random_state,
            "n_jobs": -1,
        }

    def _suggest_randomforest_params(self, trial: optuna.Trial) -> Dict[str, Any]:
        """Espacio de busqueda para hiperparametros de RandomForest."""
        return {
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "max_depth": trial.suggest_int("max_depth", 5, 30),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical(
                "max_features", ["sqrt", "log2", None]
            ),
            # Parametros fijos
            "random_state": self.random_state,
            "n_jobs": -1,
        }

    # ------------------------------------------------------------------
    # Creacion de modelo
    # ------------------------------------------------------------------

    def _create_model(self, params: Dict[str, Any]) -> Any:
        """Crea una instancia del modelo con los parametros dados."""
        if self.model_type == "xgboost":
            if not _HAS_XGBOOST:
                raise ImportError("XGBoost no instalado")
            return XGBRegressor(**params)
        elif self.model_type == "lightgbm":
            if not _HAS_LIGHTGBM:
                raise ImportError("LightGBM no instalado")
            return lgb.LGBMRegressor(**params)
        elif self.model_type == "randomforest":
            return RandomForestRegressor(**params)
        else:
            raise ValueError(f"Tipo de modelo no soportado: {self.model_type}")

    # ------------------------------------------------------------------
    # Funcion objetivo
    # ------------------------------------------------------------------

    def objective(self, trial: optuna.Trial, X: np.ndarray, y: np.ndarray) -> float:
        """Funcion objetivo para Optuna con cross-validation.

        Args:
            trial: Trial de Optuna
            X: Matriz de features (ya escalada)
            y: Vector target (ya log-transformado)

        Returns:
            Score negativo de MAE (Optuna minimiza por defecto)
        """
        # Sugerir hiperparametros segun tipo de modelo
        if self.model_type == "xgboost":
            params = self._suggest_xgboost_params(trial)
        elif self.model_type == "lightgbm":
            params = self._suggest_lightgbm_params(trial)
        elif self.model_type == "randomforest":
            params = self._suggest_randomforest_params(trial)
        else:
            raise ValueError(f"Tipo no soportado: {self.model_type}")

        # Crear modelo
        model = self._create_model(params)

        # Cross-validation
        kf = KFold(
            n_splits=self.cv_folds, shuffle=True, random_state=self.random_state,
        )

        # Usar scoring negativo de MAE (sklearn usa neg_mae para maximizar)
        scores = cross_val_score(
            model, X, y,
            cv=kf,
            scoring="neg_mean_absolute_error",
            n_jobs=-1,
        )

        # Retornar MAE promedio (Optuna minimiza, asi que retornamos el negativo)
        mean_mae = -scores.mean()

        return mean_mae

    # ------------------------------------------------------------------
    # Preparacion de datos
    # ------------------------------------------------------------------

    def _prepare_data(
        self, df: pd.DataFrame, target_col: str = "price_m2",
    ) -> tuple:
        """Prepara features y target para optimizacion.

        Realiza:
        1. Calculo de price_m2 si no existe
        2. Label encoding de categoricos
        3. Escalado de features
        4. Log-transform del target

        Returns:
            (X_scaled, y_log, feature_names)
        """
        df_work = df.copy()

        # Calcular target si no existe
        if "price_m2" not in df_work.columns and "price_mxn" in df_work.columns:
            df_work["price_m2"] = df_work["price_mxn"] / df_work["area_m2"].replace(0, np.nan)

        # Filtrar registros invalidos
        df_work = df_work.dropna(subset=[target_col])
        df_work = df_work[df_work[target_col] > 0]

        # Features numericos candidatos
        numeric_candidates = [
            "area_m2", "lat", "lon",
            "population_density", "economic_level_score",
            "unemployment_rate", "avg_income", "education_index",
            "security_score", "infrastructure_score",
            "pct_vacant_housing", "population_growth",
            "median_age", "homicide_rate_per_100k", "pct_internet", "pea_pct",
            "distance_to_center", "lat_normalized", "lon_normalized",
            "month", "quarter",
        ]

        # Generar features derivados si no existen
        if "lat" in df_work.columns and "lon" in df_work.columns:
            df_work["lat_normalized"] = (df_work["lat"] - 14) / (33 - 14)
            df_work["lon_normalized"] = (df_work["lon"] - (-118)) / ((-86) - (-118))

        if "area_m2" in df_work.columns:
            df_work["log_area"] = np.log1p(df_work["area_m2"])
            numeric_candidates.append("log_area")

        if "collection_date" in df_work.columns:
            dates = pd.to_datetime(df_work["collection_date"], errors="coerce")
            df_work["month"] = dates.dt.month.fillna(6).astype(int)
            df_work["quarter"] = dates.dt.quarter.fillna(2).astype(int)

        # Seleccionar columnas disponibles
        feature_cols = [c for c in numeric_candidates if c in df_work.columns]

        # Encodear categoricos
        for col in ["city", "state"]:
            if col in df_work.columns:
                le = LabelEncoder()
                df_work[f"{col}_encoded"] = le.fit_transform(df_work[col].astype(str))
                self.label_encoders[col] = le
                feature_cols.append(f"{col}_encoded")

        self.feature_names = feature_cols

        X = df_work[feature_cols].fillna(0).values
        y = df_work[target_col].values

        # Escalar features
        X_scaled = self.scaler.fit_transform(X)

        # Log-transform del target
        y_log = np.log1p(y)

        return X_scaled, y_log, feature_cols

    # ------------------------------------------------------------------
    # Optimizacion principal
    # ------------------------------------------------------------------

    def tune(
        self,
        df: pd.DataFrame,
        target_col: str = "price_m2",
    ) -> Dict[str, Any]:
        """Ejecuta la optimizacion de hiperparametros.

        Args:
            df: DataFrame con datos de propiedades
            target_col: Columna objetivo

        Returns:
            dict con mejores parametros, metricas y metadata
        """
        if not _HAS_OPTUNA:
            raise ImportError("Optuna es requerido. Instalar: pip install optuna")

        logger.info(
            f"=== Optimizacion Optuna: {self.model_type} | "
            f"{self.n_trials} trials | {self.cv_folds}-fold CV ==="
        )

        # Preparar datos
        X, y, feature_cols = self._prepare_data(df, target_col)
        self._X = X
        self._y = y
        logger.info(f"Datos preparados: {X.shape[0]} muestras, {X.shape[1]} features")

        # Crear estudio Optuna
        # Silenciar logs de Optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        self.study = optuna.create_study(
            direction="minimize",  # Minimizar MAE
            sampler=TPESampler(seed=self.random_state),
            study_name=f"geo-app-{self.model_type}-tuning",
        )

        # Ejecutar optimizacion
        self.study.optimize(
            lambda trial: self.objective(trial, X, y),
            n_trials=self.n_trials,
            timeout=self.timeout,
            show_progress_bar=False,
        )

        # Guardar mejores parametros
        self.best_params = self.study.best_params
        self.best_score = self.study.best_value

        logger.info(
            f"Optimizacion completada:\n"
            f"  Mejor MAE (log-space): {self.best_score:.6f}\n"
            f"  Mejores parametros: {json.dumps(self.best_params, indent=2)}"
        )

        # Entrenar modelo final con mejores parametros
        self._train_best_model(X, y)

        # Guardar resultados
        results = self._compile_results(df, target_col)
        self._save_results(results)

        return results

    # ------------------------------------------------------------------
    # Entrenamiento con mejores parametros
    # ------------------------------------------------------------------

    def _train_best_model(self, X: np.ndarray, y: np.ndarray) -> None:
        """Entrena el modelo final con los mejores hiperparametros en todos los datos."""
        # Agregar parametros fijos segun tipo de modelo
        full_params = dict(self.best_params)

        if self.model_type == "xgboost":
            full_params.update({
                "random_state": self.random_state,
                "n_jobs": -1,
                "verbosity": 0,
            })
        elif self.model_type == "lightgbm":
            full_params.update({
                "objective": "regression",
                "metric": "mae",
                "boosting_type": "gbdt",
                "verbose": -1,
                "random_state": self.random_state,
                "n_jobs": -1,
            })
        elif self.model_type == "randomforest":
            full_params.update({
                "random_state": self.random_state,
                "n_jobs": -1,
            })

        self.best_model = self._create_model(full_params)
        self.best_model.fit(X, y)
        logger.info(f"Modelo final entrenado con mejores parametros en {X.shape[0]} muestras")

    # ------------------------------------------------------------------
    # Compilar resultados
    # ------------------------------------------------------------------

    def _compile_results(
        self, df: pd.DataFrame, target_col: str,
    ) -> Dict[str, Any]:
        """Compila los resultados de la optimizacion en un dict resumido."""
        # Calcular metricas finales en escala original
        if self._X is not None and self._y is not None:
            y_pred_log = self.best_model.predict(self._X)
            y_pred_original = np.expm1(y_pred_log)
            y_original = np.expm1(self._y)

            final_metrics = {
                "r2": float(r2_score(y_original, y_pred_original)),
                "mae": float(mean_absolute_error(y_original, y_pred_original)),
                "rmse": float(np.sqrt(mean_squared_error(y_original, y_pred_original))),
                "mape": float(np.mean(np.abs(
                    (y_original - y_pred_original) / np.clip(y_original, 1, None)
                )) * 100),
            }
        else:
            final_metrics = {}

        # Historial de trials
        trials_history = []
        for trial in self.study.trials:
            trials_history.append({
                "number": trial.number,
                "value": trial.value,
                "params": trial.params,
                "state": str(trial.state),
            })

        return {
            "model_type": self.model_type,
            "best_params": self.best_params,
            "best_cv_mae_log": round(self.best_score, 6),
            "final_metrics": final_metrics,
            "n_trials": self.n_trials,
            "n_completed_trials": len([
                t for t in self.study.trials
                if t.state == optuna.trial.TrialState.COMPLETE
            ]),
            "cv_folds": self.cv_folds,
            "n_samples": len(df),
            "n_features": len(self.feature_names),
            "feature_names": self.feature_names,
            "optimization_history": trials_history,
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Guardar resultados
    # ------------------------------------------------------------------

    def _save_results(self, results: Dict[str, Any]) -> None:
        """Guarda los resultados de optimizacion a disco."""
        # Guardar mejores parametros como JSON
        params_file = _RESULTS_DIR / f"best_params_{self.model_type}.json"
        params_to_save = {
            "model_type": self.model_type,
            "best_params": results["best_params"],
            "best_cv_mae_log": results["best_cv_mae_log"],
            "final_metrics": results["final_metrics"],
            "n_trials": results["n_trials"],
            "timestamp": results["timestamp"],
        }
        with open(params_file, "w", encoding="utf-8") as f:
            json.dump(params_to_save, f, indent=2, ensure_ascii=False)
        logger.info(f"Mejores parametros guardados en: {params_file}")

        # Guardar historial de optimizacion como CSV
        history_file = _RESULTS_DIR / f"optimization_history_{self.model_type}.csv"
        history_records = []
        for trial in results["optimization_history"]:
            record = {
                "trial_number": trial["number"],
                "mae_log": trial["value"],
                "state": trial["state"],
            }
            record.update(trial["params"])
            history_records.append(record)

        if history_records:
            pd.DataFrame(history_records).to_csv(history_file, index=False)
            logger.info(f"Historial de optimizacion guardado en: {history_file}")

    # ------------------------------------------------------------------
    # Obtener mejor modelo
    # ------------------------------------------------------------------

    def get_best_model(self) -> Any:
        """Retorna el modelo entrenado con los mejores hiperparametros.

        Returns:
            Instancia del modelo entrenado (XGBRegressor, LGBMRegressor, o RandomForestRegressor)

        Raises:
            RuntimeError: Si no se ha ejecutado tune() previamente
        """
        if self.best_model is None:
            raise RuntimeError(
                "No hay modelo disponible. Ejecutar tune() primero."
            )
        return self.best_model

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def get_param_importances(self) -> Dict[str, float]:
        """Retorna la importancia de cada hiperparametro en la optimizacion.

        Returns:
            dict con importancia relativa de cada hiperparametro
        """
        if self.study is None:
            raise RuntimeError("No hay estudio disponible. Ejecutar tune() primero.")

        try:
            importances = optuna.importance.get_param_importances(self.study)
            return {k: round(v, 4) for k, v in importances.items()}
        except Exception as e:
            logger.warning(f"No se pudo calcular importancia de parametros: {e}")
            return {}

    def get_optimization_summary(self) -> str:
        """Retorna un resumen legible de la optimizacion."""
        if self.study is None:
            return "No hay resultados de optimizacion disponibles."

        completed = len([
            t for t in self.study.trials
            if t.state == optuna.trial.TrialState.COMPLETE
        ])
        pruned = len([
            t for t in self.study.trials
            if t.state == optuna.trial.TrialState.PRUNED
        ])
        failed = len([
            t for t in self.study.trials
            if t.state == optuna.trial.TrialState.FAIL
        ])

        summary = (
            f"=== Resumen de Optimizacion Optuna ===\n"
            f"Modelo: {self.model_type}\n"
            f"Trials: {completed} completados, {pruned} podados, {failed} fallidos\n"
            f"Mejor MAE (log-space): {self.best_score:.6f}\n"
            f"Mejores parametros:\n"
        )
        for k, v in self.best_params.items():
            summary += f"  {k}: {v}\n"

        return summary
