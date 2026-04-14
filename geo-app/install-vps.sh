#!/bin/bash
# ================================================================
# SCRIPT DE INSTALACIÓN AUTOMÁTICA PARA VPS
# Sistema de Análisis de Mercado Inmobiliario
# ================================================================

set -e  # Salir si hay error

echo "🚀 Iniciando instalación del sistema en VPS..."
echo "================================================"

# Verificar que está corriendo como root o con sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Por favor ejecuta este script con sudo"
    exit 1
fi

# ================================================================
# 1. ACTUALIZAR SISTEMA
# ================================================================
echo ""
echo "📦 Paso 1/10: Actualizando sistema..."
apt update && apt upgrade -y

# Instalar herramientas básicas
apt install -y curl wget git vim ufw htop

# ================================================================
# 2. CONFIGURAR FIREWALL
# ================================================================
echo ""
echo "🔥 Paso 2/10: Configurando firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 8000/tcp # Backend API
ufw status

# ================================================================
# 3. INSTALAR PYTHON 3.11
# ================================================================
echo ""
echo "🐍 Paso 3/10: Instalando Python 3.11..."

# Instalar software-properties-common si no existe
apt install -y software-properties-common

# Agregar PPA de deadsnakes
add-apt-repository ppa:deadsnakes/ppa -y
apt update

# Instalar Python 3.11 y herramientas
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Verificar instalación
python3.11 --version

# Actualizar pip
python3.11 -m pip install --upgrade pip

# ================================================================
# 4. INSTALAR LIBRERÍAS DEL SISTEMA
# ================================================================
echo ""
echo "📚 Paso 4/10: Instalando librerías del sistema..."
apt install -y \
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

# ================================================================
# 5. INSTALAR SUPERVISOR
# ================================================================
echo ""
echo "🎯 Paso 5/10: Instalando Supervisor..."
apt install -y supervisor
systemctl enable supervisor
systemctl start supervisor

# ================================================================
# 6. INSTALAR NGINX
# ================================================================
echo ""
echo "🌐 Paso 6/10: Instalando Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx

# ================================================================
# 7. INSTALAR NODE.JS
# ================================================================
echo ""
echo "📦 Paso 7/10: Instalando Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Verificar
node --version
npm --version

# ================================================================
# 8. INSTALAR CERTBOT
# ================================================================
echo ""
echo "🔒 Paso 8/10: Instalando Certbot..."
apt install -y certbot python3-certbot-nginx

# ================================================================
# 9. INSTALAR FAIL2BAN
# ================================================================
echo ""
echo "🛡️ Paso 9/10: Instalando Fail2Ban..."
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# ================================================================
# 10. CREAR DIRECTORIOS
# ================================================================
echo ""
echo "📁 Paso 10/10: Creando directorios..."
mkdir -p /var/www
mkdir -p /var/backups/inmo
chown -R $SUDO_USER:$SUDO_USER /var/www

# ================================================================
# COMPLETADO
# ================================================================
echo ""
echo "✅ Instalación de herramientas completada!"
echo "================================================"
echo ""
echo "📋 Próximos pasos:"
echo "1. Sube tu proyecto a /var/www"
echo "2. Configura el archivo .env en python_services/"
echo "3. Ejecuta: sudo bash configure-app.sh"
echo ""
echo "🎉 ¡Listo para continuar!"

