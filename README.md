<p align="center">
  <h1 align="center">Plusvalia AI</h1>
  <p align="center">
    <strong>Plataforma de analisis de mercado inmobiliario con Machine Learning para Mexico</strong>
  </p>
  <p align="center">
    <a href="https://plusvalia.iagentek.com.mx">Demo en Vivo</a> &middot;
    <a href="https://plusvalia.iagentek.com.mx/como-funciona">Como Funciona</a> &middot;
    <a href="#arquitectura">Arquitectura</a> &middot;
    <a href="#instalacion">Instalacion</a> &middot;
    <a href="geo-app/docs/api/API_REFERENCE.md">API Docs</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Angular-20-DD0031?logo=angular" alt="Angular 20" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/LightGBM-4.5-green" alt="LightGBM" />
  <img src="https://img.shields.io/badge/XGBoost-2.1-blue" alt="XGBoost" />
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?logo=supabase" alt="Supabase" />
  <img src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis" alt="Redis" />
  <img src="https://img.shields.io/badge/Docker_Swarm-Ready-2496ED?logo=docker" alt="Docker Swarm" />
  <img src="https://img.shields.io/badge/Live-plusvalia.iagentek.com.mx-16a34a" alt="Live" />
  <img src="https://img.shields.io/badge/Mobile-Responsive-blue" alt="Responsive" />
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

**Mapa Interactivo** — Heatmap de predicciones ML con Leaflet. Coropleta por estado con scores de plusvalia. Click para ver detalle. Filtros por estado, score y precio.

**Predicciones ML (Model v5.0)** — Ensemble de LightGBM + XGBoost con optimizacion Optuna. 30+ features reales. Score de plusvalia 0-100. Explicabilidad SHAP por prediccion.

**Datos Gubernamentales** — 8 scrapers automatizados: INEGI, CONAPO, DENUE, SESNSP, SHF, CENAPRED, SEDATU, CONAVI/INFONAVIT.

**ML Ops** — Drift detection automatico (KS test + PSI), model registry, bias evaluation, reentrenamiento programado con Celery Beat.

**Predicciones Bulk** — Generacion masiva de predicciones con blending vectorizado para cobertura nacional.

**Pagina "Como Funciona"** — Guia visual que explica el proceso de ML, el score de plusvalia (0-100), las fuentes de datos y como usar la plataforma.

**Mobile Responsive** — Layout adaptativo con hamburger menu, sidebar drawer, y mapa fullscreen en dispositivos moviles y tablets (breakpoint 992px).

---

<h2 id="arquitectura">Arquitectura</h2>

```
                    ┌──────────────────────────┐
                    │   Angular 20 SPA (Nginx)  │
                    │   Leaflet + Tailwind CSS  │
                    │   Forest Design System    │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼                         ▼
            ┌──────────────┐          ┌──────────────┐
            │  FastAPI      │          │  Supabase    │
            │  REST API     │          │  PostgreSQL  │
            │  ML Inference │          │  31 tablas   │
            │  SHAP Explain │          │  RLS + Audit │
            └──────┬───────┘          └──────────────┘
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
   ┌──────────┐ ┌──────┐ ┌──────────────────┐
   │  Celery  │ │Redis │ │  ML Pipeline     │
   │  3 colas │ │Cache │ │  LightGBM+XGBoost│
   │  + Beat  │ │Rate  │ │  Optuna+SHAP     │
   │          │ │Limit │ │  H3 Spatial      │
   └──────────┘ └──────┘ └──────────────────┘
```

**6 servicios en Docker Swarm** con Traefik v3 como reverse proxy y SSL automatico (Let's Encrypt).

---

## Stack Tecnologico

| Capa | Tecnologias |
|------|-------------|
| **Frontend** | Angular 20, TypeScript (strict), Leaflet, Tailwind CSS, Cypress |
| **Backend** | FastAPI, Python 3.11, Uvicorn, Celery 5 + Beat |
| **ML** | LightGBM 4.5, XGBoost 2.1, Optuna 4.1, SHAP 0.46, scikit-learn |
| **Geospatial** | H3 hexagonal indexing, GeoPandas, Shapely, Rasterio |
| **Base de datos** | PostgreSQL (Supabase), Redis 7 |
| **Infra** | Docker Swarm, Traefik v3, Nginx, Prometheus + Grafana |
| **Seguridad** | API Key auth, RLS, rate limiting, CORS, audit logs, circuit breaker |

---

## Deploy en Produccion

Desplegado en VPS Ubuntu 24.04 (8 cores, 24GB RAM) con **Docker Swarm** + **Traefik v3**.

| Servicio | URL |
|----------|-----|
| **Frontend** | https://plusvalia.iagentek.com.mx |
| **Backend API** | https://plusvalia-api.iagentek.com.mx |
| **Redis** | Interno (cache + broker Celery) |
| **Celery Worker** | Interno (3 colas: default, ml, enrichment) |
| **Celery Beat** | Interno (tareas programadas) |

### Deploy con Docker Swarm

```bash
cd /root/plusvalia-ai/geo-app

# Build imagenes
docker build -t plusvalia-ai-frontend:latest ./app
docker build -t plusvalia-ai-backend:latest ./python_services

# Configurar credenciales
cp python_services/.env.example python_services/.env
# Editar .env con credenciales reales

# Deploy
docker stack deploy -c plusvalia-ai.yaml plusvalia-ai
```

---

<h2 id="instalacion">Instalacion local</h2>

### Prerequisitos
- Python 3.11+
- Node.js 18+
- Docker (para Redis)

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

## API Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/health` | Estado del servicio |
| GET | `/predictions/heatmap` | Predicciones para heatmap |
| GET | `/predictions/stats-by-state` | Scores por estado (coropleta) |
| GET | `/predictions/nearby` | Predicciones cercanas a un punto |
| GET | `/predictions/bbox` | Predicciones en bounding box |
| GET | `/predictions/stats-by-city` | Stats por ciudad |
| POST | `/predictions/predict` | Prediccion individual |
| POST | `/predictions/explain` | Explicabilidad SHAP |
| GET | `/predictions/drift-status` | Estado de drift del modelo |
| POST | `/train` | Reentrenar modelo |
| POST | `/tasks/train` | Entrenamiento async (Celery) |
| POST | `/analytics/events` | Recepcion de eventos frontend |

---

## Seguridad

- **Autenticacion** — API Key (X-API-Key) en endpoints sensibles
- **Autorizacion** — Row-Level Security (RLS) en todas las tablas
- **Rate Limiting** — Redis sorted sets (configurable por endpoint)
- **Validacion** — Input sanitizer (XSS, SQL injection) en frontend y backend
- **Audit** — Logs automaticos con triggers en tablas principales
- **CORS** — Origenes restringidos (solo plusvalia.iagentek.com.mx)
- **Docker** — Multi-stage builds, usuario no-root (appuser:1001)

---

## Estructura del Proyecto

```
plusvalia-ai/
├── geo-app/
│   ├── app/                        # Angular 20 SPA
│   │   ├── Dockerfile              # Multi-stage (Node 18 + Nginx)
│   │   ├── nginx.conf              # SPA routing, gzip, security headers
│   │   └── src/app/
│   │       ├── components/         # 8 componentes UI (responsive)
│   │       ├── pages/
│   │       │   ├── mapa/           # Mapa interactivo principal
│   │       │   └── como-funciona/  # Pagina explicativa
│   │       ├── services/           # API, Cache, ML, Supabase, Analytics
│   │       └── validators/         # Input sanitizer, file validator
│   │
│   ├── python_services/            # FastAPI backend
│   │   ├── Dockerfile              # Multi-stage (Python 3.11)
│   │   ├── api/routers/            # predictions, training, stats, tasks
│   │   ├── ml_model/               # LightGBM, XGBoost, Optuna, SHAP
│   │   ├── middleware/             # Auth, rate limit, circuit breaker
│   │   ├── scrapers/               # 8 scrapers gubernamentales
│   │   ├── scripts/                # Data pipeline, enrichment
│   │   └── tasks/                  # Celery async tasks
│   │
│   ├── plusvalia-ai.yaml           # Docker Swarm stack (6 servicios)
│   ├── monitoring/                 # Prometheus + Grafana
│   ├── scripts/                    # Backup, load test, rollback
│   ├── scripts_sql/                # 22+ migrations SQL
│   └── docs/                       # API, security, SLA, runbooks
└── README.md
```

---

## Licencia

Todos los derechos reservados.

---

<p align="center">
  <sub>Desarrollado por Samael Hernandez &mdash; Angular 20, FastAPI, LightGBM, Supabase, Docker Swarm.</sub>
</p>
