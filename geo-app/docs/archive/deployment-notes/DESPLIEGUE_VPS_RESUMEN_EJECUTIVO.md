# 🚀 DESPLIEGUE VPS - RESUMEN EJECUTIVO

## ✅ LO QUE YA TIENES LISTO

Tu proyecto ya está **completamente preparado** para desplegarse en VPS:

### Backend Python:
- ✅ **Dockerfile** completo y optimizado
- ✅ **docker-compose.yml** para Portainer/Swarm
- ✅ **requirements.txt** con todas las dependencias
- ✅ Modelos ML entrenados incluidos
- ✅ Documentación completa de despliegue

### Frontend Angular:
- ✅ Build de producción funcional
- ✅ Environment variables configuradas
- ✅ Integración con Supabase lista
- ✅ Integración con n8n lista

---

## 🎯 DOS OPCIONES DE DESPLIEGUE

### **Opción 1: Docker con Portainer (Recomendado) ⭐**

**Ventajas:**
- ✅ Setup rápido (15 minutos)
- ✅ SSL automático con Traefik
- ✅ Reinicio automático
- ✅ Logs centralizados
- ✅ Escalado fácil

**Archivos necesarios:**
```
python_services/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── api/
├── ml_model/
├── integrations/
└── config.py
```

**Pasos:**
1. Subir archivos a VPS
2. Crear `.env` con credenciales
3. Desplegar en Portainer
4. ¡Listo!

**Ver:** `python_services/DEPLOY_VPS.md`

---

### **Opción 2: Instalación Manual (Más Control)**

**Ventajas:**
- ✅ Control total del sistema
- ✅ Debugging más fácil
- ✅ Sin dependencia de Docker

**Archivos necesarios:**
```
python_services/ (completo)
app/ (completo para build)
```

**Pasos:**
1. Ejecutar `install-vps.sh` (instala todas las herramientas)
2. Ejecutar `configure-app.sh` (configura app)
3. Configurar `.env` manualmente
4. Obtener certificado SSL
5. ¡Listo!

**Ver:** `GUIA_DESPLIEGUE_VPS.md`

---

## 📋 ARCHIVOS CLAVE

### Backend:
| Archivo | Propósito |
|---------|-----------|
| `python_services/Dockerfile` | Construcción de imagen Docker |
| `python_services/docker-compose.yml` | Stack para Portainer |
| `python_services/requirements.txt` | Dependencias Python |
| `python_services/config.py` | Configuración global |
| `python_services/api/main.py` | API FastAPI |
| `python_services/ml_model/predictor.py` | Modelo ML |
| `python_services/.env` | Variables de entorno (crear) |

### Frontend:
| Archivo | Propósito |
|---------|-----------|
| `app/src/environments/environment.prod.ts` | Configuración producción |
| `app/package.json` | Dependencias Node.js |
| `app/dist/app/` | Build de producción |

### Scripts:
| Archivo | Propósito |
|---------|-----------|
| `install-vps.sh` | Instala todas las herramientas |
| `configure-app.sh` | Configura aplicación |
| `GUIA_DESPLIEGUE_VPS.md` | Guía completa manual |

---

## 🔐 VARIABLES DE ENTORNO NECESARIAS

```env
# Supabase
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=tu_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key

# PostgreSQL
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password

# API
API_HOST=0.0.0.0
API_PORT=8000

# Seguridad
ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx

# Otros
LOG_LEVEL=ERROR
ENVIRONMENT=production
```

---

## 🚀 DEPLOYMENT RÁPIDO (Elegir una opción)

### **Opción A: Docker (Portainer)**

```bash
# 1. En VPS, clonar o subir proyecto
cd /var/www
git clone tu-repo
cd geo-app/python_services

# 2. Crear .env
nano .env  # Pegar variables de entorno

# 3. Construir imagen
docker build -t backend-inmobiliario:latest .

# 4. Desplegar en Portainer
# Portainer → Stacks → Add Stack → Paste docker-compose.yml → Deploy
```

### **Opción B: Manual (Nginx + Supervisor)**

```bash
# 1. Ejecutar script de instalación
sudo bash install-vps.sh

# 2. Subir proyecto
# Subir geo-app/ a /var/www/

# 3. Configurar app
sudo bash configure-app.sh

# 4. Obtener SSL
sudo certbot --nginx -d tu-dominio.com

# 5. Verificar
curl http://localhost:8000/health
```

---

## 🌐 CONFIGURACIÓN DE DOMINIOS

### DNS Records:

```
Tipo    Nombre                      Valor
A       iainmobiliaria              IP_DEL_VPS
A       www.iainmobiliaria          IP_DEL_VPS
A       api.iainmobiliaria          IP_DEL_VPS
```

### Nginx Reverse Proxy:

```nginx
# Backend (puerto 8000)
server {
    listen 80;
    server_name api.iainmobiliaria.iagentek.com.mx;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}

# Frontend (puerto 80)
server {
    listen 80;
    server_name iainmobiliaria.iagentek.com.mx;
    root /var/www/geo-app/app/dist/app;
    location / {
        try_files $uri /index.html;
    }
}
```

---

## 📊 VERIFICACIÓN POST-DESPLIEGUE

### Checklist:

```bash
# ✅ Backend responde
curl http://localhost:8000/health
curl https://api.iainmobiliaria.iagentek.com.mx/health

# ✅ Frontend carga
curl https://iainmobiliaria.iagentek.com.mx

# ✅ SSL funciona
openssl s_client -connect iainmobiliaria.iagentek.com.mx:443

# ✅ Base de datos conecta
# Probar desde la app web

# ✅ Logs funcionan
sudo tail -f /var/log/inmo-api.out.log
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Problema: "Cannot connect to database"
```bash
# Verificar firewall PostgreSQL
sudo ufw status

# Verificar credenciales en .env
cat .env | grep POSTGRES
```

### Problema: "CORS policy error"
```bash
# Agregar dominio a ALLOWED_ORIGINS
nano python_services/.env
# ALLOWED_ORIGINS=https://iainmobiliaria.iagentek.com.mx
```

### Problema: "Module not found"
```bash
# Reconstruir imagen Docker sin cache
docker build --no-cache -t backend-inmobiliario:latest .
```

### Problema: "502 Bad Gateway"
```bash
# Verificar que backend está corriendo
sudo supervisorctl status
# Ver logs
sudo tail -f /var/log/inmo-api.err.log
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

| Documento | Propósito |
|-----------|-----------|
| `python_services/DEPLOY_VPS.md` | Guía Docker/Portainer |
| `python_services/MIGRAR_DE_RAILWAY_A_VPS.md` | Migración desde Railway |
| `GUIA_DESPLIEGUE_VPS.md` | Guía instalación manual |
| `python_services/README_VPS.md` | Resumen VPS |
| `INSTRUCCIONES_DESPLIEGUE.md` | Guía general |

---

## 🎯 RECOMENDACIÓN FINAL

**Para tu caso:**

1. **Backend:** Usa **Docker con Portainer** (más fácil, más rápido)
2. **Frontend:** Compila y sube archivos estáticos a Hostinger o Netlify
3. **Database:** Ya tienes Supabase funcionando
4. **SSL:** Certbot o Traefik automático

**Tiempo estimado:** 30-45 minutos

---

## ✅ SIGUIENTE PASO

**Elige tu opción favorita y comienza:**

1. Docker → Ver `python_services/DEPLOY_VPS.md`
2. Manual → Ver `GUIA_DESPLIEGUE_VPS.md`
3. Migración Railway → Ver `python_services/MIGRAR_DE_RAILWAY_A_VPS.md`

---

**🎉 ¡Tu proyecto está listo para producción!**

