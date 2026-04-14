# ================================================================
# SCRAPER LAMUDI - Extracción de precios de terrenos
# ================================================================

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from loguru import logger
import pandas as pd
import sys
sys.path.append('..')
from config import SCRAPER_DELAY, SCRAPER_HEADLESS, SCRAPER_USER_AGENT, SCRAPER_MAX_RETRIES

class LamudiScraper:
    """
    Scraper para extraer datos de terrenos desde Lamudi.com.mx
    """
    
    def __init__(self, headless: bool = SCRAPER_HEADLESS):
        self.headless = headless
        self.base_url = "https://www.lamudi.com.mx"
        self.results: List[Dict] = []
        
    async def scrape_city(
        self, 
        city: str, 
        state: str, 
        property_type: str = "terreno",
        operation: str = "venta",
        max_pages: int = 5
    ) -> List[Dict]:
        """
        Extrae propiedades de una ciudad específica
        
        Args:
            city: Ciudad a buscar
            state: Estado a buscar
            property_type: Tipo de propiedad (terreno, casa, departamento)
            operation: venta o renta
            max_pages: Número máximo de páginas a scrapear
            
        Returns:
            Lista de diccionarios con los datos extraídos
        """
        logger.info(f"Iniciando scraping Lamudi: {city}, {state} - {property_type} en {operation}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent=SCRAPER_USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                locale='es-MX'
            )
            page = await context.new_page()
            
            try:
                # Construir URL de búsqueda
                search_url = self._build_search_url(city, state, property_type, operation)
                logger.info(f"URL de búsqueda: {search_url}")
                
                # Scrapear múltiples páginas
                for page_num in range(1, max_pages + 1):
                    logger.info(f"Scrapeando página {page_num}/{max_pages}")
                    
                    paginated_url = f"{search_url}?page={page_num}" if page_num > 1 else search_url
                    
                    success = await self._scrape_page(page, paginated_url, city, state)
                    
                    if not success:
                        logger.warning(f"No se pudo scrapear la página {page_num}, deteniendo")
                        break
                    
                    # Delay entre páginas
                    await asyncio.sleep(SCRAPER_DELAY)
                
                logger.success(f"Scraping completado. Total propiedades: {len(self.results)}")
                
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.error(f"Error durante scraping: {e}")
            
            finally:
                await browser.close()
        
        return self.results
    
    def _build_search_url(
        self, 
        city: str, 
        state: str, 
        property_type: str, 
        operation: str
    ) -> str:
        """Construye la URL de búsqueda"""
        # Normalizar nombres
        city_slug = city.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        state_slug = state.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        
        # Ejemplo: https://www.lamudi.com.mx/queretaro/for-sale/land/
        operation_map = {
            'venta': 'for-sale',
            'renta': 'for-rent'
        }
        
        property_map = {
            'terreno': 'land',
            'casa': 'house',
            'departamento': 'apartment'
        }
        
        url = f"{self.base_url}/{state_slug}/{operation_map.get(operation, 'for-sale')}/{property_map.get(property_type, 'land')}/"
        return url
    
    async def _scrape_page(
        self, 
        page: Page, 
        url: str, 
        city: str, 
        state: str
    ) -> bool:
        """
        Scrapea una página individual
        
        Returns:
            True si fue exitoso, False si no hay resultados
        """
        retries = 0
        
        while retries < SCRAPER_MAX_RETRIES:
            try:
                # Navegar a la página
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                
                if response.status != 200:
                    logger.warning(f"Status code {response.status} para {url}")
                    retries += 1
                    await asyncio.sleep(SCRAPER_DELAY)
                    continue
                
                # Esperar a que carguen los resultados
                # Lamudi usa diferentes selectores, ajustar según la estructura actual
                await page.wait_for_selector('div.ListingCell-row', timeout=10000)
                
                # Extraer listados
                listings = await page.query_selector_all('div.ListingCell-row')
                
                if not listings:
                    logger.warning(f"No se encontraron listados en {url}")
                    return False
                
                logger.info(f"Encontrados {len(listings)} listados")
                
                for listing in listings:
                    property_data = await self._extract_property_data(listing, city, state)
                    if property_data:
                        self.results.append(property_data)
                
                return True
                
            except (ConnectionError, TimeoutError, OSError, ValueError) as e:
                logger.error(f"Error scrapeando {url}: {e}")
                retries += 1
                await asyncio.sleep(SCRAPER_DELAY * retries)
        
        return False
    
    async def _extract_property_data(
        self, 
        listing_element, 
        city: str, 
        state: str
    ) -> Optional[Dict]:
        """
        Extrae datos de un listado individual
        """
        try:
            # Título
            title_elem = await listing_element.query_selector('h3.ListingCell-KeyInfo-title a')
            title = await title_elem.inner_text() if title_elem else "Sin título"
            
            # Precio
            price_elem = await listing_element.query_selector('span.PriceSection-FirstPrice')
            price_text = await price_elem.inner_text() if price_elem else "0"
            price_mxn = self._parse_price(price_text)
            
            # Superficie
            area_elem = await listing_element.query_selector('div.KeyInformation-surface')
            if not area_elem:
                # Intentar selector alternativo
                area_elem = await listing_element.query_selector('span[title*="m²"]')
            area_text = await area_elem.inner_text() if area_elem else "0"
            area_m2 = self._parse_area(area_text)
            
            # Dirección
            address_elem = await listing_element.query_selector('span.ListingCell-KeyInfo-address-text')
            address = await address_elem.inner_text() if address_elem else f"{city}, {state}"
            
            # Link
            link_elem = await listing_element.query_selector('h3.ListingCell-KeyInfo-title a')
            link = await link_elem.get_attribute('href') if link_elem else None
            
            # Validar datos
            if price_mxn <= 0 or area_m2 <= 0:
                logger.debug(f"Datos inválidos: precio={price_mxn}, area={area_m2}")
                return None
            
            property_data = {
                'title': title.strip(),
                'price_mxn': price_mxn,
                'area_m2': area_m2,
                'address': address.strip(),
                'city': city,
                'state': state,
                'source': 'lamudi',
                'source_url': f"{self.base_url}{link}" if link and not link.startswith('http') else link,
                'scraped_at': datetime.now().isoformat()
            }
            
            logger.debug(f"Propiedad extraída: {property_data['title']} - ${price_mxn:,.0f} - {area_m2}m²")
            
            return property_data
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error(f"Error extrayendo datos de listado: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> float:
        """Parsea el precio desde el texto"""
        try:
            # Remover símbolos y convertir
            # Ejemplo: "$ 1,500,000" -> 1500000
            cleaned = price_text.replace('$', '').replace(',', '').replace('MXN', '').replace('MX', '').strip()
            
            # Manejar millones/mil
            if 'millones' in price_text.lower() or 'M' in price_text:
                cleaned = cleaned.replace('millones', '').replace('M', '').strip()
                return float(cleaned) * 1_000_000
            elif 'mil' in price_text.lower() or 'k' in price_text.lower():
                cleaned = cleaned.replace('mil', '').replace('k', '').replace('K', '').strip()
                return float(cleaned) * 1_000
            
            return float(cleaned)
        except:
            return 0.0
    
    def _parse_area(self, area_text: str) -> float:
        """Parsea la superficie desde el texto"""
        try:
            # Ejemplo: "500 m²" o "500m2" -> 500
            cleaned = area_text.replace('m²', '').replace('m2', '').replace('m', '').replace(',', '').strip()
            return float(cleaned)
        except:
            return 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convierte resultados a DataFrame"""
        return pd.DataFrame(self.results)
    
    def save_to_csv(self, filename: str = None):
        """Guarda resultados en CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lamudi_{timestamp}.csv"
        
        df = self.to_dataframe()
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.success(f"Datos guardados en {filename}")
        return filename


# ================================================================
# SCRIPT PRINCIPAL
# ================================================================

async def main():
    """
    Función principal para ejecutar el scraper
    """
    scraper = LamudiScraper(headless=True)
    
    # Configurar ciudades a scrapear
    ciudades = [
        {"city": "Querétaro", "state": "Querétaro"},
        {"city": "Guadalajara", "state": "Jalisco"},
        {"city": "Monterrey", "state": "Nuevo León"},
        {"city": "Ciudad de México", "state": "CDMX"},
    ]
    
    all_results = []
    
    for ciudad in ciudades:
        results = await scraper.scrape_city(
            city=ciudad["city"],
            state=ciudad["state"],
            property_type="terreno",
            operation="venta",
            max_pages=3
        )
        all_results.extend(results)
    
    # Guardar resultados
    if all_results:
        df = pd.DataFrame(all_results)
        filename = scraper.save_to_csv()
        
        # Mostrar estadísticas
        logger.info("\n===== ESTADÍSTICAS =====")
        logger.info(f"Total propiedades: {len(df)}")
        logger.info(f"Precio promedio: ${df['price_mxn'].mean():,.0f}")
        logger.info(f"Superficie promedio: {df['area_m2'].mean():.0f} m²")
        logger.info(f"Precio/m² promedio: ${(df['price_mxn'] / df['area_m2']).mean():,.0f}")
        
        return filename
    else:
        logger.warning("No se obtuvieron resultados")
        return None


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Ejecutar scraper
    asyncio.run(main())

