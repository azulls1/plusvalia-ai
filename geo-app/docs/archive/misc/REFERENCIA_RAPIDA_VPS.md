# 🔑 REFERENCIA RÁPIDA: Despliegue Backend Inmobiliario

## ⚡ Valores Exactos de Tu Infraestructura

---

## 🐋 **PORTAINER**

```
URL:      https://iagentekportainer.iagentek.com.mx
User:     admin
Pass:     iagentek_123
Env:      primary
```

---

## 🌐 **REDES DOCKER**

```
Red principal:   traefik_default (SIEMPRE usar esta)
Red interna:     iagenteknet (opcional)
Tipo:            External overlay (Docker Swarm)
Verificar:       docker network ls | grep traefik
```

---

## 🔒 **TRAEFIK**

```
Stack name:        traefik
Entrypoint HTTPS:  websecure (NO "web")
Cert Resolver:     letsencryptresolver (NO "letsencrypt")
Verificar:         docker service ls | grep traefik
```

---

## 🗄️ **SUPABASE**

```
URL:      https://iagenteksupabase.iagentek.com.mx
DB Host:  iagenteksupabase.iagentek.com.mx
Port:     5432
User:     postgres
Pass:     Iagentek_123
DB:       postgres
Stack:    supabase
Network:  traefik_default
```

---

## 📁 **CONFIGURACIÓN PROYECTO**

```
Nombre:           backend-inmobiliario
Imagen:           backend-inmobiliario:latest
Stack:            backend-inmobiliario
Container:        backend-inmobiliario-api
Domain:           apiinmobiliario.iagentek.com.mx
Puerto:           8000
Directorio VPS:   /root/backend-inmobiliario
```

---

## 📋 **VARIABLES DE ENTORNO**

```env
# Supabase
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k
SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY_AQUI

# PostgreSQL
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=Iagentek_123

# CORS
ALLOWED_ORIGINS=https://iagentek.com.mx
```

---

## ⚙️ **LABELS TRAEFIK (copiar y pegar)**

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.backend-inmobiliario.rule=Host(`apiinmobiliario.iagentek.com.mx`)
  - traefik.http.routers.backend-inmobiliario.entrypoints=websecure
  - traefik.http.routers.backend-inmobiliario.tls.certresolver=letsencryptresolver
  - traefik.http.services.backend-inmobiliario.loadbalancer.server.port=8000
  - traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS
  - traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolalloworiginlist=https://iagentek.com.mx
  - traefik.http.middlewares.backend-inmobiliario-cors.headers.accesscontrolmaxage=100
  - traefik.http.middlewares.backend-inmobiliario-cors.headers.addvaryheader=true
  - traefik.http.routers.backend-inmobiliario.middlewares=backend-inmobiliario-cors@docker
```

---

## 📊 **RECURSOS**

```
CPU Máximo:    2.0 cores
RAM Máximo:    2 GB
CPU Mínimo:    0.5 cores
RAM Mínimo:    512 MB
```

---

## 🚀 **COMANDOS RÁPIDOS**

```bash
# Verificar redes
docker network ls | grep traefik

# Verificar Traefik
docker service ls | grep traefik

# Verificar Supabase
docker service ls | grep supabase

# Construir imagen
cd /root/backend-inmobiliario
docker build -t backend-inmobiliario:latest .

# Ver logs
docker service logs backend-inmobiliario_backend-api -f

# Reiniciar servicio
docker service update --force backend-inmobiliario_backend-api

# Ver uso de recursos
docker stats backend-inmobiliario-api
```

---

## ✅ **CHECKLIST**

```
[ ] Directorio creado: /root/backend-inmobiliario
[ ] Archivos subidos
[ ] Imagen construida
[ ] DNS configurado: apiinmobiliario → IP_VPS
[ ] Stack creado en Portainer
[ ] docker-compose.yml pegado
[ ] Variables configuradas
[ ] Deploy exitoso
[ ] Contenedor running
[ ] Health check: Healthy
[ ] SSL funcionando
[ ] API responde: https://apiinmobiliario.iagentek.com.mx
```

---

## 🔗 **URLS**

```
Portainer:    https://iagentekportainer.iagentek.com.mx
Supabase:     https://iagenteksupabase.iagentek.com.mx
Backend API:  https://apiinmobiliario.iagentek.com.mx
Frontend:     https://iagentek.com.mx (Hostinger)
```

---

## 🐛 **TROUBLESHOOTING RÁPIDO**

| Error | Verificar |
|-------|-----------|
| Image not found | `docker images \| grep backend-inmobiliario` |
| Network not found | `docker network ls \| grep traefik` |
| 502 Bad Gateway | Logs: `docker service logs backend-inmobiliario_backend-api` |
| CORS blocked | Variable: `ALLOWED_ORIGINS` correcta |
| SSL no funciona | DNS propagado, esperar 10 min |
| Contenedor cae | Logs con errores de BD o variables |

---

## 📚 **DOCUMENTACIÓN**

- **Guía completa:** `GUIA_DESPLIEGUE_COMPLETA.md`
- **Despliegue:** `DEPLOY_VPS.md`
- **Arquitectura:** `ARQUITECTURA_VPS.md`
- **Resumen:** `RESUMEN_MIGRACION_VPS.md`

---

**¡Todo listo para desplegar! 🚀**

