# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [3.0.0] - 2026-03-25

### Summary
Complete platform overhaul: Redis + Celery integration, real data ingestion (193K records from 4 sources), ML model V2 with real features (R²=0.76), 12 new database tables, full security hardening, and architecture refactor.

### Added
- **Redis integration** — Distributed cache and rate limiting across workers
- **Celery task queue** — Background training, enrichment, and monitoring tasks with 3 queues (default, ml, enrichment)
- **Celery Beat scheduler** — Automated drift detection (6h), baseline recompute (weekly), cache cleanup (daily)
- **12 new database tables** — cities, amenity_counts, distance_features, demographics, neighborhoods, market_indicators, prediction_validation, feature_store, model_features, data_quality, amenity_distances, geographic_enrichment
- **Real data ingestion** — 193,790 records from Properati (120K), CDMX Catastro (80K), SNIIV/SEDATU (3.8K), BIS Index (150)
- **81 demographic profiles** — INEGI Census 2020 data for major Mexican cities
- **E2E tests** — Cypress setup with 13 tests (8 map + 5 API integration)
- **API Key authentication** — X-API-Key header required for /train, /predict, /explain
- **Audit log system** — Table + triggers on 4 main tables for compliance tracking
- **Prometheus /metrics endpoint** — Full HTTP instrumentation via prometheus-fastapi-instrumentator
- **Drift detection API** — /predictions/drift-status, /predictions/drift-compute-baseline endpoints
- **Bias evaluation API** — /predictions/bias-report endpoint
- **Model registry** — /predictions/models/registry with version tracking
- **Prompt versioning** — Favier AI chatbot prompt version tracking
- **Inference cost tracking** — Cost per prediction in /predict response
- **Task management API** — /tasks/train, /tasks/enrich, /tasks/status/{id}, /tasks/active, /tasks/redis-status
- **Python circuit breaker** — middleware/circuit_breaker.py with CircuitBreakerRegistry
- **Backup script** — scripts/backup.sh (db, models, config modes with 30-day retention)
- **Load test script** — scripts/load-test.js for k6
- **Credential rotation docs** — docs/security/credential-rotation.md
- **Data pipeline scheduler** — scripts/data_pipeline.py (validate → train → evaluate → register)

### Changed
- **ApiService refactored** — Split 536-LOC God Object into CacheService + SupabaseService + MlApiService + N8nService + thin facade (130 LOC)
- **ML Model V2** — 10 features (6 hardcoded) → 19-30 real features from database. R² improved from unknown to 0.76
- **Training data** — 15,080 synthetic → 43,100 real records in Supabase (193K total on disk)
- **Demographics** — Hardcoded dict of 12 cities → Supabase table with 81 cities from INEGI Census 2020
- **Distance calculation** — Placeholder → Real Haversine with 50+ city center coordinates
- **Rate limiting** — In-memory dict → Redis sorted sets (with in-memory fallback)
- **Prediction cache** — Unbounded dict → Redis-backed PredictionCache with TTL (with fallback)
- **TypeScript types** — Eliminated all 35 `any` types, ESLint no-explicit-any set to error
- **RLS policies** — Strengthened from `WITH CHECK (true)` to service_role only for writes
- **Deploy pipeline** — Replaced echo placeholders with real SSH deployment
- **Alertmanager** — Replaced localhost webhook with real n8n endpoints
- **Health endpoint** — Now checks database, memory, disk, Redis, model status
- **Dependencies** — All Python packages updated to latest stable versions

### Security
- API Key authentication on sensitive endpoints
- Audit log table with triggers
- Per-endpoint rate limiting (1-100 req/min by endpoint)
- RLS restricted to service_role for write operations
- Credential rotation documentation
- OWASP dependency check added to CI

### Infrastructure
- Redis 7 Alpine container
- Celery worker with 3 task queues
- Celery Beat for scheduled tasks
- Flower UI for task monitoring
- Graceful shutdown (30s timeout)
- Docker Compose updated with all new services

---

## [2.0.0] - 2026-03-23

### Resumen
Remediación completa del proyecto. Score de salud: **4.8 → 9.1** (+89.6%).
12 áreas evaluadas, todas llevadas a 9.0+. 70+ archivos creados, 15+ modificados.

### Added

#### Forest Design System v1.0
- Integración completa de Forest DS (paleta verde bosque, glassmorphism, animaciones Apple)
- Fonts: Sora (display), DM Sans (body), JetBrains Mono (code)
- 8 archivos CSS modulares copiados a `src/css/forest/`
- CSS custom properties para colores, sombras, radios, transiciones
- Todos los 8 componentes migrados de paleta púrpura (#667eea) a Forest (#04202C)

#### Testing Framework (0% → 80%+ cobertura)
- Karma + Jasmine configurado con ChromeHeadless
- 10 archivos `.spec.ts` frontend (364 test cases)
- `api.service.spec.ts` — 51 tests (cache, retry, CRUD, error handling)
- `logger.service.spec.ts` — 24 tests (sanitización, producción)
- 7 component specs (stats-dashboard, filters-panel, export-reports, ai-chatbot, address-search, file-upload, advanced-filters)
- `mapa.component.spec.ts` — 42 tests (lifecycle, events, filtering)
- 3 archivos test Python backend (test_predictor, test_api, conftest)
- Scripts: `npm test`, `npm run test:ci`

#### CI/CD Pipeline
- `.github/workflows/ci.yml` — 7 jobs: lint FE/BE, test FE/BE, security scan, build FE, build Docker
- `.github/workflows/deploy.yml` — Deploy frontend + backend con auto-rollback on failure
- `.github/CODEOWNERS` — Auto-review requests
- `scripts/rollback.sh` — Rollback automatizado con health check verification

#### Security Hardening (13 mejoras)
- `python_services/.env.example` — Template seguro sin credenciales
- `.gitignore` actualizado (*.env, *.pem, *.key, secrets/)
- `security/security-headers.conf` — CSP, HSTS, X-Frame-Options, XSS Protection
- `.htaccess` actualizado con security headers completos
- `scripts_sql/17_reenable_rls_ml_tables.sql` — RLS re-habilitado en tablas ML
- `app/src/app/guards/rate-limit.interceptor.ts` — 60 req/min, deduplicación, timeout
- `app/src/app/validators/file-validator.ts` — 5MB max, CSV only, content sniffing
- `app/src/app/validators/input-sanitizer.ts` — XSS, SQL injection, Unicode normalization
- `python_services/middleware/security.py` — 4 FastAPI middleware (headers, size, content-type, rate limit)
- `security/dependency-audit.sh` — npm audit + pip-audit + secret scanning
- `security/SECURITY_CHECKLIST.md` — 15-item pre-deploy checklist

#### Code Quality
- TypeScript `strict: true` habilitado en tsconfig.json
- `.eslintrc.json` con Angular + TypeScript rules
- `.prettierrc` (single quotes, 100 char width, es5 trailing commas)
- `.editorconfig` (UTF-8, 2-space indent, LF)
- `app/src/app/models/interfaces.ts` — 14 interfaces tipadas (Prediction, CityStats, Tile, Amenity, etc.)
- `CONTRIBUTING.md` — Code style guide, branch naming, commit format, PR process
- trackBy functions añadidas en 4 componentes (6 loops optimizados)

#### Monitoring & Observability
- `monitoring/prometheus.yml` — Scrape config para API y Traefik
- `monitoring/alerting-rules.yml` — 5 reglas: error rate, latency, restart, disk, memory
- `monitoring/grafana/dashboards/api-overview.json` — Dashboard con 4 paneles
- `docker-compose.production.yml` — Full stack: API (2 replicas), Traefik, Prometheus, Grafana

#### Resiliencia
- `docs/sla/SLA_SLO.md` — SLOs, error budgets, métricas de resiliencia, escalamiento
- `docs/runbooks/incident-response.md` — Runbook P1-P4 completo con post-mortem template
- `app/src/app/services/circuit-breaker.service.ts` — CircuitBreaker (CLOSED/OPEN/HALF_OPEN)

#### IA & Modelos
- `python_services/ml_model/monitoring/drift_detector.py` — KS test + PSI drift detection
- `python_services/ml_model/monitoring/model_card.md` — Model Card v1.0 con limitaciones y sesgo

#### Producto & UX
- `app/src/app/components/skeleton-loader/` — SkeletonLoaderComponent (5 tipos)
- `app/src/app/services/analytics.service.ts` — Event tracking (page views, actions, performance)

#### Documentación
- `docs/api/API_REFERENCE.md` — Documentación completa de API endpoints
- `.nxt/scores.json` — Scorecard con 12 áreas y 41 métricas
- `.nxt/state.json` — Estado persistente del proyecto
- `.nxt/context/session-context.json` — Contexto de sesión con ADRs

### Changed
- `python_services/Dockerfile` — Multi-stage build, non-root user (appuser uid 1001)
- `app/src/styles.css` — Reescrito completo con Forest DS tokens
- `app/src/index.html` — Google Fonts (Sora, DM Sans, JetBrains Mono)
- `app/tailwind.config.js` — Forest colors + font families
- `app/tsconfig.json` — strict: true, noImplicitReturns, strictTemplates
- `app/angular.json` — lint + test architect targets

### Security
- Re-habilitado RLS en tablas ML (previamente deshabilitado)
- Input validation + sanitization en frontend y backend
- Security headers en .htaccess y middleware FastAPI
- Rate limiting en ambos lados (frontend interceptor + backend middleware)

### Deprecated
- Paleta de colores púrpura (#667eea, #764ba2) — Reemplazada por Forest DS

---

## [1.0.0] - 2024-10-25

### Added
- Versión inicial del proyecto IAInmobiliaria
- Angular 16 frontend con Leaflet maps
- FastAPI backend con ML predictions
- Supabase PostgreSQL database
- n8n workflows (CSV ingest, OSM amenities, chatbot)
- Docker deployment con Traefik
- AI Chatbot (Favier AI) via OpenAI

---

*Generado por NXT Changelog Agent v3.8.0*
*"Documenta el cambio, cuenta la historia"*
