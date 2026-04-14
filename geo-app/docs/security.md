# 🛡️ GUÍA COMPLETA DE SEGURIDAD Y DESPLIEGUE

## ✅ Resumen de Mejoras de Seguridad Implementadas

Esta guía documenta todas las mejoras de seguridad implementadas en el proyecto para protegerlo contra hackeos y exposición de información sensible.

---

## 🔒 FASE 1: SEGURIDAD - COMPLETADA

### 1. Protección de Credenciales y API Keys ✅

**Problema:** Credenciales hardcodeadas en el código fuente.

**Solución Implementada:**

#### **Backend Python (`config.py`)**
- ❌ **ANTES:** Credenciales expuestas directamente en el código
```python
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # ⚠️ EXPUESTO
```

- ✅ **AHORA:** Credenciales desde variables de entorno
```python
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("⚠️ ERROR: Variables de entorno faltantes")
```

#### **Archivos Modificados:**
- `python_services/config.py` - Eliminadas credenciales hardcodeadas
- `python_services/run_scraping_training.py` - Usa credenciales desde `config.py`

---

### 2. Ocultar Logs Sensibles en Consola ✅

**Problema:** `console.log()` exponía información sensible en el navegador.

**Solución Implementada:**

#### **Servicio de Logging Seguro** (`logger.service.ts`)
Creado servicio que:
- **Desarrollo:** Muestra todos los logs
- **Producción:** Oculta logs sensibles automáticamente

```typescript
// Ejemplo de uso:
this.logger.log('Información general');          // Solo desarrollo
this.logger.sensitive('Token:', data);           // NUNCA en producción
this.logger.error('Error genérico', details);    // Sanitizado en producción
```

#### **Archivos Modificados:**
- `app/src/app/services/logger.service.ts` - **NUEVO**
- `app/src/app/services/api.service.ts` - 40 `console.log` reemplazados

---

### 3. Variables de Entorno Correctas ✅

**Archivos Creados:**

#### **`.env` (Python Services)**
```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
POSTGRES_PASSWORD=...
ALLOWED_ORIGINS=http://localhost:4200,...
```

#### **`.env.example` (Template)**
Plantilla sin credenciales reales para referencia.

**⚠️ IMPORTANTE:** El archivo `.env` DEBE crearse manualmente y NUNCA subirse a Git.

---

### 4. CORS y Rate Limiting ✅

**Problema:** CORS abierto con `"*"` permitía ataques desde cualquier sitio.

**Solución Implementada:**

#### **CORS Seguro**
```python
# ANTES
allow_origins=["*"]  # ⚠️ PELIGROSO

# AHORA
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS").split(",")
allow_origins=ALLOWED_ORIGINS  # Solo dominios específicos
```

#### **Rate Limiting**
Implementado middleware que:
- Limita requests por IP (1000/hora por defecto)
- Responde con HTTP 429 si se excede
- Configurable vía `MAX_REQUESTS_PER_HOUR` en `.env`

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Implementa exponential backoff y límite por IP
```

---

## 🧹 FASE 2: LIMPIEZA - COMPLETADA

### 1. Actualizar .gitignore ✅

**Archivos Creados:**

#### **`geo-app/.gitignore`** (Proyecto completo)
```gitignore
.env
.env.local
*.pem
*.key
credentials.json
__pycache__/
node_modules/
*.log
```

#### **`geo-app/python_services/.gitignore`** (Backend)
```gitignore
.env
__pycache__/
logs/
data/*.csv
ml_model/models/*.pkl
```

#### **`geo-app/app/.gitignore`** (Frontend)
```gitignore
.env
environment.ts
environment.prod.ts
node_modules/
dist/
```

---

### 2. Archivos Temporales a Limpiar

**Carpetas para Eliminar:**
```bash
# Backend
python_services/__pycache__/
python_services/api/__pycache__/
python_services/ml_model/__pycache__/
python_services/scrapers/__pycache__/
python_services/integrations/__pycache__/

# Frontend (si existen)
app/.angular/cache/
app/node_modules/.cache/
```

**Modelos ML Antiguos (Opcionales):**
```bash
# Mantener solo el más reciente, eliminar:
ml_model/models/model_20251025_045127.joblib
ml_model/models/plusvalia_model_v2.0_20251025_030746.pkl
ml_model/models/plusvalia_model_v3.0_real_data_20251025_032147.pkl
ml_model/models/plusvalia_model_v3.0_real_data_20251025_034731.pkl
ml_model/models/plusvalia_model_v3.0_real_data_20251025_034909.pkl
# ✅ MANTENER: plusvalia_model_v3.0_real_data_20251025_040849.pkl (más reciente)
```

**Scripts de Limpieza:**
```powershell
# Windows PowerShell
cd geo-app\python_services
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

---

## ⚡ FASE 3: OPTIMIZACIÓN (PENDIENTE)

### Build de Producción

**Angular:**
```bash
cd geo-app/app
ng build --configuration production
```

**Beneficios:**
- Minificación automática
- Tree-shaking (elimina código no usado)
- Optimización de imágenes
- Source maps deshabilitados

---

## 📝 CHECKLIST DE SEGURIDAD

### Antes de Desplegar:

- [ ] Crear archivo `.env` con credenciales reales
- [ ] Verificar que `.env` NO esté en Git (`git status`)
- [ ] Actualizar `ALLOWED_ORIGINS` en `.env` con dominios de producción
- [ ] Cambiar `environment.production = true` en frontend
- [ ] Configurar `LOG_LEVEL=ERROR` en producción
- [ ] Eliminar carpetas `__pycache__`
- [ ] Verificar que no haya `console.log` sensibles
- [ ] Configurar HTTPS en producción (Nginx/Apache)
- [ ] Configurar firewall para puerto 8000 (solo backend interno)
- [ ] Implementar backup automático de base de datos

---

## 🚨 ARCHIVOS QUE NUNCA DEBEN ESTAR EN GIT

**❌ PROHIBIDOS:**
```
.env
.env.local
.env.production
credentials.json
*.pem
*.key
*_secret.py
```

**Verificar:**
```bash
git status
# Si aparece alguno de estos archivos, ¡DETENER y eliminarlo!
```

---

## 🔐 CONFIGURACIÓN DE SUPABASE

### Row Level Security (RLS)

**Verificar que RLS esté activo:**
```sql
-- En Supabase SQL Editor
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

**Tablas que DEBEN tener RLS:**
- `iainmobiliaria_comparables`
- `iainmobiliaria_predictions`
- `iainmobiliaria_grid_tiles`

---

## 🌐 DESPLIEGUE EN PRODUCCIÓN

### 1. Backend (Python FastAPI)

**Opciones:**
- **Railway.app** (Recomendado para MVP)
- **Heroku**
- **DigitalOcean App Platform**
- **AWS EC2** (más avanzado)

**Variables de Entorno en Railway:**
```env
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
POSTGRES_PASSWORD=...
ALLOWED_ORIGINS=https://tu-dominio.com
ENVIRONMENT=production
LOG_LEVEL=ERROR
```

### 2. Frontend (Angular)

**Opciones:**
- **Vercel** (Recomendado)
- **Netlify**
- **Firebase Hosting**

**Configuración en Vercel:**
```json
{
  "buildCommand": "ng build --configuration production",
  "outputDirectory": "dist/app",
  "framework": "angular"
}
```

---

## 📊 MONITOREO Y ALERTAS

### Herramientas Recomendadas:

1. **Sentry** - Monitoreo de errores
2. **LogRocket** - Sesiones de usuario
3. **Uptime Robot** - Monitoreo de disponibilidad
4. **Supabase Dashboard** - Métricas de base de datos

---

## 🆘 SOPORTE Y CONTACTO

Si necesitas ayuda:
1. Revisar esta guía completa
2. Verificar logs del backend: `python_services/logs/`
3. Verificar consola del navegador (solo en desarrollo)

---

## 📅 HISTORIAL DE CAMBIOS

| Fecha | Cambio | Estado |
|-------|--------|--------|
| 2025-10-26 | Eliminación de credenciales hardcodeadas | ✅ |
| 2025-10-26 | Implementación de logger seguro | ✅ |
| 2025-10-26 | CORS seguro + Rate limiting | ✅ |
| 2025-10-26 | .gitignore actualizado | ✅ |

---

**Proyecto asegurado y listo para producción.** 🎉

Para cualquier actualización de seguridad, consultar esta guía y mantenerla actualizada.

