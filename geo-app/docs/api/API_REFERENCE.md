# API Reference — IAInmobiliaria ML API

## Base URL
- Desarrollo: `http://localhost:8000`
- Produccion: `https://api.iainmobiliaria.iagentek.com.mx`

## Autenticacion
Rate limiting por IP: 1000 requests/hora (configurable via `MAX_REQUESTS_PER_HOUR`)

## Endpoints

### Health Check
```
GET /health
```

**Response 200:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "model_version": "1.0",
  "uptime_seconds": 3600
}
```

---

### Predecir Plusvalia
```
POST /predict
```

**Request Body:**
```json
{
  "lat": 19.4326,
  "lon": -99.1332,
  "city": "Ciudad de México",
  "state": "CDMX",
  "area_m2": 200,
  "amenities_nearby": 15
}
```

**Response 200:**
```json
{
  "price_m2_predicted": 15420.50,
  "plusvalia_score": 72.5,
  "potential_level": "alto",
  "confidence": 0.85,
  "model_version": "1.0",
  "features_used": ["price_m2", "distance_to_center", "amenity_count"]
}
```

**Errores:**
| Codigo | Descripcion |
|--------|-------------|
| 400 | Parametros invalidos |
| 422 | Validacion fallida (Pydantic) |
| 429 | Rate limit excedido |
| 500 | Error interno del modelo |

---

### Estadisticas del Modelo
```
GET /stats
```

**Response 200:**
```json
{
  "total_predictions": 15420,
  "model_version": "1.0",
  "last_trained": "2024-10-15T10:30:00Z",
  "metrics": {
    "r2_score": 0.82,
    "mae": 3200.50,
    "mse": 15000000.0
  },
  "cities_covered": ["Ciudad de México", "Guadalajara", "Monterrey", "Zapopan"]
}
```

---

### Heatmap de Predicciones
```
GET /predictions/heatmap?city={city}&min_score={score}
```

**Query Parameters:**
| Param | Tipo | Default | Descripcion |
|-------|------|---------|-------------|
| city | string | (todos) | Filtrar por ciudad |
| min_score | number | 0 | Score minimo de plusvalia |
| limit | number | 1000 | Max resultados |

---

### Predicciones por Bbox
```
GET /predictions/bbox?min_lat={}&max_lat={}&min_lon={}&max_lon={}
```

**Query Parameters:**
| Param | Tipo | Requerido | Descripcion |
|-------|------|-----------|-------------|
| min_lat | number | Si | Latitud minima |
| max_lat | number | Si | Latitud maxima |
| min_lon | number | Si | Longitud minima |
| max_lon | number | Si | Longitud maxima |
| limit | number | No | Max resultados (default: 500) |

---

### Reentrenar Modelo
```
POST /retrain
```

**Requiere:** Service Role Key en header `Authorization: Bearer <key>`

**Response 200:**
```json
{
  "status": "training_started",
  "estimated_time_seconds": 120,
  "new_samples": 500
}
```

---

## Codigos de Error Comunes

| Codigo | Significado | Accion |
|--------|-------------|--------|
| 400 | Bad Request | Revisar parametros |
| 401 | Unauthorized | Verificar API key |
| 404 | Not Found | Verificar endpoint URL |
| 422 | Validation Error | Verificar tipos de datos |
| 429 | Too Many Requests | Esperar 1 hora o reducir frecuencia |
| 500 | Internal Error | Contactar soporte, revisar logs |
| 503 | Service Unavailable | Modelo cargando, reintentar en 30s |

## Documentacion Interactiva

- **Swagger UI:** `{BASE_URL}/docs`
- **ReDoc:** `{BASE_URL}/redoc`
- **OpenAPI JSON:** `{BASE_URL}/openapi.json`
