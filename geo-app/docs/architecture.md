# 🏗️ ARQUITECTURA COMPLETA DEL SISTEMA

**Proyecto:** IAInmobiliaria - Análisis de Mercado Inmobiliario con ML
**Fecha:** 26 de Octubre, 2025
**Estado:** ✅ Producción

---

## 📊 DIAGRAMA DE ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            👥 USUARIOS                                   │
│                     (Navegadores Web / Móviles)                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     🌐 HOSTINGER (Frontend)                              │
│                  https://iainmobiliaria.iagentek.com.mx                  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  Angular 17 + TypeScript                                     │        │
│  │  - Leaflet.js (Mapas)                                        │        │
│  │  - TailwindCSS (Estilos)                                     │        │
│  │  - Componentes: Mapa, Filtros, Estadísticas, Chatbot        │        │
│  └─────────────────────────────────────────────────────────────┘        │
└───────────┬─────────────────────┬───────────────────┬───────────────────┘
            │                     │                   │
            │ API REST            │ API REST          │ Webhook POST
            │ (Predicciones ML)   │ (Datos BD)        │ (Chatbot IA)
            ▼                     ▼                   ▼
┌───────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
│  🚂 RAILWAY       │  │  🗄️ VPS SUPABASE     │  │  🤖 n8n             │
│  (Backend Python) │  │  (Base de Datos)     │  │  (Workflow AI)      │
└───────────────────┘  └──────────────────────┘  └─────────────────────┘
```

---

## 🎯 VISIÓN GENERAL

Tu sistema es una **aplicación web moderna de 3 capas** para análisis inmobiliario:

1. **Frontend (Hostinger)** → Interfaz web para usuarios
2. **Backend (Railway)** → API de Machine Learning para predicciones
3. **Base de Datos (Supabase en VPS)** → Almacenamiento de datos
4. **Automatización (n8n)** → Chatbot con IA

---

## 1️⃣ FRONTEND - HOSTINGER

### 🌐 ¿Qué es Hostinger?

**Hostinger** es un servicio de **hosting compartido** (como un apartamento en un edificio). Es perfecto para alojar sitios web estáticos o aplicaciones frontend porque:

- ✅ Es económico ($3-10/mes)
- ✅ Tiene buen rendimiento para HTML/CSS/JS
- ✅ Incluye SSL/HTTPS gratis
- ✅ Tiene panel de control fácil (hPanel)

### 📍 Tu URL:
```
https://iainmobiliaria.iagentek.com.mx
```

### 🔧 ¿Qué aloja Hostinger?

Tu aplicación **Angular** compilada (HTML + CSS + JavaScript):

```
public_html/
├── index.html           ← Página principal
├── main.*.js            ← Código Angular (722 KB)
├── styles.*.css         ← Estilos TailwindCSS (236 KB)
├── polyfills.*.js       ← Compatibilidad navegadores
├── runtime.*.js         ← Runtime de Angular
├── assets/              ← Imágenes, íconos, fuentes
└── .htaccess            ← Configuración de rutas
```

### ⚙️ ¿Qué hace el Frontend?

1. **Muestra el mapa interactivo** (Leaflet.js)
   - 10,561 predicciones ML como "heatmap"
   - Click en puntos para ver detalles
   - Zoom, navegación, búsqueda de direcciones

2. **Panel de control lateral**
   - Filtros por ciudad
   - Filtros avanzados (precio, score)
   - Control de amenidades (escuelas, hospitales, etc.)

3. **Estadísticas en tiempo real**
   - Gráficas por ciudad
   - Métricas de plusvalía

4. **Chatbot "Favier AI"**
   - Asistente inmobiliario
   - Responde preguntas sobre inversiones

5. **Exportar reportes**
   - CSV, PDF de predicciones filtradas

### 🔗 Conexiones del Frontend:

```typescript
// environment.prod.ts
{
  mlApiBase: "https://analisis-inmobiliario-backend-production.up.railway.app",
  supabaseUrl: "https://iagenteksupabase.iagentek.com.mx",
  n8nBase: "https://iagentekn8nwebhook.iagentek.com.mx"
}
```

**Frontend se comunica con:**
- ✅ Railway (para predicciones ML)
- ✅ Supabase (para leer datos de BD)
- ✅ n8n (para chatbot IA)

---

## 2️⃣ BACKEND - RAILWAY

### 🚂 ¿Qué es Railway?

**Railway** es una **plataforma PaaS** (Platform as a Service) moderna para desplegar aplicaciones, similar a Heroku pero más moderna. Es como tener un servidor dedicado, pero Railway se encarga de:

- ✅ Configurar el servidor automáticamente
- ✅ Instalar dependencias (Python, librerías)
- ✅ Escalar recursos según demanda
- ✅ Monitoreo y logs en tiempo real
- ✅ SSL/HTTPS automático
- ✅ Variables de entorno seguras

### 📍 Tu URL de Railway:
```
https://analisis-inmobiliario-backend-production.up.railway.app
```

### 🔧 ¿Qué aloja Railway?

Tu **API Python** con FastAPI:

```
python_services/
├── api/
│   └── main.py          ← API REST con FastAPI
├── ml_model/
│   └── predictor.py     ← Modelos de Machine Learning
├── integrations/
│   └── inegi_client.py  ← Cliente para datos INEGI
├── scrapers/            ← Web scrapers (no usados en prod)
├── requirements.txt     ← Dependencias Python
└── config.py            ← Configuración (lee variables de entorno)
```

### ⚙️ ¿Qué hace el Backend (Railway)?

Railway ejecuta tu **API FastAPI** que proporciona endpoints para:

#### 🔍 Endpoints Principales:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del servicio |
| `/predictions/heatmap` | GET | 15,000 predicciones para el mapa |
| `/predictions/stats-by-city` | GET | Estadísticas por ciudad |
| `/predictions/nearby` | GET | Predicciones cercanas a coordenadas |
| `/predictions/filter` | POST | Filtrar predicciones por criterios |
| `/predict` | POST | Generar nueva predicción ML |

#### 📊 ¿Qué hacen estos endpoints?

**Ejemplo 1: `/predictions/heatmap`**
```
Frontend solicita → Railway consulta Supabase → Railway aplica modelos ML
→ Railway devuelve JSON con predicciones → Frontend dibuja heatmap
```

**Ejemplo 2: `/predictions/nearby`**
```
Usuario hace click en el mapa (lat, lon) → Frontend llama Railway
→ Railway busca en Supabase predicciones cercanas
→ Railway devuelve top 10 más cercanos → Frontend muestra popup
```

### 🧠 Machine Learning en Railway:

El backend usa modelos ML entrenados:
- **Scikit-learn** (regresión)
- **XGBoost** (gradient boosting)
- Modelos guardados en archivos `.pkl` y `.joblib`

**Flujo ML:**
```
Datos geográficos (lat, lon, ciudad, amenidades)
    ↓
Modelo ML cargado en memoria
    ↓
Predicción: Precio/m², Plusvalía Score (0-100), Potencial
    ↓
JSON devuelto al Frontend
```

### 🔐 Variables de Entorno en Railway:

Railway almacena credenciales de forma segura:

```
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_SERVICE_ROLE_KEY=eyJhbG... (JWT token)
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_USER=postgres.iagenteksupabase
POSTGRES_PASSWORD=Iagentek_123
ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx
ENVIRONMENT=production
```

### 🚀 ¿Por qué Railway y no Hostinger para el Backend?

| Feature | Hostinger | Railway |
|---------|-----------|---------|
| **Python/FastAPI** | ❌ No soporta | ✅ Soporta nativamente |
| **Escalabilidad** | ❌ Fijo | ✅ Auto-escala |
| **Instalación de librerías** | ❌ Limitado | ✅ Automático |
| **Variables de entorno** | ⚠️ Básico | ✅ Seguro y fácil |
| **Logs en tiempo real** | ❌ No | ✅ Sí |
| **Costo** | 💰 $3-10/mes | 💰 $5-20/mes |

**Conclusión:** Hostinger = Frontend, Railway = Backend Python

---

## 3️⃣ BASE DE DATOS - SUPABASE EN VPS

### 🗄️ ¿Qué es Supabase?

**Supabase** es una **alternativa open-source a Firebase**. Es una plataforma completa que incluye:

- ✅ PostgreSQL (base de datos)
- ✅ API REST automática (PostgREST)
- ✅ Autenticación de usuarios
- ✅ Storage de archivos
- ✅ Realtime (WebSockets)

### 🖥️ ¿Qué es un VPS?

**VPS** (Virtual Private Server) es como tener tu **propio servidor** en la nube. En tu caso:

- **Proveedor:** Contabo (u otro)
- **Sistema:** Ubuntu Linux
- **Ubicación:** VPS propio (auto-hospedado)
- **Instalación:** Supabase instalado con Docker

### 📍 Tu URL de Supabase:
```
https://iagenteksupabase.iagentek.com.mx
```

**Credenciales:**
```
Usuario: admin
Password: Iagentek_123
Anon Key: eyJhbGciOiJI... (para frontend)
Service Key: eyJhbGciOiJI... (para backend)
```

### 🔧 ¿Qué almacena Supabase?

Tu **base de datos PostgreSQL** con estas tablas:

| Tabla | Descripción | Registros |
|-------|-------------|-----------|
| `iainmobiliaria_predictions` | Predicciones ML principales | ~15,000 |
| `iainmobiliaria_properties` | Propiedades inmobiliarias | Variable |
| `iainmobiliaria_amenities` | Amenidades (escuelas, hospitales) | Miles |
| `iainmobiliaria_ml_history` | Histórico de predicciones | Acumulativo |
| `ai_chat_predictions` | Vista para chatbot IA | Link a predictions |

### 📊 Estructura de Datos:

**Ejemplo de registro en `iainmobiliaria_predictions`:**

```json
{
  "id": 1234,
  "lat": 20.6737,
  "lon": -103.3444,
  "city": "Guadalajara",
  "state": "Jalisco",
  "predicted_price_m2": 42150.50,
  "plusvalia_score": 85.3,
  "growth_potential": "alto",
  "risk_level": "bajo",
  "model_confidence": 87.2,
  "prediction_date": "2025-10-26T10:30:00Z"
}
```

### 🔗 ¿Quién se conecta a Supabase?

```
Frontend (Angular)
    ↓ (Supabase Client SDK)
    ↓ (Anon Key)
Supabase API REST
    ↓
PostgreSQL
```

```
Backend (Railway)
    ↓ (psycopg2 / SQLAlchemy)
    ↓ (Service Role Key)
Supabase PostgreSQL directo
    ↓
PostgreSQL
```

### 🛡️ Seguridad (RLS - Row Level Security):

Supabase tiene **políticas de seguridad** configuradas:

```sql
-- Usuarios anónimos solo pueden LEER predicciones
CREATE POLICY "Public read access"
ON iainmobiliaria_predictions
FOR SELECT
TO anon, authenticated
USING (true);

-- Solo el backend (service_role) puede ESCRIBIR
CREATE POLICY "Service role full access"
ON iainmobiliaria_predictions
FOR ALL
TO service_role
USING (true);
```

### ⚙️ ¿Por qué Supabase en VPS y no en la nube?

| Opción | Pros | Contras |
|--------|------|---------|
| **VPS propio** | 🟢 Control total<br>🟢 Sin límites<br>🟢 Más económico a escala | 🔴 Requiere mantenimiento<br>🔴 Tú eres responsable |
| **Supabase Cloud** | 🟢 Sin mantenimiento<br>🟢 Backups automáticos | 🔴 Costo alto con escala<br>🔴 Límites de uso |

**Tu decisión:** VPS propio = Más control y económico

---

## 4️⃣ AUTOMATIZACIÓN - n8n

### 🤖 ¿Qué es n8n?

**n8n** es una herramienta de **automatización de workflows** (como Zapier pero open-source). Permite crear flujos de trabajo visuales sin código para:

- ✅ Conectar servicios (Supabase, OpenAI, Slack, etc.)
- ✅ Webhooks (recibir/enviar datos HTTP)
- ✅ IA (chatbots con OpenAI/Claude)
- ✅ Scheduled tasks (tareas programadas)

### 📍 Tu URL de n8n:
```
https://iagentekn8nwebhook.iagentek.com.mx
```

**Webhook del Chatbot:**
```
https://iagentekn8nwebhook.iagentek.com.mx/webhook/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea
```

### 🔧 ¿Qué hace n8n en tu proyecto?

**Workflow: "Chatbot Favier AI"**

```
Usuario escribe en chatbot
    ↓
Frontend envía POST al webhook de n8n
    ↓
n8n recibe mensaje (conversationId)
    ↓
n8n consulta Supabase (predicciones)
    ↓
n8n envía a AI Agent (OpenAI/Claude)
    ↓
AI Agent analiza datos y genera respuesta
    ↓
n8n devuelve JSON: {"respuesta": "..."}
    ↓
Frontend muestra respuesta en chatbot
```

### 📊 Nodos del Workflow:

| Nodo | Tipo | Función |
|------|------|---------|
| **Webhook** | Trigger | Recibe mensaje del usuario |
| **Supabase** | Action | Consulta predicciones en BD |
| **AI Agent** | Action | Procesa con IA (GPT/Claude) |
| **Respond to Webhook** | Action | Devuelve respuesta al frontend |

### 🧠 Prompt del AI Agent:

El archivo `n8n_workflows/FAVIER_AI_SYSTEM_PROMPT.md` contiene el prompt que le dice a la IA cómo comportarse:

```markdown
Eres Favier AI, un asistente inmobiliario experto...

Base de datos: iainmobiliaria_predictions
- plusvalia_score >= 60 = Buenas oportunidades
- growth_potential: "alto", "medio", "bajo"
- risk_level: "bajo", "medio", "alto"

Responde de forma amigable, profesional y concreta.
```

### 🔗 ¿Por qué usar n8n?

| Sin n8n | Con n8n |
|---------|---------|
| Código backend para chatbot | Workflow visual sin código |
| Integrar OpenAI manualmente | Nodo pre-construido |
| Manejar webhooks en código | Webhook automático |
| Más desarrollo | Menos desarrollo |

**Conclusión:** n8n = Automatización fácil y visual

---

## 🔄 FLUJO DE DATOS COMPLETO

### Caso 1: Usuario abre el mapa

```
1. Usuario → https://iainmobiliaria.iagentek.com.mx
2. Hostinger sirve index.html + JS
3. Angular carga en navegador
4. Frontend llama: GET /predictions/heatmap
   → https://analisis-inmobiliario-backend-production.up.railway.app
5. Railway consulta Supabase (15,000 registros)
6. Railway devuelve JSON al Frontend
7. Frontend dibuja heatmap en Leaflet.js
8. Usuario ve el mapa con colores de plusvalía
```

### Caso 2: Usuario hace click en el mapa

```
1. Usuario hace click en un punto (lat: 20.67, lon: -103.34)
2. Frontend detecta coordenadas
3. Frontend llama: GET /predictions/nearby?lat=20.67&lon=-103.34
   → Railway backend
4. Railway busca en Supabase las 10 predicciones más cercanas
5. Railway calcula distancias y ordena
6. Railway devuelve JSON con top 10
7. Frontend muestra popup con:
   - Precio/m²: $42,150
   - Score: 85/100
   - Potencial: Alto
   - Riesgo: Bajo
```

### Caso 3: Usuario usa el chatbot

```
1. Usuario escribe: "¿Cuáles son las mejores zonas en Guadalajara?"
2. Frontend envía POST a n8n webhook:
   {"conversationId": "¿Cuáles son...?"}
3. n8n recibe mensaje
4. n8n consulta Supabase:
   SELECT * FROM iainmobiliaria_predictions
   WHERE city = 'Guadalajara' AND plusvalia_score >= 60
   ORDER BY plusvalia_score DESC LIMIT 5
5. n8n envía datos + prompt a AI Agent
6. AI Agent analiza y genera respuesta:
   "¡Excelente pregunta! Encontré 5 zonas prometedoras:
    1. Zapopan Centro - Score: 89/100, $45,200/m²..."
7. n8n devuelve: {"respuesta": "..."}
8. Frontend muestra respuesta en chatbot
```

### Caso 4: Usuario aplica filtros

```
1. Usuario selecciona:
   - Ciudad: Guadalajara
   - Precio: $30,000 - $50,000/m²
   - Score: >= 70
2. Frontend construye query
3. Frontend llama Railway: POST /predictions/filter
   {"city": "Guadalajara", "price_min": 30000, ...}
4. Railway consulta Supabase con filtros SQL:
   WHERE city = 'Guadalajara'
   AND predicted_price_m2 BETWEEN 30000 AND 50000
   AND plusvalia_score >= 70
5. Railway devuelve resultados filtrados
6. Frontend actualiza mapa (solo puntos filtrados)
```

---

## 💰 COSTOS MENSUALES

| Servicio | Costo | Qué incluye |
|----------|-------|-------------|
| **Hostinger** | ~$5-10/mes | Hosting frontend, SSL, dominio |
| **Railway** | ~$5-20/mes | Backend Python, 500hrs compute |
| **VPS (Supabase)** | ~$5-15/mes | Servidor completo, Supabase |
| **n8n** | $0 (en VPS) | Workflows ilimitados |
| **Dominio** | ~$10-15/año | iagentek.com.mx |
| **TOTAL** | **~$20-50/mes** | Sistema completo |

---

## 🛡️ SEGURIDAD

### 1. HTTPS en todo el sistema ✅

```
Frontend: https://iainmobiliaria.iagentek.com.mx (SSL Hostinger)
Backend: https://analisis-inmobiliario-backend... (SSL Railway)
Supabase: https://iagenteksupabase.iagentek.com.mx (SSL VPS)
n8n: https://iagentekn8nwebhook.iagentek.com.mx (SSL VPS)
```

### 2. Variables de entorno (nunca en código) ✅

```
# Frontend
environment.prod.ts (compilado, no sensible)

# Backend (Railway)
Variables almacenadas en Railway Dashboard

# Supabase
Keys almacenadas en VPS (.env, docker-compose)
```

### 3. CORS configurado ✅

```python
# Backend solo acepta requests de:
ALLOWED_ORIGINS = [
  "https://iainmobiliaria.iagentek.com.mx",
  "http://localhost:4200"  # Para desarrollo
]
```

### 4. Rate Limiting ✅

```python
# Backend limita a 1000 requests/hora por IP
MAX_REQUESTS_PER_HOUR = 1000
```

### 5. Row Level Security (Supabase) ✅

```sql
-- Frontend (anon key) solo puede LEER
-- Backend (service role) puede ESCRIBIR
```

---

## 📈 ESCALABILIDAD

### ¿Qué pasa si el tráfico crece?

| Componente | Solución |
|------------|----------|
| **Frontend (Hostinger)** | ✅ CDN de Cloudflare<br>✅ Migrar a Vercel/Netlify |
| **Backend (Railway)** | ✅ Auto-escala automáticamente<br>✅ Aumentar plan Railway |
| **Supabase (VPS)** | ✅ Aumentar RAM/CPU del VPS<br>✅ PostgreSQL replica |
| **n8n** | ✅ Ya en VPS, escalar VPS<br>✅ Queue para workflows |

**Railway es especialmente bueno para escalar:**
- Auto-escala horizontal (más instancias)
- Auto-escala vertical (más CPU/RAM)
- Load balancing automático

---

## 🔍 MONITOREO Y LOGS

### Frontend (Hostinger)
- ❌ Logs limitados
- ✅ Browser DevTools (F12)
- ✅ Sentry (opcional, para errores)

### Backend (Railway)
- ✅ Logs en tiempo real: `railway logs`
- ✅ Dashboard con métricas CPU/RAM
- ✅ Logs estructurados con Loguru

### Supabase (VPS)
- ✅ Logs PostgreSQL
- ✅ Dashboard Supabase
- ✅ pgAdmin para queries

### n8n
- ✅ Logs de cada workflow
- ✅ Historial de ejecuciones
- ✅ Dashboard visual

---

## 🚀 DEPLOYMENT

### Frontend → Hostinger

```bash
# 1. Build
cd geo-app/app
ng build --configuration production

# 2. Subir via FTP a public_html/
# Todos los archivos de dist/app/
```

### Backend → Railway

```bash
# 1. Desde terminal
cd geo-app/python_services
railway up

# O via Git (push automático)
git push origin main
→ Railway detecta cambios y redeploy automático
```

### Supabase (Ya está en VPS)

```bash
# Actualizar esquema:
psql -h iagenteksupabase.iagentek.com.mx -U postgres -f scripts_sql/XX_script.sql
```

### n8n (Ya está en VPS)

- Editar workflows desde UI web
- Cambios se guardan automáticamente

---

## 🎯 RESUMEN EJECUTIVO

| ¿Qué? | ¿Dónde? | ¿Qué hace? |
|-------|---------|------------|
| **Frontend** | Hostinger | Angular app que usuarios ven |
| **Backend** | Railway | API Python con ML para predicciones |
| **Base de Datos** | Supabase (VPS) | PostgreSQL con 15,000+ predicciones |
| **Chatbot** | n8n (VPS) | Workflow de IA con OpenAI/Claude |

### Flujo Principal:

```
Usuario → Hostinger (Frontend) → Railway (Backend) ↔ Supabase (BD)
                                ↘ n8n (Chatbot) ↗
```

### ¿Por qué esta arquitectura?

✅ **Separación de responsabilidades**
- Frontend en Hostinger (económico, simple)
- Backend en Railway (potente, escalable)
- BD en VPS propio (control total)

✅ **Escalabilidad**
- Cada componente escala independientemente
- Railway auto-escala según demanda

✅ **Costo-efectividad**
- ~$20-50/mes para sistema completo
- Sin vendor lock-in (puedes migrar)

✅ **Seguridad**
- HTTPS en todo
- Variables de entorno seguras
- CORS y rate limiting

---

## 📚 DOCUMENTOS RELACIONADOS

| Documento | Descripción |
|-----------|-------------|
| `LISTO_PARA_HOSTINGER_FINAL.md` | Guía de deployment |
| `DEPLOY_COMPLETO_EXITOSO.md` | Proceso de deploy Railway |
| `ERROR_RAILWAY_SOLUCIONADO.md` | Troubleshooting |
| `FAVIER_AI_SYSTEM_PROMPT.md` | Prompt del chatbot |
| `N8N_WEBHOOKS.md` | Configuración n8n |
| `README_supabase.md` | Documentación Supabase |

---

## 🆘 CONTACTO Y SOPORTE

**Railway Dashboard:**
https://railway.com/project/e9200da6-3549-4e35-a582-436b6d2991ad

**Hostinger Panel:**
https://hpanel.hostinger.com

**Supabase Dashboard:**
https://iagenteksupabase.iagentek.com.mx

---

**¿Preguntas sobre la arquitectura?** Este documento es tu guía de referencia. 📖

**Última actualización:** 26 de Octubre, 2025

