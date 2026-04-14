# ================================================================
# SCRAPER UNIFICADO - Combina múltiples fuentes
# ================================================================

import asyncio
from datetime import datetime
from typing import List, Dict
import pandas as pd
from loguru import logger
import sys

sys.path.append('..')
from config import DATA_DIR
from scrapers.inmuebles24_scraper import Inmuebles24Scraper
from scrapers.lamudi_scraper import LamudiScraper


class UnifiedScraper:
    """
    Scraper unificado que combina múltiples fuentes de datos
    """
    
    def __init__(self):
        self.scrapers = {
            'inmuebles24': Inmuebles24Scraper(headless=True),
            'lamudi': LamudiScraper(headless=True)
        }
        self.all_results = []
    
    async def scrape_all_sources(
        self,
        cities: List[Dict],
        property_type: str = "terreno",
        operation: str = "venta",
        max_pages: int = 3
    ) -> pd.DataFrame:
        """
        Scrapea todas las fuentes configuradas
        
        Args:
            cities: Lista de diccionarios con 'city' y 'state'
            property_type: Tipo de propiedad
            operation: venta o renta
            max_pages: Páginas máximas por ciudad
            
        Returns:
            DataFrame con todos los resultados combinados
        """
        logger.info(f"🚀 Iniciando scraping unificado de {len(cities)} ciudades")
        logger.info(f"   Fuentes: {', '.join(self.scrapers.keys())}")
        
        tasks = []
        
        # Crear tareas para cada fuente y ciudad
        for source_name, scraper in self.scrapers.items():
            for city_data in cities:
                task = self._scrape_source(
                    source_name,
                    scraper,
                    city_data,
                    property_type,
                    operation,
                    max_pages
                )
                tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidar resultados
        for result in results:
            if isinstance(result, list):
                self.all_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error en tarea: {result}")
        
        # Convertir a DataFrame
        df = pd.DataFrame(self.all_results)
        
        if not df.empty:
            # Limpiar y normalizar datos
            df = self._clean_data(df)
            
            # Estadísticas
            self._print_statistics(df)
            
            # Guardar resultados
            filename = self._save_results(df)
            logger.success(f"✅ Scraping completado. {len(df)} propiedades guardadas en {filename}")
        else:
            logger.warning("⚠️ No se obtuvieron resultados")
        
        return df
    
    async def _scrape_source(
        self,
        source_name: str,
        scraper,
        city_data: Dict,
        property_type: str,
        operation: str,
        max_pages: int
    ) -> List[Dict]:
        """Scrapea una fuente individual"""
        try:
            logger.info(f"📍 {source_name}: {city_data['city']}, {city_data['state']}")
            
            # Mapear tipo de propiedad según la fuente
            property_map = {
                'inmuebles24': {'terreno': 'terrenos', 'casa': 'casas', 'departamento': 'departamentos'},
                'lamudi': {'terreno': 'terreno', 'casa': 'casa', 'departamento': 'departamento'}
            }
            
            mapped_property = property_map.get(source_name, {}).get(property_type, property_type)
            
            results = await scraper.scrape_city(
                city=city_data['city'],
                state=city_data['state'],
                property_type=mapped_property,
                operation=operation,
                max_pages=max_pages
            )
            
            logger.info(f"   ✓ {source_name}: {len(results)} propiedades de {city_data['city']}")
            return results
            
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            logger.error(f"   ✗ {source_name} falló en {city_data['city']}: {e}")
            return []
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza los datos"""
        logger.info("🧹 Limpiando datos...")
        
        initial_count = len(df)
        
        # Remover duplicados basados en título y precio
        df = df.drop_duplicates(subset=['title', 'price_mxn', 'city'], keep='first')
        
        # Remover precios/áreas inválidas
        df = df[df['price_mxn'] > 0]
        df = df[df['area_m2'] > 0]
        
        # Calcular precio/m²
        df['price_m2'] = df['price_mxn'] / df['area_m2']
        
        # Remover outliers extremos (precio/m² muy alto o muy bajo)
        q1 = df['price_m2'].quantile(0.01)
        q99 = df['price_m2'].quantile(0.99)
        df = df[(df['price_m2'] >= q1) & (df['price_m2'] <= q99)]
        
        # Normalizar strings
        df['title'] = df['title'].str.strip()
        df['address'] = df['address'].str.strip()
        df['city'] = df['city'].str.strip()
        df['state'] = df['state'].str.strip()
        
        final_count = len(df)
        removed = initial_count - final_count
        
        logger.info(f"   • Removidos {removed} registros duplicados/inválidos")
        logger.info(f"   • {final_count} propiedades válidas")
        
        return df
    
    def _print_statistics(self, df: pd.DataFrame):
        """Imprime estadísticas de los datos"""
        logger.info("\n" + "="*50)
        logger.info("📊 ESTADÍSTICAS GENERALES")
        logger.info("="*50)
        logger.info(f"Total propiedades: {len(df):,}")
        logger.info(f"\nPor fuente:")
        for source in df['source'].unique():
            count = len(df[df['source'] == source])
            logger.info(f"   • {source}: {count:,} propiedades")
        
        logger.info(f"\nPor ciudad:")
        for city in df['city'].unique():
            count = len(df[df['city'] == city])
            logger.info(f"   • {city}: {count:,} propiedades")
        
        logger.info(f"\n💰 Precios:")
        logger.info(f"   • Promedio: ${df['price_mxn'].mean():,.0f} MXN")
        logger.info(f"   • Mediana: ${df['price_mxn'].median():,.0f} MXN")
        logger.info(f"   • Mínimo: ${df['price_mxn'].min():,.0f} MXN")
        logger.info(f"   • Máximo: ${df['price_mxn'].max():,.0f} MXN")
        
        logger.info(f"\n📏 Superficies:")
        logger.info(f"   • Promedio: {df['area_m2'].mean():,.0f} m²")
        logger.info(f"   • Mediana: {df['area_m2'].median():,.0f} m²")
        
        logger.info(f"\n💵 Precio por m²:")
        logger.info(f"   • Promedio: ${df['price_m2'].mean():,.0f} MXN/m²")
        logger.info(f"   • Mediana: ${df['price_m2'].median():,.0f} MXN/m²")
        logger.info("="*50 + "\n")
    
    def _save_results(self, df: pd.DataFrame) -> str:
        """Guarda resultados en CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = DATA_DIR / f"scraping_unified_{timestamp}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"💾 Datos guardados en: {filename}")
        
        return str(filename)


# ================================================================
# SCRIPT PRINCIPAL
# ================================================================

async def save_to_supabase(df: pd.DataFrame):
    """
    Guarda los datos scrapeados en Supabase
    """
    try:
        from supabase import create_client
        from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_COMPARABLES
        
        logger.info("💾 Guardando datos en Supabase...")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Preparar datos para inserción
        records = df.to_dict('records')
        saved_count = 0
        error_count = 0
        
        # Insertar por lotes de 100 registros
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                # Preparar cada registro
                for record in batch:
                    # Añadir campos requeridos
                    record['collection_date'] = datetime.now().isoformat()
                    record['data_source'] = record.get('source', 'unknown')
                    
                    # Asegurar que lat/lon existan
                    if 'lat' not in record or record['lat'] is None:
                        record['lat'] = 0.0
                    if 'lon' not in record or record['lon'] is None:
                        record['lon'] = 0.0
                
                # Insertar lote
                response = supabase.table(TABLE_COMPARABLES).insert(batch).execute()
                saved_count += len(batch)
                logger.info(f"   ✓ Guardados {saved_count}/{len(records)} registros")
                
            except Exception as e:  # Supabase client may raise various errors
                error_count += len(batch)
                logger.error(f"   ✗ Error guardando lote: {e}")

        logger.success(f"✅ Guardados {saved_count} registros en Supabase (errores: {error_count})")
        return saved_count

    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"Error conectando a Supabase: {e}")
        return 0


async def main():
    """
    Función principal - Entrenamiento extensivo por 1+ hora
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
        {"city": "León", "state": "Guanajuato"},
        {"city": "Puebla", "state": "Puebla"},
        {"city": "Mérida", "state": "Yucatán"},
        {"city": "Tijuana", "state": "Baja California"},
    ]
    
    logger.info("="*70)
    logger.info("🚀 ENTRENAMIENTO EXTENSIVO DE MODELO ML")
    logger.info(f"   Ciudades: {len(CIUDADES_OBJETIVO)}")
    logger.info(f"   Duración estimada: 1-2 horas")
    logger.info(f"   Enfoque especial: Guadalajara y zona metropolitana")
    logger.info("="*70)
    
    # Crear scraper unificado
    scraper = UnifiedScraper()
    
    # Ejecutar scraping con más páginas para recolectar más datos
    df = await scraper.scrape_all_sources(
        cities=CIUDADES_OBJETIVO,
        property_type="terreno",
        operation="venta",
        max_pages=5  # 5 páginas por ciudad = más datos
    )
    
    # Guardar en Supabase
    if df is not None and not df.empty:
        await save_to_supabase(df)
    
    return df


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Ejecutar
    df = asyncio.run(main())
    
    if df is not None and not df.empty:
        print(f"\n✅ Proceso completado. {len(df)} propiedades extraídas.")
    else:
        print("\n⚠️ No se obtuvieron resultados.")

