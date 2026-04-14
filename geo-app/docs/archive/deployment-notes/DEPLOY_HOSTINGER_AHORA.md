# 🚀 DESPLEGAR EN HOSTINGER AHORA

## ✅ BUILD COMPLETADO

Tu frontend Angular está **compilado y listo** para subir a Hostinger.

---

## 📦 ARCHIVOS LISTOS

**Ubicación:** `geo-app/app/dist/app/`

**Archivos generados:**
```
dist/app/
├── index.html          ← Archivo principal
├── main.*.js          ← JavaScript compilado (745 KB)
├── styles.*.css       ← Estilos (245 KB)
├── polyfills.*.js     ← Compatibilidad navegadores
├── runtime.*.js       ← Runtime Angular
└── assets/            ← Imágenes, fuentes, etc.
```

---

## 🌐 PASO 1: SUBIR A HOSTINGER

### Opción A: Administrador de Archivos (Más Fácil)

1. **Ir al Panel de Hostinger**
   - https://hpanel.hostinger.com
   - Login

2. **Seleccionar tu dominio**
   - `iainmobiliaria.iagentek.com.mx`

3. **Abrir Administrador de Archivos**
   - Click en "Administrador de archivos"
   - Navegar a `public_html/`

4. **Limpiar carpeta actual** (Si hay archivos viejos)
   ```
   Seleccionar TODOS los archivos en public_html/
   Click derecho → Eliminar
   ```

5. **Subir archivos nuevos**
   - Click en "Subir archivos"
   - Seleccionar todos los archivos de `dist/app/`
   - Esperar a que termine

6. **Verificar**
   ```
   📁 public_html/
   ├── index.html
   ├── main.*.js
   ├── styles.*.css
   ├── polyfills.*.js
   ├── runtime.*.js
   └── assets/
   ```

---

### Opción B: FTP (Para usuarios avanzados)

```bash
# Usar FileZilla, WinSCP, o cualquier cliente FTP
# Configuración:
Host: ftp.iainmobiliaria.iagentek.com.mx
Usuario: tu_usuario_ftp
Password: tu_password_ftp
Puerto: 21

# Subir contenido de dist/app a public_html/
```

---

## 🔒 PASO 2: CONFIGURAR .htaccess (IMPORTANTE)

### ¿Para qué sirve?
- Redirigir todas las rutas a `index.html` (necesario para Angular SPA)
- Configurar cache de archivos estáticos

### Crear archivo en Hostinger:

1. **Crear archivo `.htaccess`**
   - Click en "Nuevo archivo"
   - Nombre: `.htaccess` (con el punto al inicio)

2. **Pegar este contenido:**

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  
  # Redirigir todo a index.html para Angular SPA
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>

# Compresión GZIP
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
</IfModule>

# Cache para archivos estáticos
<IfModule mod_expires.c>
  ExpiresActive On
  
  # Imágenes
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/gif "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType image/x-icon "access plus 1 year"
  
  # CSS y JavaScript
  ExpiresByType text/css "access plus 1 month"
  ExpiresByType text/javascript "access plus 1 month"
  ExpiresByType application/javascript "access plus 1 month"
  
  # Fuentes
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType font/woff "access plus 1 year"
  ExpiresByType font/ttf "access plus 1 year"
  
  # HTML (no cachear)
  ExpiresByType text/html "access plus 0 seconds"
</IfModule>

# Seguridad adicional
<IfModule mod_headers.c>
  # Prevenir clickjacking
  Header always set X-Frame-Options "SAMEORIGIN"
  
  # Prevenir MIME sniffing
  Header always set X-Content-Type-Options "nosniff"
  
  # XSS Protection
  Header always set X-XSS-Protection "1; mode=block"
</IfModule>

# Prevenir acceso a archivos ocultos
<FilesMatch "^\.">
  Order allow,deny
  Deny from all
</FilesMatch>
```

3. **Guardar** y listo

---

## ✅ PASO 3: VERIFICAR

### Abrir en el navegador:
```
https://iainmobiliaria.iagentek.com.mx
```

### Verificar que:
- ✅ La página carga
- ✅ El mapa se muestra
- ✅ No hay errores en consola (F12)
- ✅ Las rutas funcionan (probablemente `/#/mapa`)

### Si hay errores:

**Error: "404 Not Found"**
- Verificar que `index.html` esté en `public_html/`
- Verificar `.htaccess` está configurado

**Error: "CORS policy"**
- Verificar que backend esté corriendo
- Verificar `ALLOWED_ORIGINS` incluye tu dominio

**Error: "Cannot GET /mapa"**
- Verificar que `.htaccess` redirige a `index.html`
- Recargar con `Ctrl+F5`

---

## 🔐 PASO 4: CONFIGURAR SSL

### Si no tienes SSL activo:

1. **Ir a Hostinger → SSL**
2. **Activar Let's Encrypt SSL**
3. **Esperar a que se configure** (5-10 minutos)
4. **Forzar HTTPS** (opcional)

---

## 📊 PASO 5: ACTUALIZAR BACKEND

### Si cambiaste el dominio del frontend:

**Backend debe permitir CORS del nuevo dominio:**

```python
# En tu VPS o Railway
# Variables de entorno:
ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx,https://www.iainmobiliaria.iagentek.com.mx
```

---

## 🎉 COMPLETADO

### ✅ Tu frontend está en producción:
```
https://iainmobiliaria.iagentek.com.mx
```

### ✅ Próximos pasos:
1. Configurar backend en VPS (si aún no lo hiciste)
2. Probar todas las funcionalidades
3. Verificar que el chatbot funciona
4. Hacer pruebas de carga

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Problema: Página en blanco
**Solución:**
```bash
# Verificar consola del navegador (F12)
# Buscar errores JavaScript
# Verificar que los archivos .js se descargaron
```

### Problema: Mapa no carga
**Solución:**
```bash
# Verificar:
1. Conexión a internet
2. Que backend esté corriendo
3. Que CORS esté configurado
```

### Problema: Rutas no funcionan
**Solución:**
```bash
# Verificar .htaccess
# Debe tener la regla de RewriteRule . /index.html [L]
```

---

## 📝 CHECKLIST FINAL

- [ ] Archivos subidos a `public_html/`
- [ ] `.htaccess` configurado
- [ ] SSL activo
- [ ] Página carga sin errores
- [ ] Mapa funciona
- [ ] Backend responde
- [ ] Chatbot funciona
- [ ] Rutas funcionan

---

**🎉 ¡Frontend desplegado exitosamente!**

Ahora sigue con el backend en VPS usando:
- `GUIA_DESPLIEGUE_VPS.md`
- `DESPLIEGUE_VPS_RESUMEN_EJECUTIVO.md`

