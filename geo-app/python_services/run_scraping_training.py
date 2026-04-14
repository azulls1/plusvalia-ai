# ================================================================
# SCRIPT COMPLETO: SCRAPING + ENTRENAMIENTO ML
# Ejecuta scraping de múltiples ciudades y entrena el modelo
# ================================================================

import asyncio
import sys
import time
from datetime import datetime
from loguru import logger
import pandas as pd

sys.path.append('.')
from scrapers.inmuebles24_scraper import Inmuebles24Scraper
from scrapers.lamudi_scraper import LamudiScraper
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY  # Usa credenciales desde config

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# Conectar a Supabase usando credenciales del archivo .env
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Ciudades a scrapear (énfasis en Guadalajara)
CIUDADES = [
    {"city": "Guadalajara", "state": "Jalisco", "pages": 5},      # Prioridad alta
    {"city": "Zapopan", "state": "Jalisco", "pages": 4},          # Zona metropolitana GDL
    {"city": "Tlaquepaque", "state": "Jalisco", "pages": 3},      # Zona metropolitana GDL
    {"city": "Querétaro", "state": "Querétaro", "pages": 3},
    {"city": "Monterrey", "state": "Nuevo León", "pages": 3},
    {"city": "Ciudad de México", "state": "CDMX", "pages": 3},
    {"city": "Aguascalientes", "state": "Aguascalientes", "pages": 2},
    {"city": "León", "state": "Guanajuato", "pages": 2},
    {"city": "Puebla", "state": "Puebla", "pages": 2},
]

async def scrape_city_both_sources(city_data):
    """Scrapea una ciudad de ambas fuentes"""
    city = city_data['city']
    state = city_data['state']
    pages = city_data['pages']
    
    logger.info(f"{'='*60}")
    logger.info(f"Iniciando scraping: {city}, {state}")
    logger.info(f"{'='*60}")
    
    all_properties = []
    
    # Scraper Inmuebles24
    try:
        logger.info(f"[Inmuebles24] Scrapeando {city}...")
        scraper_i24 = Inmuebles24Scraper(headless=True)
        properties_i24 = await scraper_i24.scrape_city(
            city=city,
            state=state,
            property_type="terrenos",
            operation="venta",
            max_pages=pages
        )
        all_properties.extend(properties_i24)
        logger.success(f"[Inmuebles24] {len(properties_i24)} propiedades de {city}")
    except (ConnectionError, TimeoutError, OSError, ValueError) as e:
        logger.error(f"[Inmuebles24] Error en {city}: {e}")
    
    # Delay entre fuentes
    await asyncio.sleep(3)
    
    # Scraper Lamudi
    try:
        logger.info(f"[Lamudi] Scrapeando {city}...")
        scraper_lamudi = LamudiScraper(headless=True)
        properties_lamudi = await scraper_lamudi.scrape_city(
            city=city,
            state=state,
            property_type="terreno",
            operation="venta",
            max_pages=pages
        )
        all_properties.extend(properties_lamudi)
        logger.success(f"[Lamudi] {len(properties_lamudi)} propiedades de {city}")
    except (ConnectionError, TimeoutError, OSError, ValueError) as e:
        logger.error(f"[Lamudi] Error en {city}: {e}")
    
    return all_properties

async def scrape_all_cities():
    """Scrapea todas las ciudades"""
    logger.info("\n" + "="*60)
    logger.info("INICIANDO SCRAPING MASIVO")
    logger.info(f"Ciudades objetivo: {len(CIUDADES)}")
    logger.info(f"Hora inicio: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("="*60 + "\n")
    
    all_results = []
    
    for idx, city_data in enumerate(CIUDADES, 1):
        logger.info(f"\n[{idx}/{len(CIUDADES)}] Procesando: {city_data['city']}")
        
        try:
            properties = await scrape_city_both_sources(city_data)
            all_results.extend(properties)
            
            logger.info(f"Propiedades acumuladas: {len(all_results)}")
            
            # Guardar incrementalmente cada ciudad
            if properties:
                save_to_supabase(properties)
            
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            logger.error(f"Error procesando {city_data['city']}: {e}")
        
        # Delay entre ciudades
        await asyncio.sleep(5)
    
    logger.success(f"\n{'='*60}")
    logger.success(f"SCRAPING COMPLETADO")
    logger.success(f"Total propiedades: {len(all_results)}")
    logger.success(f"Hora fin: {datetime.now().strftime('%H:%M:%S')}")
    logger.success(f"{'='*60}\n")
    
    return all_results

def save_to_supabase(properties):
    """Guarda propiedades en Supabase"""
    if not properties:
        return 0
    
    logger.info(f"Guardando {len(properties)} propiedades en Supabase...")
    
    try:
        df = pd.DataFrame(properties)
        
        # Limpiar y preparar datos
        df = df.drop_duplicates(subset=['title', 'price_mxn', 'city'], keep='first')
        df = df[df['price_mxn'] > 0]
        df = df[df['area_m2'] > 0]
        
        # Agregar fecha de recolección
        df['collection_date'] = datetime.now().date().isoformat()
        
        # Insertar en Supabase (batch)
        records = df.to_dict('records')
        
        inserted = 0
        for record in records:
            try:
                # Preparar datos
                data = {
                    'title': record.get('title', 'Sin título'),
                    'price_mxn': float(record['price_mxn']),
                    'area_m2': float(record['area_m2']),
                    'address': record.get('address', ''),
                    'city': record.get('city', ''),
                    'state': record.get('state', ''),
                    'lat': record.get('lat'),
                    'lon': record.get('lon'),
                    'source': record.get('source', 'scraper'),
                    'source_url': record.get('source_url'),
                    'collection_date': record.get('collection_date')
                }
                
                # Insertar (ignorar duplicados)
                result = supabase.table('iainmobiliaria_comparables').insert(data).execute()
                if result.data:
                    inserted += 1
                    
            except Exception as e:  # Supabase client may raise various errors
                logger.debug(f"Error insertando registro: {e}")
                continue
        
        logger.success(f"Insertadas {inserted}/{len(records)} propiedades en Supabase")
        return inserted
        
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error guardando en Supabase: {e}")
        return 0

def train_ml_model():
    """Entrena el modelo ML con los datos de Supabase"""
    logger.info("\n" + "="*60)
    logger.info("INICIANDO ENTRENAMIENTO DEL MODELO ML")
    logger.info("="*60 + "\n")
    
    try:
        # Importar modelo
        from ml_model.predictor import PlusvaliaPredictorModel
        
        # Obtener datos de Supabase
        logger.info("Obteniendo datos de entrenamiento desde Supabase...")
        response = supabase.table('iainmobiliaria_comparables').select('*').execute()
        
        if not response.data:
            logger.error("No hay datos en Supabase para entrenar")
            return False
        
        df = pd.DataFrame(response.data)
        logger.info(f"Datos obtenidos: {len(df)} registros")
        
        # Verificar mínimo de muestras
        if len(df) < 100:
            logger.warning(f"Solo hay {len(df)} muestras. Se recomienda al menos 100.")
            logger.warning("Entrenando con datos disponibles...")
        
        # Entrenar modelo
        model = PlusvaliaPredictorModel(model_version="1.0")
        metrics = model.train(df)
        
        # Mostrar resultados
        logger.success("\n" + "="*60)
        logger.success("MODELO ENTRENADO EXITOSAMENTE")
        logger.success("="*60)
        logger.info(f"R² Score: {metrics['test_r2']:.4f}")
        logger.info(f"MAE: ${metrics['test_mae']:,.0f} MXN/m²")
        logger.info(f"RMSE: ${metrics['test_rmse']:,.0f} MXN/m²")
        logger.info(f"Muestras: {metrics['n_samples']}")
        logger.info(f"Features: {metrics['n_features']}")
        logger.success("="*60 + "\n")
        
        # Prueba de predicción
        logger.info("Probando predicción con Guadalajara...")
        test_pred = model.predict_price(
            lat=20.6597,
            lon=-103.3496,
            area_m2=500,
            city="Guadalajara",
            state="Jalisco"
        )
        
        logger.info(f"Precio predicho: ${test_pred['predicted_price_m2']:,.0f}/m²")
        logger.info(f"Score plusvalía: {test_pred['plusvalia_score']:.1f}/100")
        logger.info(f"Potencial: {test_pred['growth_potential']}")
        
        return True
        
    except (ValueError, KeyError, TypeError, RuntimeError) as e:
        logger.error(f"Error entrenando modelo: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    start_time = time.time()
    
    logger.info("""
    ╔═══════════════════════════════════════════════════════════╗
    ║       SISTEMA DE SCRAPING Y ENTRENAMIENTO ML              ║
    ║       Análisis de Mercado Inmobiliario                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Fase 1: Scraping
    logger.info("\n📍 FASE 1: SCRAPING DE DATOS\n")
    all_properties = await scrape_all_cities()
    
    # Fase 2: Entrenamiento
    logger.info("\n🧠 FASE 2: ENTRENAMIENTO ML\n")
    success = train_ml_model()
    
    # Resumen final
    elapsed = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info("PROCESO COMPLETADO")
    logger.info(f"{'='*60}")
    logger.info(f"Propiedades scrapeadas: {len(all_properties)}")
    logger.info(f"Modelo entrenado: {'SÍ' if success else 'NO'}")
    logger.info(f"Tiempo total: {elapsed/60:.1f} minutos")
    logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())

