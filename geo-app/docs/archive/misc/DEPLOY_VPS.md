# 🐳 DESPLIEGUE DEL BACKEND EN VPS CON PORTAINER + SWARM

**Guía completa para mover el backend de Railway a tu VPS con Docker Swarm**

---

## 📋 PRE-REQUISITOS

✅ VPS con Docker Swarm activo  
✅ Portainer instalado y configurado  
✅ **Traefik** configurado y corriendo  
✅ Red `traefik_default` creada en Swarm  
✅ Acceso SSH al VPS  
✅ Modelos ML ya entrenados (carpeta `ml_model/models/`)

---

## 🚀 PASO 1: Preparar archivos en tu VPS

### Opción A: Clonar desde Git (si tienes repo)

```bash
# SSH a tu VPS
ssh usuario@tu-vps-ip

# Ir al directorio donde está tu código
cd /path/to/your/project

# Clonar repo (si lo tienes)
git clone https://tu-repo.git
cd tu-repo/geo-app/python_services
```

### Opción B: Subir archivos manualmente

```bash
# En tu computadora local (Windows)
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services

# Comprimir archivos necesarios
# (usando 7-Zip o WinRAR)
# Incluir:
# - api/
# - ml_model/
# - integrations/
# - config.py
# - requirements.txt
# - Dockerfile
# - docker-compose.yml
# - .env (VER MÁS ABAJO)

# Subir a VPS vía SCP
scp -r python_services.tar.gz usuario@tu-vps-ip:/path/to/deploy/
```

---

## 🔐 PASO 2: Crear archivo .env en tu VPS

**IMPORTANTE:** Necesitas crear un archivo `.env` con tus credenciales.

```bash
# SSH a tu VPS
ssh usuario@tu-vps-ip

# Ir al directorio del proyecto
cd /path/to/python_services

# Crear archivo .env
nano .env
```

**Contenido del `.env`:**

```env
# ================================================================
# CONFIGURACIÓN BACKEND - VPS
# ================================================================

# ==================== SUPABASE ====================
# Tu Supabase auto-hospedado
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k
SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY_AQUI

# ==================== POSTGRESQL ====================
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU_PASSWORD_SUPABASE_AQUI

# ==================== API ====================
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# ==================== CORS ====================
# Dominios permitidos para hacer peticiones
ALLOWED_ORIGINS=https://iagentek.com.mx,http://localhost:4200

# ==================== LOGGING ====================
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# ==================== MODELOS ML ====================
MODEL_PATH=/app/ml_model/models
MODEL_RETRAIN_DAYS=30
```

**⚠️ IMPORTANTE:** Reemplaza:
- `TU_SERVICE_ROLE_KEY_AQUI` → Tu clave de servicio de Supabase
- `TU_PASSWORD_SUPABASE_AQUI` → Tu contraseña de PostgreSQL

**Guardar y salir:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🐳 PASO 3: Construir imagen Docker

```bash
# En tu VPS, ir al directorio del proyecto
cd /path/to/python_services

# Construir imagen
docker build -t backend-inmobiliario:latest .

# Verificar que la imagen se creó
docker images | grep backend-inmobiliario
```

---

## 🌐 PASO 4: Verificar red Traefik

```bash
# Verificar si la red traefik_default existe
docker network ls | grep traefik_default

# Si ya tienes Traefik corriendo, esta red debería existir automáticamente
# Si NO existe, algo está mal con tu configuración de Traefik
```

---

## 📝 PASO 5: Desplegar stack en Portainer

### Opción A: Interfaz de Portainer (Recomendado)

1. **Abrir Portainer:**
   - Ve a: http://tu-vps-ip:9000
   - Inicia sesión

2. **Crear Stack:**
   - Click en **"Stacks"** (menú lateral)
   - Click en **"Add stack"**
   - Nombre: `backend-inmobiliario`

3. **Copiar docker-compose.yml:**
   - En **"Web editor"**, pega el contenido de `docker-compose.yml`
   - Ver archivo adjunto: `docker-compose.yml`

4. **Configurar variables de entorno:**
   - Click en **"Environment variables"**
   - Agregar cada una de las variables del `.env`:
     ```
     SUPABASE_URL
     SUPABASE_KEY
     SUPABASE_SERVICE_ROLE_KEY
     POSTGRES_HOST
     POSTGRES_PORT
     POSTGRES_DB
     POSTGRES_USER
     POSTGRES_PASSWORD
     ALLOWED_ORIGINS
     ```

5. **Deploy:**
   - Click en **"Deploy the stack"**
   - Espera 1-2 minutos

### Opción B: CLI de Docker

```bash
# Deploy usando docker stack
docker stack deploy -c docker-compose.yml backend-inmobiliario

# Verificar logs
docker service logs -f backend-inmobiliario_backend-api
```

---

## ✅ PASO 6: Verificar funcionamiento

```bash
# Ver si el contenedor está corriendo
docker ps | grep backend-inmobiliario

# Ver logs en tiempo real
docker logs -f backend-inmobiliario-api

# Probar health check
curl http://localhost:8000/health

# Deberías ver: {"status":"healthy"}
```

---

## 🔗 PASO 7: Configurar dominio DNS

**Traefik ya configura SSL automáticamente** con Let's Encrypt, solo necesitas configurar el DNS.

### Configurar DNS en Hostinger

1. **Ir a Hostinger Dashboard**
   - https://hpanel.hostinger.com
   - **Dominios** → Tu dominio
   - **DNS / Zone Editor**

2. **Crear registro A:**
   ```
   Tipo: A
   Nombre: apiinmobiliario
   Puntos a: IP_DE_TU_VPS
   TTL: 3600
   ```

3. **Guardar y esperar propagación** (5-60 minutos)

### Verificar propagación

```bash
nslookup apiinmobiliario.iagentek.com.mx

# Debe apuntar a la IP de tu VPS
```

**✅ Traefik detectará automáticamente el contenedor y generará el certificado SSL**

---

## 🎯 PASO 8: Actualizar frontend

**Necesitas actualizar la URL del backend en tu frontend de Angular:**

```bash
# En tu computadora local
cd geo-app/app/src/environments

# Editar environment.prod.ts
nano environment.prod.ts
```

**Cambiar:**

```typescript
export const environment = {
  production: true,
  mlApiBase: "https://apiinmobiliario.iagentek.com.mx",  // ← Tu VPS con Traefik
  // ... resto de configuración
};
```

**Rebuild frontend:**

```bash
cd geo-app/app
npm run build
```

**Subir a Hostinger** con la nueva configuración.

---

## 🔍 MONITOREO Y MANTENIMIENTO

### Ver logs

```bash
# Logs en tiempo real
docker logs -f backend-inmobiliario-api

# Logs de los últimos 1000 líneas
docker logs --tail 1000 backend-inmobiliario-api

# Logs filtrados por error
docker logs backend-inmobiliario-api 2>&1 | grep ERROR
```

### Reiniciar servicio

```bash
# Reiniciar contenedor
docker restart backend-inmobiliario-api

# O desde Portainer: Services → backend-inmobiliario → Restart
```

### Actualizar código

```bash
# 1. Hacer cambios en tu código
# 2. Reconstruir imagen
docker build -t backend-inmobiliario:latest .

# 3. Actualizar servicio
docker service update --force backend-inmobiliario_backend-api

# O desde Portainer: Redeploy stack
```

### Backup modelos ML

```bash
# Backup del volumen con modelos
docker run --rm -v backend-inmobiliario_model_cache:/data -v $(pwd):/backup \
    alpine tar czf /backup/modelos-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restaurar backup
docker run --rm -v backend-inmobiliario_model_cache:/data -v $(pwd):/backup \
    alpine tar xzf /backup/modelos-backup-YYYYMMDD.tar.gz -C /data
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Error: "Cannot connect to database"

**Causa:** PostgreSQL no está accesible desde el contenedor.

**Solución:**

```bash
# Verificar que PostgreSQL acepta conexiones remotas
# En tu VPS de Supabase
sudo nano /etc/postgresql/XX/main/postgresql.conf
# Buscar: listen_addresses = '*'

sudo nano /etc/postgresql/XX/main/pg_hba.conf
# Agregar: host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql
```

### Error: "Module not found"

**Causa:** Dependencias no instaladas correctamente.

**Solución:**

```bash
# Reconstruir imagen forzando limpieza de cache
docker build --no-cache -t backend-inmobiliario:latest .
```

### Error: "CORS policy"

**Causa:** Tu dominio no está en `ALLOWED_ORIGINS`.

**Solución:**

```bash
# Agregar tu dominio a las variables de entorno
# En Portainer: Stacks → Variables → Editar ALLOWED_ORIGINS
ALLOWED_ORIGINS=https://iagentek.com.mx,https://www.iagentek.com.mx
```

### Contenedor se reinicia constantemente

**Causa:** Falla en el código o configuración.

**Solución:**

```bash
# Ver logs de error
docker logs backend-inmobiliario-api

# Revisar health check
curl http://localhost:8000/health
```

---

## 📊 COMPARACIÓN: RAILWAY vs VPS

| Aspecto | Railway | Tu VPS (Portainer+Swarm) |
|---------|---------|--------------------------|
| **Costo** | $5-20 USD/mes | Incluido en VPS |
| **Setup** | Fácil (10 min) | Medio (1-2 horas) |
| **Control** | Limitado | Completo |
| **Escalabilidad** | Automática | Manual |
| **Monitoreo** | Básico | Avanzado (Portainer) |
| **Backups** | Automáticos | Configurables |
| **Logs** | 7 días gratis | Ilimitados |
| **Updates** | Automáticos | Manuales |
| **SSL** | Incluido | Configurar Nginx + Let's Encrypt |

---

## ✅ CHECKLIST FINAL

Antes de usar en producción:

- [ ] Backend desplegado en VPS
- [ ] Container corriendo sin errores
- [ ] Health check: `curl http://localhost:8000/health` → OK
- [ ] Prueba predicción: `curl http://localhost:8000/api/predictions?lat=20.6597&lon=-103.3496`
- [ ] Frontend actualizado con nueva URL
- [ ] Nginx configurado (si aplica)
- [ ] SSL configurado (HTTPS)
- [ ] Logs funcionando
- [ ] Backup de modelos ML configurado
- [ ] Monitoreo en Portainer activo

---

## 🎉 ¡LISTO!

Tu backend ahora está en tu VPS y bajo tu control total.

**URLs:**
- **Frontend:** https://iagentek.com.mx
- **Backend:** https://api.iagentek.com.mx (tu VPS)
- **Supabase:** https://iagenteksupabase.iagentek.com.mx
- **n8n:** https://iagentekn8nwebhook.iagentek.com.mx

---

**Desarrollado con ❤️ por Samael Hernandez**

