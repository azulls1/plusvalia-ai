"""Global configuration for the Python services (API, ML model, scraper).

Loads environment variables from .env and exposes constants used across
all modules: Supabase credentials, PostgreSQL DSN, API settings, model
paths, scraper parameters and table names.
"""

# ================================================================
# CONFIGURACIÓN GLOBAL - Python Services
# ================================================================

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ==================== PATHS ====================
BASE_DIR = Path(__file__).parent

# Cargar variables de entorno
load_dotenv(dotenv_path=BASE_DIR / '.env')
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "ml_model" / "models"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ==================== SUPABASE ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validar que las credenciales críticas estén configuradas
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logger.warning(
        "Variables de entorno faltantes: SUPABASE_URL y/o SUPABASE_SERVICE_ROLE_KEY. "
        "Ver .env.example para referencia"
    )
    SUPABASE_URL = SUPABASE_URL or None
    SUPABASE_SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY or None

# ==================== POSTGRESQL ====================
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Validar credenciales de PostgreSQL si se intenta usar DATABASE_URL
if not all([POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD]):
    logger.warning(
        "Credenciales de PostgreSQL faltantes: POSTGRES_HOST, POSTGRES_USER y/o POSTGRES_PASSWORD. "
        "Configura estos valores en el archivo .env"
    )
    POSTGRES_HOST = POSTGRES_HOST or None
    POSTGRES_USER = POSTGRES_USER or None
    POSTGRES_PASSWORD = POSTGRES_PASSWORD or None
    DATABASE_URL = None
else:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# ==================== API ====================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"
API_WORKERS = int(os.getenv("API_WORKERS", "4"))

# ==================== SCRAPER ====================
SCRAPER_DELAY = float(os.getenv("SCRAPER_DELAY_SECONDS", "2"))
SCRAPER_MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
SCRAPER_HEADLESS = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
SCRAPER_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

# ==================== ML MODEL ====================
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(MODELS_DIR)))
MODEL_RETRAIN_DAYS = int(os.getenv("MODEL_RETRAIN_DAYS", "30"))
MIN_TRAINING_SAMPLES = int(os.getenv("MIN_TRAINING_SAMPLES", "50"))

# ==================== INEGI ====================
INEGI_API_TOKEN = os.getenv("INEGI_API_TOKEN")
INEGI_BASE_URL = os.getenv(
    "INEGI_BASE_URL",
    "https://www.inegi.org.mx/app/api/indicadores/"
)

# ==================== LOGGING ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(os.getenv("LOG_FILE", str(LOGS_DIR / "app.log")))

# ==================== RATE LIMITING ====================
MAX_REQUESTS_PER_HOUR = int(os.getenv("MAX_REQUESTS_PER_HOUR", "100"))

# ==================== TABLES ====================
# Tablas principales del sistema
TABLE_COMPARABLES = "iainmobiliaria_comparables"        # Propiedades comparables
TABLE_AMENITIES = "iainmobiliaria_amenities"            # Amenidades de OpenStreetMap
TABLE_GRID_TILES = "iainmobiliaria_grid_tiles"          # Grilla de precios promedio
TABLE_PRICE_HISTORY = "iainmobiliaria_price_history"    # Histórico de precios
TABLE_INEGI_DATA = "iainmobiliaria_inegi_data"          # Datos demográficos INEGI
TABLE_PREDICTIONS = "iainmobiliaria_predictions"        # Predicciones del modelo ML
TABLE_MACRO_ECONOMICS = "iainmobiliaria_macro_economics" # Datos macroeconómicos por estado

