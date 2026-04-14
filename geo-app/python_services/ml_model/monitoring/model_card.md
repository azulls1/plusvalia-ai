# Model Card — PlusvaliaPredictorModel v1.0

## Informacion General

| Campo | Valor |
|-------|-------|
| Nombre | PlusvaliaPredictorModel |
| Version | 1.0 |
| Tipo | Regression Ensemble (RandomForest + GradientBoosting) |
| Framework | scikit-learn 1.4.0 + XGBoost 2.0.3 |
| Fecha de entrenamiento | Variable (retraining cada 30 dias) |
| Autor | Samael Hernandez |

## Proposito

Predecir el precio por metro cuadrado y el score de plusvalia (0-100) de terrenos en Mexico, utilizando datos de comparables inmobiliarios, amenidades cercanas y datos demograficos de INEGI.

## Datos de Entrenamiento

### Fuentes
- Comparables inmobiliarios (scrapers: Inmuebles24, Lamudi, fuentes alternativas)
- Amenidades OpenStreetMap (Overpass API)
- Datos demograficos INEGI (Censo 2020)
- Grilla de precios promedio por zona

### Features
| Feature | Tipo | Descripcion |
|---------|------|-------------|
| price_m2 | Numerico | Precio por metro cuadrado (MXN) |
| area_m2 | Numerico | Area del terreno (m²) |
| lat, lon | Numerico | Coordenadas geograficas |
| distance_to_center | Numerico | Distancia al centro de la ciudad (km) |
| amenity_count | Numerico | Numero de amenidades cercanas |
| city | Categorico | Ciudad (Ciudad de Mexico, Guadalajara, Monterrey, Zapopan) |
| state | Categorico | Estado |
| month, quarter | Numerico | Features temporales |

### Distribucion geografica
- Ciudad de Mexico: ~40% de muestras
- Guadalajara: ~25%
- Monterrey: ~20%
- Zapopan: ~15%

## Metricas de Performance

| Metrica | Objetivo | Ultima medicion |
|---------|----------|-----------------|
| R² Score | > 0.75 | [Actualizar con cada retraining] |
| MAE (precio/m²) | < $5,000 MXN | [Actualizar] |
| MSE | Minimizar | [Actualizar] |
| Cross-validation (5-fold) | > 0.70 | [Actualizar] |

> **Nota**: Las metricas detalladas de cada entrenamiento se guardan automaticamente en un archivo `.metrics.json` junto al modelo `.pkl` (e.g., `plusvalia_model_v1.0_20240101_120000.metrics.json`). Este archivo incluye R², MAE, MSE, cross-validation scores, numero de muestras y features utilizadas.

## Limitaciones Conocidas

1. **Sesgo geografico**: Modelo entrenado solo con 4 ciudades mexicanas. No generaliza a otras regiones.
2. **Feature engineering incompleto**: `distance_to_center` usa placeholder (0.0) cuando INEGI no tiene datos del centro.
3. **Sin evaluacion de fairness**: No se ha evaluado si el modelo discrimina por zona socioeconomica.
4. **Datos temporales limitados**: El modelo no captura tendencias a largo plazo del mercado.
5. **Sin explicabilidad**: No se ha implementado SHAP ni LIME para interpretar predicciones.

## Evaluacion de Sesgo y Fairness

### Riesgos identificados
- Posible sesgo hacia zonas con mas datos (CDMX sobrerepresentada)
- Amenidades pueden correlacionar con nivel socioeconomico
- Precios historicos reflejan desigualdades existentes

### Mitigaciones pendientes
- [ ] Implementar analisis SHAP por feature
- [ ] Evaluar performance por subgrupo (ciudad, zona)
- [ ] Balancear dataset por ciudad
- [ ] Agregar intervalo de confianza a predicciones

## Monitoreo en Produccion

### Drift Detection
- **Herramienta**: `drift_detector.py`
- **Frecuencia**: Semanal (recomendado)
- **Metricas monitoreadas**: KS test por feature, PSI de predicciones
- **Umbrales**: KS > 0.2 = medium drift, > 0.35 = high drift
- **Accion**: Reentrenar si drift medium o high persiste >2 semanas

### Retraining Schedule
- Automatico: Cada 30 dias
- Manual: Cuando drift detector alerta HIGH
- Validacion: Cross-validation 5-fold obligatoria post-retraining

## Versionado

| Version | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2024-10 | Modelo inicial (RF + GB ensemble) |
| 1.1 | Pendiente | Agregar SHAP, fix distance_to_center |

## Uso Etico

Este modelo es una herramienta de apoyo para analisis inmobiliario. Las predicciones NO deben ser el unico factor en decisiones de inversion. Siempre consultar con profesionales del sector.
