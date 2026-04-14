# 🏗️ ARQUITECTURA BACKEND EN VPS

## 📊 Sistema Inmobiliario - Configuración VPS

```
┌──────────────────────────────────────────────────────┐
│                   INTERNET                           │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │     TRAEFIK            │
        │  Reverse Proxy         │
        │  + SSL/TLS Auto        │
        │  + Load Balancing      │
        └──────┬─────────────────┘
               │
               │ apis.inmobiliario.iagentek.com.mx
               │
               ▼
    ┌────────────────────────────┐
    │  BACKEND INMOBILIARIO      │
    │  ┌──────────────────────┐  │
    │  │  FastAPI            │  │
    │  │  Python 3.11        │  │
    │  │  Uvicorn (4 workers)│  │
    │  └──────────────────────┘  │
    │  ┌──────────────────────┐  │
    │  │  ML Models          │  │
    │  │  - Random Forest    │  │
    │  │  - XGBoost          │  │
    │  │  - Scikit-learn     │  │
    │  └──────────────────────┘  │
    └────────────┬───────────────┘
                 │
                 │ SQL Queries
                 ▼
    ┌────────────────────────────┐
    │      SUPABASE              │
    │  ┌──────────────────────┐  │
    │  │  PostgreSQL 15      │  │
    │  │  + pgvector         │  │
    │  └──────────────────────┘  │
    │  ┌──────────────────────┐  │
    │  │  Storage (S3)        │  │
    │  └──────────────────────┘  │
    └────────────────────────────┘
```

---

## 🎯 COMPONENTES

### 1. **Traefik** (Reverse Proxy)
- ✅ **SSL/TLS Automático** - Let's Encrypt
- ✅ **Auto-discovery** - Detecta contenedores
- ✅ **Load Balancing** - Distribuye carga
- ✅ **HTTP → HTTPS Redirect**

### 2. **Backend API** (Python FastAPI)
- ✅ **Puerto:** 8000 (interno)
- ✅ **Workers:** 4
- ✅ **Health:** `/health`
- ✅ **Docs:** `/docs` (opcional deshabilitar)

### 3. **Supabase** (PostgreSQL)
- ✅ **Tablas:** 
  - `iainmobiliaria_comparables`
  - `iainmobiliaria_amenities`
  - `iainmobiliaria_grid_tiles`
  - `iainmobiliaria_predictions`
  - `documents` (RAG)
- ✅ **pgvector** para embeddings

---

## 🔐 CONFIGURACIÓN DE SEGURIDAD

### Labels de Traefik

```yaml
# Router
traefik.http.routers.backend-inmobiliario.rule=Host(`apiinmobiliario.iagentek.com.mx`)
traefik.http.routers.backend-inmobiliario.entrypoints=websecure
traefik.http.routers.backend-inmobiliario.tls.certresolver=letsencryptresolver

# Servicio
traefik.http.services.backend-inmobiliario.loadbalancer.server.port=8000

# CORS
traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolalloworiginlist=https://iagentek.com.mx
traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS
traefik.http.routers.backend-inmobiliario.middlewares=backend-inmobiliario-cors
```

---

## 📂 ESTRUCTURA DE ARCHIVOS

```
python_services/
├── api/
│   └── main.py              # FastAPI app
├── ml_model/
│   ├── predictor.py         # Modelo ML
│   └── models/
│       ├── *.pkl            # Modelos entrenados
│       └── *.joblib
├── integrations/
│   └── inegi_client.py      # Cliente INEGI
├── scrapers/
│   └── *.py                 # Scrapers varios
├── config.py                # Configuración global
├── requirements.txt         # Dependencias
├── Dockerfile               # Imagen Docker
├── docker-compose.yml       # Stack Portainer
└── .env                     # Variables de entorno
```

---

## 🌐 DOMINIOS Y REDES

### Dominios
- **Backend:** `https://apiinmobiliario.iagentek.com.mx`
- **Supabase:** `https://iagenteksupabase.iagentek.com.mx`
- **Portainer:** `https://iagentekportainer.iagentek.com.mx`

### Redes Docker
- **Red Principal:** `traefik_default` (external overlay)
- **Propósito:** Todos los servicios comunicados

---

## 💾 RECURSOS ASIGNADOS

### Backend API
```
CPU:
  Máximo: 2.0 cores
  Mínimo: 0.5 cores

RAM:
  Máximo: 2 GB
  Mínimo: 512 MB

Volúmenes:
  model_cache:  /app/ml_model/models
  logs:         /app/logs
  data:         /app/data
```

---

## 🔄 FLUJO DE DATOS

### 1. **Usuario solicita predicción**
```
Frontend (Angular)
  ↓ HTTP Request
Traefik (SSL termination)
  ↓ Routing
Backend API (FastAPI)
  ↓ Consulta BD
Supabase (PostgreSQL)
  ↓ Select predictions
Backend API (Predicción ML)
  ↓ JSON Response
Traefik
  ↓ HTTPS Response
Frontend (Visualización)
```

### 2. **Procesamiento ML**
```
Backend recibe lat/lon
  ↓
Carga modelo ML desde cache
  ↓
Extrae features (amenities, grid, INEGI)
  ↓
Predicción de plusvalía
  ↓
Retorna JSON con score/price
```

---

## 🚀 PROCESO DE DESPLIEGUE

### 1. **Construcción**
```bash
docker build -t backend-inmobiliario:latest .
```

### 2. **Despliegue Portainer**
- Crear Stack
- Copiar `docker-compose.yml`
- Configurar variables de entorno
- Deploy

### 3. **Traefik Auto-detection**
- Lee labels del contenedor
- Genera certificado SSL
- Enruta tráfico
- ✅ **SSL listo en 1-2 minutos**

---

## 📊 TABLAS DE BASE DE DATOS

### Principales
| Tabla | Propósito |
|-------|-----------|
| `iainmobiliaria_comparables` | Propiedades comparables |
| `iainmobiliaria_amenities` | Amenidades OSM |
| `iainmobiliaria_grid_tiles` | Grilla de precios |
| `iainmobiliaria_predictions` | Predicciones ML |
| `iainmobiliaria_inegi_data` | Datos INEGI |
| `documents` | RAG knowledge base |

---

## 🔍 ENDPOINTS DE LA API

### Generales
- `GET /` - Info
- `GET /health` - Health check
- `GET /docs` - Swagger UI

### Predicciones
- `GET /api/predictions` - Listar predicciones
- `GET /api/predictions?lat=X&lon=Y` - Predicción por ubicación
- `GET /api/stats` - Estadísticas por ciudad

### Datos
- `GET /api/amenities` - Amenidades
- `GET /api/grid` - Grilla de precios
- `GET /api/comparables` - Propiedades

---

## 🛡️ SEGURIDAD

### Implementada
✅ **CORS** - Dominio específico permitido  
✅ **SSL/TLS** - Certificados automáticos  
✅ **Health Checks** - Monitoreo continuo  
✅ **Variables de Entorno** - Credenciales protegidas  
✅ **Rate Limiting** - 100 req/hora  
✅ **RLS** - Row Level Security en Supabase  

---

## 📈 MONITOREO

### Métricas
- CPU usage
- RAM usage
- Request/response times
- Error rates
- Health status

### Logs
```bash
docker service logs backend-inmobiliario_backend-api -f
```

### Portainer
- Dashboard visual
- Estadísticas en tiempo real
- Logs integrados

---

## 🔧 MANTENIMIENTO

### Actualizar código
```bash
docker build -t backend-inmobiliario:latest .
docker service update --force backend-inmobiliario_backend-api
```

### Backup modelos
```bash
docker volume ls
docker run --rm -v backend-inmobiliario_model_cache:/data -v $(pwd):/backup alpine tar czf /backup/modelos-backup.tar.gz /data
```

### Ver logs
```bash
docker logs -f backend-inmobiliario-api
```

---

## 🎯 VENTAJAS DE ESTA ARQUITECTURA

1. **Escalabilidad**
   - Fácil agregar réplicas
   - Load balancing automático

2. **Seguridad**
   - SSL automático
   - Aislamiento de servicios
   - CORS configurado

3. **Gestión Visual**
   - Portainer facilita todo
   - Logs en tiempo real
   - Métricas integradas

4. **Alta Disponibilidad**
   - Health checks
   - Reinicio automático
   - Persistencia de datos

5. **Desarrollo**
   - Auto-reload en dev
   - Hot reload de código
   - Testing integrado

---

## 🔄 INTEGRACIONES

### Activas
- ✅ Supabase (PostgreSQL + Storage)
- ✅ Traefik (Routing + SSL)
- ✅ Portainer (Gestión)
- ✅ Angular Frontend
- ✅ n8n (Automatización)

### Futuras
- 🔄 Redis (Cache)
- 🔄 Celery (Tareas async)
- 🔄 Prometheus (Métricas)
- 🔄 Grafana (Dashboards)

---

**Arquitectura Cloud-Native para Análisis Inmobiliario**  
**Desarrollado por Samael Hernandez**

