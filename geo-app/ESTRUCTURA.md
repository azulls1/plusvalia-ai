# Estructura Completa del Proyecto

```
geo-app/
│
├── README.md                          # Documentacion principal del proyecto
├── CHANGELOG.md                       # Historial de versiones (v1.0 → v3.0)
├── INSTALL.md                         # Guia de instalacion paso a paso
├── ESTRUCTURA.md                      # Este archivo (estructura visual)
├── CONTRIBUTING.md                    # Guia de contribucion (code style, PRs)
├── INICIO_RAPIDO.md                   # Guia rapida de arranque
├── GUIA_SEGURIDAD_COMPLETA.md         # Detalles tecnicos de seguridad
├── INSTRUCCIONES_DESPLIEGUE.md        # Despliegue a produccion
│
├── app/                               # Frontend Angular 17
│   │
│   ├── .gitignore                     # Archivos ignorados por Git
│   ├── .htaccess                      # Configuracion para hosting (SPA routing + security headers)
│   ├── .eslintrc.json                 # ESLint config (no-explicit-any = error)
│   ├── .prettierrc                    # Prettier config
│   ├── .editorconfig                  # Editor config (UTF-8, 2-space indent)
│   ├── package.json                   # Dependencias y scripts de npm
│   ├── angular.json                   # Configuracion de Angular CLI (lint + test targets)
│   ├── tsconfig.json                  # TypeScript (strict: true)
│   ├── tsconfig.app.json              # TypeScript (app)
│   ├── tailwind.config.js             # Tailwind CSS + Forest DS colors
│   ├── postcss.config.js              # PostCSS
│   │
│   ├── cypress/                       # E2E Tests (Cypress)
│   │   ├── e2e/                       # 13 test specs (8 map + 5 API)
│   │   └── support/                   # Cypress support files
│   │
│   └── src/                           # Codigo fuente
│       │
│       ├── index.html                 # HTML principal (Sora, DM Sans, JetBrains Mono fonts)
│       ├── main.ts                    # Punto de entrada (provideHttpClient + interceptors)
│       ├── styles.css                 # Estilos globales (Forest DS tokens)
│       │
│       ├── css/forest/                # Forest Design System (8 CSS modules)
│       │
│       ├── environments/              # Variables de entorno
│       │   ├── environment.ts         # Configuracion desarrollo
│       │   └── environment.prod.ts    # Configuracion produccion
│       │
│       ├── assets/                    # Recursos estaticos
│       │
│       └── app/                       # Codigo Angular
│           │
│           ├── app.component.ts       # Componente raiz (standalone)
│           ├── app.routes.ts          # Definicion de rutas
│           │
│           ├── models/                # Interfaces TypeScript (14 interfaces)
│           │   └── interfaces.ts      # Prediction, CityStats, Tile, Amenity, etc.
│           │
│           ├── services/              # Servicios (refactored from God Object)
│           │   ├── api.service.ts     # Thin facade (130 LOC)
│           │   ├── cache.service.ts   # Cache management
│           │   ├── supabase.service.ts # Supabase operations
│           │   ├── ml-api.service.ts  # ML API calls
│           │   ├── n8n.service.ts     # n8n webhook calls
│           │   ├── circuit-breaker.service.ts # Circuit breaker pattern
│           │   ├── analytics.service.ts # Event tracking
│           │   └── logger.service.ts  # Secure logging
│           │
│           ├── guards/                # HTTP interceptors
│           │   └── rate-limit.interceptor.ts  # 60 req/min + deduplication
│           │
│           ├── validators/            # Input validation
│           │   ├── file-validator.ts   # 5MB max, CSV only, content sniffing
│           │   └── input-sanitizer.ts  # XSS, SQL injection, Unicode normalization
│           │
│           ├── pages/                 # Paginas
│           │   └── mapa/              # Pagina principal del mapa
│           │       ├── mapa.component.ts
│           │       ├── mapa.component.html
│           │       ├── mapa.component.css
│           │       └── mapa.component.spec.ts  # 42 tests
│           │
│           └── components/            # Componentes reutilizables (8+)
│               ├── file-upload/
│               ├── filters-panel/
│               ├── stats-dashboard/
│               ├── ai-chatbot/
│               ├── address-search/
│               ├── advanced-filters/
│               ├── export-reports/
│               └── skeleton-loader/   # 5 tipos de skeleton
│
├── python_services/                   # Backend Python (FastAPI)
│   │
│   ├── api/                           # API REST endpoints
│   │   └── main.py                    # FastAPI app (health, predictions, tasks, metrics)
│   │
│   ├── ml_model/                      # Machine Learning
│   │   ├── predictor.py               # ML Model V2 (19-30 features, R²=0.76)
│   │   └── monitoring/                # Model monitoring
│   │       ├── drift_detector.py      # KS test + PSI drift detection
│   │       └── model_card.md          # Model Card v1.0
│   │
│   ├── middleware/                     # Middleware
│   │   ├── security.py                # 4 security middlewares (headers, size, content-type, rate limit)
│   │   └── circuit_breaker.py         # Python CircuitBreakerRegistry
│   │
│   ├── scrapers/                      # Web scrapers
│   ├── integrations/                  # INEGI, OSM integrations
│   │
│   ├── celery_app.py                  # Celery config + tasks (3 queues: default, ml, enrichment)
│   ├── config.py                      # Configuracion
│   ├── Dockerfile                     # Multi-stage, non-root user (appuser uid 1001)
│   ├── .env.example                   # Template seguro sin credenciales
│   ├── requirements.txt               # Dependencias Python
│   │
│   └── tests/                         # Python tests
│       ├── test_predictor.py
│       ├── test_api.py
│       └── conftest.py
│
├── data/                              # Datos reales (193K registros)
│   ├── properati/                     # 120K Properati listings
│   ├── catastro/                      # 80K CDMX Catastro records
│   ├── sniiv/                         # 3.8K SNIIV/SEDATU records
│   ├── bis/                           # 150 BIS index records
│   └── samples/
│       └── comparables_demo.csv       # CSV de ejemplo (10 propiedades)
│
├── scripts/                           # Scripts operacionales
│   ├── backup.sh                      # Backup (db, models, config; 30-day retention)
│   ├── rollback.sh                    # Rollback con health check
│   ├── load-test.js                   # k6 load testing
│   └── data_pipeline.py              # Pipeline: validate → train → evaluate → register
│
├── scripts_sql/                       # Scripts SQL (17+)
│   └── 17_reenable_rls_ml_tables.sql  # RLS re-enabled + 12 policies
│
├── monitoring/                        # Observabilidad
│   ├── prometheus.yml                 # Scrape config
│   ├── alerting-rules.yml             # 5 alertas (error rate, latency, restart, disk, memory)
│   └── grafana/
│       └── dashboards/
│           └── api-overview.json      # Dashboard 4 paneles
│
├── security/                          # Seguridad
│   ├── security-headers.conf          # CSP, HSTS, X-Frame-Options
│   ├── dependency-audit.sh            # npm audit + pip-audit + secret scanning
│   └── SECURITY_CHECKLIST.md          # 15-item pre-deploy checklist
│
├── docs/                              # Documentacion
│   ├── api/
│   │   └── API_REFERENCE.md           # Documentacion completa de API endpoints
│   ├── sla/
│   │   └── SLA_SLO.md                # SLOs, error budgets, metricas
│   ├── runbooks/
│   │   └── incident-response.md       # Runbook P1-P4 + post-mortem template
│   ├── security/
│   │   └── credential-rotation.md     # Credential rotation procedures
│   ├── README_supabase.md             # Configuracion de Supabase
│   └── N8N_WEBHOOKS.md                # Configuracion de webhooks
│
├── .github/                           # GitHub CI/CD
│   ├── workflows/
│   │   ├── ci.yml                     # 7 jobs: lint FE/BE, test FE/BE, security scan, build FE, build Docker
│   │   └── deploy.yml                 # Deploy frontend + backend con auto-rollback
│   └── CODEOWNERS                     # Auto-review requests
│
├── .nxt/                              # NXT Framework state
│   ├── state.json                     # Estado persistente del proyecto
│   ├── scores.json                    # Scorecard (12 areas, 41 metricas)
│   └── context/
│       └── session-context.json       # Contexto de sesion con ADRs
│
├── docker-compose.production.yml      # Full stack: API (2 replicas), Traefik, Prometheus, Grafana, Redis, Celery, Flower
│
└── n8n_workflows/                     # Workflows de n8n
    └── FAVIER_AI_SYSTEM_PROMPT.md     # System prompt con prompt versioning

```

---

## Archivos Clave

### Configuracion

| Archivo | Proposito |
|---------|-----------|
| `app/package.json` | Dependencias frontend (Angular, Tailwind, Leaflet, Supabase, Cypress) |
| `app/angular.json` | Configuracion Angular CLI (lint + test targets) |
| `app/tailwind.config.js` | Tailwind CSS + Forest DS colors + font families |
| `app/tsconfig.json` | TypeScript (strict: true, noImplicitReturns, strictTemplates) |
| `app/.eslintrc.json` | ESLint (no-explicit-any = error) |
| `python_services/requirements.txt` | Dependencias Python (FastAPI, Celery, Redis, sklearn, XGBoost, SHAP) |
| `python_services/celery_app.py` | Celery config + task definitions (3 queues) |
| `docker-compose.production.yml` | Full stack Docker (API, Redis, Celery, Prometheus, Grafana, Flower) |

### Servicios Frontend (Refactored)

| Servicio | Proposito |
|----------|-----------|
| `api.service.ts` | Thin facade (130 LOC) — delegates to specialized services |
| `cache.service.ts` | Cache management |
| `supabase.service.ts` | Supabase CRUD operations |
| `ml-api.service.ts` | ML API calls (predict, train, explain) |
| `n8n.service.ts` | n8n webhook calls |
| `circuit-breaker.service.ts` | Circuit breaker (CLOSED/OPEN/HALF_OPEN) |
| `analytics.service.ts` | Event tracking (page views, actions, performance) |
| `logger.service.ts` | Secure logging (sanitization, production mode) |

### Componentes

| Componente | Proposito |
|------------|-----------|
| `MapaComponent` | Mapa principal con Leaflet, heatmap y clusters |
| `FileUploadComponent` | Subida de archivos CSV (5MB max, CSV only) |
| `FiltersPanelComponent` | Filtros geograficos, tipos de amenidad, acciones |
| `StatsDashboardComponent` | Dashboard de estadisticas por ciudad |
| `AiChatbotComponent` | Chatbot Favier AI integrado |
| `AddressSearchComponent` | Busqueda por direccion |
| `AdvancedFiltersComponent` | Filtros avanzados |
| `ExportReportsComponent` | Exportacion CSV/JSON |
| `SkeletonLoaderComponent` | Loading skeletons (5 tipos) |

### API Endpoints Principales

| Endpoint | Proposito |
|----------|-----------|
| `GET /health` | Health check (DB, Redis, memory, disk, model) |
| `GET /metrics` | Prometheus metrics |
| `POST /predictions/predict` | Prediccion ML (API Key required) |
| `POST /predictions/train` | Entrenamiento ML (API Key required) |
| `POST /predictions/explain` | SHAP explainability (API Key required) |
| `GET /predictions/heatmap` | Heatmap data |
| `GET /predictions/drift-status` | Drift detection status |
| `GET /predictions/bias-report` | Bias evaluation report |
| `GET /predictions/models/registry` | Model registry |
| `POST /tasks/train` | Async training via Celery |
| `POST /tasks/enrich` | Async enrichment via Celery |
| `GET /tasks/status/{id}` | Task status |
| `GET /tasks/redis-status` | Redis connection status |

### Documentacion

| Archivo | Proposito |
|---------|-----------|
| `README.md` | Documentacion principal del proyecto |
| `CHANGELOG.md` | Historial de versiones |
| `INSTALL.md` | Guia de instalacion paso a paso |
| `ESTRUCTURA.md` | Este archivo (mapa visual) |
| `CONTRIBUTING.md` | Code style, branch naming, commit format, PR process |
| `docs/api/API_REFERENCE.md` | Referencia completa de API |
| `docs/sla/SLA_SLO.md` | SLOs, error budgets, metricas |
| `docs/runbooks/incident-response.md` | Runbook P1-P4 |
| `docs/security/credential-rotation.md` | Rotacion de credenciales |

---

## Flujo de Datos

```
┌─────────────────┐
│   Usuario Web   │
└────────┬────────┘
         │
         ↓
┌──────────────────────────────────────────────┐
│        Angular Frontend (geo-app)            │
│  ┌────────────────────────────────────────┐  │
│  │  Services (refactored facade pattern)  │  │
│  │  ApiService → CacheService             │  │
│  │             → SupabaseService           │  │
│  │             → MlApiService              │  │
│  │             → N8nService                │  │
│  │  + CircuitBreakerService               │  │
│  │  + RateLimitInterceptor                │  │
│  └────────────────────────────────────────┘  │
└──────┬────────────┬───────────┬──────────────┘
       │            │           │
       ↓            ↓           ↓
┌────────────┐ ┌─────────┐ ┌──────────────────────────┐
│  Supabase  │ │  n8n    │ │  FastAPI Backend (:8001)  │
│ PostgreSQL │ │         │ │                            │
│            │ │ Chatbot │ │  /predict  (API Key)       │
│ 12+ tables │ │ Webhooks│ │  /train    (API Key)       │
│ 193K rows  │ │ AI Agent│ │  /explain  (API Key)       │
│ RLS + Audit│ │         │ │  /metrics  (Prometheus)    │
│            │ │         │ │  /tasks/*  (Celery)        │
└────────────┘ └─────────┘ │  /health   (full check)   │
                           └──────┬───────┬────────────┘
                                  │       │
                                  ↓       ↓
                           ┌──────────┐ ┌──────────────┐
                           │  Redis 7 │ │ Celery       │
                           │          │ │ Workers      │
                           │ • Cache  │ │              │
                           │ • Rate   │ │ Q: default   │
                           │   Limit  │ │ Q: ml        │
                           │ • TTL    │ │ Q: enrichment│
                           └──────────┘ │              │
                                        │ + Beat (6h   │
                                        │   drift, 1w  │
                                        │   baseline)  │
                                        │ + Flower UI  │
                                        └──────────────┘

Data Sources (193K records):
  • Properati       — 120K listings
  • CDMX Catastro   — 80K records
  • SNIIV/SEDATU    — 3.8K records
  • BIS Index       — 150 records
  • INEGI Census    — 81 city demographic profiles
```

---

## Stack Tecnologico Completo

### Frontend
- **Framework:** Angular 17 (Standalone Components)
- **UI:** Tailwind CSS 3.x + Forest Design System (glassmorphism, Apple-style animations)
- **Fonts:** Sora (display), DM Sans (body), JetBrains Mono (code)
- **Mapas:** Leaflet 1.9.x (leaflet.heat + leaflet.markercluster)
- **HTTP:** Supabase JS Client + HttpClient con interceptors
- **Testing:** Karma + Jasmine (364 unit tests) + Cypress (13 E2E tests)
- **TypeScript:** strict mode, zero `any` types

### Backend
- **Runtime:** Python 3.11 + FastAPI + Uvicorn
- **ML:** scikit-learn + XGBoost (RandomForest + GradientBoosting ensemble, R²=0.76)
- **Explainability:** SHAP 0.45.1
- **Cache:** Redis 7 (distributed cache + rate limiting)
- **Task Queue:** Celery 5 + Celery Beat (3 queues: default, ml, enrichment)
- **Monitoring:** Prometheus + Grafana + Flower

### Base de Datos
- **Supabase:** PostgreSQL managed (12+ tables, RLS, audit logs, 193K records)
- **Data Sources:** Properati, CDMX Catastro, SNIIV/SEDATU, BIS Index, INEGI Census 2020

### Servicios
- **ETL/Webhooks:** n8n (self-hosted)
- **AI Chat:** OpenAI via n8n (Favier AI, prompt versioning)
- **Datos Geoespaciales:** OpenStreetMap (Nominatim + Overpass API)

### DevOps
- **CI/CD:** GitHub Actions (7-job CI + deploy with auto-rollback)
- **Containers:** Docker + Docker Compose (multi-stage, non-root user)
- **Proxy:** Traefik
- **Hosting:** Hostinger VPS
- **Runtime:** Node.js 22+

---

## Caracteristicas Implementadas

### Core
- Mapa interactivo con Leaflet + heatmap + clusters
- Predicciones ML con 19-30 features reales (R²=0.76)
- SHAP explainability por prediccion
- Chatbot AI (Favier AI) con prompt versioning
- Dashboard de estadisticas (81 ciudades INEGI)
- Exportacion CSV/JSON
- Busqueda por direccion

### Data
- 193K registros reales de 4 fuentes
- 12+ tablas en Supabase
- 81 perfiles demograficos INEGI Census 2020
- Real Haversine distance con 50+ coordenadas de ciudades
- Data pipeline automatizado (validate, train, evaluate, register)

### Infrastructure
- Redis 7 (cache distribuido + rate limiting)
- Celery (3 queues) + Celery Beat (drift 6h, baseline semanal, cache cleanup diario)
- Prometheus /metrics + Grafana dashboards
- Flower UI para monitoreo de tasks
- Docker Compose full stack

### Security
- API Key authentication en endpoints sensibles
- Audit logs con triggers en 4 tablas
- Rate limiting Redis sorted sets (1-100 req/min por endpoint)
- RLS service_role only para escrituras
- Input validation + sanitization (frontend + backend)
- Circuit breaker (frontend TS + backend Python)
- OWASP dependency check en CI

### Testing & CI/CD
- 364 unit tests (Karma + Jasmine)
- 13 E2E tests (Cypress)
- 30+ Python tests
- GitHub Actions CI (7 jobs) + Deploy con auto-rollback
- k6 load testing

---

**Generado:** Marzo 2026
**Version:** 3.0

