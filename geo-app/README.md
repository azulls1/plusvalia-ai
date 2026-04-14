# Analisis de Mercado Inmobiliario - Sistema Completo

**Sistema profesional de analisis de mercado inmobiliario con Machine Learning, predicciones de plusvalia y chatbot AI.**

**Version:** 3.0.0 | **Ultima actualizacion:** 2026-03-25

---

## Que es este proyecto?

Un sistema completo que combina:
- **Mapa Interactivo** con heatmap de predicciones ML
- **Chatbot AI** (Favier AI) para consultas inmobiliarias
- **Predicciones de Plusvalia** basadas en Machine Learning (R²=0.76)
- **Datos Reales** — 193K registros de 4 fuentes (Properati, CDMX Catastro, SNIIV/SEDATU, BIS)
- **Task Queue** — Entrenamiento y enriquecimiento en background con Celery
- **Sistema Asegurado** — API Key auth, audit logs, rate limiting, RLS

---

## Inicio Rapido

### 1. Iniciar Redis
```bash
docker run -d --name geo-redis -p 6379:6379 redis:7-alpine
```

### 2. Iniciar Backend
```bash
cd python_services && python -m uvicorn api.main:app --port 8001 --reload
```

### 3. Iniciar Celery Worker
```bash
cd python_services && python -m celery -A celery_app worker --loglevel=info --pool=solo -Q default,ml,enrichment
```

### 4. Iniciar Frontend
```bash
cd app && npm start
```

### 5. Abrir Navegador
http://localhost:4200

**Ver:** `INICIO_RAPIDO.md` para guia detallada

---

## Documentacion Completa

| Documento | Descripcion |
|-----------|-------------|
| **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** | Guia de 5 minutos para arrancar |
| **[GUIA_SEGURIDAD_COMPLETA.md](GUIA_SEGURIDAD_COMPLETA.md)** | Detalles tecnicos de seguridad |
| **[INSTRUCCIONES_DESPLIEGUE.md](INSTRUCCIONES_DESPLIEGUE.md)** | Despliegue a produccion |
| **[RESUMEN_SEGURIDAD_Y_LIMPIEZA.md](RESUMEN_SEGURIDAD_Y_LIMPIEZA.md)** | Resumen ejecutivo de mejoras |
| **[COMPLETADO_EXITOSAMENTE.md](COMPLETADO_EXITOSAMENTE.md)** | Estado final del proyecto |
| **[docs/security/credential-rotation.md](docs/security/credential-rotation.md)** | Rotacion de credenciales |
| **[docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)** | Referencia completa de API |

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                   USUARIO FINAL                      │
│           (Navegador Web - localhost:4200)           │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│              FRONTEND (Angular 17)                   │
│  • Mapa Interactivo (Leaflet)                       │
│  • Chatbot Favier AI                                │
│  • Dashboard de Estadisticas                        │
│  • Componentes de Filtros                           │
│  • Forest Design System (glassmorphism)             │
└────────────────┬────────────────────────────────────┘
                 │
                 ├──────────────┬──────────────┬──────────────┐
                 ▼              ▼              ▼              ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Backend Python  │  │  Redis 7     │  │  n8n AI      │  │  Supabase    │
│  (FastAPI:8001)  │  │              │  │  Workflows   │  │  PostgreSQL  │
│                  │  │  • Cache     │  │              │  │              │
│  • ML Model V2   │  │  • Rate Lim  │  │  • Chatbot   │  │  • 193K rows │
│  • Predicciones  │  │  • Sessions  │  │  • Webhooks  │  │  • 12+ tablas│
│  • /metrics      │  │              │  │  • AI Agent  │  │  • RLS + Auth│
│  • API Key Auth  │  └──────────────┘  └──────────────┘  │  • Audit Log │
│  • Circuit Break │                                      └──────────────┘
└────────┬─────────┘
         │
         ▼
┌──────────────────┐  ┌──────────────┐
│  Celery Workers  │  │  Celery Beat │
│                  │  │              │
│  • Q: default    │  │  • Drift 6h  │
│  • Q: ml         │  │  • Baseline  │
│  • Q: enrichment │  │    weekly    │
│                  │  │  • Cache     │
│  + Flower UI     │  │    cleanup   │
└──────────────────┘  └──────────────┘
```

---

## Tecnologias Utilizadas

### Frontend:
- **Angular 17** — Framework principal
- **TypeScript** (strict mode) — Lenguaje, zero `any` types
- **Leaflet** — Mapas interactivos + heatmaps + clusters
- **Tailwind CSS 3** + **Forest Design System** — UI/UX
- **Cypress** — E2E testing (13 tests)

### Backend:
- **Python 3.11** — Lenguaje
- **FastAPI** — API REST
- **Uvicorn** — Servidor ASGI
- **Pandas** — Analisis de datos
- **Scikit-learn + XGBoost** — Machine Learning (R²=0.76)
- **SHAP** — Explainability

### Cache:
- **Redis 7** — Distributed cache + rate limiting

### Task Queue:
- **Celery 5** + **Celery Beat** — Background ML training, enrichment
- **Flower** — Task monitoring UI

### Base de Datos:
- **Supabase** — PostgreSQL gestionado (12+ tablas, RLS, audit logs)
- **PostgREST** — API REST automatica

### Monitoring:
- **Prometheus** + **Grafana** — Metricas y dashboards
- **Flower** — Celery task monitoring

### Workflows:
- **n8n** — Automatizacion y chatbot
- **OpenAI** — AI Agent para chatbot

---

## Seguridad Implementada

| Proteccion | Estado | Descripcion |
|------------|--------|-------------|
| **API Key Authentication** | Activo | X-API-Key en /train, /predict, /explain |
| **CORS Restringido** | Activo | Solo dominios especificos |
| **Rate Limiting (Redis)** | Activo | 1-100 req/min por endpoint (Redis sorted sets) |
| **Audit Logs** | Activo | Tabla + triggers en 4 tablas principales |
| **RLS Policies** | Activo | service_role only para escrituras |
| **Input Validation** | Activo | Frontend (sanitizer) + Backend (FastAPI) |
| **Variables de Entorno** | Activo | Credenciales en `.env` |
| **Circuit Breaker** | Activo | Frontend (TS) + Backend (Python) |
| **OWASP Dep Check** | Activo | En CI pipeline |
| **Credential Rotation** | Documentado | docs/security/credential-rotation.md |

**Ver:** `GUIA_SEGURIDAD_COMPLETA.md` para detalles

---

## Caracteristicas Principales

### Mapa Interactivo
- Visualizacion de predicciones ML con heatmap
- Click para ver predicciones cercanas
- Filtros por ciudad, score, riesgo
- Busqueda por direccion
- Clusters de marcadores

### Chatbot Favier AI
- Asistente inmobiliario inteligente
- Consultas en lenguaje natural
- Recomendaciones personalizadas
- Prompt versioning integrado

### Predicciones ML (Model V2)
- 19-30 features reales desde base de datos
- Precio por m2 predicho (R²=0.76)
- Score de plusvalia (0-100)
- SHAP explainability por prediccion
- Inference cost tracking
- Drift detection automatico (cada 6h)
- Bias evaluation report

### Task Queue (Celery)
- Entrenamiento ML en background
- Enriquecimiento geografico asincrono
- Monitoreo via Flower UI
- Status tracking por task ID

### Dashboard
- Estadisticas por ciudad (81 ciudades con datos INEGI)
- Graficos interactivos
- Exportacion a CSV/JSON
- Top 10 inversiones

---

## Estructura del Proyecto

```
geo-app/
│
├── python_services/           # Backend Python (FastAPI)
│   ├── api/                  # API REST endpoints
│   ├── ml_model/             # Modelos ML + monitoring (drift, model card)
│   ├── middleware/            # Security, rate limiting, circuit breaker
│   ├── scrapers/             # Web scrapers
│   ├── integrations/         # INEGI, OSM
│   ├── celery_app.py         # Celery config + task definitions
│   ├── config.py             # Configuracion
│   ├── .env                  # Credenciales (NO en Git)
│   └── requirements.txt      # Dependencias
│
├── app/                       # Frontend Angular
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/   # Componentes UI (8+)
│   │   │   ├── pages/        # Paginas
│   │   │   ├── services/     # CacheService, SupabaseService, MlApiService, N8nService
│   │   │   ├── guards/       # Rate limit interceptor
│   │   │   ├── validators/   # File validator, input sanitizer
│   │   │   └── models/       # 14 interfaces tipadas
│   │   └── environments/     # Configuracion
│   ├── cypress/              # E2E tests (13 tests)
│   └── package.json          # Dependencias
│
├── data/                      # Datos reales (193K registros)
│   ├── properati/            # 120K listings
│   ├── catastro/             # 80K CDMX records
│   ├── sniiv/                # 3.8K SEDATU records
│   └── bis/                  # 150 BIS index records
│
├── scripts/                   # Operaciones
│   ├── backup.sh             # Backup (db, models, config)
│   ├── load-test.js          # k6 load testing
│   ├── data_pipeline.py      # Data pipeline scheduler
│   └── rollback.sh           # Rollback con health check
│
├── scripts_sql/              # Scripts de base de datos (17+)
├── monitoring/               # Prometheus, Grafana, alertas
├── security/                 # Headers, audit scripts
├── docs/                     # API reference, SLA, runbooks, security
├── .github/workflows/        # CI (7 jobs) + Deploy pipeline
├── docker-compose.production.yml  # Full stack + Redis + Celery
│
├── CHANGELOG.md              # Historial de versiones
├── INICIO_RAPIDO.md          # Guia rapida
├── GUIA_SEGURIDAD_COMPLETA.md    # Seguridad
├── INSTRUCCIONES_DESPLIEGUE.md   # Despliegue
└── README.md                 # Este archivo
```

---

## Testing

### Backend:
```bash
# Health check (checks DB, Redis, memory, disk, model)
curl http://localhost:8001/health

# Prometheus metrics
curl http://localhost:8001/metrics

# Ver documentacion interactiva
http://localhost:8001/docs

# Test de predicciones
curl http://localhost:8001/predictions/heatmap?limit=10

# Python unit tests
cd python_services && python -m pytest tests/
```

### Frontend:
```bash
# Unit tests (364 test cases)
cd app && npm test

# E2E tests (13 Cypress tests)
cd app && npx cypress run
```

### Load Testing:
```bash
k6 run scripts/load-test.js
```

---

## 🚀 DESPLIEGUE A PRODUCCIÓN

### Backend:
- **Railway.app** (Recomendado)
- **DigitalOcean App Platform**
- **VPS (Ubuntu/Debian)**

### Frontend:
- **Vercel** (Recomendado)
- **Netlify**
- **Firebase Hosting**

**Ver:** `INSTRUCCIONES_DESPLIEGUE.md` para paso a paso completo

---

## Requisitos

### Backend:
- Python 3.11+
- pip
- Virtualenv (recomendado)

### Frontend:
- Node.js 18+
- npm
- Angular CLI (`npm install -g @angular/cli`)

### Infraestructura:
- Docker + Docker Compose
- Redis 7 (o Docker: `redis:7-alpine`)

### Base de Datos:
- Cuenta en Supabase
- PostgreSQL 14+

### Workflows:
- Instancia de n8n
- API key de OpenAI

---

## 📝 CONFIGURACIÓN INICIAL

### 1. Backend:
```bash
cd python_services
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

pip install -r requirements.txt

# Crear .env (usar credenciales reales)
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Frontend:
```bash
cd app
npm install
```

### 3. Base de Datos:
- Ejecutar scripts SQL en `scripts_sql/`
- Configurar RLS en Supabase
- Obtener API keys

### 4. n8n:
- Importar workflow
- Configurar credenciales de Supabase
- Configurar API key de OpenAI
- Activar workflow

**Ver:** `INSTRUCCIONES_DESPLIEGUE.md` para detalles completos

---

## 🆘 PROBLEMAS COMUNES

### "Variables de entorno faltantes"
**Solución:** Crear archivo `.env` en `python_services/`

### "CORS policy error"
**Solución:** Verificar backend esté corriendo y `ALLOWED_ORIGINS` en `.env`

### "Chatbot no responde"
**Solución:** Verificar n8n workflow esté activo (no en test mode)

### "Mapa no carga"
**Solución:** Verificar conexión a internet y limpiar cache del navegador

**Ver:** `INICIO_RAPIDO.md` → Sección "SOLUCIÓN RÁPIDA DE PROBLEMAS"

---

## Estado del Proyecto

| Componente | Estado | Version |
|------------|--------|---------|
| **Backend API** | Funcional | 3.0.0 |
| **Frontend** | Funcional | 3.0.0 |
| **Chatbot AI** | Funcional | 3.0.0 |
| **ML Model V2** | Entrenado (R²=0.76) | 3.0.0 |
| **Redis Cache** | Funcional | 7-alpine |
| **Celery Workers** | Funcional | 5.x |
| **Data Ingestion** | 193K registros | 3.0.0 |
| **Seguridad** | API Key + Audit + RLS | 3.0.0 |
| **Monitoring** | Prometheus + Grafana | 3.0.0 |
| **E2E Tests** | 13 Cypress tests | 3.0.0 |
| **Produccion** | Listo | 3.0.0 |

---

## 👥 EQUIPO

- **Desarrollo:** Sistema completo
- **ML Model:** Predicciones de plusvalía
- **Chatbot:** Favier AI con n8n + OpenAI
- **Seguridad:** Implementación completa

---

## 📜 LICENCIA

Este proyecto es propietario. Todos los derechos reservados.

---

## 🔗 ENLACES ÚTILES

| Recurso | URL |
|---------|-----|
| **Frontend Local** | http://localhost:4200 |
| **Backend API** | http://localhost:8001 |
| **API Docs** | http://localhost:8001/docs |
| **Prometheus Metrics** | http://localhost:8001/metrics |
| **Flower (Celery)** | http://localhost:5555 |
| **Supabase** | https://iagenteksupabase.iagentek.com.mx |
| **n8n Webhook** | https://iagentekn8nwebhook.iagentek.com.mx |

---

## 📞 SOPORTE

Para problemas o preguntas:
1. Ver `INICIO_RAPIDO.md` para soluciones rápidas
2. Consultar `GUIA_SEGURIDAD_COMPLETA.md` para detalles técnicos
3. Revisar `INSTRUCCIONES_DESPLIEGUE.md` para despliegue
4. Contactar al equipo de desarrollo

---

## 🎉 AGRADECIMIENTOS

- **Angular Team** - Framework frontend
- **FastAPI Team** - Framework backend
- **Leaflet** - Mapas interactivos
- **Supabase** - Base de datos
- **n8n** - Automatización
- **OpenAI** - AI Agent

---

## Version

**v3.0.0** — Overhaul completo: Redis + Celery, 193K datos reales, ML V2 (R²=0.76), 12 tablas nuevas (2026-03-25)
**v2.0.0** — Remediacion total: Forest DS, testing, CI/CD, security (2026-03-23)
**v1.0.0** — Sistema completo asegurado y documentado (Octubre 2025)

**Ultima actualizacion:** 25 de Marzo de 2026

---

**Sistema profesional de analisis inmobiliario listo para produccion.**

Para comenzar: Ver `INICIO_RAPIDO.md`
