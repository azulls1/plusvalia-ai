# 🚀 Pipeline Completo de Entrenamiento con Datos Reales

Este documento describe el **flujo completo** para entrenar el modelo ML con datos reales usando todas las tablas de Supabase.

---

## 📊 Arquitectura de Datos en Supabase

### Tablas Utilizadas

1. **`iainmobiliaria_comparables`** 
   - Propiedades scraped o cargadas manualmente
   - Columnas: id, title, price_mxn, area_m2, address, city, state, lat, lon

2. **`iainmobiliaria_amenities`**
   - Amenidades extraídas de OpenStreetMap
   - Columnas: id, osm_id, name, amenity_type, lat, lon, city, state, tags

3. **`iainmobiliaria_inegi_data`**
   - Datos demográficos y socioeconómicos
   - Columnas: id, city, state, population, population_density, median_income, etc.

4. **`iainmobiliaria_grid_tiles`**
   - Grilla de precios promedio por zona
   - Columnas: id, lat, lon, price_m2_avg, count_properties

5. **`iainmobiliaria_price_history`**
   - Histórico de precios para tracking temporal
   - Columnas: id, comparable_id, price_m2, recorded_at

6. **`iainmobiliaria_predictions`**
   - Predicciones del modelo ML
   - Columnas: id, comparable_id, predicted_price_m2, plusvalia_score, confidence, etc.

---

## 🔄 Flujo del Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  FASE 1: SCRAPING DE DATOS REALES                          │
│  - Scraping de portales inmobiliarios                       │
│  - Guardar en: iainmobiliaria_comparables                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  FASE 2: ENRIQUECIMIENTO CON DATOS EXTERNOS                │
│  - Extraer amenidades de OpenStreetMap                      │
│    → Guardar en: iainmobiliaria_amenities                  │
│  - Obtener datos de INEGI (demográficos/económicos)        │
│    → Guardar en: iainmobiliaria_inegi_data                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  FASE 3: CONSTRUCCIÓN DE FEATURES AVANZADAS                │
│  - Calcular distancias a amenidades                         │
│  - Agregar indicadores socioeconómicos                      │
│  - Generar grilla de precios                                │
│    → Guardar en: iainmobiliaria_grid_tiles                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  FASE 4: ENTRENAMIENTO DEL MODELO ML                       │
│  - Combinar datos de todas las fuentes                      │
│  - Entrenar Random Forest con features enriquecidas        │
│  - Guardar modelo entrenado (.pkl)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  FASE 5: GENERACIÓN Y GUARDADO DE PREDICCIONES            │
│  - Generar predicciones para todas las propiedades         │
│  - Calcular scores de plusvalía                             │
│    → Guardar en: iainmobiliaria_predictions                │
│  - Registrar histórico de precios                           │
│    → Guardar en: iainmobiliaria_price_history              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Cómo Usar el Pipeline

### Opción 1: Ejecutar Pipeline Completo

```bash
cd python_services
python pipeline_entrenamiento_completo.py
```

Este comando ejecuta **todas las fases** automáticamente.

### Opción 2: Ejecutar Fases Individuales

```python
from pipeline_entrenamiento_completo import RealEstatePipeline
import asyncio

async def entrenar():
    pipeline = RealEstatePipeline()
    
    ciudades = [
        {"city": "Guadalajara", "state": "Jalisco"},
        {"city": "Monterrey", "state": "Nuevo León"},
    ]
    
    # Solo scraping
    await pipeline.fase1_scraping_real(ciudades, max_pages=5)
    
    # Solo enriquecimiento
    await pipeline.fase2_enriquecimiento()
    
    # Solo features
    pipeline.fase3_construccion_features()
    
    # Solo entrenamiento
    df = pipeline.fase3_construccion_features()
    modelo = pipeline.fase4_entrenamiento_modelo(df)
    
    # Solo predicciones
    pipeline.fase5_generar_predicciones(modelo, df)

asyncio.run(entrenar())
```

---

## 📈 Features del Modelo Enriquecido

El modelo entrenado con datos reales incluye:

### Features Básicas
- `area_m2` - Superficie del terreno
- `lat`, `lon` - Ubicación geográfica
- `city_encoded`, `state_encoded` - Ciudad y estado

### Features de Amenidades (OpenStreetMap)
- `dist_to_nearest_school` - Distancia a escuela más cercana
- `dist_to_nearest_hospital` - Distancia a hospital
- `dist_to_nearest_supermarket` - Distancia a supermercado
- `count_amenities_1km` - Cantidad de amenidades en 1km
- `count_schools_2km` - Escuelas en 2km

### Features Socioeconómicas (INEGI)
- `population_density` - Densidad poblacional
- `median_income` - Ingreso mediano del área
- `unemployment_rate` - Tasa de desempleo
- `education_level` - Nivel educativo promedio

### Features Calculadas
- `price_m2_avg_zone` - Precio promedio de la zona (grid)
- `distance_to_center` - Distancia al centro de la ciudad
- `log_area` - Logaritmo del área
- `is_premium_zone` - Zona premium (basado en amenidades)

---

## 🔧 Configuración Requerida

### 1. Variables de Entorno

Asegúrate de tener en `config.py`:

```python
SUPABASE_URL = "https://iagenteksupabase.iagentek.com.mx"
SUPABASE_SERVICE_ROLE_KEY = "tu_service_role_key"

TABLE_COMPARABLES = "iainmobiliaria_comparables"
TABLE_AMENITIES = "iainmobiliaria_amenities"
TABLE_INEGI_DATA = "iainmobiliaria_inegi_data"
TABLE_PREDICTIONS = "iainmobiliaria_predictions"
TABLE_PRICE_HISTORY = "iainmobiliaria_price_history"
TABLE_GRID_TILES = "iainmobiliaria_grid_tiles"
```

### 2. Dependencias Python

```bash
pip install supabase pandas numpy scikit-learn loguru overpy playwright
```

### 3. Tablas en Supabase

Ejecutar los scripts SQL en orden:
```bash
01_crear_tablas.sql
02_indices.sql
03_rls_policies.sql
04_funciones_utiles.sql
07_tablas_ml_historico.sql
```

---

## 📊 Métricas Esperadas

Con datos reales, esperamos mejores métricas que con datos sintéticos:

| Métrica | Datos Sintéticos | Datos Reales (Esperado) |
|---------|------------------|-------------------------|
| R²      | 0.44             | **0.70 - 0.85**        |
| MAE     | $2,404/m²        | **$1,200 - $1,800/m²** |
| RMSE    | $3,242/m²        | **$1,800 - $2,500/m²** |

---

## 🔄 Reentrenamiento Periódico

### Configurar Cron Job (Linux/Mac)

```bash
# Ejecutar pipeline cada domingo a las 2 AM
0 2 * * 0 cd /ruta/python_services && python pipeline_entrenamiento_completo.py
```

### Task Scheduler (Windows)

1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Acción: Ejecutar programa
4. Programa: `python`
5. Argumentos: `pipeline_entrenamiento_completo.py`
6. Iniciar en: `C:\ruta\python_services`

---

## 🐛 Troubleshooting

### Error: "No se obtuvieron datos del scraping"
- **Causa**: Protecciones anti-scraping
- **Solución**: Usar proxies rotativos o APIs de pago

### Error: "overpy no instalado"
- **Solución**: `pip install overpy`

### Error: "Invalid authentication credentials"
- **Causa**: Service role key incorrecta
- **Solución**: Verificar credenciales en config.py

### Error: "Could not find column X"
- **Causa**: Esquema de tabla no coincide
- **Solución**: Ejecutar scripts SQL de migración

---

## 📝 Próximos Pasos

1. ✅ Pipeline completo implementado
2. ⏳ Integrar con API FastAPI
3. ⏳ Crear dashboard de monitoreo
4. ⏳ Implementar reentrenamiento automático
5. ⏳ Agregar validación de calidad de datos

---

## 📞 Soporte

Para dudas o problemas:
- Revisar logs en `logs/app.log`
- Verificar estado de tablas en Supabase
- Consultar métricas del modelo en `ml_model/models/`

---

**Última actualización**: Octubre 2025

