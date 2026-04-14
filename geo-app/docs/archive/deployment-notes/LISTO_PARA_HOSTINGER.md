# ✅ ARCHIVOS LISTOS PARA HOSTINGER

**Fecha:** 26 de Octubre de 2025  
**Estado:** 🎉 **TODO LISTO PARA SUBIR**

---

## 📦 ARCHIVOS GENERADOS

**Ubicación:** `app/dist/app/`

```
✅ .htaccess                          (3 KB) ← IMPORTANTE
✅ index.html                         (6 KB) ← IMPORTANTE
✅ main.3b794d33264a7aa1.js        (739 KB)
✅ styles.eea81502e9239dcb.css     (241 KB)
✅ polyfills.5f8d7c42b667f3ae.js    (33 KB)
✅ runtime.cda8f8730340ba6c.js       (1 KB)
✅ favicon.ico
✅ 3rdpartylicenses.txt
✅ layers.png
✅ layers-2x.png
✅ marker-icon.png
```

**Total:** ~1 MB (optimizado y comprimido)

---

## 🚀 PROCESO DE SUBIDA A HOSTINGER

### PASO 1: Preparar Archivos (YA HECHO ✅)

```powershell
# YA EJECUTADO:
cd app
ng build --configuration production
Copy-Item .htaccess -Destination dist/app/
```

### PASO 2: Abrir Panel de Hostinger

1. **Ir a:** https://hpanel.hostinger.com
2. **Seleccionar:** `iainmobiliaria.iagentek.com.mx`
3. **Click en:** "Administrador de archivos"

### PASO 3: Limpiar Carpeta `public_html/`

1. **Navegar a:** `public_html/`
2. **Seleccionar TODO** (Ctrl+A o Click en checkbox superior)
3. **Click derecho → Eliminar**
4. **Confirmar eliminación**

### PASO 4: Subir Archivos

1. **En Administrador de Archivos:**
   - Asegurarse de estar en: `public_html/`
   - Click en "Subir archivos" o "Upload"

2. **Seleccionar archivos:**
   - Navegar a: `C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\app\dist\app\`
   - Seleccionar **TODOS** los archivos (Ctrl+A)
   - Click en "Abrir"

3. **Esperar la subida:**
   - Barra de progreso se completará
   - Verificar que todos los archivos estén subidos

### PASO 5: Verificar Estructura

**En `public_html/` debe quedar:**

```
public_html/
├── .htaccess          ← Debe estar aquí
├── index.html         ← Debe estar aquí
├── main.....js
├── styles.....css
├── polyfills.....js
├── runtime.....js
├── favicon.ico
├── layers.png
├── layers-2x.png
├── marker-icon.png
└── 3rdpartylicenses.txt
```

⚠️ **NO debe quedar:** `public_html/app/` ni `public_html/browser/`

### PASO 6: Activar SSL (Si no está activo)

1. **En Panel Hostinger:**
   - Sitios web → iainmobiliaria.iagentek.com.mx
   - SSL → "Activar SSL gratuito"
   - Esperar 1-5 minutos

### PASO 7: Probar el Sitio

**Abrir navegador:**
```
https://iainmobiliaria.iagentek.com.mx
```

**Verificar:**
- [ ] Página carga
- [ ] Mapa se ve
- [ ] HTTPS activo (candado verde)
- [ ] No hay errores en consola (F12)

---

## ⚠️ IMPORTANTE: BACKEND

El **backend Python NO puede ir en Hostinger** (es hosting compartido PHP).

### Opciones para el Backend:

| Plataforma | Dificultad | Costo | Recomendado |
|------------|------------|-------|-------------|
| **Railway.app** | Fácil | Gratis | ✅ **SÍ** |
| **DigitalOcean** | Media | $5/mes | ✅ Sí |
| **VPS** | Difícil | Variable | ❌ No (si no tienes experiencia) |

### 🔥 RECOMENDACIÓN: Railway.app

1. **Ir a:** https://railway.app/
2. **Sign up** con GitHub
3. **New Project → Deploy from GitHub**
4. **Seleccionar** tu repositorio
5. **Root Directory:** `geo-app/python_services`
6. **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

7. **Variables de Entorno en Railway:**
   ```
   SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
   SUPABASE_SERVICE_ROLE_KEY=tu_key_aqui
   POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
   POSTGRES_PORT=5432
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres.iagenteksupabase
   POSTGRES_PASSWORD=tu_password
   ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx
   ENVIRONMENT=production
   LOG_LEVEL=ERROR
   MAX_REQUESTS_PER_HOUR=1000
   ```

8. **Generate Domain** → Copiar URL (ej: `https://tu-proyecto.up.railway.app`)

### Actualizar Frontend con URL del Backend:

**Archivo:** `app/src/environments/environment.prod.ts`

```typescript
mlApiBase: "https://tu-proyecto-real.up.railway.app"  // Cambiar
```

**Después de cambiar:**
```powershell
cd app
ng build --configuration production
Copy-Item .htaccess -Destination dist/app/
# Volver a subir archivos a Hostinger
```

---

## 🔍 VERIFICACIÓN POST-DESPLIEGUE

### 1. Frontend en Hostinger:

```bash
# Probar HTTPS
curl -I https://iainmobiliaria.iagentek.com.mx

# Debe responder: 200 OK
```

### 2. Backend en Railway (cuando lo despliegues):

```bash
# Probar health check
curl https://tu-proyecto.up.railway.app/health

# Debe responder: {"status":"healthy"}
```

### 3. Conexión Frontend → Backend:

1. Abrir: https://iainmobiliaria.iagentek.com.mx
2. Abrir DevTools (F12) → Network
3. Interactuar con el mapa
4. Verificar requests a backend:
   - Status: 200 OK
   - URL: `https://tu-proyecto.up.railway.app/predictions/...`

---

## 🚨 PROBLEMAS COMUNES

### Error: "index.html not found"

**Solución:**
- Verificar que `index.html` esté en `public_html/`
- NO en `public_html/app/`

### Error: Rutas de Angular no funcionan (404)

**Solución:**
- Verificar que `.htaccess` esté en `public_html/`
- Permisos de `.htaccess`: 644

### Error: "CORS policy" en consola

**Solución:**
```python
# En backend Railway, .env:
ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx,http://localhost:4200
```

### Error: Backend no responde

**Solución:**
1. Verificar que backend esté desplegado y corriendo
2. Verificar URL en `environment.prod.ts`
3. Probar backend directamente: `curl URL_BACKEND/health`

---

## 📊 ARQUITECTURA FINAL

```
┌─────────────────────────────────────────┐
│  FRONTEND (Angular)                     │
│  Hostinger                              │
│  https://iainmobiliaria.iagentek.com.mx│
│  ✅ LISTO PARA SUBIR                    │
└─────────────────┬───────────────────────┘
                  │
                  ├──────────┬──────────────┐
                  ▼          ▼              ▼
         ┌────────────┐ ┌──────────┐ ┌────────────┐
         │  Backend   │ │   n8n    │ │  Supabase  │
         │  Python    │ │ Chatbot  │ │ PostgreSQL │
         │  Railway   │ │   ✅     │ │    ✅      │
         │  ⏳ TODO   │ └──────────┘ └────────────┘
         └────────────┘
```

---

## ✅ CHECKLIST FINAL

### Archivos:
- [x] Build de producción generado
- [x] .htaccess incluido
- [x] Todos los archivos en `dist/app/`
- [x] Total: ~1 MB

### Hostinger:
- [ ] Archivos subidos a `public_html/`
- [ ] `.htaccess` presente
- [ ] `index.html` presente
- [ ] SSL activo
- [ ] Sitio carga correctamente

### Backend (Siguiente paso):
- [ ] Backend desplegado en Railway
- [ ] URL del backend en `environment.prod.ts`
- [ ] CORS configurado
- [ ] Frontend re-buildeado con nueva URL
- [ ] Re-subido a Hostinger

---

## 📁 UBICACIÓN DE ARCHIVOS

### Local (tu computadora):
```
C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\app\dist\app\
```

### Hostinger (destino):
```
public_html/
```

---

## 🎯 ORDEN DE DESPLIEGUE

1. ✅ **Frontend Build** - COMPLETADO
2. ⏳ **Subir a Hostinger** - TÚ LO HACES AHORA
3. ⏳ **Desplegar Backend en Railway** - SIGUIENTE
4. ⏳ **Actualizar URL backend en frontend** - DESPUÉS
5. ⏳ **Re-subir frontend a Hostinger** - FINAL

---

## 📚 DOCUMENTACIÓN

| Documento | Para qué |
|-----------|----------|
| **LISTO_PARA_HOSTINGER.md** | Este archivo - Guía rápida |
| **DESPLIEGUE_HOSTINGER.md** | Guía detallada completa |
| **INSTRUCCIONES_DESPLIEGUE.md** | Despliegue general (todas las plataformas) |
| **INICIO_RAPIDO.md** | Para desarrollo local |

---

## 🆘 SI NECESITAS AYUDA

1. Ver `DESPLIEGUE_HOSTINGER.md` para guía detallada
2. Soporte Hostinger: https://www.hostinger.mx/contacto
3. Chat de Hostinger: Disponible 24/7 en el panel

---

**¡Archivos listos para subir a Hostinger!** 🚀

**Siguiente paso:** Subir archivos desde `dist/app/` a `public_html/` en Hostinger

