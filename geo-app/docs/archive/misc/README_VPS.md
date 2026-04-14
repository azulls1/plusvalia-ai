# 🐳 BACKEND - Listo para VPS con Traefik

## 🎯 ¿Qué tienes aquí?

**Backend completo para análisis inmobiliario** configurado para desplegarse en tu VPS con:
- ✅ Docker Swarm
- ✅ Portainer (gestión visual)
- ✅ Traefik (reverse proxy + SSL automático)
- ✅ Supabase (base de datos)

---

## 📁 ARCHIVOS PRINCIPALES

### Para Deployment:
- **`docker-compose.yml`** ← Principal, cópialo en Portainer
- **`Dockerfile`** ← Construcción de imagen
- **`.dockerignore`** ← Optimización

### Documentación:
- **`DEPLOY_VPS.md`** ← Guía paso a paso
- **`ARQUITECTURA_VPS.md`** ← Explicación técnica
- **`RESUMEN_MIGRACION_VPS.md`** ← Resumen ejecutivo
- **`MIGRAR_DE_RAILWAY_A_VPS.md`** ← Quick start

---

## 🚀 DESPLIEGUE RÁPIDO (3 pasos)

### 1️⃣ Subir a VPS
```bash
scp -r python_services/* usuario@vps:/root/backend-inmobiliario/
```

### 2️⃣ Configurar .env
```bash
# En tu VPS
cd /root/backend-inmobiliario
nano .env  # Ver DEPLOY_VPS.md para contenido
```

### 3️⃣ Desplegar en Portainer
```
Portainer → Stacks → Add Stack
Nombre: backend-inmobiliario
Pegar: docker-compose.yml
Configurar variables → Deploy
```

**✅ Listo** - Traefik configura SSL automáticamente

---

## 🔗 URLs

| Servicio | URL |
|----------|-----|
| Backend API | `https://apiinmobiliario.iagentek.com.mx` |
| Frontend | `https://iagentek.com.mx` |
| Supabase | `https://iagenteksupabase.iagentek.com.mx` |
| Portainer | `https://iagentekportainer.iagentek.com.mx` |

---

## ⚙️ VARIABLES DE ENTORNO REQUERIDAS

```env
# Supabase
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...

# PostgreSQL
POSTGRES_HOST=iagenteksupabase.iagentek.com.mx
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU_PASSWORD

# CORS
ALLOWED_ORIGINS=https://iagentek.com.mx
```

---

## 📊 RECURSOS

| Recurso | Límite |
|---------|--------|
| CPU | 0.5 - 2.0 cores |
| RAM | 512 MB - 2 GB |
| Storage | Volúmenes persistentes |

---

## 🎯 DOMINIO SUGERIDO

Configura DNS en Hostinger:
```
Tipo: A
Nombre: apiinmobiliario
Puntos a: IP_TU_VPS
```

---

## 📚 LECTURA RECOMENDADA

1. **Primera vez:** `RESUMEN_MIGRACION_VPS.md`
2. **Desplegar:** `DEPLOY_VPS.md`
3. **Arquitectura:** `ARQUITECTURA_VPS.md`
4. **Problemas:** Ver sección troubleshooting en `DEPLOY_VPS.md`

---

## 🆘 AYUDA RÁPIDA

```bash
# Ver logs
docker service logs backend-inmobiliario_backend-api -f

# Verificar health
curl https://apiinmobiliario.iagentek.com.mx/health

# Reiniciar servicio
docker service update --force backend-inmobiliario_backend-api

# Ver recursos
docker stats
```

---

## ✅ CHECKLIST

- [ ] Archivos subidos a VPS
- [ ] .env configurado
- [ ] Stack desplegado en Portainer
- [ ] DNS configurado
- [ ] SSL generado (Traefik)
- [ ] Health check pasando
- [ ] Frontend actualizado
- [ ] Todo funcionando

---

**Ready to deploy! 🚀**

*Desarrollado con ❤️ por Samael Hernandez*

