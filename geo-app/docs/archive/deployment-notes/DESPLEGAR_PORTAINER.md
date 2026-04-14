# 🚀 DESPLEGAR EN PORTAINER

## ✅ IMAGEN CONSTRUIDA

Tu imagen Docker `backend-inmobiliario:latest` está lista ✅

---

## 🎯 SIGUIENTE PASO: DESPLEGAR

### Opción A: Desde Portainer (Navegador) - MÁS FÁCIL ⭐

#### 1. Abrir Portainer

```
https://iagentekportainer.iagentek.com.mx
```

#### 2. Login

```
Usuario: admin
Password: (tu password de Portainer)
```

#### 3. Ir a Stacks

```
Click en: Stacks
Click en: Add Stack
```

#### 4. Configurar Stack

**Nombre:**
```
backend-inmobiliario
```

**Compose file:**

En PuTTY, ejecuta:
```bash
cat docker-compose.yml
```

**Copia TODO el contenido** del archivo y pégalo en Portainer.

#### 5. Environment Variables

**NO necesitas agregar nada** - Ya están configuradas en el docker-compose.yml

#### 6. Deploy

```
Click en: "Deploy the stack"
```

---

### Opción B: Desde PuTTY (Línea de comandos)

```bash
# Desplegar stack
docker stack deploy -c docker-compose.yml backend-inmobiliario

# Ver logs en tiempo real
docker service logs -f backend-inmobiliario_backend-api

# Presionar Ctrl+C para salir de los logs
```

---

## ✅ VERIFICAR

### Ver estado del servicio:

```bash
# Ver todos los servicios
docker service ls

# Ver detalles del servicio
docker service ps backend-inmobiliario_backend-api

# Ver logs
docker service logs backend-inmobiliario_backend-api --tail 50
```

### Probar que funciona:

```bash
# Health check
curl http://localhost:8000/health

# O desde tu PC:
curl https://apiinmobiliario.iagentek.com.mx/health
```

**Deberías ver:**
```json
{"status": "ok"}
```

---

## 🐛 SI HAY ERROR

### Error: "Traefik network not found"

```bash
# Crear red
docker network create --driver overlay traefik_default
```

### Error: "Cannot connect to database"

```bash
# Ver variables de entorno
docker service inspect backend-inmobiliario_backend-api

# Ver logs
docker service logs backend-inmobiliario_backend-api
```

---

**Abra Portainer y despliega el stack** 🚀

