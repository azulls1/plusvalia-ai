# 🚀 GUÍA COMPLETA DE DESPLIEGUE EN VPS

Esta guía te ayudará a configurar tu VPS para desplegar el sistema completo de análisis de mercado inmobiliario.

---

## 📋 REQUISITOS PREVIOS

### Hardware Recomendado:
- **CPU:** 2+ núcleos
- **RAM:** 4GB+ (8GB recomendado)
- **Disco:** 20GB+ SSD
- **Sistema:** Ubuntu 22.04 LTS o Debian 11+

### Acceso:
- SSH al servidor
- Permisos de sudo (root)

---

## 🔧 PASO 1: CONFIGURACIÓN INICIAL DEL VPS

### 1.1 Actualizar el Sistema

```bash
# Conectar al VPS
ssh usuario@tu-servidor.com

# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar herramientas básicas
sudo apt install -y curl wget git vim ufw
```

### 1.2 Configurar Firewall

```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH (IMPORTANTE: Antes de bloquear)
sudo ufw allow 22/tcp

# Permitir puertos necesarios
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8000/tcp    # Backend API (o el puerto que uses)

# Ver estado
sudo ufw status
```

---

## 🐍 PASO 2: INSTALAR PYTHON Y DEPENDENCIAS

### 2.1 Instalar Python 3.11

```bash
# Instalar Python 3.11 desde deadsnakes PPA
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Verificar instalación
python3.11 --version

# Actualizar pip
python3.11 -m pip install --upgrade pip
```

### 2.2 Instalar Librerías del Sistema

```bash
# Librerías necesarias para dependencias Python
sudo apt install -y \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev
```

---

## 📦 PASO 3: SUBIR EL PROYECTO

### 3.1 Crear Directorio del Proyecto

```bash
# Crear directorio de proyectos
sudo mkdir -p /var/www
sudo chown -R $USER:$USER /var/www
cd /var/www

# Clonar repositorio (reemplazar con tu repo)
git clone https://github.com/tu-usuario/Analisis-mercado-evaluacion-terrenos.git
cd Analisis-mercado-evaluacion-terrenos/geo-app

# O subir archivos manualmente si no usas Git
```

### 3.2 Configurar Backend Python

```bash
# Ir a directorio de Python services
cd python_services

# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalación
pip list
```

### 3.3 Crear Archivo .env

```bash
# Crear archivo .env
nano .env
```

**Contenido del archivo .env:**

```env
# ================================================================
# CONFIGURACIÓN SUPABASE
# ================================================================
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogInNlcnZpY2Vfcm9sZSIsCiAgImlzcyI6ICJzdXBhYmFzZSIsCiAgImlhdCI6IDE3MTUwNTA4MDAsCiAgImV4cCI6IDE4NzI4MTcyMDAKfQ.YOUR_SERVICE_ROLE_KEY_HERE

# ================================================================
# CONFIGURACIÓN POSTGRESQL
# ================================================================
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.iagenteksupabase
POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE

# ================================================================
# CONFIGURACIÓN API
# ================================================================
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production
LOG_LEVEL=ERROR
DEBUG=false

# ================================================================
# SEGURIDAD
# ================================================================
ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx,https://www.iainmobiliaria.iagentek.com.mx
MAX_REQUESTS_PER_HOUR=1000

# ================================================================
# EXTERNAL SERVICES
# ================================================================
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
NOMINATIM_BASE=https://nominatim.openstreetmap.org
OVERPASS_BASE=https://overpass-api.de/api/interpreter
OSM_USER_AGENT=inmo-geo-mvp/1.0 (contacto@iagentek.com.mx)
```

**⚠️ IMPORTANTE:** Reemplazar:
- `YOUR_SERVICE_ROLE_KEY_HERE` con tu service role key real
- `YOUR_POSTGRES_PASSWORD_HERE` con tu password de PostgreSQL
- `YOUR_OPENAI_API_KEY_HERE` con tu API key de OpenAI

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🎯 PASO 4: CONFIGURAR SUPERVISOR

Supervisor mantendrá el backend Python corriendo automáticamente.

### 4.1 Instalar Supervisor

```bash
sudo apt install -y supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

### 4.2 Crear Configuración de Supervisor

```bash
sudo nano /etc/supervisor/conf.d/inmo-api.conf
```

**Contenido:**

```ini
[program:inmo-api]
directory=/var/www/Analisis-mercado-evaluacion-terrenos/geo-app/python_services
command=/var/www/Analisis-mercado-evaluacion-terrenos/geo-app/python_services/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/inmo-api.err.log
stdout_logfile=/var/log/inmo-api.out.log
redirect_stderr=true
stopwaitsecs=10
environment=PATH="/var/www/Analisis-mercado-evaluacion-terrenos/geo-app/python_services/venv/bin"
```

**⚠️ IMPORTANTE:** Ajustar rutas según tu instalación

### 4.3 Iniciar Servicio

```bash
# Recargar supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar servicio
sudo supervisorctl start inmo-api

# Verificar estado
sudo supervisorctl status

# Ver logs
sudo tail -f /var/log/inmo-api.out.log
```

---

## 🌐 PASO 5: CONFIGURAR NGINX (Reverso Proxy)

Nginx servirá el frontend Angular y actuará como proxy reverso para el backend.

### 5.1 Instalar Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 5.2 Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/iainmobiliaria
```

**Contenido:**

```nginx
# Backend API
server {
    listen 80;
    server_name api.iainmobiliaria.iagentek.com.mx;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para peticiones largas
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Frontend Angular
server {
    listen 80;
    server_name iainmobiliaria.iagentek.com.mx www.iainmobiliaria.iagentek.com.mx;

    root /var/www/Analisis-mercado-evaluacion-terrenos/geo-app/app/dist/app;
    index index.html;

    # Compresión gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;

    # Cache para assets estáticos
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Rutas de Angular (SPA)
    location / {
        try_files $uri $uri/ /index.html;
        
        # No cache para index.html
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    }

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5.3 Habilitar Sitio

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/iainmobiliaria /etc/nginx/sites-enabled/

# Eliminar sitio por defecto
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Recargar nginx
sudo systemctl reload nginx
```

---

## 📦 PASO 6: INSTALAR CERTIFICADO SSL

### 6.1 Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 6.2 Obtener Certificado

```bash
# Obtener certificado para todos los dominios
sudo certbot --nginx -d iainmobiliaria.iagentek.com.mx -d www.iainmobiliaria.iagentek.com.mx -d api.iainmobiliaria.iagentek.com.mx

# Seguir el wizard interactivo
# Contestar preguntas:
# - Email: tu@email.com
# - Aceptar términos: Yes
# - Compartir email con EFF: No (o Yes si quieres)
# - Redirect HTTP to HTTPS: Yes
```

### 6.3 Configurar Renovación Automática

```bash
# Verificar que certbot está configurado
sudo certbot renew --dry-run

# Los certificados se renuevan automáticamente
```

---

## 🏗️ PASO 7: COMPILAR Y DESPLEGAR FRONTEND

### 7.1 Instalar Node.js

```bash
# Instalar Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar
node --version  # Debería mostrar v18.x.x
npm --version   # Debería mostrar 9.x.x
```

### 7.2 Instalar Angular CLI

```bash
sudo npm install -g @angular/cli@16.2.8

# Verificar
ng version
```

### 7.3 Compilar Frontend

```bash
# Ir a directorio de app
cd /var/www/Analisis-mercado-evaluacion-terrenos/geo-app/app

# Instalar dependencias
npm install

# Editar environment.prod.ts para apuntar a backend real
nano src/environments/environment.prod.ts

# Compilar para producción
ng build --configuration production

# Verificar que se creó la carpeta dist/app
ls -la dist/app/
```

---

## ✅ PASO 8: VERIFICAR DESPLIEGUE

### 8.1 Verificar Backend

```bash
# Verificar logs
sudo tail -f /var/log/inmo-api.out.log

# Verificar que está corriendo
curl http://localhost:8000/health

# Verificar desde el host
curl http://api.iainmobiliaria.iagentek.com.mx/health
```

### 8.2 Verificar Frontend

```bash
# Verificar archivos
ls -la /var/www/Analisis-mercado-evaluacion-terrenos/geo-app/app/dist/app/

# Verificar nginx
sudo nginx -t
sudo systemctl status nginx

# Verificar acceso
curl https://iainmobiliaria.iagentek.com.mx
```

---

## 🔄 PASO 9: CONFIGURAR ACTUALIZACIONES AUTOMÁTICAS

### 9.1 Script de Actualización

```bash
nano /var/www/update-app.sh
```

**Contenido:**

```bash
#!/bin/bash
# Script de actualización del sistema

cd /var/www/Analisis-mercado-evaluacion-terrenos/geo-app

echo "🔄 Actualizando aplicación..."

# Actualizar código
git pull origin main

# Backend
echo "📦 Actualizando backend..."
cd python_services
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo supervisorctl restart inmo-api

# Frontend
echo "🌐 Actualizando frontend..."
cd ../app
npm install
ng build --configuration production
sudo systemctl reload nginx

echo "✅ Actualización completada"
```

```bash
# Hacer ejecutable
chmod +x /var/www/update-app.sh
```

---

## 📊 PASO 10: MONITOREO Y MANTENIMIENTO

### 10.1 Ver Logs

```bash
# Logs del backend
sudo tail -f /var/log/inmo-api.out.log
sudo tail -f /var/log/inmo-api.err.log

# Logs de nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs de supervisor
sudo supervisorctl tail -f inmo-api
```

### 10.2 Comandos Útiles

```bash
# Reiniciar backend
sudo supervisorctl restart inmo-api

# Reiniciar nginx
sudo systemctl restart nginx

# Reiniciar supervisor
sudo systemctl restart supervisor

# Ver estado de todo
sudo supervisorctl status
sudo systemctl status nginx
```

---

## 🔒 PASO 11: SEGURIDAD ADICIONAL

### 11.1 Fail2Ban (Protección contra Brute Force)

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 11.2 Backup Automático

```bash
nano /var/www/backup.sh
```

**Contenido:**

```bash
#!/bin/bash
# Script de backup

BACKUP_DIR="/var/backups/inmo"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup de archivos
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
    /var/www/Analisis-mercado-evaluacion-terrenos/geo-app

# Mantener solo últimos 7 backups
find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup creado: app_backup_$DATE.tar.gz"
```

```bash
chmod +x /var/www/backup.sh

# Agregar a crontab (backup diario a las 3 AM)
(crontab -l 2>/dev/null; echo "0 3 * * * /var/www/backup.sh") | crontab -
```

---

## 📝 RESUMEN DE COMANDOS IMPORTANTES

```bash
# Reiniciar backend
sudo supervisorctl restart inmo-api

# Reiniciar nginx
sudo systemctl restart nginx

# Ver logs
sudo tail -f /var/log/inmo-api.out.log

# Actualizar aplicación
/var/www/update-app.sh

# Crear backup
/var/www/backup.sh

# Ver estado
sudo supervisorctl status
```

---

## ✅ CHECKLIST FINAL

- [ ] Backend Python corriendo en puerto 8000
- [ ] Frontend compilado en dist/app
- [ ] Nginx configurado y sirviendo archivos
- [ ] SSL instalado y funcionando
- [ ] Supervisor mantiene backend activo
- [ ] Firewall configurado correctamente
- [ ] Backups automáticos configurados
- [ ] Logs accesibles y funcionando
- [ ] Acceso HTTPS funcionando
- [ ] API respondiendo en /health

---

**🎉 ¡Despliegue completado!**

Tu sistema ahora está funcionando en:
- Frontend: `https://iainmobiliaria.iagentek.com.mx`
- Backend API: `https://api.iainmobiliaria.iagentek.com.mx`

