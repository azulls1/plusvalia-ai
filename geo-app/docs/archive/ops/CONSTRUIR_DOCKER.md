# 🐳 CONSTRUIR IMAGEN DOCKER

## ✅ ARCHIVOS VERIFICADOS

Todos los archivos están en `/root/backend-inmobiliario` ✅

---

## 🚀 SIGUIENTE PASO: CONSTRUIR IMAGEN

### En PuTTY, ejecuta:

```bash
# Ya estás en el directorio correcto
# Verificar que estás ahí:
pwd
# Debe mostrar: /root/backend-inmobiliario

# Construir imagen Docker
docker build -t backend-inmobiliario:latest .

# ⏳ Esto tomará varios minutos (5-10 minutos)
# Espera a ver "Successfully built"
```

---

## ⏳ QUÉ VA A PASAR

Durante la construcción verás:
1. Descargando capas de Python
2. Instalando dependencias
3. Copiando archivos
4. "Successfully tagged backend-inmobiliario:latest"

---

## ✅ CUANDO TERMINE

Verificar que se creó:

```bash
# Ver imagen
docker images | grep backend-inmobiliario

# Deberías ver:
# backend-inmobiliario   latest    abc123def456   2 minutes ago   1.5GB
```

---

## 🚀 SIGUIENTE DESPUÉS

Una vez construida la imagen:

**Desplegar en Portainer**

Opción A: Desde navegador
1. Abre: https://iagentekportainer.iagentek.com.mx
2. Stacks → Add Stack
3. Pegar contenido de docker-compose.yml
4. Deploy

Opción B: Desde PuTTY
```bash
docker stack deploy -c docker-compose.yml backend-inmobiliario
```

---

**Ejecuta `docker build -t backend-inmobiliario:latest .` ahora** 🚀

