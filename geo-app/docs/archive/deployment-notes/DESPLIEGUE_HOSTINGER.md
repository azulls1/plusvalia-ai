# 🚀 DESPLIEGUE EN HOSTINGER - Guía Paso a Paso

**Para desplegar el frontend Angular en Hostinger (iainmobiliaria.iagentek.com.mx)**

---

## ⚠️ IMPORTANTE: ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────┐
│  FRONTEND (Angular)                     │
│  Hostinger                              │
│  iainmobiliaria.iagentek.com.mx        │
└─────────────────┬───────────────────────┘
                  │
                  ├──────────┬──────────────┐
                  ▼          ▼              ▼
         ┌────────────┐ ┌──────────┐ ┌────────────┐
         │  Backend   │ │   n8n    │ │  Supabase  │
         │  Python    │ │ Chatbot  │ │ PostgreSQL │
         │  Railway   │ │          │ │            │
         └────────────┘ └──────────┘ └────────────┘
```

**Hostinger = Solo Frontend (Angular)**  
**Backend Python = Railway / DigitalOcean / VPS**

---

## 📋 CHECKLIST PRE-DESPLIEGUE

### 1. Backend Debe Estar Desplegado PRIMERO

- [ ] Backend Python desplegado en Railway/DigitalOcean
- [ ] URL del backend disponible (ej: `https://api-iainmobiliaria.up.railway.app`)
- [ ] Backend responde en `/health`
- [ ] CORS configurado con dominio de Hostinger

---

## 🛠️ PASO 1: PREPARAR EL BUILD

### 1.1 Actualizar URL del Backend

**Archivo:** `app/src/environments/environment.prod.ts`

```typescript
export const environment = {
  production: true,
  mlApiBase: "https://TU-BACKEND-REAL.up.railway.app", // ⚠️ CAMBIAR
  // ... resto de config
};
```

### 1.2 Ejecutar Build de Producción

```powershell
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\app

# Instalar dependencias (si es necesario)
npm install

# Build de producción
ng build --configuration production
```

**Resultado:**
- Carpeta: `dist/app/browser/` (o `dist/app/`)
- Contiene: `index.html`, archivos `.js`, `.css`, assets

### 1.3 Copiar .htaccess al Build

```powershell
# Copiar .htaccess a la carpeta de build
Copy-Item .htaccess -Destination dist/app/browser/
```

---

## 📤 PASO 2: SUBIR A HOSTINGER

### Opción A: Usando Administrador de Archivos (Recomendado)

1. **Ir al Panel de Hostinger**
   - https://hpanel.hostinger.com
   - Seleccionar sitio: `iainmobiliaria.iagentek.com.mx`

2. **Abrir Administrador de Archivos**
   - Click en "Administrador de archivos"
   - Navegar a `public_html/`

3. **Limpiar Carpeta (si ya hay archivos)**
   ```
   Seleccionar TODOS los archivos en public_html/
   Click derecho → Eliminar
   ```

4. **Subir Archivos del Build**
   ```
   Click en "Subir archivos"
   Seleccionar TODO el contenido de: dist/app/browser/
   ⚠️ NO subir la carpeta "browser", subir su CONTENIDO
   ```

   **Archivos que deben estar en `public_html/`:**
   ```
   public_html/
   ├── index.html          ← IMPORTANTE
   ├── .htaccess           ← IMPORTANTE
   ├── main-XXX.js
   ├── polyfills-XXX.js
   ├── styles-XXX.css
   ├── assets/
   └── favicon.ico
   ```

5. **Verificar Permisos**
   - Seleccionar `.htaccess`
   - Click derecho → Permisos
   - Debe ser `644`

### Opción B: Usando FTP (Alternativa)

1. **Obtener credenciales FTP de Hostinger**
   - Panel → Sitios web → FTP
   - Host: `ftp.iainmobiliaria.iagentek.com.mx`
   - Usuario: (proporcionado por Hostinger)
   - Password: (proporcionado por Hostinger)

2. **Conectar con FileZilla**
   - Instalar FileZilla (https://filezilla-project.org/)
   - Conectar con credenciales FTP
   - Navegar a carpeta remota: `/public_html/`

3. **Subir Archivos**
   - Carpeta local: `dist/app/browser/`
   - Arrastrar TODO el contenido a `/public_html/`

---

## 🔒 PASO 3: CONFIGURAR SSL/HTTPS

1. **En Panel de Hostinger:**
   - Sitios web → iainmobiliaria.iagentek.com.mx
   - SSL → Activar SSL gratuito

2. **Forzar HTTPS:**
   - Ya está configurado en `.htaccess`
   - Todas las peticiones HTTP → redirigen a HTTPS

---

## ✅ PASO 4: VERIFICAR DESPLIEGUE

### 4.1 Probar Frontend

1. **Abrir navegador:**
   ```
   https://iainmobiliaria.iagentek.com.mx
   ```

2. **Verificar:**
   - [ ] Página carga correctamente
   - [ ] Mapa se visualiza
   - [ ] No hay errores en consola (F12)
   - [ ] HTTPS activo (candado verde)

### 4.2 Probar Conexión con Backend

1. **Abrir DevTools (F12)**
2. **Ir a pestaña "Network"**
3. **Interactuar con el mapa**
4. **Verificar requests:**
   - Deben ir a: `https://TU-BACKEND.up.railway.app`
   - Status: `200 OK`
   - Si hay error CORS, configurar backend

### 4.3 Probar Chatbot

1. **Click en botón inferior izquierdo**
2. **Escribir: "Hola"**
3. **Verificar respuesta del AI**

---

## 🚨 PROBLEMAS COMUNES

### Error: "index.html not found" o Error 404

**Causa:** Archivos no están en `public_html/` correctamente

**Solución:**
```
1. Verificar que index.html esté en public_html/
2. NO debe estar en public_html/browser/
3. Debe ser: public_html/index.html
```

### Error: "CORS policy" en consola

**Causa:** Backend no permite requests desde Hostinger

**Solución en Backend:**
```python
# En python_services/.env
ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx,http://localhost:4200
```

### Error: "Rutas de Angular no funcionan"

**Causa:** `.htaccess` no está o tiene permisos incorrectos

**Solución:**
```
1. Verificar que .htaccess esté en public_html/
2. Permisos: 644
3. Si no existe, subir el que creamos
```

### Error: "Failed to load resource" en assets

**Causa:** Rutas incorrectas en build

**Solución:**
```bash
# Rebuild con base href correcto
ng build --configuration production --base-href /
```

---

## 🔄 ACTUALIZAR EL SITIO

Cuando hagas cambios:

```powershell
# 1. Hacer cambios en código
# 2. Rebuild
cd app
ng build --configuration production

# 3. Copiar .htaccess
Copy-Item .htaccess -Destination dist/app/browser/

# 4. Subir a Hostinger
# - Ir a Administrador de Archivos
# - Eliminar archivos viejos de public_html/
# - Subir nuevo contenido de dist/app/browser/
```

---

## 🎯 CHECKLIST FINAL

### Frontend en Hostinger:
- [ ] `index.html` en `public_html/`
- [ ] `.htaccess` en `public_html/`
- [ ] Todos los archivos JS/CSS subidos
- [ ] Carpeta `assets/` subida
- [ ] SSL/HTTPS activo
- [ ] Sitio carga sin errores

### Backend Configurado:
- [ ] Backend desplegado en Railway/DigitalOcean
- [ ] CORS permite dominio de Hostinger
- [ ] URL del backend actualizada en `environment.prod.ts`
- [ ] Backend responde correctamente

### Testing:
- [ ] Frontend carga: https://iainmobiliaria.iagentek.com.mx
- [ ] Mapa se visualiza
- [ ] Heatmap de predicciones carga
- [ ] Chatbot responde
- [ ] No hay errores en consola

---

## 📊 ESTRUCTURA FINAL EN HOSTINGER

```
public_html/
├── index.html                    ← Página principal
├── .htaccess                     ← Configuración Apache
├── main.abc123.js               ← Angular app
├── polyfills.def456.js          ← Polyfills
├── styles.ghi789.css            ← Estilos
├── runtime.jkl012.js            ← Runtime
├── assets/                       ← Recursos
│   ├── images/
│   └── ...
└── favicon.ico                   ← Icono
```

---

## 🔗 RECURSOS ÚTILES

| Recurso | URL |
|---------|-----|
| **Panel Hostinger** | https://hpanel.hostinger.com |
| **Sitio Web** | https://iainmobiliaria.iagentek.com.mx |
| **Documentación Hostinger** | https://support.hostinger.com |

---

## 💡 TIPS

### Optimizar Velocidad:

1. **Comprimir Imágenes:**
   - Usar TinyPNG antes de subir
   - Máximo 200KB por imagen

2. **Limpiar Cache:**
   - Hostinger Panel → "Borrar caché"
   - Hacer después de cada actualización

3. **Verificar PageSpeed:**
   - Panel muestra score actual (99/100 ✅)
   - Mantener optimizaciones

### Backup:

1. **Hostinger hace backup semanal** (automático)
2. **Guardar copia local:**
   ```powershell
   # Guardar build local
   Copy-Item -Recurse dist/app/browser/ -Destination backups/$(Get-Date -Format 'yyyy-MM-dd')/
   ```

---

## 🆘 SOPORTE

**Si algo falla:**

1. Ver logs en Hostinger Panel → Errores
2. Ver consola del navegador (F12) → Console
3. Verificar `.htaccess` tiene permisos correctos
4. Contactar soporte de Hostinger: https://www.hostinger.mx/contacto

---

**Frontend listo para Hostinger.** 🚀

**Siguiente:** Desplegar backend en Railway (ver `INSTRUCCIONES_DESPLIEGUE.md`)

