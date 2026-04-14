# ================================================================
# GENERADOR DE DATOS SINTÉTICOS PARA ENTRENAMIENTO
# Este script genera datos realistas de terrenos para entrenar el modelo ML
# ================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from loguru import logger
import sys

sys.path.append('.')
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_COMPARABLES

# Semilla para reproducibilidad
np.random.seed(42)
random.seed(42)

# ================================================================
# CONFIGURACIÓN COMPLETA DE TODOS LOS ESTADOS DE MÉXICO
# Precios/m² basados en datos reales SHF y mercado nacional
# ================================================================

# Configuración de ciudades con precios promedio/m² realistas
CIUDADES_CONFIG = {
    # ==================== AGUASCALIENTES ====================
    'Aguascalientes': {
        'state': 'Aguascalientes',
        'lat': 21.8853, 'lon': -102.2916,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 150
    },
    'Jesús María': {
        'state': 'Aguascalientes',
        'lat': 21.9392, 'lon': -102.3425,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 80
    },
    
    # ==================== BAJA CALIFORNIA ====================
    'Tijuana': {
        'state': 'Baja California',
        'lat': 32.5149, 'lon': -117.0382,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 200
    },
    'Mexicali': {
        'state': 'Baja California',
        'lat': 32.6278, 'lon': -115.4544,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 150
    },
    'Ensenada': {
        'state': 'Baja California',
        'lat': 31.8614, 'lon': -116.6017,
        'price_m2_base': 6500,
        'price_m2_std': 2500,
        'n_samples': 120
    },
    'Rosarito': {
        'state': 'Baja California',
        'lat': 32.3384, 'lon': -117.0558,
        'price_m2_base': 9000,
        'price_m2_std': 3500,
        'n_samples': 90
    },
    
    # ==================== BAJA CALIFORNIA SUR ====================
    'La Paz': {
        'state': 'Baja California Sur',
        'lat': 24.1428, 'lon': -110.3096,
        'price_m2_base': 8000,
        'price_m2_std': 3000,
        'n_samples': 150
    },
    'Los Cabos': {
        'state': 'Baja California Sur',
        'lat': 22.8906, 'lon': -109.9167,
        'price_m2_base': 18000,
        'price_m2_std': 7000,
        'n_samples': 120
    },
    'Cabo San Lucas': {
        'state': 'Baja California Sur',
        'lat': 22.8863, 'lon': -109.9070,
        'price_m2_base': 20000,
        'price_m2_std': 8000,
        'n_samples': 80
    },
    
    # ==================== CAMPECHE ====================
    'Campeche': {
        'state': 'Campeche',
        'lat': 19.8301, 'lon': -90.5359,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 100
    },
    'Ciudad del Carmen': {
        'state': 'Campeche',
        'lat': 18.6478, 'lon': -91.8304,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 80
    },
    
    # ==================== CHIAPAS ====================
    'Tuxtla Gutiérrez': {
        'state': 'Chiapas',
        'lat': 16.7550, 'lon': -93.1341,
        'price_m2_base': 3000,
        'price_m2_std': 1200,
        'n_samples': 120
    },
    'Tapachula': {
        'state': 'Chiapas',
        'lat': 14.9078, 'lon': -92.2651,
        'price_m2_base': 3500,
        'price_m2_std': 1300,
        'n_samples': 100
    },
    'San Cristóbal de las Casas': {
        'state': 'Chiapas',
        'lat': 16.7333, 'lon': -92.6414,
        'price_m2_base': 4500,
        'price_m2_std': 1800,
        'n_samples': 80
    },
    
    # ==================== CHIHUAHUA ====================
    'Chihuahua': {
        'state': 'Chihuahua',
        'lat': 28.6329, 'lon': -106.0691,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 150
    },
    'Ciudad Juárez': {
        'state': 'Chihuahua',
        'lat': 31.6904, 'lon': -106.4245,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 180
    },
    'Cuauhtémoc (Chihuahua)': {
        'state': 'Chihuahua',
        'lat': 28.4063, 'lon': -106.8675,
        'price_m2_base': 3500,
        'price_m2_std': 1400,
        'n_samples': 80
    },
    
    # ==================== CIUDAD DE MÉXICO ====================
    'Ciudad de México': {
        'state': 'Ciudad de México',
        'lat': 19.4326, 'lon': -99.1332,
        'price_m2_base': 18000,
        'price_m2_std': 8000,
        'n_samples': 300
    },
    'Benito Juárez': {
        'state': 'Ciudad de México',
        'lat': 19.3727, 'lon': -99.1564,
        'price_m2_base': 25000,
        'price_m2_std': 10000,
        'n_samples': 120
    },
    'Miguel Hidalgo': {
        'state': 'Ciudad de México',
        'lat': 19.4250, 'lon': -99.2002,
        'price_m2_base': 30000,
        'price_m2_std': 12000,
        'n_samples': 100
    },
    'Cuauhtémoc': {
        'state': 'Ciudad de México',
        'lat': 19.4328, 'lon': -99.1332,
        'price_m2_base': 22000,
        'price_m2_std': 9000,
        'n_samples': 150
    },
    'Polanco': {
        'state': 'Ciudad de México',
        'lat': 19.4339, 'lon': -99.2008,
        'price_m2_base': 35000,
        'price_m2_std': 15000,
        'n_samples': 80
    },
    
    # ==================== COAHUILA ====================
    'Saltillo': {
        'state': 'Coahuila',
        'lat': 25.4240, 'lon': -101.0053,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 150
    },
    'Torreón': {
        'state': 'Coahuila',
        'lat': 25.5409, 'lon': -103.4271,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 180
    },
    'Monclova': {
        'state': 'Coahuila',
        'lat': 26.9036, 'lon': -101.4209,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 100
    },
    'Piedras Negras': {
        'state': 'Coahuila',
        'lat': 28.7008, 'lon': -100.5176,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 80
    },
    
    # ==================== COLIMA ====================
    'Colima': {
        'state': 'Colima',
        'lat': 19.2456, 'lon': -103.7245,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 100
    },
    'Manzanillo': {
        'state': 'Colima',
        'lat': 19.0512, 'lon': -104.3184,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 120
    },
    
    # ==================== DURANGO ====================
    'Durango': {
        'state': 'Durango',
        'lat': 24.0244, 'lon': -104.6644,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 120
    },
    'Gómez Palacio': {
        'state': 'Durango',
        'lat': 25.5587, 'lon': -103.4958,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 100
    },
    
    # ==================== ESTADO DE MÉXICO ====================
    'Naucalpan': {
        'state': 'Estado de México',
        'lat': 19.4784, 'lon': -99.2386,
        'price_m2_base': 10000,
        'price_m2_std': 4000,
        'n_samples': 180
    },
    'Tlalnepantla': {
        'state': 'Estado de México',
        'lat': 19.5287, 'lon': -99.1950,
        'price_m2_base': 9000,
        'price_m2_std': 3500,
        'n_samples': 150
    },
    'Ecatepec': {
        'state': 'Estado de México',
        'lat': 19.6047, 'lon': -99.0607,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 200
    },
    'Toluca': {
        'state': 'Estado de México',
        'lat': 19.2925, 'lon': -99.6573,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 180
    },
    'Atizapán de Zaragoza': {
        'state': 'Estado de México',
        'lat': 19.5700, 'lon': -99.2697,
        'price_m2_base': 8000,
        'price_m2_std': 3000,
        'n_samples': 150
    },
    'Huixquilucan': {
        'state': 'Estado de México',
        'lat': 19.3600, 'lon': -99.3500,
        'price_m2_base': 12000,
        'price_m2_std': 5000,
        'n_samples': 120
    },
    'Cuautitlán Izcalli': {
        'state': 'Estado de México',
        'lat': 19.6472, 'lon': -99.2079,
        'price_m2_base': 7500,
        'price_m2_std': 2900,
        'n_samples': 130
    },
    'Metepéc': {
        'state': 'Estado de México',
        'lat': 19.2567, 'lon': -99.6044,
        'price_m2_base': 6500,
        'price_m2_std': 2500,
        'n_samples': 100
    },
    'Nicolás Romero': {
        'state': 'Estado de México',
        'lat': 19.6253, 'lon': -99.3150,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 100
    },
    'Ixtapaluca': {
        'state': 'Estado de México',
        'lat': 19.3180, 'lon': -98.8803,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 120
    },
    
    # ==================== GUANAJUATO ====================
    'León': {
        'state': 'Guanajuato',
        'lat': 21.1221, 'lon': -101.6827,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 200
    },
    'Guanajuato': {
        'state': 'Guanajuato',
        'lat': 21.0190, 'lon': -101.2569,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 100
    },
    'San Miguel de Allende': {
        'state': 'Guanajuato',
        'lat': 20.9142, 'lon': -100.7436,
        'price_m2_base': 12000,
        'price_m2_std': 5000,
        'n_samples': 120
    },
    'Irapuato': {
        'state': 'Guanajuato',
        'lat': 20.6760, 'lon': -101.3520,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 150
    },
    'Celaya': {
        'state': 'Guanajuato',
        'lat': 20.5232, 'lon': -100.8131,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 130
    },
    'Salamanca': {
        'state': 'Guanajuato',
        'lat': 20.5699, 'lon': -101.1920,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 100
    },
    
    # ==================== GUERRERO ====================
    'Acapulco': {
        'state': 'Guerrero',
        'lat': 16.8606, 'lon': -99.8830,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 150
    },
    'Chilpancingo': {
        'state': 'Guerrero',
        'lat': 17.5500, 'lon': -99.4996,
        'price_m2_base': 3500,
        'price_m2_std': 1300,
        'n_samples': 100
    },
    'Taxco': {
        'state': 'Guerrero',
        'lat': 18.5573, 'lon': -99.6049,
        'price_m2_base': 6000,
        'price_m2_std': 2500,
        'n_samples': 80
    },
    'Zihuatanejo': {
        'state': 'Guerrero',
        'lat': 17.6434, 'lon': -101.5521,
        'price_m2_base': 9000,
        'price_m2_std': 3500,
        'n_samples': 100
    },
    
    # ==================== HIDALGO ====================
    'Pachuca': {
        'state': 'Hidalgo',
        'lat': 20.1120, 'lon': -98.7534,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 120
    },
    'Tulancingo': {
        'state': 'Hidalgo',
        'lat': 20.0824, 'lon': -98.3601,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 100
    },
    
    # ==================== JALISCO ====================
    'Guadalajara': {
        'state': 'Jalisco',
        'lat': 20.6597, 'lon': -103.3496,
        'price_m2_base': 8000,
        'price_m2_std': 3000,
        'n_samples': 300
    },
    'Zapopan': {
        'state': 'Jalisco',
        'lat': 20.7214, 'lon': -103.3918,
        'price_m2_base': 9000,
        'price_m2_std': 3500,
        'n_samples': 250
    },
    'Tlaquepaque': {
        'state': 'Jalisco',
        'lat': 20.6408, 'lon': -103.2931,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 180
    },
    'Tonalá': {
        'state': 'Jalisco',
        'lat': 20.6235, 'lon': -103.2329,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 150
    },
    'Tlajomulco de Zúñiga': {
        'state': 'Jalisco',
        'lat': 20.4725, 'lon': -103.4447,
        'price_m2_base': 6500,
        'price_m2_std': 2500,
        'n_samples': 130
    },
    'El Salto': {
        'state': 'Jalisco',
        'lat': 20.5233, 'lon': -103.1797,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 120
    },
    'Puerto Vallarta': {
        'state': 'Jalisco',
        'lat': 20.6534, 'lon': -105.2253,
        'price_m2_base': 15000,
        'price_m2_std': 6000,
        'n_samples': 150
    },
    'Ajijic': {
        'state': 'Jalisco',
        'lat': 20.2997, 'lon': -103.2525,
        'price_m2_base': 12000,
        'price_m2_std': 5000,
        'n_samples': 80
    },
    
    # ==================== MICHOACÁN ====================
    'Morelia': {
        'state': 'Michoacán',
        'lat': 19.7019, 'lon': -101.1848,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 150
    },
    'Uruapan': {
        'state': 'Michoacán',
        'lat': 19.4219, 'lon': -102.0607,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 120
    },
    'Zamora': {
        'state': 'Michoacán',
        'lat': 19.9850, 'lon': -102.2839,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 100
    },
    
    # ==================== MORELOS ====================
    'Cuernavaca': {
        'state': 'Morelos',
        'lat': 18.9186, 'lon': -99.2340,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 150
    },
    'Cuautla': {
        'state': 'Morelos',
        'lat': 18.8121, 'lon': -98.9548,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 100
    },
    
    # ==================== NAYARIT ====================
    'Tepic': {
        'state': 'Nayarit',
        'lat': 21.5084, 'lon': -104.8938,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 100
    },
    'Bahía de Banderas': {
        'state': 'Nayarit',
        'lat': 20.7820, 'lon': -105.2696,
        'price_m2_base': 12000,
        'price_m2_std': 5000,
        'n_samples': 120
    },
    
    # ==================== NUEVO LEÓN ====================
    'Monterrey': {
        'state': 'Nuevo León',
        'lat': 25.6866, 'lon': -100.3161,
        'price_m2_base': 10000,
        'price_m2_std': 4000,
        'n_samples': 250
    },
    'San Pedro Garza García': {
        'state': 'Nuevo León',
        'lat': 25.6614, 'lon': -100.4069,
        'price_m2_base': 20000,
        'price_m2_std': 8000,
        'n_samples': 150
    },
    'Guadalupe': {
        'state': 'Nuevo León',
        'lat': 25.6784, 'lon': -100.2564,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 180
    },
    'Apodaca': {
        'state': 'Nuevo León',
        'lat': 25.7942, 'lon': -100.1929,
        'price_m2_base': 8000,
        'price_m2_std': 3000,
        'n_samples': 150
    },
    'Santa Catarina': {
        'state': 'Nuevo León',
        'lat': 25.6812, 'lon': -100.4504,
        'price_m2_base': 9000,
        'price_m2_std': 3500,
        'n_samples': 120
    },
    'Escobedo': {
        'state': 'Nuevo León',
        'lat': 25.7910, 'lon': -100.3517,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 130
    },
    
    # ==================== OAXACA ====================
    'Oaxaca': {
        'state': 'Oaxaca',
        'lat': 17.0659, 'lon': -96.7267,
        'price_m2_base': 5000,
        'price_m2_std': 2000,
        'n_samples': 120
    },
    'Salina Cruz': {
        'state': 'Oaxaca',
        'lat': 16.1697, 'lon': -95.1961,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 80
    },
    'Puerto Escondido': {
        'state': 'Oaxaca',
        'lat': 15.8750, 'lon': -97.0738,
        'price_m2_base': 9000,
        'price_m2_std': 3500,
        'n_samples': 100
    },
    'Huatulco': {
        'state': 'Oaxaca',
        'lat': 15.7662, 'lon': -96.1169,
        'price_m2_base': 12000,
        'price_m2_std': 5000,
        'n_samples': 90
    },
    
    # ==================== PUEBLA ====================
    'Puebla': {
        'state': 'Puebla',
        'lat': 19.0414, 'lon': -98.2063,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 200
    },
    'Cholula': {
        'state': 'Puebla',
        'lat': 19.0619, 'lon': -98.3039,
        'price_m2_base': 7000,
        'price_m2_std': 2800,
        'n_samples': 120
    },
    'Tehuacán': {
        'state': 'Puebla',
        'lat': 18.4604, 'lon': -97.3925,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 100
    },
    
    # ==================== QUERÉTARO ====================
    'Querétaro': {
        'state': 'Querétaro',
        'lat': 20.5888, 'lon': -100.3899,
        'price_m2_base': 8000,
        'price_m2_std': 3000,
        'n_samples': 200
    },
    'Corregidora': {
        'state': 'Querétaro',
        'lat': 20.5294, 'lon': -100.4384,
        'price_m2_base': 7500,
        'price_m2_std': 2900,
        'n_samples': 100
    },
    'San Juan del Río': {
        'state': 'Querétaro',
        'lat': 20.3840, 'lon': -99.9958,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 120
    },
    
    # ==================== QUINTANA ROO ====================
    'Cancún': {
        'state': 'Quintana Roo',
        'lat': 21.1619, 'lon': -86.8515,
        'price_m2_base': 15000,
        'price_m2_std': 6000,
        'n_samples': 200
    },
    'Playa del Carmen': {
        'state': 'Quintana Roo',
        'lat': 20.6283, 'lon': -87.0722,
        'price_m2_base': 18000,
        'price_m2_std': 7000,
        'n_samples': 180
    },
    'Tulum': {
        'state': 'Quintana Roo',
        'lat': 20.2114, 'lon': -87.4633,
        'price_m2_base': 20000,
        'price_m2_std': 8000,
        'n_samples': 150
    },
    'Chetumal': {
        'state': 'Quintana Roo',
        'lat': 18.5149, 'lon': -88.3038,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 100
    },
    
    # ==================== SAN LUIS POTOSÍ ====================
    'San Luis Potosí': {
        'state': 'San Luis Potosí',
        'lat': 22.1565, 'lon': -100.9855,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 150
    },
    'Soledad': {
        'state': 'San Luis Potosí',
        'lat': 22.1744, 'lon': -100.9726,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 100
    },
    
    # ==================== SINALOA ====================
    'Culiacán': {
        'state': 'Sinaloa',
        'lat': 24.8047, 'lon': -107.3948,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 180
    },
    'Mazatlán': {
        'state': 'Sinaloa',
        'lat': 23.2494, 'lon': -106.4091,
        'price_m2_base': 8000,
        'price_m2_std': 3000,
        'n_samples': 150
    },
    'Los Mochis': {
        'state': 'Sinaloa',
        'lat': 25.7921, 'lon': -108.9925,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 120
    },
    
    # ==================== SONORA ====================
    'Hermosillo': {
        'state': 'Sonora',
        'lat': 29.0892, 'lon': -110.9613,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 150
    },
    'Ciudad Obregón': {
        'state': 'Sonora',
        'lat': 27.4951, 'lon': -109.9338,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 120
    },
    'Navojoa': {
        'state': 'Sonora',
        'lat': 27.0810, 'lon': -109.4450,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 100
    },
    'Nogales': {
        'state': 'Sonora',
        'lat': 31.3069, 'lon': -110.9429,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 100
    },
    'Puerto Peñasco': {
        'state': 'Sonora',
        'lat': 31.3139, 'lon': -113.5375,
        'price_m2_base': 10000,
        'price_m2_std': 4000,
        'n_samples': 80
    },
    
    # ==================== TABASCO ====================
    'Villahermosa': {
        'state': 'Tabasco',
        'lat': 17.9892, 'lon': -92.9478,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 150
    },
    'Cárdenas': {
        'state': 'Tabasco',
        'lat': 18.0014, 'lon': -93.3756,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 100
    },
    
    # ==================== TAMAULIPAS ====================
    'Tampico': {
        'state': 'Tamaulipas',
        'lat': 22.2331, 'lon': -97.8611,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 150
    },
    'Reynosa': {
        'state': 'Tamaulipas',
        'lat': 26.0791, 'lon': -98.2978,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 150
    },
    'Matamoros': {
        'state': 'Tamaulipas',
        'lat': 25.8689, 'lon': -97.5067,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 120
    },
    'Ciudad Victoria': {
        'state': 'Tamaulipas',
        'lat': 23.7417, 'lon': -99.1461,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 100
    },
    
    # ==================== TLAXCALA ====================
    'Tlaxcala': {
        'state': 'Tlaxcala',
        'lat': 19.3183, 'lon': -98.2377,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 100
    },
    'Apizaco': {
        'state': 'Tlaxcala',
        'lat': 19.4134, 'lon': -98.1437,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 80
    },
    
    # ==================== VERACRUZ ====================
    'Veracruz': {
        'state': 'Veracruz',
        'lat': 19.1738, 'lon': -96.1342,
        'price_m2_base': 6000,
        'price_m2_std': 2300,
        'n_samples': 180
    },
    'Xalapa': {
        'state': 'Veracruz',
        'lat': 19.5417, 'lon': -96.9244,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 150
    },
    'Coatzacoalcos': {
        'state': 'Veracruz',
        'lat': 18.1410, 'lon': -94.4159,
        'price_m2_base': 5000,
        'price_m2_std': 1900,
        'n_samples': 120
    },
    'Córdoba': {
        'state': 'Veracruz',
        'lat': 18.8873, 'lon': -96.9301,
        'price_m2_base': 5500,
        'price_m2_std': 2100,
        'n_samples': 100
    },
    'Poza Rica': {
        'state': 'Veracruz',
        'lat': 20.5368, 'lon': -97.4584,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 100
    },
    
    # ==================== YUCATÁN ====================
    'Mérida': {
        'state': 'Yucatán',
        'lat': 20.9674, 'lon': -89.5926,
        'price_m2_base': 7000,
        'price_m2_std': 2700,
        'n_samples': 180
    },
    'Progreso': {
        'state': 'Yucatán',
        'lat': 21.2819, 'lon': -89.6612,
        'price_m2_base': 8000,
        'price_m2_std': 3000,
        'n_samples': 100
    },
    'Valladolid': {
        'state': 'Yucatán',
        'lat': 20.6882, 'lon': -88.2014,
        'price_m2_base': 5000,
        'price_m2_std': 2000,
        'n_samples': 80
    },
    
    # ==================== ZACATECAS ====================
    'Zacatecas': {
        'state': 'Zacatecas',
        'lat': 22.7709, 'lon': -102.5832,
        'price_m2_base': 4500,
        'price_m2_std': 1700,
        'n_samples': 120
    },
    'Fresnillo': {
        'state': 'Zacatecas',
        'lat': 23.1750, 'lon': -102.8719,
        'price_m2_base': 4000,
        'price_m2_std': 1500,
        'n_samples': 100
    },
}

# Nombres de colonias/zonas típicas
COLONIAS = [
    'Centro', 'Residencial', 'Industrial', 'Campestre', 'Del Valle',
    'Las Águilas', 'Santa Fe', 'Colinas', 'Arboledas', 'Puerta de Hierro',
    'Providencia', 'Americana', 'Chapultepec', 'Country Club', 'Jardines',
    'Lomas', 'Bosques', 'Andares', 'Vista Hermosa', 'El Mirador'
]


def generate_property_data(city: str, config: dict, index: int) -> dict:
    """
    Genera datos realistas para una propiedad individual
    """
    # Precio/m² con distribución normal y algunos outliers
    if random.random() < 0.05:  # 5% outliers
        price_m2 = config['price_m2_base'] * random.uniform(0.4, 2.5)
    else:
        price_m2 = np.random.normal(config['price_m2_base'], config['price_m2_std'])
        price_m2 = max(price_m2, 1000)  # Precio mínimo
    
    # Área del terreno (distribución log-normal)
    area_m2 = np.random.lognormal(mean=np.log(400), sigma=0.7)
    area_m2 = max(50, min(area_m2, 10000))  # Entre 50 y 10,000 m²
    
    # Precio total
    price_mxn = price_m2 * area_m2
    
    # Coordenadas con algo de variación
    lat = config['lat'] + np.random.normal(0, 0.05)
    lon = config['lon'] + np.random.normal(0, 0.05)
    
    # Fecha de recolección (últimos 6 meses)
    days_ago = random.randint(0, 180)
    collection_date = datetime.now() - timedelta(days=days_ago)
    
    # Generar dirección
    colonia = random.choice(COLONIAS)
    calle = random.choice(['Av.', 'Calle', 'Boulevard', 'Privada'])
    numero = random.randint(100, 9999)
    
    property_data = {
        'title': f"Terreno en {colonia}, {city}",
        'price_mxn': round(price_mxn, 2),
        'area_m2': round(area_m2, 2),
        'price_m2': round(price_m2, 2),
        'address': f"{calle} {numero}, {colonia}",
        'city': city,
        'state': config['state'],
        'lat': round(lat, 6),
        'lon': round(lon, 6),
        'collection_date': collection_date.date().isoformat(),
        'source': 'synthetic_data_v1',
        'source_url': f"https://example.com/property/{city.lower().replace(' ', '-')}/{index}"
    }
    
    return property_data


def generate_dataset():
    """
    Genera dataset completo de propiedades sintéticas
    """
    logger.info("🏗️  Generando dataset sintético de entrenamiento...")
    logger.info(f"   Ciudades: {len(CIUDADES_CONFIG)}")
    
    all_properties = []
    
    for city, config in CIUDADES_CONFIG.items():
        logger.info(f"   📍 Generando {config['n_samples']} propiedades para {city}...")
        
        for i in range(config['n_samples']):
            property_data = generate_property_data(city, config, i)
            all_properties.append(property_data)
    
    df = pd.DataFrame(all_properties)
    
    logger.success(f"✅ Dataset generado: {len(df)} propiedades")
    logger.info(f"   💰 Precio promedio: ${df['price_mxn'].mean():,.0f} MXN")
    logger.info(f"   📏 Área promedio: {df['area_m2'].mean():,.0f} m²")
    logger.info(f"   💵 Precio/m² promedio: ${df['price_m2'].mean():,.0f} MXN/m²")
    
    return df


def save_to_supabase(df: pd.DataFrame):
    """
    Guarda datos en Supabase
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
                # Insertar lote
                response = supabase.table(TABLE_COMPARABLES).insert(batch).execute()
                saved_count += len(batch)
                if (i // batch_size + 1) % 10 == 0:
                    logger.info(f"   ✓ Guardados {saved_count}/{len(records)} registros")
                
            except Exception as e:  # Supabase client may raise various errors
                error_count += len(batch)
                logger.warning(f"   ⚠ Error guardando lote {i//batch_size + 1}: {str(e)[:100]}")

        logger.success(f"✅ Guardados {saved_count} registros en Supabase (errores: {error_count})")
        return saved_count

    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"❌ Error conectando a Supabase: {e}")
        return 0


def save_to_csv(df: pd.DataFrame):
    """
    Guarda datos en CSV
    """
    try:
        from config import DATA_DIR
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = DATA_DIR / f"synthetic_training_data_{timestamp}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.success(f"💾 Datos guardados en CSV: {filename}")
        
        return str(filename)
        
    except (FileNotFoundError, IOError, OSError) as e:
        logger.error(f"❌ Error guardando CSV: {e}")
        return None


def main():
    """
    Función principal
    """
    logger.info("="*70)
    logger.info("🎯 GENERADOR DE DATOS SINTÉTICOS PARA ENTRENAMIENTO ML")
    logger.info("="*70 + "\n")
    
    # Generar dataset
    df = generate_dataset()
    
    # Estadísticas por ciudad
    logger.info("\n📊 Distribución por ciudad (Top 10):")
    city_counts = df['city'].value_counts().head(10)
    for city, count in city_counts.items():
        logger.info(f"   • {city}: {count} propiedades")
    
    # Guardar en CSV
    csv_file = save_to_csv(df)
    
    # Guardar en Supabase
    saved_count = save_to_supabase(df)
    
    logger.info("\n" + "="*70)
    logger.success("✅ PROCESO COMPLETADO")
    logger.info("="*70)
    logger.info(f"   • Total propiedades generadas: {len(df)}")
    logger.info(f"   • Guardadas en Supabase: {saved_count}")
    if csv_file:
        logger.info(f"   • Archivo CSV: {csv_file}")
    logger.info("="*70)
    
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
    df = main()
    
    logger.info("\n💡 Ahora puedes entrenar el modelo con:")
    logger.info("   python ml_model/predictor.py")

