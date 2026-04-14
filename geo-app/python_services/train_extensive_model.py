# ================================================================
# ENTRENAMIENTO EXTENSIVO DE MODELO ML
# Este script ejecutará el scraping durante ~1 hora y luego entrenará el modelo
# ================================================================

import asyncio
import sys
from datetime import datetime
from loguru import logger
import pandas as pd

# Importar scrapers y modelo
sys.path.append('.')
from scrapers.unified_scraper import UnifiedScraper
from ml_model.predictor import PlusvaliaPredictorModel
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_COMPARABLES

async def save_to_supabase(df: pd.DataFrame):
    """
    Guarda los datos scrapeados en Supabase
    """
    try:
        from supabase import create_client
        
        logger.info("💾 Guardando datos en Supabase...")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Preparar datos para inserción
        records = df.to_dict('records')
        saved_count = 0
        error_count = 0
        
        # Insertar por lotes de 50 registros
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                # Preparar cada registro
                batch_prepared = []
                for record in batch:
                    # Añadir campos requeridos
                    prepared = {
                        'title': str(record.get('title', '')),
                        'price_mxn': float(record.get('price_mxn', 0)),
                        'area_m2': float(record.get('area_m2', 0)),
                        'price_m2': float(record.get('price_m2', 0)),
                        'address': str(record.get('address', '')),
                        'city': str(record.get('city', '')),
                        'state': str(record.get('state', '')),
                        'lat': float(record.get('lat', 0.0)),
                        'lon': float(record.get('lon', 0.0)),
                        'collection_date': datetime.now().isoformat(),
                        'data_source': str(record.get('source', 'unified_scraper')),
                        'url': str(record.get('url', ''))
                    }
                    batch_prepared.append(prepared)
                
                # Insertar lote
                response = supabase.table(TABLE_COMPARABLES).insert(batch_prepared).execute()
                saved_count += len(batch_prepared)
                logger.info(f"   ✓ Guardados {saved_count}/{len(records)} registros")
                
            except Exception as e:  # Supabase client may raise various errors
                error_count += len(batch)
                logger.warning(f"   ⚠ Error guardando lote {i//batch_size + 1}: {str(e)[:100]}")

        logger.success(f"✅ Guardados {saved_count} registros en Supabase (errores: {error_count})")
        return saved_count

    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"❌ Error conectando a Supabase: {e}")
        return 0


def load_from_supabase():
    """
    Carga todos los datos de Supabase para entrenamiento
    """
    try:
        from supabase import create_client
        
        logger.info("📥 Cargando datos desde Supabase...")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Obtener todos los comparables
        response = supabase.table(TABLE_COMPARABLES).select('*').execute()
        
        if not response.data:
            logger.warning("⚠️ No hay datos en Supabase")
            return None
        
        df = pd.DataFrame(response.data)
        logger.success(f"✅ Cargados {len(df)} registros desde Supabase")
        
        return df
        
    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"❌ Error cargando desde Supabase: {e}")
        return None


async def run_extensive_scraping():
    """
    Ejecuta scraping extensivo de múltiples ciudades
    """
    # Configurar ciudades objetivo - ENFOQUE EN GUADALAJARA
    CIUDADES_OBJETIVO = [
        # Guadalajara - múltiples zonas (principal para pruebas)
        {"city": "Guadalajara", "state": "Jalisco"},
        {"city": "Zapopan", "state": "Jalisco"},
        {"city": "Tlaquepaque", "state": "Jalisco"},
        {"city": "Tonalá", "state": "Jalisco"},
        {"city": "Tlajomulco de Zúñiga", "state": "Jalisco"},
        
        # Aguascalientes
        {"city": "Aguascalientes", "state": "Aguascalientes"},
        
        # Ciudad de México y área metropolitana
        {"city": "Ciudad de México", "state": "Ciudad de México"},
        {"city": "Naucalpan", "state": "Estado de México"},
        {"city": "Tlalnepantla", "state": "Estado de México"},
        
        # Otras ciudades importantes
        {"city": "Querétaro", "state": "Querétaro"},
        {"city": "Monterrey", "state": "Nuevo León"},
        {"city": "San Pedro Garza García", "state": "Nuevo León"},
        {"city": "León", "state": "Guanajuato"},
        {"city": "Puebla", "state": "Puebla"},
        {"city": "Mérida", "state": "Yucatán"},
        {"city": "Tijuana", "state": "Baja California"},
        {"city": "Cancún", "state": "Quintana Roo"},
        {"city": "San Luis Potosí", "state": "San Luis Potosí"},
    ]
    
    logger.info("="*70)
    logger.info("🚀 ENTRENAMIENTO EXTENSIVO DE MODELO ML")
    logger.info(f"   📍 Ciudades: {len(CIUDADES_OBJETIVO)}")
    logger.info(f"   ⏱️  Duración estimada: 1-2 horas")
    logger.info(f"   🎯 Enfoque especial: Guadalajara y zona metropolitana (Jalisco)")
    logger.info("="*70 + "\n")
    
    # Crear scraper unificado
    scraper = UnifiedScraper()
    
    # Ejecutar scraping con múltiples páginas
    logger.info("Fase 1: Scraping extensivo...")
    df = await scraper.scrape_all_sources(
        cities=CIUDADES_OBJETIVO,
        property_type="terreno",
        operation="venta",
        max_pages=5  # 5 páginas por ciudad y fuente
    )
    
    # Guardar en Supabase
    if df is not None and not df.empty:
        await save_to_supabase(df)
    
    return df


def train_model_with_data(df_new=None):
    """
    Entrena el modelo con todos los datos disponibles
    """
    logger.info("\n" + "="*70)
    logger.info("🤖 FASE 2: ENTRENAMIENTO DEL MODELO ML")
    logger.info("="*70)
    
    # Cargar datos existentes de Supabase
    df_existing = load_from_supabase()
    
    # Combinar con nuevos datos si existen
    if df_new is not None and not df_new.empty:
        if df_existing is not None and not df_existing.empty:
            # Combinar ambos DataFrames
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            
            # Eliminar duplicados
            df_combined = df_combined.drop_duplicates(subset=['title', 'price_mxn', 'city'], keep='last')
            
            logger.info(f"📊 Datos combinados:")
            logger.info(f"   • Datos existentes: {len(df_existing)}")
            logger.info(f"   • Datos nuevos: {len(df_new)}")
            logger.info(f"   • Total único: {len(df_combined)}")
        else:
            df_combined = df_new
    else:
        df_combined = df_existing
    
    if df_combined is None or df_combined.empty:
        logger.error("❌ No hay datos suficientes para entrenar")
        return None
    
    # Limpiar datos
    logger.info("\n🧹 Limpiando datos...")
    df_clean = df_combined.copy()
    
    # Asegurar tipos correctos
    df_clean['price_mxn'] = pd.to_numeric(df_clean['price_mxn'], errors='coerce')
    df_clean['area_m2'] = pd.to_numeric(df_clean['area_m2'], errors='coerce')
    
    # Filtrar datos válidos
    df_clean = df_clean[
        (df_clean['price_mxn'] > 0) &
        (df_clean['area_m2'] > 0) &
        (df_clean['price_mxn'] < 100_000_000) &  # Filtrar precios irreales
        (df_clean['area_m2'] < 100_000)  # Filtrar áreas irreales
    ]
    
    logger.info(f"   ✓ Datos limpios: {len(df_clean)} registros")
    
    # Verificar datos suficientes
    if len(df_clean) < 50:
        logger.warning(f"⚠️ Solo hay {len(df_clean)} muestras. Se recomienda al menos 100.")
        logger.info("   Continuando de todas formas...")
    
    # Estadísticas por ciudad
    logger.info("\n📊 Distribución por ciudad:")
    city_counts = df_clean['city'].value_counts().head(10)
    for city, count in city_counts.items():
        logger.info(f"   • {city}: {count} propiedades")
    
    # Entrenar modelo
    logger.info("\n🎯 Iniciando entrenamiento...")
    model = PlusvaliaPredictorModel(model_version="2.0")
    
    try:
        metrics = model.train(df_clean, target_col='price_m2', test_size=0.2)
        
        logger.success("\n✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        logger.info("\n📈 Métricas del modelo:")
        logger.info(f"   • R² (test): {metrics['test_r2']:.4f}")
        logger.info(f"   • MAE (test): ${metrics['test_mae']:,.0f} MXN/m²")
        logger.info(f"   • RMSE (test): ${metrics['test_rmse']:,.0f} MXN/m²")
        logger.info(f"   • Muestras: {metrics['n_samples']:,}")
        logger.info(f"   • Features: {metrics['n_features']}")
        
        # Prueba de predicción con Guadalajara
        logger.info("\n🔮 PRUEBA DE PREDICCIÓN - Guadalajara, Jalisco:")
        test_prediction = model.predict_price(
            lat=20.6597,
            lon=-103.3496,
            area_m2=500,
            city="Guadalajara",
            state="Jalisco"
        )
        
        logger.info(f"   📍 Terreno: 500 m² en Guadalajara")
        logger.info(f"   💰 Precio/m²: ${test_prediction['predicted_price_m2']:,.0f} MXN")
        logger.info(f"   💵 Precio total: ${test_prediction['predicted_total_price']:,.0f} MXN")
        logger.info(f"   📈 Score plusvalía: {test_prediction['plusvalia_score']:.1f}/100")
        logger.info(f"   🎯 Potencial: {test_prediction['growth_potential']}")
        logger.info(f"   ✅ Confianza: {test_prediction['confidence']:.1f}%")
        
        return model
        
    except (ValueError, KeyError, TypeError, RuntimeError) as e:
        logger.error(f"❌ Error durante el entrenamiento: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """
    Función principal - Ejecuta todo el proceso
    """
    start_time = datetime.now()
    
    logger.info("╔═══════════════════════════════════════════════════════════════════╗")
    logger.info("║        ENTRENAMIENTO EXTENSIVO DE MODELO ML - INICIO             ║")
    logger.info("╚═══════════════════════════════════════════════════════════════════╝")
    logger.info(f"⏰ Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Fase 1: Scraping extensivo
    df_scraped = await run_extensive_scraping()
    
    # Fase 2: Entrenamiento
    model = train_model_with_data(df_scraped)
    
    # Resumen final
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "="*70)
    logger.info("🏁 PROCESO COMPLETADO")
    logger.info("="*70)
    logger.info(f"⏰ Duración total: {duration}")
    logger.info(f"📊 Datos scrapeados: {len(df_scraped) if df_scraped is not None else 0} registros")
    logger.info(f"🤖 Modelo entrenado: {'✅ SÍ' if model is not None else '❌ NO'}")
    logger.info("="*70)


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Ejecutar proceso completo
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:  # Intentional broad catch: top-level script handler
        logger.error(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()

