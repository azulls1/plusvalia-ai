# 🐍 Python Services - Sistema ML y Scraping

Sistema completo de Machine Learning, scraping y API para análisis de mercado inmobiliario.

---

## 📁 Estructura del Proyecto

```
python_services/
│
├── requirements.txt          # Dependencias Python
├── config.py                 # Configuración global
├── README.md                 # Esta documentación
│
├── scrapers/                 # Módulos de scraping
│   ├── inmuebles24_scraper.py
│   ├── lamudi_scraper.py
│   └── unified_scraper.py
│
├── ml_model/                 # Modelo de Machine Learning
│   ├── predictor.py          # Modelo de predicción
│   └── models/               # Modelos entrenados (.pkl)
│
├── api/                      # API FastAPI
│   └── main.py               # Servidor API
│
├── integrations/             # Integraciones externas
│   └── inegi_client.py       # Cliente INEGI
│
├── data/                     # Datos scrapeados (CSV)
└── logs/                     # Logs de ejecución
```

---

## 🚀 Instalación

### 1. Instalar Python

Requiere **Python 3.9+**

```bash
python --version
```

### 2. Crear entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
cd python_services
pip install -r requirements.txt
```

### 4. Instalar Playwright (para scraping)

```bash
playwright install chromium
```

### 5. Configurar variables de entorno

Crear archivo `.env` en `python_services/` con:

```env
# Supabase
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=tu_service_role_key_aqui

# PostgreSQL
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password_aqui

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 📊 Uso

### 🕷️ 1. Scraping de Datos

#### Scraper de Inmuebles24

```bash
python scrapers/inmuebles24_scraper.py
```

#### Scraper de Lamudi

```bash
python scrapers/lamudi_scraper.py
```

#### Scraper Unificado (Recomendado)

```bash
python scrapers/unified_scraper.py
```

**Salida**: CSV en `data/` con formato:

| title | price_mxn | area_m2 | address | city | state | source | scraped_at |
|-------|-----------|---------|---------|------|-------|--------|------------|
| Terreno... | 1500000 | 500 | Col. Centro | Querétaro | Querétaro | inmuebles24 | 2025-10-25... |

---

### 🧠 2. Entrenar Modelo ML

```bash
python ml_model/predictor.py
```

**Proceso**:
1. ✅ Conecta a Supabase
2. ✅ Obtiene datos de `iainmobiliaria_comparables`
3. ✅ Prepara features (geográficas, temporales, demográficas)
4. ✅ Entrena Random Forest Regressor
5. ✅ Evalúa métricas (R², MAE, RMSE)
6. ✅ Guarda modelo en `ml_model/models/`

**Métricas esperadas**:
- R² Test: > 0.80
- MAE Test: < $1,000 MXN/m²

---

### 🌐 3. Iniciar API

```bash
python api/main.py
```

**API corre en**: `http://localhost:8000`

**Documentación**: `http://localhost:8000/docs` (Swagger UI)

---

## 🔌 Endpoints de la API

### **POST /predict**

Predice precio y plusvalía de un terreno.

**Request**:
```json
{
  "lat": 20.5888,
  "lon": -100.3899,
  "area_m2": 500,
  "city": "Querétaro",
  "state": "Querétaro"
}
```

**Response**:
```json
{
  "predicted_price_m2": 8500.25,
  "predicted_total_price": 4250125.0,
  "plusvalia_score": 72.5,
  "growth_potential": "alto",
  "confidence": 85.0,
  "model_version": "1.0",
  "features_used": {
    "area_m2": 500,
    "distance_to_center": 2.5,
    "city": "Querétaro",
    "state": "Querétaro"
  },
  "prediction_id": 123,
  "timestamp": "2025-10-25T14:30:00"
}
```

---

### **POST /train**

Re-entrena el modelo con datos actuales.

**Request**:
```json
{
  "min_samples": 100,
  "force_retrain": true
}
```

**Response**:
```json
{
  "message": "Modelo entrenado exitosamente",
  "model_version": "1.0",
  "metrics": {
    "test_r2": 0.85,
    "test_mae": 850.5,
    "test_rmse": 1200.3,
    "n_samples": 500
  },
  "status": "success"
}
```

---

### **GET /predictions/history**

Obtiene historial de predicciones.

**Query params**:
- `limit`: Número de resultados (default: 100)
- `city`: Filtrar por ciudad (opcional)
- `state`: Filtrar por estado (opcional)

**Response**:
```json
{
  "predictions": [...],
  "count": 100,
  "filters": {
    "city": "Querétaro",
    "state": "Querétaro"
  }
}
```

---

### **GET /stats**

Estadísticas generales del sistema.

**Response**:
```json
{
  "comparables": 1250,
  "predictions": 450,
  "amenities": 3500,
  "model_loaded": true,
  "model_version": "1.0",
  "timestamp": "2025-10-25T14:30:00"
}
```

---

### **GET /health**

Health check de la API.

---

## 🔄 Integración con N8N

Puedes invocar la API desde n8n usando el nodo **HTTP Request**.

### Workflow: Predicción Automática

```
Trigger (Schedule: Daily)
  ↓
Supabase Query (Obtener nuevos comparables)
  ↓
Loop
  ↓
HTTP Request → POST http://localhost:8000/predict
  ↓
Supabase Insert (Guardar predicción)
```

---

## 🗄️ Datos INEGI

### Cliente INEGI

```python
from integrations.inegi_client import INEGIClient

client = INEGIClient()

# Obtener código de estado
code = client.get_state_code("Querétaro")  # "22"

# Calcular distancia al centro
distance = client.get_distance_to_center(20.6, -100.4, "Querétaro")

# Enriquecer datos con demografía
df_enriched = client.enrich_with_demographics(df)
```

---

## 📈 Features del Modelo ML

El modelo utiliza las siguientes features:

| Feature | Descripción | Importancia |
|---------|-------------|-------------|
| `area_m2` | Superficie del terreno | ⭐⭐⭐⭐⭐ |
| `distance_to_center` | Distancia al centro de la ciudad (km) | ⭐⭐⭐⭐ |
| `city_encoded` | Ciudad codificada | ⭐⭐⭐⭐ |
| `state_encoded` | Estado codificado | ⭐⭐⭐ |
| `population_density` | Densidad poblacional | ⭐⭐⭐ |
| `economic_level_score` | Nivel socioeconómico (1-5) | ⭐⭐⭐ |
| `month` | Mes de recolección | ⭐⭐ |
| `is_large_lot` | ¿Es lote grande? (bool) | ⭐⭐ |

---

## 🧪 Testing

### Test del Scraper

```bash
python scrapers/unified_scraper.py
```

### Test del Modelo

```bash
python ml_model/predictor.py
```

### Test de la API

```bash
# Iniciar API
python api/main.py

# En otra terminal
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 20.5888,
    "lon": -100.3899,
    "area_m2": 500,
    "city": "Querétaro",
    "state": "Querétaro"
  }'
```

---

## 📅 Automatización

### Script de Ejecución Mensual

Crear archivo `run_monthly_scraping.bat` (Windows):

```batch
@echo off
cd python_services
call venv\Scripts\activate
python scrapers/unified_scraper.py
python ml_model/predictor.py
deactivate
```

Programar en **Task Scheduler** (Windows) o **cron** (Linux) para ejecutar mensualmente.

---

## 🐛 Troubleshooting

### Error: "playwright not found"

```bash
playwright install chromium
```

### Error: "Module not found"

```bash
pip install -r requirements.txt
```

### Error: "Supabase connection failed"

Verificar variables de entorno en `.env`

### Error: "Model not trained"

```bash
python ml_model/predictor.py
```

O llamar al endpoint `/train` de la API.

---

## 📦 Dependencias Principales

| Librería | Versión | Uso |
|----------|---------|-----|
| playwright | 1.40.0 | Scraping web |
| pandas | 2.1.3 | Manipulación de datos |
| scikit-learn | 1.3.2 | Machine Learning |
| fastapi | 0.104.1 | API REST |
| supabase | 2.0.3 | Base de datos |
| geopandas | 0.14.1 | Datos geoespaciales |

---

## 📧 Soporte

**Email**: contacto@iagentek.com.mx  
**Documentación completa**: Ver carpeta `docs/`

---

## ✅ Checklist de Implementación

- [x] Scrapers de Inmuebles24 y Lamudi
- [x] Modelo ML con Random Forest
- [x] API FastAPI con endpoints
- [x] Integración con Supabase
- [x] Cliente INEGI
- [x] Documentación completa
- [ ] Tests unitarios
- [ ] CI/CD
- [ ] Deploy en producción

---

**Versión**: 1.0  
**Fecha**: Octubre 2025  
**Autor**: IAgentek

