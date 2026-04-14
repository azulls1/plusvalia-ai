# 🚀 DEPLOY EN PROGRESO - Railway

**Estado:** Subiendo código a Railway...

---

## ✅ LO QUE YA SE HIZO

1. ✅ Railway CLI instalado
2. ✅ Login exitoso (azull.samael@gmail.com)
3. ✅ Proyecto creado: `analisis-inmobiliario-backend`
4. ✅ Código subiendo con `railway up`

**URL del proyecto:** https://railway.com/project/e9200da6-3549-4e35-a582-436b6d2991ad

---

## ⏳ LO QUE ESTÁ PASANDO AHORA

Railway está:
1. Subiendo tu código
2. Detectando que es Python
3. Instalando dependencias (`requirements.txt`)
4. Creando un servicio
5. Intentando iniciar el servidor

---

## ⚠️ LO QUE FALTA (TÚ DEBES HACER)

### 1. Configurar Variables de Entorno

**IMPORTANTE:** El servidor NO iniciará sin las variables de entorno.

Una vez que termine `railway up`, ejecuta:

```powershell
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services

# Configurar TODAS las variables:
railway variables --set "SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx" --set "SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogInNlcnZpY2Vfcm9sZSIsCiAgImlzcyI6ICJzdXBhYmFzZSIsCiAgImlhdCI6IDE3MTUwNTA4MDAsCiAgImV4cCI6IDE4NzI4MTcyMDAKfQ.82nFc9RPC-0tzN0svrqQrnHUHHe51bJkpCUiC_uTypo" --set "POSTGRES_HOST=iagenteksupabase.iagentek.com.mx" --set "POSTGRES_PORT=5432" --set "POSTGRES_DB=postgres" --set "POSTGRES_USER=postgres.iagenteksupabase" --set "POSTGRES_PASSWORD=TU_PASSWORD_REAL" --set "ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx,http://localhost:4200" --set "ENVIRONMENT=production" --set "LOG_LEVEL=ERROR" --set "MAX_REQUESTS_PER_HOUR=1000"
```

**⚠️ CAMBIAR:** `TU_PASSWORD_REAL` por tu password real de PostgreSQL.

### 2. Generar Dominio Público

```powershell
railway domain
```

Esto te dará una URL como:
```
https://analisis-inmobiliario-backend-production.up.railway.app
```

### 3. Verificar que Funcione

```powershell
# Reemplazar con tu URL
curl https://TU-URL.up.railway.app/health
```

Debe responder: `{"status":"healthy"}`

---

## 🔍 VERIFICAR PROGRESO

### Opción 1: Ver en el Navegador

Ir a: https://railway.com/project/e9200da6-3549-4e35-a582-436b6d2991ad

- Ver el servicio creado
- Ver logs del deploy
- Ver si hay errores

### Opción 2: Ver Logs en Terminal

```powershell
railway logs
```

---

## 🚨 POSIBLES ERRORES

### Error: "Application failed to start"

**Causa:** Falta configurar variables de entorno

**Solución:** Ejecutar el comando de variables (Paso 1 arriba)

### Error: "Module not found"

**Causa:** Falta una dependencia

**Solución:**
```powershell
# Ver qué falta
railway logs

# Si falta algo, agregarlo a requirements.txt y re-deploy
railway up
```

### Error: "Port already in use"

**Causa:** Railway usa variable `$PORT` automática

**Solución:** Ya está configurado en `Procfile`, no hacer nada.

---

## 📋 PASOS DESPUÉS DEL DEPLOY

1. ✅ Obtener URL del backend
2. ✅ Actualizar `environment.prod.ts`
3. ✅ Re-build frontend
4. ✅ Re-subir a Hostinger

**Ver:** `ACTUALIZAR_FRONTEND_CON_RAILWAY.md`

---

## 💡 COMANDOS ÚTILES

```powershell
# Ver logs en tiempo real
railway logs

# Ver estado
railway status

# Ver variables configuradas
railway variables

# Re-deploy
railway up

# Abrir proyecto en navegador
railway open
```

---

**Deploy en progreso...** ⏳

Espera a que `railway up` termine y luego configura las variables de entorno.

