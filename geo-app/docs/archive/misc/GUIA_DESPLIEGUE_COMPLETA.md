# 🚀 GUÍA COMPLETA: Desplegar Backend Inmobiliario en VPS

## Guía Específica para tu Proyecto de Análisis Inmobiliario

Esta guía combina los archivos ya creados con el proceso paso a paso adaptado a tu infraestructura específica.

---

## 📋 ÍNDICE

1. [Antes de Empezar](#antes-de-empezar)
2. [Paso 1: Preparar Espacio en VPS](#paso-1-preparar-espacio-en-vps)
3. [Paso 2: Subir Archivos del Proyecto](#paso-2-subir-archivos-del-proyecto)
4. [Paso 3: Construir Imagen Docker](#paso-3-construir-imagen-docker)
5. [Paso 4: Configurar DNS en Hostinger](#paso-4-configurar-dns-en-hostinger)
6. [Paso 5: Crear Stack en Portainer](#paso-5-crear-stack-en-portainer)
7. [Paso 6: Desplegar y Verificar](#paso-6-desplegar-y-verificar)
8. [Troubleshooting](#troubleshooting)

---

## ✅ ANTES DE EMPEZAR

### Ya tienes configurado:
- ✅ VPS con Docker Swarm
- ✅ Portainer: https://iagentekportainer.iagentek.com.mx
- ✅ Traefik corriendo
- ✅ Supabase: https://iagenteksupabase.iagentek.com.mx
- ✅ Red `traefik_default` activa

### Información de tu proyecto:
```
Nombre del proyecto: backend-inmobiliario
Subdominio backend:  apiinmobiliario.iagentek.com.mx
Puerto interno:     8000
Stack name:         backend-inmobiliario
Imagen Docker:      backend-inmobiliario:latest
```

---

## 🔧 PASO 1: PREPARAR ESPACIO EN VPS

### Conectar por SSH

**Usando PuTTY:**
```
1. Abre PuTTY
2. Host Name: [IP_DE_TU_VPS]
3. Port: 22
4. Login: root
5. Password: [tu_contraseña]
```

### Crear Directorio

```bash
# Crear directorio específico para este proyecto
mkdir -p /root/backend-inmobiliario

# Entrar
cd /root/backend-inmobiliario

# Verificar
pwd
# Debería mostrar: /root/backend-inmobiliario
```

---

## 📤 PASO 2: SUBIR ARCHIVOS DEL PROYECTO

### Opción A: WinSCP (Recomendado)

#### Conectar WinSCP:
```
1. Abre WinSCP
2. Host name: [IP_DE_TU_VPS]
3. Username: root
4. Password: [tu_contraseña]
5. Port: 22
6. Click: "Login"
```

#### Subir archivos:
```
Panel izquierdo (tu PC):
  → C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services

Panel derecho (VPS):
  → /root/backend-inmobiliario/

Acción:
  → Selecciona TODOS los archivos:
     ✓ api/
     ✓ ml_model/
     ✓ integrations/
     ✓ scrapers/
     ✓ Dockerfile
     ✓ docker-compose.yml
     ✓ requirements.txt
     ✓ config.py
     ✓ .dockerignore
  
  → Arrastra del izquierdo al derecho
  → Espera a que termine la transferencia
```

#### Verificar archivos:
```bash
# Desde PuTTY
cd /root/backend-inmobiliario
ls -la

# Deberías ver:
# Dockerfile
# docker-compose.yml
# requirements.txt
# api/
# ml_model/
# etc.
```

### Opción B: SCP desde PowerShell

```powershell
# Desde PowerShell en tu PC
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services

scp -r * root@[IP_VPS]:/root/backend-inmobiliario/
```

---

## 🐳 PASO 3: CONSTRUIR IMAGEN DOCKER

### Verificar Dockerfile

```bash
# Desde PuTTY
cd /root/backend-inmobiliario

ls -la Dockerfile

# Si existe, continuar
# Si NO existe, ya deberías haberlo subido en el paso anterior
```

### Construir la Imagen

```bash
# Asegúrate de estar en el directorio correcto
cd /root/backend-inmobiliario

# Construir imagen (toma 5-15 minutos)
docker build -t backend-inmobiliario:latest .

# Ver progreso...
```

**⚠️ Importante:** La primera vez puede tardar porque descarga:
- Python 3.11 base image
- Todas las dependencias Python (FastAPI, scikit-learn, XGBoost, etc.)
- Compila algunas dependencias (XGBoost requiere compilación)

### Verificar que la Imagen se Creó

```bash
# Listar imágenes
docker images | grep backend-inmobiliario

# Deberías ver algo como:
# backend-inmobiliario   latest   abc123def456   5 minutes ago   1.2GB
```

**💡 Tamaño esperado:** ~1-1.5GB (incluye modelos ML y dependencias)

---

## 🌐 PASO 4: CONFIGURAR DNS EN HOSTINGER

### Acceder a Hostinger

```
1. Abre: https://hpanel.hostinger.com/
2. Login con tu cuenta
3. Ve a: Dominios
4. Click en: iagentek.com.mx
5. Click: "Zona DNS" o "DNS"
```

### Crear Registro DNS para Backend

```
Click: "Agregar registro" o "Añadir registro"

Configurar:
┌─────────────────────────────────────────┐
│ Tipo:        A                          │
│ Nombre:      apiinmobiliario           │
│ Apunta a:    [IP_DE_TU_VPS]             │
│ TTL:         3600 (1 hora)              │
└─────────────────────────────────────────┘

Click: "Guardar"
```

**⚠️ Restricciones de Hostinger:**
- ❌ NO puedes usar wildcards (`*.iagentek.com.mx`) en planes básicos
- ✅ SÍ puedes crear múltiples subdominios manualmente
- ⏰ Propagación: 5 minutos - 2 horas

### Verificar Propagación DNS

```
Abre: https://dnschecker.org/

Busca: apiinmobiliario.iagentek.com.mx

Debería mostrar tu IP_VPS en todos los servidores DNS mundialmente
```

**⏰ Espera antes de continuar:** Al menos 10 minutos para que DNS se propague

---

## 🐋 PASO 5: CREAR STACK EN PORTAINER

### Acceder a Portainer

```
1. Abre: https://iagentekportainer.iagentek.com.mx
2. Login:
   - Usuario: admin
   - Password: [tu_contraseña]
3. Seleccionar Environment: "primary"
```

### Crear Nuevo Stack

```
1. Menú lateral → Click: "Stacks"

2. Click: "+ Add stack" (botón verde arriba)

3. Configurar:
   ┌─────────────────────────────────────┐
   │ Name: backend-inmobiliario         │
   │                                     │
   │ Build method:                      │
   │   🔘 Web editor                    │
   │   ⚪ Upload                        │
   │   ⚪ Repository                    │
   └─────────────────────────────────────┘
```

### Copiar docker-compose.yml

**📋 Ya está listo en tu proyecto:** `docker-compose.yml`

Abre este archivo en tu PC y **copia TODO el contenido**, luego pégalo en el Web editor de Portainer.

**O mejor:** Lee el archivo completo desde aquí:

```yaml
version: '3.8'

services:
  backend-api:
    image: backend-inmobiliario:latest
    build:
      context: .
      dockerfile: Dockerfile
    
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - API_WORKERS=4
      
      # Supabase
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      
      # PostgreSQL
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_PORT=${POSTGRES_PORT:-5432}
      - POSTGRES_DB=${POSTGRES_DB:-postgres}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      
      # CORS Origins
      - ALLOWED_ORIGINS=https://iagentek.com.mx,http://localhost:4200
      
      # ML Model
      - MODEL_PATH=/app/ml_model/models
      - MODEL_RETRAIN_DAYS=30
      
      # Logging
      - LOG_LEVEL=INFO
      - PYTHONUNBUFFERED=1
    
    volumes:
      - model_cache:/app/ml_model/models
      - logs:/app/logs
      - data:/app/data
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    labels:
      - traefik.enable=true
      - traefik.http.routers.backend-inmobiliario.rule=Host(`apiinmobiliario.iagentek.com.mx`)
      - traefik.http.routers.backend-inmobiliario.entrypoints=websecure
      - traefik.http.routers.backend-inmobiliario.tls.certresolver=letsencryptresolver
      - traefik.http.services.backend-inmobiliario.loadbalancer.server.port=8000
      - traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolalloworiginlist=https://iagentek.com.mx
      - traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS
      - traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolmaxage=100
      - traefik.http.middlewares.backend-inmobiliario-cors.headers.addvaryheader=true
      - traefik.http.routers.backend-inmobiliario.middlewares=backend-inmobiliario-cors@docker
    
    networks:
      - traefik_default
    
    deploy:
      replicas: 1
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3
        window: 120s
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

volumes:
  model_cache:
    driver: local
  logs:
    driver: local
  data:
    driver: local

networks:
  traefik_default:
    external: true
```

**✅ Este YAML ya está optimizado para tu infraestructura**

---

## 🔐 PASO 6: CONFIGURAR VARIABLES DE ENTORNO

### En Portainer

```
Scroll hacia abajo en la página de crear stack

Click: "Environment variables"

Click: "Advanced mode"
```

### Variables Requeridas

Pega esto en Advanced mode y **reemplaza los valores con los tuyos**:

```env
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k
SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY_AQUI
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU_PASSWORD_SUPABASE_AQUI
ALLOWED_ORIGINS=https://iagentek.com.mx
```

**⚠️ IMPORTANTE:** Reemplaza:
- `TU_SERVICE_ROLE_KEY_AQUI` → Tu service role key de Supabase
- `TU_PASSWORD_SUPABASE_AQUI` → Tu contraseña de PostgreSQL

**💡 Formato:**
- Una variable por línea
- Formato: `NOMBRE=valor` (sin espacios alrededor del =)
- Sin comillas (a menos que el valor tenga espacios)
- No dejar líneas en blanco entre variables

---

## 🚀 PASO 7: DESPLEGAR Y VERIFICAR

### Desplegar el Stack

```
1. En Portainer, scroll hasta el final

2. Verifica que:
   ✓ docker-compose.yml está pegado
   ✓ Variables de entorno configuradas
   ✓ No hay errores de sintaxis (rojos en el editor)

3. Click: "Deploy the stack" (botón azul grande)

4. Espera 3-8 minutos mientras:
   🔄 Portainer construye la imagen
   🔄 Traefik detecta el nuevo servicio
   🔄 SSL se configura automáticamente
   🔄 Contenedor inicia
```

### Verificar Estado en Portainer

```
1. Ve a: Stacks → backend-inmobiliario

2. Debe mostrar:
   Status: ✅ 1 running (verde)

3. Click en el contenedor para ver detalles

4. Ve a: "Logs"
   - Busca: "🚀 Iniciando servidor en 0.0.0.0:8000"
   - No debe haber errores rojos

5. Ve a: "Health"
   - Espera 60 segundos
   - Status: ✅ Healthy
```

### Verificar Health Check

```bash
# Desde PuTTY o tu PC
curl https://apiinmobiliario.iagentek.com.mx/health

# Deberías ver:
{
  "status": "healthy",
  "model_loaded": true
}
```

### Verificar desde Navegador

```
Abre: https://apiinmobiliario.iagentek.com.mx/

Deberías ver respuesta JSON con información de la API
```

**✅ Respuesta esperada:**
```json
{
  "name": "Análisis de Mercado Inmobiliario - API ML",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### Verificar SSL

```
En el navegador:
✓ Candado verde en la barra de direcciones
✓ "Conexión segura" visible
✓ Certificado válido de Let's Encrypt
✓ Sin advertencias de seguridad
```

**⏰ SSL:** Puede tardar 5-10 minutos después del primer deploy

---

## 📝 PASO 8: ACTUALIZAR FRONTEND

### Actualizar environment.prod.ts

```bash
# En tu PC
cd geo-app/app/src/environments

# Editar environment.prod.ts
nano environment.prod.ts
```

**Cambiar:**
```typescript
export const environment = {
  production: true,
  // Cambiar esta línea:
  mlApiBase: "https://apiinmobiliario.iagentek.com.mx",  // ← Nueva URL VPS
  // Ya no: https://analisis-inmobiliario-backend-production.up.railway.app
  // ... resto de configuración
};
```

### Rebuild Frontend

```bash
cd geo-app/app
npm run build

# Verificar que se creó la carpeta dist/app/
```

### Subir a Hostinger

```
1. Abre Hostinger File Manager
2. Sube todos los archivos de geo-app/app/dist/app/
3. Verifica que .htaccess esté incluido
4. Accede a: https://iagentek.com.mx
```

---

## 🔧 TROUBLESHOOTING

### ❌ Error: "Cannot connect to database"

**Causa:** PostgreSQL no permite conexiones remotas

**Solución:**
```bash
# En tu VPS de Supabase
sudo nano /etc/postgresql/15/main/postgresql.conf

# Buscar y cambiar:
listen_addresses = '*'

# Guardar y continuar
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Agregar al final:
host all all 0.0.0.0/0 md5

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

---

### ❌ Error: "Network traefik_default not found"

**Solución:**
```bash
# Verificar que Traefik esté corriendo
docker service ls | grep traefik

# Verificar red existe
docker network ls | grep traefik_default

# Si NO existe (raro):
docker network create --driver overlay traefik_default
```

---

### ❌ Error: "502 Bad Gateway"

**Solución:**
```
1. Ver logs del contenedor:
   Portainer → backend-inmobiliario → Logs
   Busca errores

2. Verificar puerto:
   Debe ser: traefik.http.services.backend-inmobiliario.loadbalancer.server.port=8000

3. Verificar DNS propagado:
   https://dnschecker.org/

4. Reiniciar contenedor:
   Portainer → Stacks → backend-inmobiliario → Restart
```

---

### ❌ Error: "CORS blocked"

**Solución:**
```
1. Verificar ALLOWED_ORIGINS en variables:
   Debe ser: https://iagentek.com.mx

2. Verificar labels de CORS coinciden

3. Actualizar stack en Portainer
```

---

### ❌ SSL no se genera

**Solución:**
```
1. Verificar DNS propagado completamente:
   https://dnschecker.org/
   Debe mostrar IP_VPS en TODO el mundo

2. Verificar label correcto:
   Host(`apiinmobiliario.iagentek.com.mx`)
   Sin espacios, exactamente así

3. Esperar 10 minutos (Let's Encrypt puede tardar)

4. Ver logs de Traefik:
   docker service logs traefik_traefik -f
```

---

### ❌ Contenedor se detiene inmediatamente

**Solución:**
```
1. Ver logs:
   Portainer → Container → Logs
   
   Busca:
   - "Variables de entorno faltantes"
   - "Cannot connect to database"
   - Errores de Python

2. Verificar variables de entorno:
   Todas las que terminan en _KEY o _PASSWORD deben estar configuradas

3. Probar localmente:
   Desde PuTTY:
   docker run --rm -p 8000:8000 \
     --env SUPABASE_URL=https://... \
     --env POSTGRES_HOST=... \
     backend-inmobiliario:latest
```

---

### ⚠️ Modelo ML no carga

**Posible causa:** Volumen vacío

**Solución:**
```bash
# Copiar modelos al volumen
docker exec backend-inmobiliario-api cp -r /app/ml_model/models/* /app/ml_model/models/

# O reconstruir con modelos incluidos
# Los modelos ya están en el directorio, deberían copiarse automáticamente
```

---

## ✅ CHECKLIST COMPLETO

```
PREPARACIÓN:
⬜ Directorio creado: /root/backend-inmobiliario
⬜ Archivos subidos al VPS
⬜ Dockerfile presente
⬜ docker-compose.yml presente
⬜ Imagen construida: backend-inmobiliario:latest
⬜ Imagen verificada (docker images)

DNS:
⬜ Registro A creado: apiinmobiliario → IP_VPS
⬜ DNS propagado (verificado en dnschecker.org)

PORTAINER:
⬜ Stack creado: backend-inmobiliario
⬜ docker-compose.yml pegado
⬜ Variables de entorno configuradas:
  ⬜ SUPABASE_URL
  ⬜ SUPABASE_KEY
  ⬜ SUPABASE_SERVICE_ROLE_KEY
  ⬜ POSTGRES_HOST
  ⬜ POSTGRES_PORT
  ⬜ POSTGRES_DB
  ⬜ POSTGRES_USER
  ⬜ POSTGRES_PASSWORD
  ⬜ ALLOWED_ORIGINS
⬜ Stack desplegado exitosamente

VERIFICACIÓN:
⬜ Contenedor corriendo (Status: Running)
⬜ Health check: Healthy
⬜ API responde: https://apiinmobiliario.iagentek.com.mx
⬜ SSL funcionando (candado verde)
⬜ Logs sin errores críticos
⬜ /health retorna status: healthy
⬜ Modelo ML cargado

FRONTEND:
⬜ environment.prod.ts actualizado con nueva URL
⬜ ng build completado
⬜ Frontend subido a Hostinger
⬜ Frontend puede conectar al backend
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

- **Guía completa:** `DEPLOY_VPS.md`
- **Arquitectura técnica:** `ARQUITECTURA_VPS.md`
- **Resumen ejecutivo:** `RESUMEN_MIGRACION_VPS.md`
- **Quick start:** `MIGRAR_DE_RAILWAY_A_VPS.md`
- **README:** `README_VPS.md`

---

## 🎯 RESUMEN DEL PROCESO

```
1. Preparar → mkdir /root/backend-inmobiliario en VPS
2. Subir → Archivos vía WinSCP/SCP
3. Build → docker build -t backend-inmobiliario:latest .
4. DNS → Hostinger → A → apiinmobiliario → IP_VPS
5. Stack → Portainer → Crear → Pegar docker-compose.yml
6. Env → Variables de entorno configuradas
7. Deploy → Click "Deploy the stack"
8. Verify → https://apiinmobiliario.iagentek.com.mx funcionando
9. Frontend → Actualizar environment.prod.ts → ng build → Subir a Hostinger
```

---

## 🎉 ¡LISTO!

**Tu backend inmobiliario está 100% desplegado en tu VPS** 🚀

**URLs finales:**
- Backend: https://apiinmobiliario.iagentek.com.mx
- Frontend: https://iagentek.com.mx
- Supabase: https://iagenteksupabase.iagentek.com.mx
- Portainer: https://iagentekportainer.iagentek.com.mx

---

**Desarrollado con ❤️ por Samael Hernandez**

