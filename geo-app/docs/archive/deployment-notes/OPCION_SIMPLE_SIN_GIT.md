# ⚡ OPCIÓN SIMPLE: Desplegar Backend SIN Git/GitHub

**Si no quieres usar GitHub, puedes desplegar directamente desde Railway CLI**

---

## 📋 OPCIÓN A: Railway CLI (Sin GitHub)

### 1. Instalar Railway CLI

```powershell
# Instalar con npm
npm i -g @railway/cli

# O descargar desde:
# https://railway.app/cli
```

### 2. Login

```powershell
railway login
```

Abrirá navegador para autorizar.

### 3. Inicializar proyecto

```powershell
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services

railway init
```

### 4. Configurar variables de entorno

```powershell
# Agregar cada variable
railway variables set SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogInNlcnZpY2Vfcm9sZSIsCiAgImlzcyI6ICJzdXBhYmFzZSIsCiAgImlhdCI6IDE3MTUwNTA4MDAsCiAgImV4cCI6IDE4NzI4MTcyMDAKfQ.82nFc9RPC-0tzN0svrqQrnHUHHe51bJkpCUiC_uTypo
railway variables set POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
railway variables set POSTGRES_PORT=5432
railway variables set POSTGRES_DB=postgres
railway variables set POSTGRES_USER=postgres.iagenteksupabase
railway variables set POSTGRES_PASSWORD=TU_PASSWORD_REAL
railway variables set ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=ERROR
```

### 5. Deploy

```powershell
railway up
```

### 6. Obtener URL

```powershell
railway domain
```

---

## 📋 OPCIÓN B: DigitalOcean App Platform ($5/mes)

Más fácil que Railway, con UI simple.

### 1. Crear cuenta

https://www.digitalocean.com

### 2. Crear App

1. Apps → Create App
2. Seleccionar: "Upload your code"
3. Subir carpeta: `python_services/`
4. Tipo: Python
5. Start command: `uvicorn api.main:app --host 0.0.0.0 --port 8080`

### 3. Variables de entorno

Agregar las mismas variables que Railway.

### 4. Deploy

Click "Deploy" - toma 5-10 minutos.

---

## 📋 OPCIÓN C: Render.com (Gratis)

Similar a Railway pero más simple.

### 1. Crear cuenta

https://render.com

### 2. New Web Service

1. Connect Repository o Upload folder
2. Seleccionar carpeta `python_services/`
3. Environment: Python 3
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### 3. Variables

Agregar en Environment section.

### 4. Create Web Service

Deploy automático.

---

## 🎯 COMPARACIÓN

| Plataforma | Costo | Dificultad | Velocidad |
|------------|-------|------------|-----------|
| **Railway** | Gratis | Media | Rápido |
| **Railway CLI** | Gratis | Fácil | Más rápido |
| **DigitalOcean** | $5/mes | Muy fácil | Medio |
| **Render** | Gratis | Fácil | Lento |

---

## ✅ RECOMENDACIÓN

**Railway CLI** (Opción A) - Es la más fácil sin necesidad de GitHub.

**Pasos resumidos:**
```powershell
# 1. Instalar
npm i -g @railway/cli

# 2. Login
railway login

# 3. Ir a carpeta
cd geo-app\python_services

# 4. Inicializar
railway init

# 5. Configurar variables (copiar todas del .env)
railway variables set NOMBRE=valor

# 6. Deploy
railway up

# 7. Obtener URL
railway domain
```

---

**Elige la opción que prefieras.** 🚀

