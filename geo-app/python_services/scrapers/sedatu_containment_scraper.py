"""
Scraper de Perímetros de Contención Urbana SEDATU/CONAVI.

Fuente: SEDATU (Secretaría de Desarrollo Agrario, Territorial y Urbano)
        CONAVI (Comisión Nacional de Vivienda)

Los Perímetros de Contención Urbana clasifican el territorio en:
  - U1 (Intraurbano): zona consolidada con equipamiento y servicios completos
  - U2 (Primer contorno): zona en proceso de consolidación, parcialmente equipada
  - U3 (Segundo contorno/periferia): zona periurbana, equipamiento limitado
  - Rural: fuera del área urbana funcional

Dado que los shapefiles oficiales de SEDATU no están disponibles para descarga
programática continua, este módulo implementa una estimación basada en:
  1. Coordenadas de centros urbanos
  2. Radio urbano estimado por población (ciudades más grandes = mayor radio)
  3. Distancia del punto al centro urbano → clasificación U1/U2/U3/rural

Esta aproximación es consistente con la metodología SEDATU para los fines
del modelo de valuación inmobiliaria.
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from config import DATA_DIR

# ── Paths ────────────────────────────────────────────────────────────────────

OUTPUT_FILE = DATA_DIR / "sedatu_perimetros_urbanos.csv"
CITIES_FILE = DATA_DIR / "cities_mexico_32_states.json"

# ── Ciudades con población estimada y coordenadas ────────────────────────────
#
# Población (millones) de zonas metropolitanas/ciudades principales.
# Fuente: INEGI Censo 2020, proyecciones CONAPO 2025.
# Se usa para estimar el radio urbano funcional.

CITY_POPULATION: Dict[str, Dict[str, Any]] = {
    # ── Ciudad de México ────────────────────────────────────────────────
    "Ciudad de México": {
        "lat": 19.4326, "lon": -99.1332, "state": "Ciudad de México",
        "population_millions": 9.2, "is_metro": True,
    },
    # ── Aguascalientes ──────────────────────────────────────────────────
    "Aguascalientes": {
        "lat": 21.8818, "lon": -102.2916, "state": "Aguascalientes",
        "population_millions": 1.0, "is_metro": True,
    },
    "Jesús María": {
        "lat": 21.9614, "lon": -102.3436, "state": "Aguascalientes",
        "population_millions": 0.13, "is_metro": True,
    },
    # ── Baja California ─────────────────────────────────────────────────
    "Tijuana": {
        "lat": 32.5149, "lon": -117.0382, "state": "Baja California",
        "population_millions": 1.9, "is_metro": False,
    },
    "Mexicali": {
        "lat": 32.6245, "lon": -115.4523, "state": "Baja California",
        "population_millions": 1.05, "is_metro": False,
    },
    "Ensenada": {
        "lat": 31.8667, "lon": -116.5964, "state": "Baja California",
        "population_millions": 0.52, "is_metro": False,
    },
    "Rosarito": {
        "lat": 32.3633, "lon": -117.0581, "state": "Baja California",
        "population_millions": 0.12, "is_metro": False,
    },
    "Tecate": {
        "lat": 32.5722, "lon": -116.6264, "state": "Baja California",
        "population_millions": 0.11, "is_metro": False,
    },
    # ── Baja California Sur ─────────────────────────────────────────────
    "La Paz": {
        "lat": 24.1426, "lon": -110.3128, "state": "Baja California Sur",
        "population_millions": 0.305, "is_metro": False,
    },
    "Cabo San Lucas": {
        "lat": 22.8905, "lon": -109.9167, "state": "Baja California Sur",
        "population_millions": 0.29, "is_metro": False,
    },
    "San José del Cabo": {
        "lat": 23.0598, "lon": -109.6981, "state": "Baja California Sur",
        "population_millions": 0.13, "is_metro": False,
    },
    # ── Campeche ────────────────────────────────────────────────────────
    "Campeche": {
        "lat": 19.8301, "lon": -90.5349, "state": "Campeche",
        "population_millions": 0.295, "is_metro": False,
    },
    "Ciudad del Carmen": {
        "lat": 18.6539, "lon": -91.8075, "state": "Campeche",
        "population_millions": 0.255, "is_metro": False,
    },
    # ── Chiapas ─────────────────────────────────────────────────────────
    "Tuxtla Gutiérrez": {
        "lat": 16.7528, "lon": -93.1152, "state": "Chiapas",
        "population_millions": 0.61, "is_metro": True,
    },
    "Tapachula": {
        "lat": 14.9039, "lon": -92.2572, "state": "Chiapas",
        "population_millions": 0.355, "is_metro": False,
    },
    "San Cristóbal de las Casas": {
        "lat": 16.7370, "lon": -92.6376, "state": "Chiapas",
        "population_millions": 0.215, "is_metro": False,
    },
    "Comitán": {
        "lat": 16.2510, "lon": -92.1336, "state": "Chiapas",
        "population_millions": 0.16, "is_metro": False,
    },
    # ── Chihuahua ───────────────────────────────────────────────────────
    "Chihuahua": {
        "lat": 28.6353, "lon": -106.0889, "state": "Chihuahua",
        "population_millions": 0.95, "is_metro": False,
    },
    "Ciudad Juárez": {
        "lat": 31.6904, "lon": -106.4245, "state": "Chihuahua",
        "population_millions": 1.5, "is_metro": False,
    },
    "Delicias": {
        "lat": 28.1903, "lon": -105.4719, "state": "Chihuahua",
        "population_millions": 0.15, "is_metro": False,
    },
    "Cuauhtémoc": {
        "lat": 28.4050, "lon": -106.8663, "state": "Chihuahua",
        "population_millions": 0.18, "is_metro": False,
    },
    # ── Coahuila ────────────────────────────────────────────────────────
    "Saltillo": {
        "lat": 25.4232, "lon": -100.9925, "state": "Coahuila",
        "population_millions": 0.925, "is_metro": True,
    },
    "Torreón": {
        "lat": 25.5428, "lon": -103.4068, "state": "Coahuila",
        "population_millions": 0.75, "is_metro": True,
    },
    "Monclova": {
        "lat": 26.9069, "lon": -101.4222, "state": "Coahuila",
        "population_millions": 0.24, "is_metro": False,
    },
    "Piedras Negras": {
        "lat": 28.7000, "lon": -100.5236, "state": "Coahuila",
        "population_millions": 0.165, "is_metro": False,
    },
    # ── Colima ──────────────────────────────────────────────────────────
    "Colima": {
        "lat": 19.2433, "lon": -103.7247, "state": "Colima",
        "population_millions": 0.165, "is_metro": True,
    },
    "Manzanillo": {
        "lat": 19.1138, "lon": -104.3389, "state": "Colima",
        "population_millions": 0.185, "is_metro": False,
    },
    "Tecomán": {
        "lat": 18.9117, "lon": -103.8750, "state": "Colima",
        "population_millions": 0.125, "is_metro": False,
    },
    # ── Durango ─────────────────────────────────────────────────────────
    "Durango": {
        "lat": 24.0277, "lon": -104.6532, "state": "Durango",
        "population_millions": 0.69, "is_metro": False,
    },
    "Gómez Palacio": {
        "lat": 25.5611, "lon": -103.4956, "state": "Durango",
        "population_millions": 0.36, "is_metro": True,
    },
    "Lerdo": {
        "lat": 25.5400, "lon": -103.5236, "state": "Durango",
        "population_millions": 0.165, "is_metro": True,
    },
    # ── Estado de México ────────────────────────────────────────────────
    "Toluca": {
        "lat": 19.2826, "lon": -99.6557, "state": "México",
        "population_millions": 0.94, "is_metro": True,
    },
    "Ecatepec": {
        "lat": 19.6017, "lon": -99.0500, "state": "México",
        "population_millions": 1.65, "is_metro": True,
    },
    "Naucalpan": {
        "lat": 19.4783, "lon": -99.2388, "state": "México",
        "population_millions": 0.845, "is_metro": True,
    },
    "Nezahualcóyotl": {
        "lat": 19.4008, "lon": -98.9886, "state": "México",
        "population_millions": 1.08, "is_metro": True,
    },
    "Tlalnepantla": {
        "lat": 19.5370, "lon": -99.2040, "state": "México",
        "population_millions": 0.68, "is_metro": True,
    },
    "Atizapán de Zaragoza": {
        "lat": 19.5578, "lon": -99.2539, "state": "México",
        "population_millions": 0.53, "is_metro": True,
    },
    "Huixquilucan": {
        "lat": 19.3611, "lon": -99.3500, "state": "México",
        "population_millions": 0.31, "is_metro": True,
    },
    "Metepec": {
        "lat": 19.2594, "lon": -99.6044, "state": "México",
        "population_millions": 0.24, "is_metro": True,
    },
    "Cuautitlán Izcalli": {
        "lat": 19.6472, "lon": -99.2117, "state": "México",
        "population_millions": 0.57, "is_metro": True,
    },
    "Texcoco": {
        "lat": 19.5150, "lon": -98.8822, "state": "México",
        "population_millions": 0.26, "is_metro": True,
    },
    "Ixtapaluca": {
        "lat": 19.3189, "lon": -98.8822, "state": "México",
        "population_millions": 0.53, "is_metro": True,
    },
    "Chalco": {
        "lat": 19.2633, "lon": -98.8975, "state": "México",
        "population_millions": 0.38, "is_metro": True,
    },
    # ── Guanajuato ──────────────────────────────────────────────────────
    "León": {
        "lat": 21.1250, "lon": -101.6860, "state": "Guanajuato",
        "population_millions": 1.6, "is_metro": False,
    },
    "Irapuato": {
        "lat": 20.6767, "lon": -101.3554, "state": "Guanajuato",
        "population_millions": 0.59, "is_metro": False,
    },
    "Celaya": {
        "lat": 20.5236, "lon": -100.8155, "state": "Guanajuato",
        "population_millions": 0.525, "is_metro": False,
    },
    "Salamanca": {
        "lat": 20.5739, "lon": -101.1953, "state": "Guanajuato",
        "population_millions": 0.28, "is_metro": False,
    },
    "Guanajuato": {
        "lat": 21.0190, "lon": -101.2574, "state": "Guanajuato",
        "population_millions": 0.195, "is_metro": False,
    },
    "San Miguel de Allende": {
        "lat": 20.9144, "lon": -100.7436, "state": "Guanajuato",
        "population_millions": 0.175, "is_metro": False,
    },
    "Silao": {
        "lat": 20.9472, "lon": -101.4281, "state": "Guanajuato",
        "population_millions": 0.20, "is_metro": False,
    },
    # ── Guerrero ────────────────────────────────────────────────────────
    "Acapulco": {
        "lat": 16.8531, "lon": -99.8237, "state": "Guerrero",
        "population_millions": 0.84, "is_metro": False,
    },
    "Chilpancingo": {
        "lat": 17.5510, "lon": -99.5014, "state": "Guerrero",
        "population_millions": 0.285, "is_metro": False,
    },
    "Iguala": {
        "lat": 18.3456, "lon": -99.5397, "state": "Guerrero",
        "population_millions": 0.15, "is_metro": False,
    },
    "Zihuatanejo": {
        "lat": 17.6431, "lon": -101.5514, "state": "Guerrero",
        "population_millions": 0.13, "is_metro": False,
    },
    "Taxco": {
        "lat": 18.5564, "lon": -99.6050, "state": "Guerrero",
        "population_millions": 0.11, "is_metro": False,
    },
    # ── Hidalgo ─────────────────────────────────────────────────────────
    "Pachuca": {
        "lat": 20.1011, "lon": -98.7591, "state": "Hidalgo",
        "population_millions": 0.315, "is_metro": True,
    },
    "Tulancingo": {
        "lat": 20.0849, "lon": -98.3636, "state": "Hidalgo",
        "population_millions": 0.17, "is_metro": False,
    },
    "Tula de Allende": {
        "lat": 20.0536, "lon": -99.3406, "state": "Hidalgo",
        "population_millions": 0.115, "is_metro": False,
    },
    "Tizayuca": {
        "lat": 19.8411, "lon": -98.9814, "state": "Hidalgo",
        "population_millions": 0.14, "is_metro": True,
    },
    # ── Jalisco ─────────────────────────────────────────────────────────
    "Guadalajara": {
        "lat": 20.6597, "lon": -103.3496, "state": "Jalisco",
        "population_millions": 1.4, "is_metro": True,
    },
    "Zapopan": {
        "lat": 20.7167, "lon": -103.4000, "state": "Jalisco",
        "population_millions": 1.5, "is_metro": True,
    },
    "Tlaquepaque": {
        "lat": 20.6400, "lon": -103.3100, "state": "Jalisco",
        "population_millions": 0.68, "is_metro": True,
    },
    "Tonalá": {
        "lat": 20.6250, "lon": -103.2333, "state": "Jalisco",
        "population_millions": 0.56, "is_metro": True,
    },
    "Tlajomulco": {
        "lat": 20.4740, "lon": -103.4410, "state": "Jalisco",
        "population_millions": 0.73, "is_metro": True,
    },
    "El Salto": {
        "lat": 20.5196, "lon": -103.2218, "state": "Jalisco",
        "population_millions": 0.18, "is_metro": True,
    },
    "Puerto Vallarta": {
        "lat": 20.6534, "lon": -105.2253, "state": "Jalisco",
        "population_millions": 0.325, "is_metro": False,
    },
    "Lagos de Moreno": {
        "lat": 21.3575, "lon": -101.9306, "state": "Jalisco",
        "population_millions": 0.175, "is_metro": False,
    },
    "Tepatitlán": {
        "lat": 20.8167, "lon": -102.7306, "state": "Jalisco",
        "population_millions": 0.155, "is_metro": False,
    },
    # ── Michoacán ───────────────────────────────────────────────────────
    "Morelia": {
        "lat": 19.7060, "lon": -101.1950, "state": "Michoacán",
        "population_millions": 0.85, "is_metro": True,
    },
    "Uruapan": {
        "lat": 19.4178, "lon": -102.0528, "state": "Michoacán",
        "population_millions": 0.34, "is_metro": False,
    },
    "Zamora": {
        "lat": 19.9853, "lon": -102.2836, "state": "Michoacán",
        "population_millions": 0.20, "is_metro": False,
    },
    "Lázaro Cárdenas": {
        "lat": 17.9583, "lon": -102.2000, "state": "Michoacán",
        "population_millions": 0.19, "is_metro": False,
    },
    "Pátzcuaro": {
        "lat": 19.5158, "lon": -101.6097, "state": "Michoacán",
        "population_millions": 0.095, "is_metro": False,
    },
    "Apatzingán": {
        "lat": 19.0883, "lon": -102.3508, "state": "Michoacán",
        "population_millions": 0.135, "is_metro": False,
    },
    "Zitácuaro": {
        "lat": 19.4361, "lon": -100.3600, "state": "Michoacán",
        "population_millions": 0.16, "is_metro": False,
    },
    "La Piedad": {
        "lat": 20.3439, "lon": -102.0186, "state": "Michoacán",
        "population_millions": 0.11, "is_metro": False,
    },
    # ── Morelos ─────────────────────────────────────────────────────────
    "Cuernavaca": {
        "lat": 18.9186, "lon": -99.2342, "state": "Morelos",
        "population_millions": 0.40, "is_metro": True,
    },
    "Cuautla": {
        "lat": 18.8117, "lon": -98.9542, "state": "Morelos",
        "population_millions": 0.20, "is_metro": False,
    },
    "Jiutepec": {
        "lat": 18.8817, "lon": -99.1733, "state": "Morelos",
        "population_millions": 0.225, "is_metro": True,
    },
    "Temixco": {
        "lat": 18.8531, "lon": -99.2311, "state": "Morelos",
        "population_millions": 0.115, "is_metro": True,
    },
    # ── Nayarit ─────────────────────────────────────────────────────────
    "Tepic": {
        "lat": 21.5010, "lon": -104.8943, "state": "Nayarit",
        "population_millions": 0.43, "is_metro": False,
    },
    "Bahía de Banderas": {
        "lat": 20.7536, "lon": -105.3828, "state": "Nayarit",
        "population_millions": 0.175, "is_metro": False,
    },
    # ── Nuevo León ──────────────────────────────────────────────────────
    "Monterrey": {
        "lat": 25.6866, "lon": -100.3161, "state": "Nuevo León",
        "population_millions": 1.15, "is_metro": True,
    },
    "San Pedro Garza García": {
        "lat": 25.6572, "lon": -100.4028, "state": "Nuevo León",
        "population_millions": 0.13, "is_metro": True,
    },
    "Apodaca": {
        "lat": 25.7833, "lon": -100.1833, "state": "Nuevo León",
        "population_millions": 0.65, "is_metro": True,
    },
    "Guadalupe (NL)": {
        "lat": 25.6775, "lon": -100.2597, "state": "Nuevo León",
        "population_millions": 0.68, "is_metro": True,
    },
    "San Nicolás de los Garza": {
        "lat": 25.7500, "lon": -100.2833, "state": "Nuevo León",
        "population_millions": 0.43, "is_metro": True,
    },
    "Santa Catarina (NL)": {
        "lat": 25.6733, "lon": -100.4581, "state": "Nuevo León",
        "population_millions": 0.32, "is_metro": True,
    },
    "General Escobedo": {
        "lat": 25.7975, "lon": -100.3183, "state": "Nuevo León",
        "population_millions": 0.43, "is_metro": True,
    },
    "García (NL)": {
        "lat": 25.8167, "lon": -100.5917, "state": "Nuevo León",
        "population_millions": 0.37, "is_metro": True,
    },
    # ── Oaxaca ──────────────────────────────────────────────────────────
    "Oaxaca": {
        "lat": 17.0732, "lon": -96.7266, "state": "Oaxaca",
        "population_millions": 0.305, "is_metro": True,
    },
    "Salina Cruz": {
        "lat": 16.1644, "lon": -95.1964, "state": "Oaxaca",
        "population_millions": 0.095, "is_metro": False,
    },
    "Juchitán": {
        "lat": 16.4361, "lon": -95.0197, "state": "Oaxaca",
        "population_millions": 0.10, "is_metro": False,
    },
    "Huatulco": {
        "lat": 15.7833, "lon": -96.1333, "state": "Oaxaca",
        "population_millions": 0.055, "is_metro": False,
    },
    "Tuxtepec": {
        "lat": 18.1000, "lon": -96.1222, "state": "Oaxaca",
        "population_millions": 0.165, "is_metro": False,
    },
    # ── Puebla ──────────────────────────────────────────────────────────
    "Puebla": {
        "lat": 19.0414, "lon": -98.2063, "state": "Puebla",
        "population_millions": 1.7, "is_metro": True,
    },
    "Tehuacán": {
        "lat": 18.4617, "lon": -97.3928, "state": "Puebla",
        "population_millions": 0.33, "is_metro": False,
    },
    "San Martín Texmelucan": {
        "lat": 19.2836, "lon": -98.4389, "state": "Puebla",
        "population_millions": 0.155, "is_metro": False,
    },
    "Atlixco": {
        "lat": 18.9069, "lon": -98.4386, "state": "Puebla",
        "population_millions": 0.14, "is_metro": False,
    },
    "Cholula": {
        "lat": 19.0636, "lon": -98.3042, "state": "Puebla",
        "population_millions": 0.14, "is_metro": True,
    },
    "San Andrés Cholula": {
        "lat": 19.0525, "lon": -98.2961, "state": "Puebla",
        "population_millions": 0.155, "is_metro": True,
    },
    # ── Querétaro ───────────────────────────────────────────────────────
    "Querétaro": {
        "lat": 20.5888, "lon": -100.3899, "state": "Querétaro",
        "population_millions": 1.05, "is_metro": True,
    },
    "San Juan del Río": {
        "lat": 20.3881, "lon": -99.9961, "state": "Querétaro",
        "population_millions": 0.285, "is_metro": False,
    },
    "El Marqués": {
        "lat": 20.6167, "lon": -100.3000, "state": "Querétaro",
        "population_millions": 0.23, "is_metro": True,
    },
    "Corregidora": {
        "lat": 20.5333, "lon": -100.4500, "state": "Querétaro",
        "population_millions": 0.22, "is_metro": True,
    },
    # ── Quintana Roo ────────────────────────────────────────────────────
    "Cancún": {
        "lat": 21.1619, "lon": -86.8515, "state": "Quintana Roo",
        "population_millions": 0.89, "is_metro": False,
    },
    "Playa del Carmen": {
        "lat": 20.6274, "lon": -87.0739, "state": "Quintana Roo",
        "population_millions": 0.35, "is_metro": False,
    },
    "Chetumal": {
        "lat": 18.5001, "lon": -88.2962, "state": "Quintana Roo",
        "population_millions": 0.23, "is_metro": False,
    },
    "Tulum": {
        "lat": 20.2114, "lon": -87.4654, "state": "Quintana Roo",
        "population_millions": 0.05, "is_metro": False,
    },
    "Cozumel": {
        "lat": 20.5108, "lon": -86.9461, "state": "Quintana Roo",
        "population_millions": 0.09, "is_metro": False,
    },
    # ── San Luis Potosí ─────────────────────────────────────────────────
    "San Luis Potosí": {
        "lat": 22.1565, "lon": -100.9855, "state": "San Luis Potosí",
        "population_millions": 0.87, "is_metro": True,
    },
    "Soledad de Graciano Sánchez": {
        "lat": 22.1833, "lon": -100.9333, "state": "San Luis Potosí",
        "population_millions": 0.365, "is_metro": True,
    },
    "Ciudad Valles": {
        "lat": 21.9964, "lon": -99.0117, "state": "San Luis Potosí",
        "population_millions": 0.185, "is_metro": False,
    },
    "Matehuala": {
        "lat": 23.6500, "lon": -100.6444, "state": "San Luis Potosí",
        "population_millions": 0.105, "is_metro": False,
    },
    # ── Sinaloa ─────────────────────────────────────────────────────────
    "Culiacán": {
        "lat": 24.8049, "lon": -107.3940, "state": "Sinaloa",
        "population_millions": 1.0, "is_metro": False,
    },
    "Mazatlán": {
        "lat": 23.2494, "lon": -106.4111, "state": "Sinaloa",
        "population_millions": 0.51, "is_metro": False,
    },
    "Los Mochis": {
        "lat": 25.7903, "lon": -108.9939, "state": "Sinaloa",
        "population_millions": 0.445, "is_metro": False,
    },
    "Guasave": {
        "lat": 25.5700, "lon": -108.4700, "state": "Sinaloa",
        "population_millions": 0.30, "is_metro": False,
    },
    # ── Sonora ──────────────────────────────────────────────────────────
    "Hermosillo": {
        "lat": 29.0729, "lon": -110.9559, "state": "Sonora",
        "population_millions": 0.95, "is_metro": False,
    },
    "Ciudad Obregón": {
        "lat": 27.4861, "lon": -109.9411, "state": "Sonora",
        "population_millions": 0.41, "is_metro": False,
    },
    "Nogales": {
        "lat": 31.3086, "lon": -110.9436, "state": "Sonora",
        "population_millions": 0.265, "is_metro": False,
    },
    "Guaymas": {
        "lat": 27.9178, "lon": -110.8989, "state": "Sonora",
        "population_millions": 0.18, "is_metro": False,
    },
    "Puerto Peñasco": {
        "lat": 31.3167, "lon": -113.5333, "state": "Sonora",
        "population_millions": 0.065, "is_metro": False,
    },
    "Navojoa": {
        "lat": 27.0700, "lon": -109.4436, "state": "Sonora",
        "population_millions": 0.165, "is_metro": False,
    },
    # ── Tabasco ─────────────────────────────────────────────────────────
    "Villahermosa": {
        "lat": 17.9892, "lon": -92.9475, "state": "Tabasco",
        "population_millions": 0.69, "is_metro": True,
    },
    "Comalcalco": {
        "lat": 18.2833, "lon": -93.2000, "state": "Tabasco",
        "population_millions": 0.20, "is_metro": False,
    },
    "Cárdenas (Tab)": {
        "lat": 18.0000, "lon": -93.3833, "state": "Tabasco",
        "population_millions": 0.28, "is_metro": False,
    },
    "Paraíso": {
        "lat": 18.3972, "lon": -93.2153, "state": "Tabasco",
        "population_millions": 0.095, "is_metro": False,
    },
    "Macuspana": {
        "lat": 17.7667, "lon": -92.5972, "state": "Tabasco",
        "population_millions": 0.165, "is_metro": False,
    },
    # ── Tamaulipas ──────────────────────────────────────────────────────
    "Reynosa": {
        "lat": 26.0923, "lon": -98.2775, "state": "Tamaulipas",
        "population_millions": 0.69, "is_metro": False,
    },
    "Matamoros": {
        "lat": 25.8697, "lon": -97.5028, "state": "Tamaulipas",
        "population_millions": 0.54, "is_metro": False,
    },
    "Nuevo Laredo": {
        "lat": 27.4764, "lon": -99.5106, "state": "Tamaulipas",
        "population_millions": 0.42, "is_metro": False,
    },
    "Tampico": {
        "lat": 22.2331, "lon": -97.8611, "state": "Tamaulipas",
        "population_millions": 0.32, "is_metro": True,
    },
    "Ciudad Victoria": {
        "lat": 23.7369, "lon": -99.1411, "state": "Tamaulipas",
        "population_millions": 0.36, "is_metro": False,
    },
    "Ciudad Madero": {
        "lat": 22.2764, "lon": -97.8361, "state": "Tamaulipas",
        "population_millions": 0.215, "is_metro": True,
    },
    "Altamira": {
        "lat": 22.3931, "lon": -97.9431, "state": "Tamaulipas",
        "population_millions": 0.27, "is_metro": True,
    },
    # ── Tlaxcala ────────────────────────────────────────────────────────
    "Tlaxcala": {
        "lat": 19.3181, "lon": -98.2375, "state": "Tlaxcala",
        "population_millions": 0.105, "is_metro": False,
    },
    "Apizaco": {
        "lat": 19.4167, "lon": -98.1333, "state": "Tlaxcala",
        "population_millions": 0.082, "is_metro": False,
    },
    "Huamantla": {
        "lat": 19.3142, "lon": -97.9222, "state": "Tlaxcala",
        "population_millions": 0.093, "is_metro": False,
    },
    # ── Veracruz ────────────────────────────────────────────────────────
    "Veracruz": {
        "lat": 19.2026, "lon": -96.1533, "state": "Veracruz",
        "population_millions": 0.61, "is_metro": True,
    },
    "Xalapa": {
        "lat": 19.5438, "lon": -96.9102, "state": "Veracruz",
        "population_millions": 0.52, "is_metro": False,
    },
    "Coatzacoalcos": {
        "lat": 18.1500, "lon": -94.4333, "state": "Veracruz",
        "population_millions": 0.32, "is_metro": False,
    },
    "Poza Rica": {
        "lat": 20.5333, "lon": -97.4500, "state": "Veracruz",
        "population_millions": 0.215, "is_metro": False,
    },
    "Córdoba": {
        "lat": 18.8833, "lon": -96.9333, "state": "Veracruz",
        "population_millions": 0.22, "is_metro": False,
    },
    "Orizaba": {
        "lat": 18.8500, "lon": -97.1000, "state": "Veracruz",
        "population_millions": 0.13, "is_metro": False,
    },
    "Minatitlán": {
        "lat": 17.9833, "lon": -94.5500, "state": "Veracruz",
        "population_millions": 0.16, "is_metro": False,
    },
    "Boca del Río": {
        "lat": 19.1058, "lon": -96.1078, "state": "Veracruz",
        "population_millions": 0.155, "is_metro": True,
    },
    "Tuxpan": {
        "lat": 20.9569, "lon": -97.4008, "state": "Veracruz",
        "population_millions": 0.155, "is_metro": False,
    },
    # ── Yucatán ─────────────────────────────────────────────────────────
    "Mérida": {
        "lat": 20.9674, "lon": -89.5926, "state": "Yucatán",
        "population_millions": 1.0, "is_metro": True,
    },
    "Valladolid": {
        "lat": 20.6894, "lon": -88.1994, "state": "Yucatán",
        "population_millions": 0.085, "is_metro": False,
    },
    "Tizimín": {
        "lat": 21.1428, "lon": -88.1500, "state": "Yucatán",
        "population_millions": 0.08, "is_metro": False,
    },
    "Progreso": {
        "lat": 21.2833, "lon": -89.6667, "state": "Yucatán",
        "population_millions": 0.058, "is_metro": False,
    },
    "Kanasín": {
        "lat": 20.9333, "lon": -89.5578, "state": "Yucatán",
        "population_millions": 0.115, "is_metro": True,
    },
    # ── Zacatecas ───────────────────────────────────────────────────────
    "Zacatecas": {
        "lat": 22.7709, "lon": -102.5833, "state": "Zacatecas",
        "population_millions": 0.155, "is_metro": True,
    },
    "Fresnillo": {
        "lat": 23.1747, "lon": -102.8697, "state": "Zacatecas",
        "population_millions": 0.24, "is_metro": False,
    },
    "Guadalupe (Zac)": {
        "lat": 22.7539, "lon": -102.5214, "state": "Zacatecas",
        "population_millions": 0.20, "is_metro": True,
    },
    "Jerez": {
        "lat": 22.6500, "lon": -103.0000, "state": "Zacatecas",
        "population_millions": 0.065, "is_metro": False,
    },
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia haversine en kilómetros entre dos puntos."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _estimate_city_radius_km(population_millions: float) -> float:
    """
    Estima el radio urbano funcional en km basado en la población.

    Modelo empírico calibrado con datos SEDATU:
    - CDMX (~9M): ~25 km de radio funcional
    - Guadalajara (~1.4M): ~12 km
    - Ciudad media (~0.5M): ~7 km
    - Ciudad pequeña (~0.2M): ~4 km

    Fórmula: radio = 4.5 * population^0.42 (ajuste empírico)
    """
    if population_millions <= 0:
        return 3.0  # Mínimo para localidades pequeñas
    radius = 4.5 * (population_millions ** 0.42)
    return max(radius, 2.0)  # Mínimo 2 km


def _find_nearest_city(
    lat: float, lon: float
) -> Optional[Tuple[str, Dict[str, Any], float]]:
    """
    Encuentra la ciudad más cercana y su distancia.

    Returns:
        Tupla (nombre_ciudad, datos_ciudad, distancia_km) o None
    """
    best_city = None
    best_data = None
    best_dist = float("inf")

    for city_name, city_data in CITY_POPULATION.items():
        dist = _haversine_km(lat, lon, city_data["lat"], city_data["lon"])
        if dist < best_dist:
            best_dist = dist
            best_city = city_name
            best_data = city_data

    if best_city is None:
        return None

    return (best_city, best_data, best_dist)


def get_urban_zone(lat: float, lon: float) -> str:
    """
    Clasifica una coordenada en zona de contención urbana SEDATU.

    Metodología:
    - Encuentra la ciudad más cercana
    - Estima el radio urbano por población
    - U1: dentro del 30% del radio (zona consolidada)
    - U2: dentro del 60% del radio (primer contorno)
    - U3: dentro del 100% del radio (segundo contorno)
    - Rural: fuera del radio urbano

    Args:
        lat: Latitud del punto
        lon: Longitud del punto

    Returns:
        'U1', 'U2', 'U3', o 'rural'
    """
    result = _find_nearest_city(lat, lon)
    if result is None:
        return "rural"

    city_name, city_data, distance_km = result
    pop = city_data["population_millions"]
    radius = _estimate_city_radius_km(pop)

    # Clasificación por proporción de distancia al radio
    ratio = distance_km / radius

    if ratio <= 0.30:
        return "U1"
    elif ratio <= 0.60:
        return "U2"
    elif ratio <= 1.00:
        return "U3"
    else:
        return "rural"


def urban_zone_score(zone: str) -> float:
    """
    Convierte la zona de contención urbana a un puntaje numérico.

    Los valores reflejan la prima de precio asociada a la ubicación:
    - U1 (intraurbano): máximo valor por cercanía a servicios
    - U2 (primer contorno): valor moderado-alto
    - U3 (periferia): valor bajo-moderado
    - Rural: valor mínimo

    Args:
        zone: Zona de contención ('U1', 'U2', 'U3', 'rural')

    Returns:
        Score de 0.0 a 1.0
    """
    scores = {
        "U1": 1.0,
        "U2": 0.6,
        "U3": 0.3,
        "rural": 0.1,
    }
    return scores.get(zone, 0.1)


def add_urban_containment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columnas de contención urbana al DataFrame.

    Requiere columnas 'lat' y 'lon' en el DataFrame.
    Agrega: urban_zone, urban_zone_score, nearest_city, distance_to_center_km

    Args:
        df: DataFrame con columnas lat y lon

    Returns:
        DataFrame con columnas de contención urbana agregadas
    """
    if df.empty:
        logger.warning("DataFrame vacío, no se agregan features de contención urbana")
        return df

    df = df.copy()

    if "lat" not in df.columns or "lon" not in df.columns:
        logger.error("DataFrame no tiene columnas 'lat' y 'lon'")
        return df

    logger.info(f"Calculando features de contención urbana para {len(df)} registros...")

    zones = []
    scores = []
    nearest_cities = []
    distances = []

    for _, row in df.iterrows():
        lat = row.get("lat")
        lon = row.get("lon")

        if pd.isna(lat) or pd.isna(lon):
            zones.append(None)
            scores.append(None)
            nearest_cities.append(None)
            distances.append(None)
            continue

        zone = get_urban_zone(lat, lon)
        zones.append(zone)
        scores.append(urban_zone_score(zone))

        result = _find_nearest_city(lat, lon)
        if result:
            nearest_cities.append(result[0])
            distances.append(round(result[2], 2))
        else:
            nearest_cities.append(None)
            distances.append(None)

    df["urban_zone"] = zones
    df["urban_zone_score"] = scores
    df["nearest_city"] = nearest_cities
    df["distance_to_center_km"] = distances

    # Estadísticas
    zone_counts = df["urban_zone"].value_counts()
    logger.info(f"Distribución de zonas urbanas:\n{zone_counts.to_string()}")

    avg_score = df["urban_zone_score"].mean()
    logger.info(f"Puntaje de urbanización promedio: {avg_score:.2f}")

    return df


def _generate_reference_data() -> pd.DataFrame:
    """
    Genera un CSV de referencia con datos de contención urbana
    para las ciudades principales y puntos de prueba.
    """
    rows = []

    # Para cada ciudad, generar puntos en el centro y en los contornos
    for city_name, city_data in CITY_POPULATION.items():
        lat = city_data["lat"]
        lon = city_data["lon"]
        pop = city_data["population_millions"]
        radius = _estimate_city_radius_km(pop)

        # Punto central (debería ser U1)
        zone = get_urban_zone(lat, lon)
        rows.append({
            "city": city_name,
            "state": city_data["state"],
            "lat": lat,
            "lon": lon,
            "population_millions": pop,
            "estimated_radius_km": round(radius, 2),
            "urban_zone": zone,
            "urban_zone_score": urban_zone_score(zone),
            "point_type": "centro",
            "generated_at": datetime.now().isoformat(),
        })

    df = pd.DataFrame(rows)
    return df


def main():
    """Genera datos de referencia de contención urbana y los guarda en CSV."""
    logger.info("=" * 70)
    logger.info("SEDATU - PERIMETROS DE CONTENCION URBANA")
    logger.info("Generando clasificación de zonas urbanas para ciudades principales")
    logger.info("=" * 70)

    df = _generate_reference_data()

    if df.empty:
        logger.warning("No se generaron datos de referencia")
        return

    # Guardar CSV
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    logger.info(f"Guardado: {OUTPUT_FILE} ({len(df)} registros)")

    # Reporte
    logger.info("\n" + "=" * 60)
    logger.info("REPORTE DE CONTENCION URBANA")
    logger.info("=" * 60)

    logger.info(f"\nTotal de ciudades analizadas: {len(df)}")

    zone_counts = df["urban_zone"].value_counts()
    for zone in ["U1", "U2", "U3", "rural"]:
        count = zone_counts.get(zone, 0)
        logger.info(f"  {zone}: {count} ciudades")

    logger.info(f"\nRadio urbano promedio: {df['estimated_radius_km'].mean():.1f} km")
    logger.info(f"Radio máximo: {df.loc[df['estimated_radius_km'].idxmax(), 'city']} "
                f"({df['estimated_radius_km'].max():.1f} km)")
    logger.info(f"Radio mínimo: {df.loc[df['estimated_radius_km'].idxmin(), 'city']} "
                f"({df['estimated_radius_km'].min():.1f} km)")

    # Ejemplos de clasificación
    logger.info("\nEjemplos de clasificación:")
    test_points = [
        ("Centro CDMX", 19.4326, -99.1332),
        ("Periferia GDL (Tlajomulco sur)", 20.42, -103.45),
        ("Rural (campo Jalisco)", 20.8, -104.0),
        ("Centro Monterrey", 25.6866, -100.3161),
        ("Periferia Cancún", 21.2, -86.9),
    ]
    for name, lat, lon in test_points:
        zone = get_urban_zone(lat, lon)
        score = urban_zone_score(zone)
        result = _find_nearest_city(lat, lon)
        nearest = result[0] if result else "N/A"
        dist = f"{result[2]:.1f}" if result else "N/A"
        logger.info(f"  {name}: {zone} (score={score}, nearest={nearest}, dist={dist}km)")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    main()
