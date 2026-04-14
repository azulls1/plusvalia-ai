#!/bin/bash
# ================================================================
# SCRIPT DE CONFIGURACIÓN DE LA APLICACIÓN
# Configura supervisor, nginx y compila frontend
# ================================================================

set -e

echo "⚙️ Configurando aplicación..."
echo "============================="

# Verificar que está corriendo como root o con sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Por favor ejecuta este script con sudo"
    exit 1
fi

# Variables (AJUSTAR SEGÚN TU INSTALACIÓN)
APP_DIR="/var/www/Analisis-mercado-evaluacion-terrenos/geo-app"
BACKEND_DIR="$APP_DIR/python_services"
FRONTEND_DIR="$APP_DIR/app"
DOMAIN="iainmobiliaria.iagentek.com.mx"

# Verificar que existe el proyecto
if [ ! -d "$APP_DIR" ]; then
    echo "❌ No se encontró el proyecto en $APP_DIR"
    echo "Por favor sube el proyecto primero"
    exit 1
fi

# ================================================================
# 1. CONFIGURAR BACKEND
# ================================================================
echo ""
echo "🐍 Configurando backend Python..."

if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
else
    echo "⚠️ No se encontró $BACKEND_DIR, saltando..."
fi

# ================================================================
# 2. CONFIGURAR SUPERVISOR
# ================================================================
echo ""
echo "🎯 Configurando Supervisor..."

cat > /etc/supervisor/conf.d/inmo-api.conf <<EOF
[program:inmo-api]
directory=$BACKEND_DIR
command=$BACKEND_DIR/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/inmo-api.err.log
stdout_logfile=/var/log/inmo-api.out.log
redirect_stderr=true
stopwaitsecs=10
environment=PATH="$BACKEND_DIR/venv/bin"
EOF

supervisorctl reread
supervisorctl update
supervisorctl start inmo-api || true

echo "✅ Supervisor configurado"

# ================================================================
# 3. CONFIGURAR NGINX
# ================================================================
echo ""
echo "🌐 Configurando Nginx..."

cat > /etc/nginx/sites-available/iainmobiliaria <<'EOF'
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

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    }

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
EOF

# Crear symlink
ln -sf /etc/nginx/sites-available/iainmobiliaria /etc/nginx/sites-enabled/

# Eliminar default
rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
nginx -t

# Recargar nginx
systemctl reload nginx

echo "✅ Nginx configurado"

# ================================================================
# 4. COMPILAR FRONTEND
# ================================================================
echo ""
echo "📦 Compilando frontend Angular..."

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    # Instalar dependencias
    if [ ! -d "node_modules" ]; then
        npm install -g @angular/cli@16.2.8
        npm install
    fi
    
    # Compilar
    ng build --configuration production
    
    echo "✅ Frontend compilado"
else
    echo "⚠️ No se encontró $FRONTEND_DIR, saltando..."
fi

# ================================================================
# COMPLETADO
# ================================================================
echo ""
echo "✅ Configuración completada!"
echo "============================="
echo ""
echo "📋 Próximos pasos:"
echo "1. Edita el archivo .env en python_services/"
echo "2. Ejecuta: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN -d api.$DOMAIN"
echo "3. Verifica: curl http://localhost:8000/health"
echo ""
echo "🎉 ¡Listo para usar!"

