#!/usr/bin/env python3
"""
Massive expansion of Mexico cities catalog.
Target: 500-600 cities covering all 32 states thoroughly.
Adds municipalities >50k pop, tourist towns, border towns, coastal towns, interior gap-fillers.
"""

import json
import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "python_services", "data", "cities_mexico_32_states.json"
)

# ──────────────────────────────────────────────────────────────────
# NEW CITIES TO ADD PER STATE
# Format: (name, lat, lon, population, is_capital)
# Coordinates verified against INEGI / known references
# ──────────────────────────────────────────────────────────────────

NEW_CITIES = {
    "Aguascalientes": [
        ("San Francisco de los Romo", 22.07, -102.27, 55000, False),
        ("Tepezalá", 22.22, -102.17, 20000, False),
        ("Asientos", 22.24, -102.08, 25000, False),
        ("El Llano", 21.92, -101.97, 12000, False),
        ("Cosío", 22.37, -102.30, 15000, False),
        ("San José de Gracia", 22.15, -102.42, 9000, False),
    ],
    "Baja California": [
        ("Vicente Guerrero", 30.73, -115.99, 12000, False),
        ("Guadalupe Victoria", 32.29, -115.10, 10000, False),
        ("Ejido Nuevo León", 32.40, -115.20, 8000, False),
    ],
    "Baja California Sur": [
        ("Mulegé", 26.88, -111.98, 4500, False),
        ("Todos Santos", 23.45, -110.22, 6000, False),
        ("El Triunfo", 23.55, -110.10, 1500, False),
        ("San Bartolo", 23.74, -109.98, 2000, False),
        ("Villa Alberto Alvarado Arámburo", 24.83, -111.58, 3000, False),
        ("Vizcaíno", 27.16, -112.97, 4000, False),
        ("Bahía Tortugas", 27.69, -114.90, 3500, False),
        ("San Ignacio", 27.29, -112.90, 2500, False),
    ],
    "Campeche": [
        ("Candelaria", 18.19, -91.04, 25000, False),
        ("Hopelchén", 19.74, -89.84, 20000, False),
        ("Seybaplaya", 19.65, -90.70, 8000, False),
        ("Hecelchakán", 20.17, -90.13, 15000, False),
        ("Palizada", 18.25, -91.43, 8000, False),
        ("Tenabo", 20.04, -90.22, 6000, False),
        ("Xpujil", 18.53, -89.42, 5000, False),
    ],
    "Chiapas": [
        ("Pichucalco", 17.51, -93.12, 30000, False),
        ("Cintalapa", 16.69, -93.72, 45000, False),
        ("Reforma", 17.86, -93.15, 25000, False),
        ("Las Margaritas", 16.31, -91.98, 20000, False),
        ("Arriaga", 16.24, -93.90, 35000, False),
        ("Motozintla", 15.37, -92.25, 20000, False),
        ("Mapastepec", 15.44, -92.90, 18000, False),
        ("Berriozábal", 16.80, -93.27, 30000, False),
        ("Venustiano Carranza", 16.33, -92.57, 15000, False),
        ("Chiapa de Corzo", 16.71, -93.01, 50000, False),
        ("Jiquipilas", 16.67, -93.57, 12000, False),
        ("Yajalón", 17.17, -92.33, 12000, False),
        ("Simojovel", 17.14, -92.72, 10000, False),
        ("Suchiapa", 16.62, -93.10, 15000, False),
    ],
    "Chihuahua": [
        ("Jiménez", 27.13, -104.93, 40000, False),
        ("Madera", 29.19, -108.15, 15000, False),
        ("Creel", 27.75, -107.63, 6000, False),
        ("Guachochi", 26.82, -107.07, 15000, False),
        ("Bocoyna", 27.84, -107.60, 8000, False),
        ("Meoqui", 28.27, -105.48, 25000, False),
        ("Saucillo", 28.03, -105.28, 20000, False),
        ("Guerrero", 28.97, -107.48, 8000, False),
        ("Aldama", 28.84, -105.92, 10000, False),
        ("Rosales", 28.03, -105.57, 8000, False),
        ("Casas Grandes", 30.37, -107.95, 7000, False),
        ("Buenaventura", 29.84, -107.47, 6000, False),
        ("Namiquipa", 29.25, -107.42, 7000, False),
        ("Santa Bárbara", 26.80, -105.82, 12000, False),
    ],
    "Ciudad de México": [
        ("Azcapotzalco", 19.49, -99.18, 400000, False),
        ("Gustavo A. Madero", 19.48, -99.11, 1185000, False),
        ("Venustiano Carranza", 19.43, -99.10, 427000, False),
        ("Álvaro Obregón", 19.36, -99.20, 749000, False),
        ("Miguel Hidalgo", 19.43, -99.19, 414000, False),
        ("Milpa Alta", 19.19, -99.02, 152000, False),
        ("Tláhuac", 19.29, -99.00, 392000, False),
        ("Magdalena Contreras", 19.33, -99.24, 247000, False),
    ],
    "Coahuila": [
        ("Nueva Rosita", 27.94, -101.22, 50000, False),
        ("Allende", 28.35, -100.87, 25000, False),
        ("Francisco I. Madero", 25.77, -103.27, 50000, False),
        ("Frontera", 26.93, -101.45, 75000, False),
        ("Castaños", 26.79, -101.42, 25000, False),
        ("Ramos Arizpe", 25.54, -100.95, 100000, False),
        ("Zaragoza", 28.48, -100.92, 12000, False),
        ("Nava", 28.42, -100.77, 30000, False),
        ("Jiménez", 29.07, -100.70, 10000, False),
        ("San Buenaventura", 27.06, -101.54, 22000, False),
    ],
    "Colima": [
        ("Villa de Álvarez", 19.27, -103.74, 140000, False),
        ("Armería", 18.93, -103.96, 30000, False),
        ("Coquimatlán", 19.20, -103.81, 20000, False),
        ("Cuauhtémoc", 19.33, -103.60, 28000, False),
        ("Ixtlahuacán", 19.00, -103.73, 6000, False),
        ("Minatitlán", 19.39, -104.05, 8000, False),
    ],
    "Durango": [
        ("El Salto", 23.78, -105.36, 20000, False),
        ("Nombre de Dios", 23.85, -104.25, 18000, False),
        ("Vicente Guerrero", 23.73, -103.99, 30000, False),
        ("Pueblo Nuevo", 23.38, -105.37, 10000, False),
        ("Nuevo Ideal", 24.89, -105.07, 12000, False),
        ("Guadalupe Victoria", 24.45, -104.11, 15000, False),
        ("Peñón Blanco", 24.77, -103.97, 8000, False),
        ("Cuencamé", 24.87, -103.70, 10000, False),
        ("Mapimí", 25.84, -103.85, 12000, False),
        ("Nazas", 25.23, -104.11, 8000, False),
        ("San Juan del Río", 24.78, -104.48, 7000, False),
        ("Tamazula", 24.97, -106.96, 5000, False),
    ],
    "Estado de México": [
        ("Zinacantepec", 19.28, -99.73, 190000, False),
        ("Almoloya de Juárez", 19.38, -99.75, 180000, False),
        ("Tecámac", 19.71, -98.97, 500000, False),
        ("Nicolás Romero", 19.59, -99.31, 420000, False),
        ("Chimalhuacán", 19.43, -98.95, 680000, False),
        ("La Paz", 19.36, -98.94, 300000, False),
        ("Tultitlán", 19.65, -99.17, 560000, False),
        ("Coacalco", 19.63, -99.11, 300000, False),
        ("Zumpango", 19.80, -99.10, 250000, False),
        ("Tenancingo", 18.96, -99.59, 100000, False),
        ("Temascaltepec", 19.04, -100.04, 35000, False),
        ("Atlacomulco", 19.80, -99.87, 95000, False),
        ("El Oro", 19.80, -100.13, 35000, False),
        ("Teotihuacán", 19.69, -98.86, 55000, False),
        ("Otumba", 19.70, -98.76, 35000, False),
        ("Amecameca", 19.12, -98.76, 52000, False),
    ],
    "Guanajuato": [
        ("Pénjamo", 20.43, -101.72, 75000, False),
        ("Acámbaro", 20.03, -100.72, 65000, False),
        ("San Felipe", 21.48, -101.22, 50000, False),
        ("Juventino Rosas", 20.65, -101.00, 60000, False),
        ("Cortazar", 20.48, -100.95, 55000, False),
        ("Salvatierra", 20.21, -100.88, 50000, False),
        ("Romita", 20.87, -101.52, 35000, False),
        ("Manuel Doblado", 20.73, -101.95, 25000, False),
        ("San Luis de la Paz", 21.30, -100.52, 55000, False),
        ("San José Iturbide", 21.00, -100.38, 40000, False),
        ("Purísima del Rincón", 21.04, -101.88, 60000, False),
        ("Jaral del Progreso", 20.37, -101.07, 25000, False),
        ("Yuriria", 20.20, -101.13, 30000, False),
        ("Comonfort", 20.72, -100.76, 35000, False),
        ("Abasolo", 20.45, -101.53, 42000, False),
    ],
    "Guerrero": [
        ("Ometepec", 16.69, -98.41, 40000, False),
        ("Coyuca de Benítez", 17.00, -100.09, 18000, False),
        ("Petatlán", 17.54, -101.27, 20000, False),
        ("Tlapa de Comonfort", 17.55, -98.58, 60000, False),
        ("Ayutla de los Libres", 16.96, -99.10, 15000, False),
        ("Arcelia", 18.32, -100.28, 15000, False),
        ("Coyuca de Catalán", 18.32, -100.70, 10000, False),
        ("Ciudad Altamirano", 18.36, -100.67, 30000, False),
        ("Atoyac de Álvarez", 17.21, -100.43, 25000, False),
        ("Tecpan de Galeana", 17.25, -100.63, 15000, False),
        ("San Marcos", 16.78, -99.38, 12000, False),
        ("Huitzuco", 18.31, -99.34, 10000, False),
        ("Teloloapan", 18.37, -99.88, 20000, False),
        ("Cruz Grande", 16.73, -99.13, 8000, False),
        ("Copala", 16.60, -98.99, 6000, False),
    ],
    "Hidalgo": [
        ("Tepeji del Río", 19.90, -99.34, 80000, False),
        ("Mixquiahuala", 20.23, -99.21, 45000, False),
        ("Apan", 19.71, -98.45, 45000, False),
        ("Atotonilco el Grande", 20.28, -98.67, 25000, False),
        ("Actopan", 20.27, -98.94, 55000, False),
        ("Tepeapulco", 19.79, -98.55, 50000, False),
        ("Progreso de Obregón", 20.25, -99.19, 25000, False),
        ("Santiago Tulantepec", 20.04, -98.36, 40000, False),
        ("Mineral de la Reforma", 20.07, -98.69, 190000, False),
        ("Ciudad Sahagún", 19.79, -98.58, 35000, False),
        ("Metztitlán", 20.60, -98.76, 10000, False),
        ("Molango", 20.79, -98.73, 8000, False),
        ("Jacala", 21.01, -99.19, 7000, False),
    ],
    "Jalisco": [
        ("Ocotlán", 20.35, -102.77, 95000, False),
        ("Arandas", 20.70, -102.35, 55000, False),
        ("La Barca", 20.29, -102.55, 40000, False),
        ("Zapotlán el Grande (Ciudad Guzmán)", 19.70, -103.46, 105000, False),
        ("Atotonilco el Alto", 20.55, -102.52, 30000, False),
        ("Tala", 20.65, -103.70, 50000, False),
        ("Ameca", 20.55, -104.05, 35000, False),
        ("Sayula", 19.88, -103.60, 25000, False),
        ("Zapotiltic", 19.63, -103.42, 22000, False),
        ("Tequila", 20.88, -103.83, 30000, False),
        ("Tamazula de Gordiano", 19.67, -103.25, 30000, False),
        ("Colotlán", 22.11, -103.27, 12000, False),
        ("Tomatlán", 19.93, -105.25, 10000, False),
        ("Cihuatlán", 19.24, -104.57, 22000, False),
        ("Mascota", 20.53, -104.79, 10000, False),
        ("Talpa de Allende", 20.38, -104.82, 8000, False),
        ("San Juan de los Lagos", 21.25, -102.33, 55000, False),
        ("Encarnación de Díaz", 21.52, -102.23, 25000, False),
        ("Yahualica", 21.18, -102.88, 12000, False),
        ("Jocotepec", 20.28, -103.43, 25000, False),
        ("Chapala", 20.30, -103.19, 25000, False),
        ("Ajijic", 20.30, -103.26, 15000, False),
    ],
    "Michoacán": [
        ("Los Reyes", 19.59, -102.47, 35000, False),
        ("Zacapu", 19.82, -101.79, 50000, False),
        ("Coalcomán", 18.78, -103.16, 12000, False),
        ("Huetamo", 18.63, -100.90, 20000, False),
        ("Maravatío", 19.89, -100.44, 35000, False),
        ("Jiquilpan", 19.99, -102.72, 25000, False),
        ("Tacámbaro", 19.24, -101.46, 20000, False),
        ("Puruándiro", 20.09, -101.51, 30000, False),
        ("Hidalgo (Ciudad Hidalgo)", 19.69, -100.55, 75000, False),
        ("Nueva Italia", 19.00, -102.12, 25000, False),
        ("Paracho", 19.65, -102.05, 15000, False),
        ("Cotija", 19.81, -102.70, 12000, False),
        ("Jacona", 19.96, -102.30, 55000, False),
        ("Tlalpujahua", 19.80, -100.17, 8000, False),
        ("Tanhuato", 20.28, -102.55, 8000, False),
        ("Villamar", 20.00, -102.60, 7000, False),
    ],
    "Morelos": [
        ("Zacatepec", 18.66, -99.19, 30000, False),
        ("Puente de Ixtla", 18.62, -99.33, 28000, False),
        ("Axochiapan", 18.50, -98.75, 20000, False),
        ("Emiliano Zapata", 18.83, -99.17, 60000, False),
        ("Xoxocotla", 18.62, -99.24, 15000, False),
        ("Tepoztlán", 18.98, -99.10, 15000, False),
        ("Tlaltizapán", 18.68, -99.12, 15000, False),
        ("Tlaquiltenango", 18.63, -99.16, 20000, False),
    ],
    "Nayarit": [
        ("Tuxpan", 21.93, -105.27, 15000, False),
        ("Ruiz", 21.95, -105.17, 12000, False),
        ("Tecuala", 22.40, -105.48, 18000, False),
        ("Las Varas", 21.17, -105.17, 10000, False),
        ("Ixtlán del Río", 21.04, -104.37, 20000, False),
        ("Ahuacatlán", 21.06, -104.50, 15000, False),
        ("Jala", 21.05, -104.43, 10000, False),
        ("San Blas", 21.54, -105.28, 10000, False),
        ("Santa María del Oro", 21.33, -104.58, 8000, False),
        ("Rosamorada", 22.12, -105.22, 8000, False),
    ],
    "Nuevo León": [
        ("Cadereyta Jiménez", 25.59, -99.98, 95000, False),
        ("Santiago", 25.43, -100.15, 45000, False),
        ("Allende", 25.28, -100.02, 35000, False),
        ("Cerralvo", 26.08, -99.62, 8000, False),
        ("Dr. Arroyo", 23.67, -100.18, 25000, False),
        ("Galeana", 24.83, -100.07, 20000, False),
        ("China", 25.70, -99.23, 10000, False),
        ("General Terán", 25.26, -99.68, 8000, False),
        ("Anáhuac", 27.24, -100.13, 20000, False),
        ("General Zuazua", 25.88, -100.10, 60000, False),
        ("Ciénega de Flores", 25.95, -100.17, 40000, False),
        ("Pesquería", 25.78, -100.05, 90000, False),
    ],
    "Oaxaca": [
        ("Tehuantepec", 16.33, -95.24, 50000, False),
        ("Ixtlán de Juárez", 17.33, -96.48, 8000, False),
        ("Pochutla", 15.74, -96.47, 25000, False),
        ("Puerto Escondido", 15.86, -97.07, 35000, False),
        ("Matías Romero", 16.88, -95.04, 25000, False),
        ("Loma Bonita", 18.10, -95.88, 30000, False),
        ("Puerto Ángel", 15.67, -96.50, 5000, False),
        ("Miahuatlán", 16.33, -96.59, 25000, False),
        ("Huajuapan de León", 17.81, -97.77, 55000, False),
        ("Tlaxiaco", 17.27, -97.68, 20000, False),
        ("Ocotlán de Morelos", 16.79, -96.67, 18000, False),
        ("Tlacolula de Matamoros", 16.95, -96.48, 15000, False),
        ("Zimatlán de Álvarez", 16.87, -96.78, 10000, False),
        ("Etla", 17.21, -96.80, 8000, False),
        ("Putla Villa de Guerrero", 17.03, -97.93, 12000, False),
        ("Jamiltepec", 16.28, -97.82, 10000, False),
        ("Nochixtlán", 17.46, -97.22, 12000, False),
        ("Teotitlán de Flores Magón", 18.13, -97.08, 8000, False),
        ("Mazunte", 15.67, -96.55, 2000, False),
        ("Zipolite", 15.67, -96.52, 1500, False),
    ],
    "Puebla": [
        ("Acatzingo", 18.97, -97.78, 30000, False),
        ("Ajalpan", 18.38, -97.13, 30000, False),
        ("Libres", 19.47, -97.68, 15000, False),
        ("Acatlán de Osorio", 18.21, -98.05, 20000, False),
        ("Chignahuapan", 19.84, -97.96, 25000, False),
        ("Zacatlán", 19.93, -97.96, 30000, False),
        ("Tecamachalco", 18.88, -97.73, 35000, False),
        ("Xicotepec", 20.28, -97.96, 30000, False),
        ("Huejotzingo", 19.16, -98.41, 60000, False),
        ("Amozoc", 19.04, -98.05, 100000, False),
        ("Oriental", 19.34, -97.63, 12000, False),
        ("Cuetzalan", 20.03, -97.52, 10000, False),
        ("Tetela de Ocampo", 19.82, -97.80, 8000, False),
    ],
    "Querétaro": [
        ("Pedro Escobedo", 20.50, -100.14, 55000, False),
        ("Amealco", 20.19, -100.14, 35000, False),
        ("Ezequiel Montes", 20.67, -99.90, 25000, False),
        ("Colón", 20.78, -100.05, 20000, False),
        ("Huimilpan", 20.37, -100.28, 15000, False),
        ("Pinal de Amoles", 21.13, -99.63, 8000, False),
        ("Tolimán", 20.92, -99.95, 15000, False),
    ],
    "Quintana Roo": [
        ("Isla Mujeres", 21.23, -86.73, 20000, False),
        ("Lázaro Cárdenas", 20.65, -87.38, 15000, False),
        ("José María Morelos", 19.75, -88.71, 12000, False),
        ("Kantunilkín", 21.10, -87.48, 8000, False),
        ("Holbox", 21.52, -87.38, 3000, False),
        ("Puerto Morelos", 20.85, -86.88, 15000, False),
        ("Mahahual", 18.71, -87.71, 2000, False),
    ],
    "San Luis Potosí": [
        ("Charcas", 23.13, -101.11, 15000, False),
        ("Cerritos", 22.43, -100.28, 15000, False),
        ("Cárdenas", 21.99, -99.65, 15000, False),
        ("Ébano", 22.23, -98.38, 20000, False),
        ("Ciudad del Maíz", 22.40, -99.62, 10000, False),
        ("Salinas de Hidalgo", 22.63, -101.71, 12000, False),
        ("Mexquitic", 22.27, -101.12, 8000, False),
        ("Guadalcázar", 22.62, -100.40, 6000, False),
        ("Tancanhuitz", 21.59, -98.97, 12000, False),
        ("Aquismón", 21.62, -99.02, 10000, False),
        ("Xilitla", 21.39, -98.99, 15000, False),
        ("Axtla de Terrazas", 21.43, -98.87, 10000, False),
        ("Venado", 22.92, -101.08, 8000, False),
        ("Villa de Reyes", 21.81, -100.93, 15000, False),
    ],
    "Sinaloa": [
        ("El Rosario", 22.99, -105.86, 20000, False),
        ("Concordia", 23.28, -105.97, 12000, False),
        ("Mocorito", 25.48, -107.92, 10000, False),
        ("Cosalá", 24.41, -106.69, 6000, False),
        ("Angostura", 25.37, -108.15, 18000, False),
        ("Salvador Alvarado (Guamúchil)", 25.46, -108.08, 70000, False),
        ("El Fuerte", 26.42, -108.62, 15000, False),
        ("Choix", 26.71, -108.33, 8000, False),
        ("Sinaloa de Leyva", 25.83, -108.22, 8000, False),
        ("Badiraguato", 25.37, -107.55, 5000, False),
    ],
    "Sonora": [
        ("Cananea", 30.97, -110.30, 35000, False),
        ("Magdalena de Kino", 30.63, -110.97, 30000, False),
        ("Álamos", 27.02, -108.94, 10000, False),
        ("Huatabampo", 26.83, -109.64, 35000, False),
        ("Etchojoa", 26.91, -109.64, 15000, False),
        ("Benito Juárez", 31.60, -109.75, 6000, False),
        ("Santa Ana", 30.54, -111.12, 15000, False),
        ("Moctezuma", 29.80, -109.68, 6000, False),
        ("Ures", 29.43, -110.40, 5000, False),
        ("Altar", 30.73, -111.84, 5000, False),
        ("Sonoyta", 31.86, -112.85, 8000, False),
        ("Bahía de Kino", 28.83, -111.94, 5000, False),
        ("San Carlos Nuevo Guaymas", 27.95, -111.06, 8000, False),
        ("Sahuaripa", 29.05, -109.24, 3000, False),
    ],
    "Tabasco": [
        ("Emiliano Zapata", 17.73, -91.77, 30000, False),
        ("Balancán", 17.81, -91.53, 20000, False),
        ("Jalpa de Méndez", 18.17, -93.06, 30000, False),
        ("Centro (Nacajuca)", 18.17, -93.02, 35000, False),
        ("Cunduacán", 18.07, -93.18, 30000, False),
        ("Jonuta", 18.09, -92.14, 10000, False),
        ("Tacotalpa", 17.60, -92.82, 15000, False),
        ("Jalapa", 17.67, -92.82, 20000, False),
        ("Centla", 18.35, -92.58, 15000, False),
    ],
    "Tamaulipas": [
        ("Soto la Marina", 23.77, -98.21, 12000, False),
        ("Jiménez", 24.33, -99.43, 8000, False),
        ("Padilla", 24.05, -99.15, 7000, False),
        ("Tula", 23.00, -99.73, 25000, False),
        ("González", 22.83, -98.43, 15000, False),
        ("Antiguo Morelos", 22.55, -99.09, 8000, False),
        ("Llera", 23.32, -99.02, 6000, False),
        ("Jaumave", 23.42, -99.38, 6000, False),
        ("Abasolo", 24.06, -98.38, 5000, False),
        ("Xicoténcatl", 22.98, -98.95, 10000, False),
        ("Ocampo", 22.85, -99.33, 6000, False),
        ("Aldama", 22.92, -98.07, 18000, False),
        ("Güémez", 23.92, -99.10, 7000, False),
        ("Casas", 23.12, -98.75, 5000, False),
    ],
    "Tlaxcala": [
        ("Tlaxco", 19.62, -98.13, 15000, False),
        ("Ixtacuixtla", 19.35, -98.37, 15000, False),
        ("Panotla", 19.32, -98.27, 10000, False),
        ("Tetla de la Solidaridad", 19.43, -98.07, 20000, False),
        ("Nativitas", 19.22, -98.32, 15000, False),
        ("Contla de Juan Cuamatzi", 19.33, -98.17, 30000, False),
        ("Santa Cruz Tlaxcala", 19.35, -98.23, 12000, False),
        ("Yauhquemehcan", 19.42, -98.10, 15000, False),
        ("Teolocholco", 19.25, -98.18, 12000, False),
    ],
    "Veracruz": [
        ("Perote", 19.56, -97.24, 30000, False),
        ("Catemaco", 18.42, -95.12, 25000, False),
        ("Huatusco", 19.15, -96.97, 22000, False),
        ("Martínez de la Torre", 20.07, -97.06, 55000, False),
        ("Las Choapas", 17.90, -94.10, 40000, False),
        ("Agua Dulce", 17.98, -94.14, 20000, False),
        ("Nanchital", 18.07, -94.41, 25000, False),
        ("Cosamaloapan", 18.37, -95.80, 30000, False),
        ("Tlacotalpan", 18.61, -95.66, 8000, False),
        ("Alvarado", 18.77, -95.76, 35000, False),
        ("Tantoyuca", 21.35, -98.23, 20000, False),
        ("Chicontepec", 20.97, -98.17, 12000, False),
        ("Tempoal", 21.52, -98.39, 10000, False),
        ("Álamo Temapache", 20.92, -97.68, 20000, False),
        ("Gutiérrez Zamora", 20.45, -97.08, 12000, False),
        ("Misantla", 19.93, -96.85, 25000, False),
        ("José Cardel", 19.37, -96.38, 18000, False),
        ("Fortín de las Flores", 18.90, -97.00, 35000, False),
        ("Ixhuatlán de Madero", 20.68, -98.02, 8000, False),
        ("Nautla", 20.22, -96.78, 6000, False),
        ("Jáltipan", 17.97, -94.72, 25000, False),
        ("Cosoleacaque", 18.00, -94.62, 30000, False),
        ("Isla", 18.03, -95.53, 20000, False),
        ("Playa Vicente", 17.83, -95.82, 15000, False),
        ("Tres Valles", 18.23, -96.13, 15000, False),
    ],
    "Yucatán": [
        ("Oxkutzcab", 20.30, -89.42, 18000, False),
        ("Espita", 20.86, -88.31, 12000, False),
        ("Maxcanú", 20.58, -90.00, 10000, False),
        ("Peto", 20.13, -89.09, 12000, False),
        ("Hunucmá", 21.02, -89.87, 18000, False),
        ("Umán", 20.88, -89.75, 40000, False),
        ("Halachó", 20.48, -90.08, 10000, False),
        ("Sotuta", 20.60, -89.00, 5000, False),
        ("Celestún", 20.86, -90.40, 6000, False),
        ("Tinum (Pisté)", 20.68, -88.58, 5000, False),
        ("Dzilam de Bravo", 21.39, -88.90, 4000, False),
        ("Sisal", 21.16, -90.03, 2000, False),
        ("Tixkokob", 21.00, -89.39, 12000, False),
        ("Acanceh", 20.81, -89.45, 10000, False),
        ("Muna", 20.49, -89.72, 8000, False),
    ],
    "Zacatecas": [
        ("Valparaíso", 22.77, -103.57, 15000, False),
        ("Villanueva", 22.35, -102.88, 18000, False),
        ("Ojocaliente", 22.41, -102.27, 12000, False),
        ("Tlaltenango", 21.78, -103.30, 15000, False),
        ("Loreto", 22.27, -101.98, 20000, False),
        ("Calera", 22.90, -102.65, 30000, False),
        ("Pinos", 22.28, -101.58, 10000, False),
        ("Miguel Auza", 24.20, -103.72, 8000, False),
        ("Juan Aldama", 24.29, -103.38, 10000, False),
        ("Teúl de González Ortega", 21.45, -103.45, 5000, False),
        ("Concepción del Oro", 24.62, -101.40, 8000, False),
        ("Mazapil", 24.63, -101.56, 3000, False),
        ("Tepechitlán", 21.63, -103.32, 4000, False),
        ("Juchipila", 21.40, -103.12, 8000, False),
        ("Tabasco (Zac)", 21.63, -103.13, 5000, False),
        ("García de la Cadena", 21.60, -103.47, 3000, False),
        ("Chalchihuites", 23.24, -103.94, 5000, False),
        ("General Pánfilo Natera", 22.60, -102.10, 6000, False),
        ("Villa de Cos", 23.30, -102.35, 7000, False),
    ],
}


def main():
    # Read existing data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build lookup: state name -> index
    state_index = {}
    for i, state in enumerate(data["states"]):
        state_index[state["name"]] = i

    # Track counts
    before_counts = {}
    after_counts = {}

    for state in data["states"]:
        before_counts[state["name"]] = len(state["cities"])

    # Add new cities, avoiding duplicates
    total_added = 0
    for state_name, new_cities in NEW_CITIES.items():
        if state_name not in state_index:
            print(f"WARNING: State '{state_name}' not found in data!")
            continue

        idx = state_index[state_name]
        existing_names = {c["name"].lower().strip() for c in data["states"][idx]["cities"]}

        added = 0
        for (name, lat, lon, pop, is_cap) in new_cities:
            if name.lower().strip() in existing_names:
                continue
            data["states"][idx]["cities"].append({
                "name": name,
                "lat": lat,
                "lon": lon,
                "population": pop,
                "is_capital": is_cap
            })
            existing_names.add(name.lower().strip())
            added += 1

        total_added += added

    for state in data["states"]:
        after_counts[state["name"]] = len(state["cities"])

    # Save
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Report
    print("=" * 65)
    print(f"{'State':<30} {'Before':>8} {'After':>8} {'Added':>8}")
    print("=" * 65)
    grand_before = 0
    grand_after = 0
    for state in data["states"]:
        name = state["name"]
        b = before_counts[name]
        a = after_counts[name]
        grand_before += b
        grand_after += a
        diff = a - b
        marker = f" +{diff}" if diff > 0 else ""
        print(f"{name:<30} {b:>8} {a:>8} {marker:>8}")
    print("=" * 65)
    print(f"{'TOTAL':<30} {grand_before:>8} {grand_after:>8} {'+' + str(grand_after - grand_before):>8}")
    print(f"\nTotal cities added: {total_added}")
    print(f"Grand total cities: {grand_after}")


if __name__ == "__main__":
    main()
