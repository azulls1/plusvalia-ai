# 🚀 ENTRENAMIENTO MODELO ML - 32 ESTADOS DE MÉXICO

## 📋 RESUMEN

Pipeline completo para generar datos y entrenar el modelo ML con **TODOS los estados de México** (32 estados, 50 ciudades principales).

---

## 🎯 OBJETIVO

1. ✅ Generar propiedades comparables para 50 ciudades de los 32 estados
2. ✅ Scraping de amenidades desde OpenStreetMap
3. ✅ Generar grid de precios por metro cuadrado
4. ✅ Entrenar modelo ML con más datos
5. ✅ Generar predicciones en Supabase

---

## 📁 ARCHIVOS CREADOS

| Archivo | Descripción |
|---------|-------------|
| **`cities_mexico_32_states.json`** | Lista de 50 ciudades de los 32 estados |
| **`pipeline_32_states_mexico.py`** | Script principal del pipeline |

---

## 🗂️ ESTRUCTURA DE DATOS

### Propiedades por Ciudad
- **50 propiedades** por ciudad
- Áreas: 150-5000 m² (distribución realista)
- Precios basados en índices oficiales (SHF, INEGI, mercado 2025)

### Total de Datos
- **2,500 propiedades** comparables (50 ciudades × 50 propiedades)
- **~20,000 amenidades** OSM (escuelas, hospitales, etc.)
- **~500 grid tiles** de precios promedio
- **2,500 predicciones** ML generadas

---

## 💰 PRECIOS BASE POR ESTADO (MXN/m²)

| Estado | Precio/m² | Ciudades Principales |
|--------|-----------|---------------------|
| Ciudad de México | $56,000 | CDMX |
| Quintana Roo | $45,000 | Cancún, Playa del Carmen |
| Baja California Sur | $42,000 | La Paz, Cabo San Lucas |
| Nuevo León | $39,000 | Monterrey, Apodaca, San Nicolás |
| Baja California | $38,000 | Tijuana, Mexicali, Ensenada |
| Querétaro | $32,000 | Querétaro |
| Jalisco | $25,000 | Guadalajara, Zapopan, Tlaquepaque |
| México | $28,000 | Toluca, Ecatepec, Naucalpan |
| Yucatán | $22,000 | Mérida |
| Sonora | $23,000 | Hermosillo, Nogales |
| Chihuahua | $22,000 | Chihuahua, Ciudad Juárez |
| Coahuila | $21,000 | Saltillo, Torreón |
| Aguascalientes | $20,000 | Aguascalientes |
| Sinaloa | $20,000 | Culiacán, Mazatlán |
| Guanajuato | $20,000 | León, Irapuato, Celaya |
| Tamaulipas | $19,000 | Reynosa, Matamoros |
| Puebla | $18,000 | Puebla, Cholula |
| Morelos | $16,000 | Cuernavaca |
| Zacatecas | $16,000 | Zacatecas |
| Durango | $18,000 | Durango |
| Campeche | $18,000 | Campeche, Ciudad del Carmen |
| San Luis Potosí | $17,000 | San Luis Potosí |
| Nayarit | $17,000 | Tepic |
| Hidalgo | $17,000 | Pachuca |
| Guerrero | $14,000 | Acapulco, Chilpancingo |
| Tabasco | $14,000 | Villahermosa |
| Veracruz | $15,000 | Veracruz, Xalapa |
| Colima | $18,000 | Colima, Manzanillo |
| Tlaxcala | $15,000 | Tlaxcala |
| Oaxaca | $13,000 | Oaxaca |
| Michoacán | $15,000 | Morelia |
| Chiapas | $12,000 | Tuxtla Gutiérrez, Tapachula |

---

## 🚀 EJECUTAR PIPELINE

### Opción 1: Ejecución Completa

```bash
cd geo-app/python_services

python pipeline_32_states_mexico.py
```

**Tiempo estimado:** 30-60 minutos (dependiendo de velocidad OSM)

---

### Opción 2: Por Fases (Recomendado)

```bash
# Abrir Python interactivo
cd geo-app/python_services
python

# Importar y ejecutar fases
import asyncio
from pipeline_32_states_mexico import Mexico32StatesPipeline

pipeline = Mexico32StatesPipeline()

# Fase 1: Propiedades
df = pipeline.fase1_generar_propiedades()

# Fase 2: Amenidades OSM (toma tiempo)
await pipeline.fase2_scrape_amenities()

# Fase 3: Grid
pipeline.fase3_generar_grid_tiles()

# Fase 4: Entrenar modelo
model = pipeline.fase4_entrenar_modelo()

# Fase 5: Predicciones
pipeline.fase5_generar_predicciones(model)
```

---

## 📊 FASES DEL PIPELINE

### FASE 1: Generar Propiedades Comparables
- **Input:** None
- **Output:** 2,500 propiedades en `iainmobiliaria_comparables`
- **Tiempo:** ~2 minutos
- **Descripción:** Genera propiedades realistas con precios basados en índices oficiales

### FASE 2: Scraping OSM Amenities
- **Input:** Lista de ciudades
- **Output:** ~20,000 amenidades en `iainmobiliaria_amenities`
- **Tiempo:** ~20-30 minutos
- **Descripción:** Extrae escuelas, hospitales, universidades, comercios, etc.

### FASE 3: Generar Grid Tiles
- **Input:** Propiedades comparables
- **Output:** ~500 tiles en `iainmobiliaria_grid_tiles`
- **Tiempo:** ~1 minuto
- **Descripción:** Calcula precios promedio por zona (grid 0.01° ~1km)

### FASE 4: Entrenar Modelo ML
- **Input:** Todas las propiedades
- **Output:** Modelo entrenado guardado en `ml_model/models/`
- **Tiempo:** ~5-10 minutos
- **Descripción:** Entrena Random Forest con features geográficas y demográficas

### FASE 5: Generar Predicciones
- **Input:** Modelo entrenado + Propiedades
- **Output:** 2,500 predicciones en `iainmobiliaria_predictions`
- **Tiempo:** ~2 minutos
- **Descripción:** Genera predicciones de plusvalía y precios para todas las ubicaciones

---

## 🎯 RESULTADOS ESPERADOS

### En Supabase

| Tabla | Registros Esperados |
|-------|---------------------|
| `iainmobiliaria_comparables` | ~2,500 |
| `iainmobiliaria_amenities` | ~20,000 |
| `iainmobiliaria_grid_tiles` | ~500 |
| `iainmobiliaria_predictions` | ~2,500 |

### Métricas del Modelo

| Métrica | Valor Esperado |
|---------|----------------|
| **R² Score** | 0.85-0.95 |
| **MAE** | $2,000-5,000 MXN/m² |
| **Muestras** | 2,000+ |

---

## 🔍 VERIFICAR RESULTADOS

### En Supabase Dashboard

```sql
-- Verificar propiedades
SELECT state, COUNT(*) as propiedades
FROM iainmobiliaria_comparables
GROUP BY state
ORDER BY propiedades DESC;

-- Verificar predicciones
SELECT state, 
       COUNT(*) as predicciones,
       AVG(plusvalia_score) as score_promedio,
       AVG(predicted_price_m2) as precio_promedio_m2
FROM iainmobiliaria_predictions
GROUP BY state
ORDER BY score_promedio DESC;

-- Verificar grid tiles
SELECT state, COUNT(*) as tiles, AVG(price_m2_avg) as precio_promedio
FROM iainmobiliaria_grid_tiles g
JOIN iainmobiliaria_comparables c ON 
     ABS(g.lat - c.lat) < 0.01 AND ABS(g.lon - c.lon) < 0.01
GROUP BY state;
```

---

## 📊 TABLAS DE SUPABASE

### `iainmobiliaria_comparables`
```sql
CREATE TABLE iainmobiliaria_comparables (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  price_mxn NUMERIC(12,2) NOT NULL,
  area_m2 NUMERIC(10,2) NOT NULL,
  price_m2 NUMERIC(10,2) GENERATED ALWAYS AS (price_mxn / area_m2) STORED,
  address TEXT NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  lat FLOAT8,
  lon FLOAT8,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

✅ **Ya existe** - No necesitas crear nada

### `iainmobiliaria_grid_tiles`
```sql
CREATE TABLE iainmobiliaria_grid_tiles (
  id BIGSERIAL PRIMARY KEY,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  price_m2_avg FLOAT8 NOT NULL,  -- ← PRECIO POR m²
  count_properties INT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(lat, lon)
);
```

✅ **Ya existe** - Con campo `price_m2_avg` ✅

### `iainmobiliaria_predictions`
```sql
CREATE TABLE iainmobiliaria_predictions (
  id BIGSERIAL PRIMARY KEY,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  predicted_price_m2 FLOAT8 NOT NULL,  -- ← PRECIO POR m²
  plusvalia_score FLOAT8 NOT NULL,
  growth_potential TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  current_price_m2 FLOAT8,
  model_confidence FLOAT8,
  model_version TEXT,
  prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

✅ **Ya existe** - Con campo `predicted_price_m2` ✅

---

## 🔧 TROUBLESHOOTING

### Error: "No hay datos para entrenar"

**Causa:** Fase 1 no se ejecutó correctamente

**Solución:**
```bash
# Re-ejecutar Fase 1
python -c "
import asyncio
from pipeline_32_states_mexico import Mexico32StatesPipeline
pipeline = Mexico32StatesPipeline()
df = pipeline.fase1_generar_propiedades()
print(f'Propiedades: {len(df)}')
"
```

---

### Error: "OSM timeout" en Fase 2

**Causa:** OSM está lento o hay problemas de red

**Solución:**
```bash
# Saltar Fase 2 y continuar (amenidades son opcionales para el entrenamiento)
# Ejecutar Fase 3, 4, 5 directamente
```

---

### Error: "Model not found"

**Causa:** Fase 4 no se ejecutó

**Solución:**
```bash
# Re-ejecutar Fase 4
from pipeline_32_states_mexico import Mexico32StatesPipeline
pipeline = Mexico32StatesPipeline()
model = pipeline.fase4_entrenar_modelo()
```

---

## ✅ CHECKLIST

```
PREPARACIÓN:
[ ] Archivo cities_mexico_32_states.json existe
[ ] Supabase conectado (config.py configurado)
[ ] Tablas creadas en Supabase

EJECUCIÓN:
[ ] Fase 1: Propiedades generadas (2,500)
[ ] Fase 2: Amenidades scraped (opcional)
[ ] Fase 3: Grid tiles generados
[ ] Fase 4: Modelo entrenado
[ ] Fase 5: Predicciones guardadas

VERIFICACIÓN:
[ ] SELECT COUNT(*) FROM iainmobiliaria_comparables; -- Debe ser ~2,500
[ ] SELECT COUNT(*) FROM iainmobiliaria_grid_tiles; -- Debe ser ~500
[ ] SELECT COUNT(*) FROM iainmobiliaria_predictions; -- Debe ser ~2,500
[ ] Modelo guardado en ml_model/models/
```

---

## 🎉 BENEFICIOS

### ✅ Cobertura Nacional
- 32 estados completos
- 50 ciudades principales
- Datos representativos de todo México

### ✅ Mejor Precisión
- Más datos = mejor modelo
- 2,000+ muestras vs 800 anteriores
- R² Score esperado: 0.90+

### ✅ Grid Completo
- Precios por m² por zona
- Cobertura nacional de precios promedio
- Visualización en mapa mejorada

---

## 📈 PRÓXIMOS PASOS

Una vez completado el pipeline:

1. ✅ Verificar resultados en Supabase
2. ✅ Actualizar frontend para mostrar mapa de 32 estados
3. ✅ Probar predicciones en diferentes ubicaciones
4. ✅ Validar precisión del modelo

---

## 🐛 PROBLEMAS CONOCIDOS

### OSM Scraping Lento
- **Causa:** OSM es gratuito pero lento
- **Solución:** Esperar 30 minutos o saltar esta fase

### Memoria insuficiente
- **Causa:** 2,500 registros pueden consumir RAM
- **Solución:** Cerrar otras apps, ejecutar por fases

---

**Listo para entrenar con datos de TODO México** 🇲🇽

**Desarrollado por Samael Hernandez**

