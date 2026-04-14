# ================================================================
# CLIENTE INEGI - Integración con API de INEGI
# ================================================================

import requests
import time
from typing import Dict, List, Optional
from loguru import logger
import pandas as pd
import json
import math

# Importar geopandas solo si está disponible
try:
    import geopandas as gpd
    from shapely.geometry import Point, shape
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    logger.warning("geopandas no está disponible. Algunas funciones geoespaciales estarán limitadas.")

import sys
sys.path.append('..')
from config import INEGI_API_TOKEN, INEGI_BASE_URL

class INEGIClient:
    """
    Cliente para interactuar con la API de INEGI y obtener datos demográficos
    """
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or INEGI_API_TOKEN
        self.base_url = INEGI_BASE_URL
        self.session = requests.Session()
        
        # Mapeo de estados (código INEGI -> nombre)
        self.estados = {
            "01": "Aguascalientes", "02": "Baja California", "03": "Baja California Sur",
            "04": "Campeche", "05": "Coahuila", "06": "Colima", "07": "Chiapas",
            "08": "Chihuahua", "09": "Ciudad de México", "10": "Durango",
            "11": "Guanajuato", "12": "Guerrero", "13": "Hidalgo", "14": "Jalisco",
            "15": "México", "16": "Michoacán", "17": "Morelos", "18": "Nayarit",
            "19": "Nuevo León", "20": "Oaxaca", "21": "Puebla", "22": "Querétaro",
            "23": "Quintana Roo", "24": "San Luis Potosí", "25": "Sinaloa",
            "26": "Sonora", "27": "Tabasco", "28": "Tamaulipas", "29": "Tlaxcala",
            "30": "Veracruz", "31": "Yucatán", "32": "Zacatecas"
        }
    
    def get_state_code(self, state_name: str) -> Optional[str]:
        """Obtiene el código de estado por nombre"""
        for code, name in self.estados.items():
            if name.lower() == state_name.lower():
                return code
        return None
    
    def fetch_population_data(self, state_code: str = None) -> pd.DataFrame:
        """
        Obtiene datos de población de INEGI
        
        Args:
            state_code: Código del estado (01-32), None para todo el país
            
        Returns:
            DataFrame con datos poblacionales
        """
        logger.info(f"Obteniendo datos de población{f' para estado {state_code}' if state_code else ' nacional'}")
        
        # Indicador de población total (ejemplo)
        # https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/1002000001/es/0700/false/BIE/2.0/<TOKEN>
        
        try:
            # Construcción de URL de API de INEGI
            # Nota: INEGI tiene múltiples APIs, esta es una simplificación
            url = f"{self.base_url}INDICATOR/1002000001/es/{state_code or '0700'}/false/BIE/2.0/{self.api_token}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parsear respuesta (estructura específica de INEGI)
            if 'Series' in data:
                records = []
                for serie in data['Series']:
                    for obs in serie.get('OBSERVATIONS', []):
                        records.append({
                            'year': obs.get('TIME_PERIOD'),
                            'value': float(obs.get('OBS_VALUE', 0)),
                            'indicator': serie.get('INDICADOR'),
                            'region': serie.get('REGION')
                        })
                
                df = pd.DataFrame(records)
                logger.success(f"Datos de población obtenidos: {len(df)} registros")
                return df
            else:
                logger.warning("No se encontraron datos en la respuesta")
                return pd.DataFrame()
                
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f"Error obteniendo datos de INEGI: {e}")
            return pd.DataFrame()
    
    def fetch_economic_indicators(
        self, 
        municipality_code: str
    ) -> Dict:
        """
        Obtiene indicadores económicos de un municipio
        
        Args:
            municipality_code: Código del municipio (5 dígitos: estado + municipio)
            
        Returns:
            Diccionario con indicadores económicos
        """
        logger.info(f"Obteniendo indicadores económicos para municipio {municipality_code}")
        
        # Placeholder: En producción, usar API real de INEGI
        # Por ahora, devolvemos datos sintéticos basados en patrones reales
        
        indicators = {
            'municipality_code': municipality_code,
            'unemployment_rate': None,
            'employed_population': None,
            'avg_income': None,
            'economic_level': self._estimate_economic_level(municipality_code)
        }
        
        return indicators
    
    def _estimate_economic_level(self, municipality_code: str) -> str:
        """
        Estima el nivel económico basado en datos históricos
        (Placeholder - en producción usar datos reales)
        """
        # Mapeo simplificado de municipios principales
        high_income = ['22014', '19039', '14039']  # Querétaro, Monterrey, Guadalajara
        medium_high = ['09', '21114']  # CDMX, Puebla
        
        if municipality_code in high_income:
            return 'alto'
        elif municipality_code in medium_high:
            return 'medio-alto'
        else:
            return 'medio'
    
    def load_agebs_shapefile(
        self, 
        shapefile_path: str, 
        state_filter: str = None
    ):
        """
        Carga shapefiles de AGEBs de INEGI
        
        Args:
            shapefile_path: Ruta al shapefile
            state_filter: Código de estado para filtrar (opcional)
            
        Returns:
            GeoDataFrame con geometrías de AGEBs
        """
        if not HAS_GEOPANDAS:
            logger.error("geopandas no está disponible. No se pueden cargar shapefiles.")
            return pd.DataFrame()
        
        logger.info(f"Cargando AGEBs desde {shapefile_path}")
        
        try:
            gdf = gpd.read_file(shapefile_path)
            
            if state_filter:
                gdf = gdf[gdf['CVE_ENT'] == state_filter]
            
            logger.success(f"Cargados {len(gdf)} AGEBs")
            return gdf
            
        except (FileNotFoundError, ValueError, OSError) as e:
            logger.error(f"Error cargando shapefile: {e}")
            return pd.DataFrame()
    
    def enrich_with_demographics(
        self, 
        df: pd.DataFrame,
        lat_col: str = 'lat',
        lon_col: str = 'lon'
    ) -> pd.DataFrame:
        """
        Enriquece un DataFrame con datos demográficos basados en coordenadas
        
        Args:
            df: DataFrame con datos geográficos
            lat_col: Nombre de la columna de latitud
            lon_col: Nombre de la columna de longitud
            
        Returns:
            DataFrame enriquecido con datos demográficos
        """
        logger.info(f"Enriqueciendo {len(df)} registros con datos demográficos")
        
        # Trabajar con una copia
        df_enriched = df.copy()
        
        # Placeholder: En producción, hacer spatial join con AGEBs
        # Por ahora, asignar valores por defecto
        df_enriched['population_density'] = 1000.0  # habitantes/km²
        df_enriched['economic_level'] = 'medio'
        df_enriched['avg_schooling_years'] = 9.5
        
        logger.success("Enriquecimiento completado")
        return df_enriched
    
    def get_distance_to_center(
        self, 
        lat: float, 
        lon: float, 
        city: str
    ) -> float:
        """
        Calcula distancia al centro de la ciudad usando la fórmula de Haversine
        
        Args:
            lat: Latitud del punto
            lon: Longitud del punto
            city: Nombre de la ciudad
            
        Returns:
            Distancia en kilómetros
        """
        # Coordenadas de centros de ciudades principales
        city_centers = {
            'Querétaro': (20.5888, -100.3899),
            'Guadalajara': (20.6597, -103.3496),
            'Monterrey': (25.6866, -100.3161),
            'Ciudad de México': (19.4326, -99.1332),
            'Puebla': (19.0414, -98.2063),
            'León': (21.1221, -101.6827),
            'Zapopan': (20.7214, -103.3918),
            'Tlaquepaque': (20.6408, -103.2931),
            'Tonalá': (20.6235, -103.2329),
            'Tlajomulco de Zúñiga': (20.4725, -103.4447),
            'Aguascalientes': (21.8853, -102.2916),
            'Naucalpan': (19.4784, -99.2386),
            'Tlalnepantla': (19.5287, -99.1950),
            'San Pedro Garza García': (25.6614, -100.4069),
            'Mérida': (20.9674, -89.5926),
            'Tijuana': (32.5149, -117.0382),
            'Cancún': (21.1619, -86.8515),
            'San Luis Potosí': (22.1565, -100.9855)
        }
        
        center = city_centers.get(city)
        if not center:
            logger.debug(f"Centro no definido para {city}, usando punto como referencia")
            return 5.0  # Distancia por defecto
        
        # Fórmula de Haversine
        R = 6371  # Radio de la Tierra en km
        
        lat1, lon1 = math.radians(lat), math.radians(lon)
        lat2, lon2 = math.radians(center[0]), math.radians(center[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        return round(distance, 2)


# ================================================================
# SCRIPT DE EJEMPLO
# ================================================================

def main():
    """
    Ejemplo de uso del cliente INEGI
    """
    client = INEGIClient()
    
    # Test 1: Obtener código de estado
    state_code = client.get_state_code("Querétaro")
    logger.info(f"Código de Querétaro: {state_code}")
    
    # Test 2: Obtener datos de población
    # df_pop = client.fetch_population_data(state_code)
    # if not df_pop.empty:
    #     print(df_pop.head())
    
    # Test 3: Calcular distancia
    distance = client.get_distance_to_center(20.6, -100.4, "Querétaro")
    logger.info(f"Distancia al centro: {distance} km")
    
    # Test 4: Enriquecer datos
    sample_data = pd.DataFrame({
        'city': ['Querétaro', 'Guadalajara'],
        'lat': [20.5888, 20.6597],
        'lon': [-100.3899, -103.3496]
    })
    
    enriched = client.enrich_with_demographics(sample_data)
    print("\nDatos enriquecidos:")
    print(enriched[['city', 'population_density', 'economic_level']])


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    main()

