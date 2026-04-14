<p align="center">
  <h1 align="center">Plusvalia AI</h1>
  <p align="center">
    <strong>Plataforma de analisis de mercado inmobiliario con Machine Learning para Mexico</strong>
  </p>
  <p align="center">
    <a href="#demo">Ver Demo</a> &middot;
    <a href="#arquitectura">Arquitectura</a> &middot;
    <a href="#instalacion">Instalacion</a> &middot;
    <a href="geo-app/docs/api/API_REFERENCE.md">API Docs</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Angular-17-DD0031?logo=angular" alt="Angular 17" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/LightGBM-4.5-green" alt="LightGBM" />
  <img src="https://img.shields.io/badge/XGBoost-2.1-blue" alt="XGBoost" />
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?logo=supabase" alt="Supabase" />
  <img src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis" alt="Redis" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker" alt="Docker" />
</p>

---

## Que es Plusvalia AI?

Plusvalia AI es una plataforma full-stack que predice la plusvalia (apreciacion) de terrenos e inmuebles en Mexico usando modelos de Machine Learning entrenados con datos reales de multiples fuentes gubernamentales y de mercado.

### Numeros clave

| Metrica | Valor |
|---------|-------|
| **Registros de entrenamiento** | 420,000+ propiedades reales |
| **Cobertura geografica** | 4,027 ciudades (32 estados) |
| **Precision del modelo (R²)** | 0.95 |
| **Fuentes de datos** | 8 scrapers gubernamentales + 4 fuentes de mercado |
| **Tablas en base de datos** | 31 |
| **Modelo ML** | Ensemble LightGBM + XGBoost + Optuna |

---

## Funcionalidades

**Mapa Interactivo** — Heatmap de predicciones ML con Leaflet. Click para ver predicciones, filtros por ciudad, score y riesgo. Clusters de marcadores.

**Predicciones ML (Model v5.0)** — Ensemble de LightGBM + XGBoost con optimizacion Optuna. 30+ features reales. Score de plusvalia 0-100. Explicabilidad SHAP por prediccion.

**Chatbot AI (Favier AI)** — Asistente inmobiliario con lenguaje natural via n8n + OpenAI. Consultas de mercado y recomendaciones personalizadas.

**Datos Gubernamentales** — 8 scrapers automatizados: INEGI, CONAPO, DENUE, SESNSP, SHF, CENAPRED, SEDATU, CONAVI/INFONAVIT.

**ML Ops** — Drift detection automatico (KS test + PSI), model registry, bias evaluation, reentrenamiento programado con Celery Beat.

**Predicciones Bulk** — Generacion masiva de predicciones con blending vectorizado para cobertura nacional.

---

<h2 id="arquitectura">Arquitectura</h2>

```
                        ┌──────────────────────┐
                        │    Angular 17 SPA     │
                        │  Leaflet + Tailwind   │
                        │  Forest Design System │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌──────────────┐ ┌──────────┐ ┌──────────────┐
            │  FastAPI      │ │  n8n     │ │  Supabase    │
            │  REST API     │ │  AI Chat │ │  PostgreSQL  │
            │  ML Inference │ │  Webhooks│ │  31 tablas   │
            │  SHAP Explain │ │          │ │  RLS + Audit │
            └──────┬───────┘ └──────────┘ └──────────────┘
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
   ┌──────────┐ ┌──────┐ ┌──────────────────┐
   │  Celery  │ │Redis │ │  ML Pipeline     │
   │  3 colas │ │Cache │ │  LightGBM+XGBoost│
   │  + Beat  │ │Rate  │ │  Optuna+SHAP     │
   │  + Flower│ │Limit │ │  H3 Spatial      │
   └──────────┘ └──────┘ └──────────────────┘
```

---

## Stack Tecnologico

| Capa | Tecnologias |
|------|-------------|
| **Frontend** | Angular 17, TypeScript (strict), Leaflet, Tailwind CSS, Cypress |
| **Backend** | FastAPI, Python 3.11, Uvicorn, Celery 5 + Beat + Flower |
| **ML** | LightGBM 4.5, XGBoost 2.1, Optuna 4.1, SHAP 0.46, scikit-learn |
| **Geospatial** | H3 hexagonal indexing, GeoPandas, Shapely, Rasterio |
| **Base de datos** | PostgreSQL (Supabase), Redis 7 |
| **Infra** | Docker, Traefik, GitHub Actions CI/CD (7 jobs), Prometheus + Grafana |
| **Seguridad** | API Key auth, RLS, rate limiting, CORS, audit logs, circuit breaker |

---

<h2 id="instalacion">Instalacion</h2>

### Prerequisitos
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- Redis 7

### Inicio rapido

```bash
# 1. Clonar
git clone https://github.com/azulls1/plusvalia-ai.git
cd plusvalia-ai/geo-app

# 2. Backend
cd python_services
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
cp .env.example .env            # Configurar credenciales

# 3. Redis
docker run -d --name geo-redis -p 6379:6379 redis:7-alpine

# 4. Iniciar backend
python -m uvicorn api.main:app --port 8001 --reload

# 5. Celery worker (otra terminal)
python -m celery -A celery_app worker --loglevel=info --pool=solo -Q default,ml,enrichment

# 6. Frontend (otra terminal)
cd ../app
npm install
npm start
```

Abrir **http://localhost:4200**

> Para instrucciones detalladas ver [INICIO_RAPIDO.md](geo-app/INICIO_RAPIDO.md)

---

## Fuentes de Datos

| Fuente | Tipo | Registros |
|--------|------|-----------|
| Properati | Listings inmobiliarios | 120K+ |
| CDMX Catastro | Registro catastral | 80K+ |
| SNIIV/SEDATU | Desarrollo urbano | 3.8K+ |
| BIS Index | Indices de precios | 150+ |
| INEGI/DENUE | Demografia y negocios | 178 perfiles |
| CONAPO | Marginacion | Nacional |
| SESNSP | Criminalidad | Nacional |
| CENAPRED | Riesgo natural | Nacional |
| SHF | Indices de precios vivienda | Nacional |
| CONAVI/INFONAVIT | Vivienda social | Nacional |

---

## Seguridad

- **Autenticacion** — API Key (X-API-Key) en endpoints sensibles
- **Autorizacion** — Row-Level Security (RLS) en todas las tablas
- **Rate Limiting** — Redis sorted sets (1-100 req/min configurable)
- **Validacion** — Input sanitizer (XSS, SQL injection) en frontend y backend
- **Audit** — Logs automaticos con triggers en tablas principales
- **Headers** — HSTS, CSP, X-Frame-Options, CORS restringido
- **Docker** — Multi-stage builds, usuario no-root (appuser:1001)

---

## Documentacion

| Documento | Descripcion |
|-----------|-------------|
| [INICIO_RAPIDO.md](geo-app/INICIO_RAPIDO.md) | Guia de 5 minutos |
| [API Reference](geo-app/docs/api/API_REFERENCE.md) | Endpoints completos |
| [Seguridad](geo-app/GUIA_SEGURIDAD_COMPLETA.md) | Detalles tecnicos |
| [Despliegue](geo-app/INSTRUCCIONES_DESPLIEGUE.md) | Produccion paso a paso |
| [Credential Rotation](geo-app/docs/security/credential-rotation.md) | Gestion de secretos |
| [SLA/SLO](geo-app/docs/sla/SLA_SLO.md) | Objetivos de servicio |
| [Runbook](geo-app/docs/runbooks/incident-response.md) | Respuesta a incidentes |

---

## Estructura del Proyecto

```
plusvalia-ai/
├── geo-app/
│   ├── app/                    # Angular 17 SPA
│   │   ├── src/app/
│   │   │   ├── components/     # 8+ componentes UI
│   │   │   ├── services/       # API, Cache, ML, Supabase
│   │   │   └── validators/     # Input sanitizer, file validator
│   │   └── cypress/            # 13 E2E tests
│   │
│   ├── python_services/        # FastAPI backend
│   │   ├── api/routers/        # predictions, training, stats, tasks
│   │   ├── ml_model/           # LightGBM, XGBoost, Optuna, SHAP
│   │   ├── middleware/         # Auth, rate limit, circuit breaker
│   │   ├── scrapers/           # 8 scrapers gubernamentales
│   │   ├── scripts/            # Data pipeline, enrichment
│   │   └── tasks/              # Celery async tasks
│   │
│   ├── monitoring/             # Prometheus + Grafana + alertas
│   ├── scripts/                # Backup, load test, rollback
│   ├── scripts_sql/            # 22+ migrations SQL
│   ├── docs/                   # API, security, SLA, runbooks
│   └── docker-compose.*.yml    # Local y produccion
└── README.md
```

---

## Licencia

Todos los derechos reservados.

---

<p align="center">
  <sub>Desarrollado con Angular, FastAPI, LightGBM y datos reales del mercado inmobiliario mexicano.</sub>
</p>
