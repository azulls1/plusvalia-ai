# 🚀 INSTRUCCIONES DE DESPLIEGUE - Análisis de Mercado Inmobiliario

## 📋 RESUMEN EJECUTIVO

Este documento contiene las instrucciones paso a paso para desplegar el sistema completo de análisis de mercado inmobiliario de forma segura.

---

## 🎯 COMPONENTES DEL SISTEMA

| Componente | Tecnología | Puerto | URL Producción |
|------------|------------|--------|----------------|
| **Frontend** | Angular 17 | 4200 | https://tu-dominio.com |
| **Backend API** | Python FastAPI | 8000 | https://api.tu-dominio.com |
| **Database** | Supabase PostgreSQL | 5432 | iagenteksupabase.iagentek.com.mx |
| **Workflows** | n8n | - | iagentekn8nwebhook.iagentek.com.mx |
| **Chatbot** | Favier AI | - | (Integrado en frontend) |

---

## ⚙️ CONFIGURACIÓN INICIAL

### 1. Clonar el Repositorio

```bash
git clone <tu-repositorio>
cd Analisis-mercado-evaluacion-terrenos/geo-app
```

### 2. Configurar Variables de Entorno

#### **Backend Python**

```bash
cd python_services
```

**Crear archivo `.env`:**
```env
# Copiar desde .env.example y completar con valores reales
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=tu_anon_key_real
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key_real
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.iagenteksupabase
POSTGRES_PASSWORD=tu_password_real
ALLOWED_ORIGINS=http://localhost:4200,https://tu-dominio.com
ENVIRONMENT=production
LOG_LEVEL=ERROR
MAX_REQUESTS_PER_HOUR=1000
```

#### **Frontend Angular**

```bash
cd ../app/src/environments
```

**Editar `environment.prod.ts`:**
```typescript
export const environment = {
  production: true,
  supabaseUrl: "https://iagenteksupabase.iagentek.com.mx",
  supabaseAnonKey: "tu_anon_key",  // OK para frontend (es pública)
  n8nBase: "https://iagentekn8nwebhook.iagentek.com.mx",
  mlApiBase: "https://api.tu-dominio.com",  // ⚠️ Cambiar por URL real
  // ... resto de config
};
```

---

## 🐍 DESPLEGAR BACKEND (Python FastAPI)

### Opción A: Railway.app (Recomendado)

1. **Crear cuenta en Railway.app**
   - https://railway.app/

2. **Conectar repositorio**
   - New Project → Deploy from GitHub
   - Seleccionar repositorio

3. **Configurar servicio**
   ```
   Root Directory: geo-app/python_services
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Agregar variables de entorno**
   - Ir a Variables
   - Copiar todas las variables del `.env`
   - ⚠️ Cambiar `ENVIRONMENT=production`

5. **Generar dominio**
   - Settings → Generate Domain
   - Copiar URL (ej: `https://tu-proyecto.up.railway.app`)

6. **Verificar**
   ```bash
   curl https://tu-proyecto.up.railway.app/health
   ```

### Opción B: DigitalOcean App Platform

1. **Crear cuenta en DigitalOcean**
2. **Apps → Create App**
3. **Conectar repositorio GitHub**
4. **Configurar:**
   ```
   Source Directory: geo-app/python_services
   Build Command: pip install -r requirements.txt
   Run Command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app
   HTTP Port: 8000
   ```

5. **Environment Variables:** Copiar todas del `.env`

### Opción C: VPS (Servidor Propio)

```bash
# Conectar al servidor
ssh user@tu-servidor.com

# Instalar Python 3.9+
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Clonar proyecto
git clone <repo>
cd geo-app/python_services

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear .env
nano .env
# (Pegar configuración)

# Instalar supervisor para mantener API corriendo
sudo apt install supervisor

# Crear config supervisor
sudo nano /etc/supervisor/conf.d/inmo-api.conf
```

**Contenido de `inmo-api.conf`:**
```ini
[program:inmo-api]
directory=/home/user/geo-app/python_services
command=/home/user/geo-app/python_services/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
stderr_logfile=/var/log/inmo-api.err.log
stdout_logfile=/var/log/inmo-api.out.log
```

```bash
# Iniciar servicio
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start inmo-api
```

---

## 🌐 DESPLEGAR FRONTEND (Angular)

### Opción A: Vercel (Recomendado)

1. **Crear cuenta en Vercel**
   - https://vercel.com/

2. **Importar proyecto**
   - New Project → Import Git Repository

3. **Configurar build**
   ```
   Framework Preset: Angular
   Root Directory: geo-app/app
   Build Command: npm run build -- --configuration production
   Output Directory: dist/app
   Install Command: npm install
   ```

4. **Environment Variables:**
   ```
   No necesarias (Angular usa environment.prod.ts en build time)
   ```

5. **Deploy**
   - Click "Deploy"
   - Copiar URL generada

6. **Custom Domain (Opcional)**
   - Settings → Domains
   - Agregar tu dominio

### Opción B: Netlify

1. **Crear cuenta en Netlify**
2. **New site from Git**
3. **Configurar:**
   ```
   Base directory: geo-app/app
   Build command: ng build --configuration production
   Publish directory: geo-app/app/dist/app
   ```

4. **Deploy**

### Opción C: Firebase Hosting

```bash
cd geo-app/app

# Instalar Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Inicializar
firebase init hosting

# Build
ng build --configuration production

# Deploy
firebase deploy --only hosting
```

---

## 🔗 CONECTAR FRONTEND CON BACKEND

### Actualizar URL del Backend

**En `geo-app/app/src/environments/environment.prod.ts`:**
```typescript
export const environment = {
  production: true,
  mlApiBase: "https://tu-backend.railway.app",  // ⚠️ URL real del backend
  // ... resto
};
```

**Re-build y re-deploy:**
```bash
ng build --configuration production
# Volver a desplegar en Vercel/Netlify
```

---

## 🔐 CONFIGURAR HTTPS Y DOMINIOS

### Backend (Railway/DigitalOcean)

1. **Railway:** HTTPS automático en dominio generado
2. **Custom Domain:**
   - Settings → Custom Domain
   - Agregar CNAME en tu DNS:
     ```
     api.tu-dominio.com → CNAME → tu-proyecto.up.railway.app
     ```

### Frontend (Vercel/Netlify)

1. **Vercel:** HTTPS automático
2. **Custom Domain:**
   - Settings → Domains → Add
   - Configurar DNS:
     ```
     A Record: @ → 76.76.19.19 (Vercel IP)
     CNAME: www → cname.vercel-dns.com
     ```

---

## ✅ CHECKLIST DE DESPLIEGUE

### Pre-Despliegue

- [ ] `.env` creado con credenciales reales
- [ ] `.env` NO está en Git
- [ ] `environment.prod.ts` actualizado
- [ ] Credenciales de Supabase verificadas
- [ ] n8n workflows activos

### Post-Despliegue Backend

- [ ] `/health` responde 200
- [ ] `/docs` accesible (solo en desarrollo)
- [ ] CORS configurado con dominio del frontend
- [ ] Rate limiting activo
- [ ] Logs no muestran información sensible

### Post-Despliegue Frontend

- [ ] Aplicación carga correctamente
- [ ] Mapa de Leaflet se visualiza
- [ ] Heatmap de predicciones carga
- [ ] Chatbot Favier AI responde
- [ ] No hay errores en consola (F12)

---

## 🧪 TESTING POST-DESPLIEGUE

### 1. Test de API

```bash
# Health check
curl https://tu-backend.com/health

# Test predicciones
curl "https://tu-backend.com/predictions/heatmap?limit=10"

# Test estadísticas
curl "https://tu-backend.com/predictions/stats-by-city"
```

### 2. Test de Frontend

1. Abrir https://tu-dominio.com
2. Verificar que el mapa carga
3. Click en "Predicciones ML"
4. Hacer zoom en Guadalajara
5. Click en cualquier punto del mapa
6. Verificar que aparecen predicciones cercanas
7. Abrir Chatbot (botón abajo-izquierda)
8. Escribir: "¿Dónde invertir en Guadalajara?"
9. Verificar respuesta del AI

### 3. Test de Chatbot n8n

1. Verificar que webhook esté activo en n8n
2. Test manual:
```bash
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/webhook/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea \
  -H "Content-Type: application/json" \
  -d '{"conversationId": "Hola"}'
```

---

## 🚨 TROUBLESHOOTING

### Backend no inicia

```bash
# Ver logs
# Railway: Dashboard → Deployments → Logs
# DigitalOcean: App → Runtime Logs
# VPS: sudo tail -f /var/log/inmo-api.err.log
```

**Error común:** "Variables de entorno faltantes"
- **Solución:** Verificar que TODAS las variables del `.env` estén configuradas

### Frontend no conecta con Backend

**Error:** CORS policy
- **Solución:** Verificar `ALLOWED_ORIGINS` en backend incluye dominio del frontend

**Error:** NetworkError
- **Solución:** Verificar `mlApiBase` en `environment.prod.ts`

### Chatbot no responde

1. Verificar n8n workflow esté ACTIVO (no en test mode)
2. Verificar webhook URL en `ai-chatbot.component.ts`
3. Ver logs de n8n → Executions

---

## 📊 MONITOREO

### Logs del Backend

**Railway:**
- Dashboard → Logs

**DigitalOcean:**
- App → Runtime Logs

**VPS:**
```bash
sudo tail -f /var/log/inmo-api.out.log
sudo tail -f /var/log/inmo-api.err.log
```

### Métricas de Supabase

- Dashboard → Database → Query Performance
- Table Editor → Ver datos

### Uptime Monitoring

**Herramientas:**
- UptimeRobot (gratis hasta 50 monitores)
- Pingdom
- StatusCake

**Configurar:**
1. Monitor para `https://tu-backend.com/health`
2. Monitor para `https://tu-dominio.com`
3. Alertas por email

---

## 🔄 ACTUALIZAR PRODUCCIÓN

### Backend

```bash
# Opción A: Auto-deploy (Railway/DigitalOcean)
git push origin main
# Deploy automático

# Opción B: Manual (VPS)
ssh user@servidor
cd geo-app/python_services
git pull
sudo supervisorctl restart inmo-api
```

### Frontend

```bash
# Build local
cd geo-app/app
ng build --configuration production

# Opción A: Vercel (auto-deploy)
git push origin main

# Opción B: Manual
vercel --prod

# Opción C: Firebase
firebase deploy --only hosting
```

---

## ✅ SISTEMA DESPLEGADO

Una vez completados todos los pasos:

✅ **Backend:** https://tu-backend.com  
✅ **Frontend:** https://tu-dominio.com  
✅ **Database:** Supabase (Configurado)  
✅ **Chatbot:** Favier AI (Activo)  
✅ **Seguridad:** HTTPS, CORS, Rate Limiting  

---

**Sistema listo para producción.** 🎉

Para soporte, consultar `GUIA_SEGURIDAD_COMPLETA.md`.

