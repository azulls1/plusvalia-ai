"""
Scraper de OpenStreetMap para obtener amenidades REALES
Usa Overpass API para consultar POIs (Points of Interest)
"""

import requests
import time
from typing import List, Dict
from loguru import logger
from supabase import create_client
import sys
import os

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


class OSMAmenitiesScraper:
    """Scraper de amenidades desde OpenStreetMap"""
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
    def get_amenities_in_area(self, lat: float, lon: float, radius_km: float = 2.0) -> List[Dict]:
        """
        Obtiene amenidades reales desde OSM en un radio especificado
        
        Args:
            lat: Latitud del centro
            lon: Longitud del centro
            radius_km: Radio de búsqueda en kilómetros
        """
        
        radius_m = radius_km * 1000  # Convertir a metros
        
        # Query Overpass QL para obtener diversos tipos de amenidades
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"](around:{radius_m},{lat},{lon});
          node["shop"](around:{radius_m},{lat},{lon});
          node["leisure"](around:{radius_m},{lat},{lon});
          node["tourism"](around:{radius_m},{lat},{lon});
          way["amenity"](around:{radius_m},{lat},{lon});
          way["shop"](around:{radius_m},{lat},{lon});
        );
        out center;
        """
        
        try:
            logger.info(f"Consultando OSM en ({lat}, {lon}) radio {radius_km}km...")
            response = requests.post(
                self.overpass_url,
                data=query,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            elements = data.get('elements', [])
            
            logger.success(f"Obtenidos {len(elements)} elementos de OSM")
            
            # Procesar elementos
            amenidades = []
            for element in elements:
                tags = element.get('tags', {})
                
                # Obtener coordenadas
                elem_lat = element.get('lat')
                elem_lon = element.get('lon')
                
                # Para ways, usar el centro
                if not elem_lat and 'center' in element:
                    elem_lat = element['center'].get('lat')
                    elem_lon = element['center'].get('lon')
                
                if not elem_lat or not elem_lon:
                    continue
                
                # Determinar tipo de amenidad
                amenity_type = tags.get('amenity') or tags.get('shop') or tags.get('leisure') or tags.get('tourism')
                
                if not amenity_type:
                    continue
                
                # Mapear a categorías estándar
                categoria = self._map_category(amenity_type)
                
                amenidad = {
                    'osm_id': element.get('id'),
                    'name': tags.get('name', f'{amenity_type.title()}'),
                    'amenity_type': amenity_type,
                    'lat': float(elem_lat),
                    'lon': float(elem_lon),
                    'tags': tags  # Guardar todos los tags como JSON
                }
                
                amenidades.append(amenidad)
            
            return amenidades
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error consultando OSM: {e}")
            return []
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error procesando datos OSM: {e}")
            return []
    
    def _map_category(self, amenity_type: str) -> str:
        """Mapea tipos de OSM a categorías estándar"""
        
        categorias = {
            'restaurant': 'comercio',
            'cafe': 'comercio',
            'fast_food': 'comercio',
            'bar': 'comercio',
            'pub': 'comercio',
            'bank': 'servicios',
            'atm': 'servicios',
            'pharmacy': 'salud',
            'hospital': 'salud',
            'clinic': 'salud',
            'doctors': 'salud',
            'school': 'educacion',
            'kindergarten': 'educacion',
            'college': 'educacion',
            'university': 'educacion',
            'library': 'educacion',
            'bus_station': 'transporte',
            'parking': 'transporte',
            'fuel': 'transporte',
            'park': 'recreacion',
            'playground': 'recreacion',
            'sports_centre': 'recreacion',
            'cinema': 'recreacion',
            'theatre': 'recreacion',
            'supermarket': 'comercio',
            'convenience': 'comercio',
            'mall': 'comercio',
        }
        
        return categorias.get(amenity_type, 'otros')
    
    def save_to_supabase(self, amenidades: List[Dict]) -> int:
        """Guarda amenidades en Supabase"""
        
        if not amenidades:
            logger.warning("No hay amenidades para guardar")
            return 0
        
        try:
            logger.info(f"Guardando {len(amenidades)} amenidades en Supabase...")
            
            # Insertar en lotes
            batch_size = 100
            saved_count = 0
            
            for i in range(0, len(amenidades), batch_size):
                batch = amenidades[i:i+batch_size]
                
                try:
                    self.supabase.table("iainmobiliaria_amenities").insert(batch).execute()
                    saved_count += len(batch)
                    logger.info(f"  ✓ Guardadas {saved_count}/{len(amenidades)}")
                    time.sleep(0.5)  # Pequeña pausa
                    
                except Exception as e:  # Supabase client may raise various errors
                    logger.error(f"  ✗ Error en lote: {e}")

            logger.success(f"✅ Total guardado: {saved_count} amenidades")
            return saved_count

        except Exception as e:  # Supabase client may raise various errors
            logger.error(f"Error guardando en Supabase: {e}")
            return 0


def scrape_cities():
    """Scrape amenidades para las ciudades principales"""
    
    scraper = OSMAmenitiesScraper()
    
    # Coordenadas centrales de cada ciudad
    ciudades = [
        {"name": "Guadalajara", "lat": 20.6737, "lon": -103.3440},
        {"name": "Zapopan", "lat": 20.7214, "lon": -103.3918},
        {"name": "Tlaquepaque", "lat": 20.6147, "lon": -103.3106},
        {"name": "Tonalá", "lat": 20.6227, "lon": -103.2324},
        {"name": "Tlajomulco", "lat": 20.4740, "lon": -103.4410},
        {"name": "El Salto", "lat": 20.5196, "lon": -103.2218},
        {"name": "Monterrey", "lat": 25.6866, "lon": -100.3161},
        {"name": "Ciudad de México", "lat": 19.4326, "lon": -99.1332},
    ]
    
    total_amenidades = 0
    
    for ciudad in ciudades:
        logger.info(f"\n{'='*70}")
        logger.info(f"🏙️  Procesando: {ciudad['name']}")
        logger.info(f"{'='*70}")
        
        # Obtener amenidades
        amenidades = scraper.get_amenities_in_area(
            ciudad['lat'], 
            ciudad['lon'], 
            radius_km=3.0  # Radio de 3km
        )
        
        if amenidades:
            # Guardar en Supabase
            count = scraper.save_to_supabase(amenidades)
            total_amenidades += count
        
        # Pausa entre ciudades (respetar límites de API)
        time.sleep(2)
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📊 RESUMEN FINAL")
    logger.info(f"{'='*70}")
    logger.success(f"✅ Total de amenidades scrapeadas: {total_amenidades}")
    logger.info(f"✅ Ciudades procesadas: {len(ciudades)}")


if __name__ == "__main__":
    logger.info("="*70)
    logger.info("🗺️  SCRAPER DE AMENIDADES REALES DESDE OPENSTREETMAP")
    logger.info("="*70)
    scrape_cities()

