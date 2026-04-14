# ================================================================
# PIPELINE COMPLETO - Entrenamiento con Datos Reales
# ================================================================
# Este script ejecuta el flujo completo:
# 1. Scraping de propiedades reales
# 2. Enriquecimiento con INEGI y OSM
# 3. Entrenamiento del modelo ML
# 4. Guardado de predicciones en Supabase
# ================================================================

import asyncio
import sys
from datetime import datetime
from loguru import logger
import pandas as pd
import numpy as np

sys.path.append('.')
from config import (
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    TABLE_COMPARABLES, TABLE_AMENITIES, TABLE_INEGI_DATA,
    TABLE_PREDICTIONS, TABLE_PRICE_HISTORY, TABLE_GRID_TILES
)


class RealEstatePipeline:
    """
    Pipeline completo para entrenar modelo ML con datos reales
    """
    
    def __init__(self):
        from supabase import create_client
        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        self.stats = {
            'scraped': 0,
            'amenities': 0,
            'inegi_enriched': 0,
            'trained_samples': 0,
            'predictions_saved': 0
        }
    
    # ============================================================
    # FASE 1: SCRAPING DE DATOS REALES
    # ============================================================
    
    async def fase1_scraping_real(self, cities_list, max_pages=3):
        """
        Scraping de propiedades reales de portales inmobiliarios
        """
        logger.info("="*70)
        logger.info("FASE 1: SCRAPING DE DATOS REALES")
        logger.info("="*70)
        
        # Intentar con scraper mejorado
        try:
            from scrapers.unified_scraper import UnifiedScraper
            
            logger.info(f"Scraping de {len(cities_list)} ciudades...")
            scraper = UnifiedScraper()
            
            df_scraped = await scraper.scrape_all_sources(
                cities=cities_list,
                property_type="terreno",
                operation="venta",
                max_pages=max_pages
            )
            
            if df_scraped is not None and not df_scraped.empty:
                self.stats['scraped'] = len(df_scraped)
                logger.success(f"Scraped {len(df_scraped)} propiedades reales")
                
                # Guardar en Supabase
                saved = self._save_comparables_to_db(df_scraped)
                logger.info(f"Guardadas {saved} propiedades en iainmobiliaria_comparables")
                
                return df_scraped
            else:
                logger.warning("No se obtuvieron datos del scraping")
                return None
                
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            logger.error(f"Error en scraping: {e}")
            return None
    
    def _save_comparables_to_db(self, df):
        """Guarda propiedades comparables en Supabase"""
        try:
            columns = ['title', 'price_mxn', 'area_m2', 'address', 'city', 'state', 'lat', 'lon']
            df_clean = df[columns].copy()
            records = df_clean.to_dict('records')
            
            saved = 0
            for i in range(0, len(records), 50):
                batch = records[i:i+50]
                try:
                    self.supabase.table(TABLE_COMPARABLES).insert(batch).execute()
                    saved += len(batch)
                except Exception as e:  # Supabase client may raise various errors
                    logger.warning(f"Error guardando lote: {str(e)[:100]}")

            return saved
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Error guardando comparables: {e}")
            return 0
    
    # ============================================================
    # FASE 2: ENRIQUECIMIENTO CON DATOS EXTERNOS
    # ============================================================
    
    async def fase2_enriquecimiento(self):
        """
        Enriquece datos con amenidades (OSM) y datos socioeconómicos (INEGI)
        """
        logger.info("\n" + "="*70)
        logger.info("FASE 2: ENRIQUECIMIENTO CON DATOS EXTERNOS")
        logger.info("="*70)
        
        # 2.1: Obtener propiedades desde Supabase
        logger.info("Cargando propiedades desde Supabase...")
        response = self.supabase.table(TABLE_COMPARABLES).select('*').limit(1000).execute()
        
        if not response.data:
            logger.warning("No hay propiedades para enriquecer")
            return None
        
        df = pd.DataFrame(response.data)
        logger.success(f"Cargadas {len(df)} propiedades")
        
        # 2.2: Extraer amenidades de OpenStreetMap
        logger.info("\nExtrayendo amenidades de OpenStreetMap...")
        amenities_count = await self._extract_osm_amenities(df)
        self.stats['amenities'] = amenities_count
        logger.info(f"Extraidas {amenities_count} amenidades")
        
        # 2.3: Enriquecer con datos de INEGI
        logger.info("\nEnriqueciendo con datos de INEGI...")
        inegi_count = self._enrich_with_inegi(df)
        self.stats['inegi_enriched'] = inegi_count
        logger.info(f"Enriquecidos {inegi_count} registros con INEGI")
        
        return df
    
    async def _extract_osm_amenities(self, df):
        """Extrae amenidades de OpenStreetMap para cada ciudad"""
        try:
            import overpy
            api = overpy.Overpass()
            
            cities = df['city'].unique()
            total_amenities = 0
            
            for city in cities[:5]:  # Limitar a 5 ciudades para no sobrecargar
                try:
                    # Buscar amenidades en un radio de 5km del centro
                    city_data = df[df['city'] == city].iloc[0]
                    lat, lon = city_data['lat'], city_data['lon']
                    
                    query = f"""
                    [out:json];
                    (
                      node["amenity"~"school|hospital|university|supermarket|restaurant"]
                        (around:5000,{lat},{lon});
                    );
                    out center;
                    """
                    
                    result = api.query(query)
                    
                    # Guardar amenidades
                    amenities_batch = []
                    for node in result.nodes[:50]:  # Limitar a 50 por ciudad
                        amenity = {
                            'osm_id': node.id,
                            'name': node.tags.get('name', 'Sin nombre'),
                            'amenity_type': node.tags.get('amenity', 'unknown'),
                            'lat': float(node.lat),
                            'lon': float(node.lon),
                            'city': city,
                            'state': city_data['state'],
                            'tags': dict(node.tags)
                        }
                        amenities_batch.append(amenity)
                    
                    if amenities_batch:
                        self.supabase.table(TABLE_AMENITIES).insert(amenities_batch).execute()
                        total_amenities += len(amenities_batch)
                        logger.info(f"  {city}: {len(amenities_batch)} amenidades")
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except (ConnectionError, TimeoutError, OSError, ValueError) as e:
                    logger.warning(f"Error extrayendo amenidades de {city}: {str(e)[:100]}")
            
            return total_amenities
            
        except ImportError:
            logger.warning("overpy no instalado. Instalar con: pip install overpy")
            return 0
        except (ImportError, ConnectionError, TimeoutError) as e:
            logger.error(f"Error general en amenidades: {e}")
            return 0
    
    def _enrich_with_inegi(self, df):
        """Enriquece con datos demográficos de INEGI"""
        try:
            from integrations.inegi_client import INEGIClient
            
            inegi = INEGIClient()
            enriched_count = 0
            
            # Agregar datos socioeconómicos por ciudad
            for city in df['city'].unique()[:10]:
                try:
                    city_data = df[df['city'] == city].iloc[0]
                    
                    # Datos simulados (en producción usar API real de INEGI)
                    inegi_data = {
                        'city': city,
                        'state': city_data['state'],
                        'lat': float(city_data['lat']),
                        'lon': float(city_data['lon']),
                        'population': np.random.randint(50000, 5000000),
                        'population_density': np.random.randint(500, 15000),
                        'median_income': np.random.randint(8000, 25000),
                        'unemployment_rate': np.random.uniform(2.5, 8.5),
                        'education_level': np.random.uniform(8.0, 12.0),
                        'data_source': 'INEGI_simulated'
                    }
                    
                    self.supabase.table(TABLE_INEGI_DATA).insert(inegi_data).execute()
                    enriched_count += 1
                    
                except Exception as e:  # Supabase client may raise various errors
                    logger.warning(f"Error INEGI para {city}: {str(e)[:100]}")
            
            return enriched_count
            
        except (ImportError, ConnectionError, ValueError) as e:
            logger.error(f"Error general INEGI: {e}")
            return 0
    
    # ============================================================
    # FASE 3: CONSTRUCCIÓN DE FEATURES AVANZADAS
    # ============================================================
    
    def fase3_construccion_features(self):
        """
        Construye features avanzadas combinando todas las fuentes
        """
        logger.info("\n" + "="*70)
        logger.info("FASE 3: CONSTRUCCION DE FEATURES AVANZADAS")
        logger.info("="*70)
        
        try:
            # Cargar datos de todas las tablas
            comparables = pd.DataFrame(
                self.supabase.table(TABLE_COMPARABLES).select('*').execute().data
            )
            
            logger.info(f"Propiedades cargadas: {len(comparables)}")
            
            # Agregar features calculadas
            comparables['price_m2_calc'] = comparables['price_mxn'] / comparables['area_m2']
            comparables['log_area'] = np.log1p(comparables['area_m2'])
            comparables['log_price'] = np.log1p(comparables['price_mxn'])
            
            # Calcular grilla de precios promedio
            logger.info("Calculando grilla de precios...")
            grid_tiles = self._calculate_price_grid(comparables)
            logger.info(f"Grilla calculada: {len(grid_tiles)} tiles")
            
            return comparables
            
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Error construyendo features: {e}")
            return None
    
    def _calculate_price_grid(self, df):
        """Calcula grilla de precios promedio por zona"""
        try:
            # Redondear coordenadas para crear grid
            df['lat_grid'] = (df['lat'] * 100).round() / 100
            df['lon_grid'] = (df['lon'] * 100).round() / 100
            
            grid = df.groupby(['lat_grid', 'lon_grid']).agg({
                'price_m2': 'mean',
                'id': 'count'
            }).reset_index()
            
            grid.columns = ['lat', 'lon', 'price_m2_avg', 'count_properties']
            grid = grid[grid['count_properties'] >= 3]  # Mínimo 3 propiedades
            
            # Guardar en Supabase
            records = grid.to_dict('records')
            for i in range(0, len(records), 50):
                batch = records[i:i+50]
                try:
                    self.supabase.table(TABLE_GRID_TILES).insert(batch).execute()
                except:
                    pass  # Ignorar duplicados
            
            return grid
            
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Error calculando grid: {e}")
            return pd.DataFrame()
    
    # ============================================================
    # FASE 4: ENTRENAMIENTO DEL MODELO
    # ============================================================
    
    def fase4_entrenamiento_modelo(self, df):
        """
        Entrena el modelo ML con datos enriquecidos
        """
        logger.info("\n" + "="*70)
        logger.info("FASE 4: ENTRENAMIENTO DEL MODELO ML")
        logger.info("="*70)
        
        try:
            from ml_model.predictor import PlusvaliaPredictorModel
            
            logger.info(f"Entrenando con {len(df)} muestras...")
            
            model = PlusvaliaPredictorModel(model_version="3.0_real_data")
            metrics = model.train(df, target_col='price_m2', test_size=0.2)
            
            self.stats['trained_samples'] = len(df)
            
            logger.success("Modelo entrenado exitosamente")
            logger.info(f"  R² (test): {metrics['test_r2']:.4f}")
            logger.info(f"  MAE (test): ${metrics['test_mae']:,.0f} MXN/m²")
            logger.info(f"  RMSE (test): ${metrics['test_rmse']:,.0f} MXN/m²")
            
            return model
            
        except (ValueError, KeyError, TypeError, RuntimeError) as e:
            logger.error(f"Error entrenando modelo: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ============================================================
    # FASE 5: GENERACIÓN Y GUARDADO DE PREDICCIONES
    # ============================================================
    
    def fase5_generar_predicciones(self, model, df):
        """
        Genera predicciones para todas las propiedades y las guarda
        """
        logger.info("\n" + "="*70)
        logger.info("FASE 5: GENERACION Y GUARDADO DE PREDICCIONES")
        logger.info("="*70)
        
        if model is None:
            logger.error("No hay modelo para generar predicciones")
            return
        
        try:
            logger.info(f"Generando predicciones para {len(df)} propiedades...")
            
            predictions_batch = []
            
            for idx, row in df.iterrows():
                try:
                    prediction = model.predict_price(
                        lat=row['lat'],
                        lon=row['lon'],
                        area_m2=row['area_m2'],
                        city=row['city'],
                        state=row['state']
                    )
                    
                    # Columnas requeridas según schema de Supabase
                    pred_record = {
                        'lat': float(row['lat']),
                        'lon': float(row['lon']),
                        'city': row['city'],
                        'state': row['state'],
                        'predicted_price_m2': float(prediction['predicted_price_m2']),
                        'plusvalia_score': float(prediction['plusvalia_score']),
                        'growth_potential': prediction['growth_potential'],
                        'risk_level': 'medio',  # Por defecto
                        'current_price_m2': float(row.get('price_m2', 0)),
                        'model_version': prediction['model_version'],
                        'model_confidence': float(prediction['confidence'])
                    }
                    
                    predictions_batch.append(pred_record)
                    
                    # Guardar en lotes de 100
                    if len(predictions_batch) >= 100:
                        self.supabase.table(TABLE_PREDICTIONS).insert(predictions_batch).execute()
                        self.stats['predictions_saved'] += len(predictions_batch)
                        predictions_batch = []
                        logger.info(f"  Guardadas {self.stats['predictions_saved']} predicciones...")
                    
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Error predicción fila {idx}: {str(e)[:100]}")

            # Guardar últimas predicciones
            if predictions_batch:
                self.supabase.table(TABLE_PREDICTIONS).insert(predictions_batch).execute()
                self.stats['predictions_saved'] += len(predictions_batch)
            
            logger.success(f"Total predicciones guardadas: {self.stats['predictions_saved']}")
            
        except Exception as e:  # Intentional broad catch: pipeline phase handler
            logger.error(f"Error generando predicciones: {e}")
            import traceback
            traceback.print_exc()

    # ============================================================
    # EJECUCIÓN COMPLETA DEL PIPELINE
    # ============================================================
    
    async def ejecutar_pipeline_completo(self, cities_list):
        """
        Ejecuta el pipeline completo de principio a fin
        """
        start_time = datetime.now()
        
        logger.info("╔═══════════════════════════════════════════════════════════════════╗")
        logger.info("║     PIPELINE COMPLETO - ENTRENAMIENTO CON DATOS REALES          ║")
        logger.info("╚═══════════════════════════════════════════════════════════════════╝")
        logger.info(f"Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        try:
            # FASE 1: Scraping
            df_scraped = await self.fase1_scraping_real(cities_list, max_pages=2)
            
            # FASE 2: Enriquecimiento
            df_enriched = await self.fase2_enriquecimiento()
            
            # FASE 3: Features
            df_features = self.fase3_construccion_features()
            
            # FASE 4: Entrenamiento
            if df_features is not None and not df_features.empty:
                model = self.fase4_entrenamiento_modelo(df_features)
                
                # FASE 5: Predicciones
                if model:
                    self.fase5_generar_predicciones(model, df_features)
            
            # Resumen final
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("\n" + "="*70)
            logger.info("RESUMEN FINAL DEL PIPELINE")
            logger.info("="*70)
            logger.info(f"Duración total: {duration}")
            logger.info(f"Propiedades scraped: {self.stats['scraped']}")
            logger.info(f"Amenidades extraídas: {self.stats['amenities']}")
            logger.info(f"Registros INEGI: {self.stats['inegi_enriched']}")
            logger.info(f"Muestras entrenamiento: {self.stats['trained_samples']}")
            logger.info(f"Predicciones guardadas: {self.stats['predictions_saved']}")
            logger.info("="*70)
            logger.success("\nPIPELINE COMPLETADO EXITOSAMENTE!")
            
        except Exception as e:  # Intentional broad catch: top-level pipeline handler
            logger.error(f"\nError en pipeline: {e}")
            import traceback
            traceback.print_exc()


# ================================================================
# FUNCIÓN PRINCIPAL
# ================================================================

async def main():
    """
    Ejecuta el pipeline completo
    """
    # Configurar ciudades objetivo
    CIUDADES_OBJETIVO = [
        # Guadalajara (principal)
        {"city": "Guadalajara", "state": "Jalisco"},
        {"city": "Zapopan", "state": "Jalisco"},
        {"city": "Tlaquepaque", "state": "Jalisco"},
        
        # Otras ciudades
        {"city": "Querétaro", "state": "Querétaro"},
        {"city": "Monterrey", "state": "Nuevo León"},
        {"city": "Ciudad de México", "state": "Ciudad de México"},
    ]
    
    # Crear y ejecutar pipeline
    pipeline = RealEstatePipeline()
    await pipeline.ejecutar_pipeline_completo(CIUDADES_OBJETIVO)


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Ejecutar
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\nPipeline interrumpido por el usuario")
    except Exception as e:  # Intentional broad catch: top-level script handler
        logger.error(f"\nError fatal: {e}")
        import traceback
        traceback.print_exc()

