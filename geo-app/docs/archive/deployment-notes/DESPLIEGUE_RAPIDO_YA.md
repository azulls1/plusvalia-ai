# 🚀 DESPLIEGUE RÁPIDO - YA TODO LISTO

## ✅ LO QUE YA TIENES

✅ Código compilado  
✅ Dockerfile listo  
✅ docker-compose.yml configurado  
✅ .env con credenciales  
✅ Traefik configurado  
✅ Portainer instalado  

---

## 🎯 PASOS PARA DESPLEGAR

### 1️⃣ CONECTARSE AL VPS

**Opción A: SSH desde PowerShell**
```powershell
ssh root@tu-ip-vps
```

**Opción B: Usar WinSCP o FileZilla**
- Host: tu-ip-vps
- Usuario: root (o tu usuario)
- Puerto: 22

---

### 2️⃣ CREAR DIRECTORIO EN EL VPS

```bash
# Una vez conectado al VPS, ejecuta:
mkdir -p /root/backend-inmobiliario
cd /root/backend-inmobiliario
```

---

### 3️⃣ SUBIR ARCHIVOS

**Método A: Con WinSCP**
1. Abre WinSCP
2. Conéctate a tu VPS
3. Ve a `/root/backend-inmobiliario`
4. Arrastra y suelta estos archivos desde tu PC:
   - `python_services/api/`
   - `python_services/ml_model/`
   - `python_services/integrations/`
   - `python_services/scrapers/`
   - `python_services/Dockerfile`
   - `python_services/docker-compose.yml`
   - `python_services/requirements.txt`
   - `python_services/config.py`
   - `python_services/.env`

**Método B: Con SCP desde PowerShell**
```powershell
# Desde tu PC, en PowerShell:
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app

scp -r python_services/* root@tu-ip-vps:/root/backend-inmobiliario/
```

---

### 4️⃣ CONECTARSE AL VPS Y DESPLEGAR

```bash
# Conéctate al VPS
ssh root@tu-ip-vps

# Ve al directorio
cd /root/backend-inmobiliario

# Construir la imagen Docker (solo la primera vez)
docker build -t backend-inmobiliario:latest .

# Verificar que se creó
docker images | grep backend-inmobiliario
```

---

### 5️⃣ DESPLEGAR EN PORTAINER

**Método A: Desde Portainer UI (Más fácil)**

1. **Abrir Portainer:**
   ```
   https://iagentekportainer.iagentek.com.mx
   ```

2. **Ir a Stacks → Add Stack**

3. **Nombre:** `backend-inmobiliario`

4. **Compose file:** Copia el contenido de `docker-compose.yml`

5. **Environment variables:** No necesitas agregar nada, ya están en docker-compose.yml

6. **Deploy:** Click en "Deploy the stack"

---

**Método B: Desde línea de comandos**

```bash
# En el VPS
docker stack deploy -c docker-compose.yml backend-inmobiliario

# Verificar
docker stack services backend-inmobiliario
docker service logs backend-inmobiliario_backend-api
```

---

### 6️⃣ VERIFICAR QUE FUNCIONA

```bash
# Ver logs en tiempo real
docker service logs -f backend-inmobiliario_backend-api

# Ver estado
docker service ps backend-inmobiliario_backend-api

# Verificar health check
curl https://apiinmobiliario.iagentek.com.mx/health
```

**Deberías ver:**
```json
{"status": "ok"}
```

---

## ✅ CHECKLIST

- [ ] Me conecté al VPS
- [ ] Creé directorio /root/backend-inmobiliario
- [ ] Subí todos los archivos necesarios
- [ ] Construí la imagen Docker
- [ ] Desplegué en Portainer
- [ ] Backend responde en /health

---

## 🐛 SI ALGO SALE MAL

**Error: "Cannot connect to database"**
```bash
# Verificar variables de entorno
docker service inspect backend-inmobiliario_backend-api

# Ver logs
docker service logs backend-inmobiliario_backend-api
```

**Error: "Image not found"**
```bash
# Construir la imagen
docker build -t backend-inmobiliario:latest .
```

**Error: "Traefik network not found"**
```bash
# Verificar que Traefik esté corriendo
docker network ls | grep traefik

# Crear red si no existe
docker network create --driver overlay traefik_default
```

---

## 🎉 LISTO

**Tu backend debería estar corriendo en:**
```
https://apiinmobiliario.iagentek.com.mx
```

---

## 📞 PRÓXIMO PASO

Una vez que el backend esté funcionando:

**Desplegar Frontend en Hostinger**

Lee: `INSTRUCCIONES_SUBIR_HOSTINGER.md`

---

**¡Éxito!** 🚀

