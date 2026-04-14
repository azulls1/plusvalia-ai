# 🚀 DESPLIEGUE CON PuTTY + WinSCP

## 🎯 HERRAMIENTAS

- **PuTTY:** Para conectarte al VPS y ejecutar comandos
- **WinSCP:** Para subir archivos fácilmente

---

## 📋 PASO A PASO

### PASO 1: DESCARGAR HERRAMIENTAS (Si no las tienes)

**PuTTY:**
```
https://www.putty.org/
Descargar: putty.exe
```

**WinSCP:**
```
https://winscp.net/
Descargar e instalar
```

---

### PASO 2: CONFIGURAR PuTTY

1. **Abrir PuTTY**

2. **Configuración inicial:**
   ```
   Host Name: tu-ip-vps
   Port: 22
   Connection type: SSH
   ```

3. **Configurar sesión:**
   - En "Saved Sessions" escribe: `VPS-Inmobiliario`
   - Click en "Save"

4. **Click en "Open"**

5. **Login:**
   ```
   Usuario: root (o tu usuario)
   Password: tu_password
   ```

---

### PASO 3: CREAR DIRECTORIO EN EL VPS

**En PuTTY (después de conectarte):**

```bash
# Crear directorio
mkdir -p /root/backend-inmobiliario
cd /root/backend-inmobiliario

# Verificar que funciona
pwd
# Debe mostrar: /root/backend-inmobiliario
```

---

### PASO 4: ABRIR WinSCP

1. **Abrir WinSCP**

2. **Configurar conexión:**
   ```
   File protocol: SFTP
   Host name: tu-ip-vps
   Port number: 22
   User name: root (o tu usuario)
   Password: tu_password
   ```

3. **Guardar sesión:**
   - Click en "Save"
   - Nombre: `VPS-Inmobiliario`
   - Click en "Save"

4. **Click en "Login"**

---

### PASO 5: SUBIR ARCHIVOS CON WinSCP

**En WinSCP:**

1. **Panel izquierdo (tu PC):**
   ```
   Navegar a: C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services
   ```

2. **Panel derecho (VPS):**
   ```
   Navegar a: /root/backend-inmobiliario
   ```

3. **Seleccionar archivos a subir:**
   ```
   ✅ Seleccionar estas carpetas y archivos:
   - api/ (carpeta completa)
   - ml_model/ (carpeta completa)
   - integrations/ (carpeta completa)
   - scrapers/ (carpeta completa)
   - Dockerfile (archivo)
   - docker-compose.yml (archivo)
   - requirements.txt (archivo)
   - config.py (archivo)
   - .env (archivo)
   ```

4. **Subir:**
   - Click derecho en los archivos seleccionados
   - Click en "Upload" o arrastra y suelta

5. **Verificar:**
   ```
   En WinSCP, panel derecho, deberías ver:
   /root/backend-inmobiliario/
   ├── api/
   ├── ml_model/
   ├── integrations/
   ├── scrapers/
   ├── Dockerfile
   ├── docker-compose.yml
   ├── requirements.txt
   ├── config.py
   └── .env
   ```

---

### PASO 6: CONSTRUIR IMAGEN DOCKER

**En PuTTY:**

```bash
# Asegurarse de estar en el directorio correcto
cd /root/backend-inmobiliario
pwd

# Construir la imagen Docker
docker build -t backend-inmobiliario:latest .

# Esperar... esto tomará varios minutos la primera vez
# Deberías ver: "Successfully built" y "Successfully tagged"

# Verificar que la imagen se creó
docker images | grep backend-inmobiliario
```

**Deberías ver algo como:**
```
backend-inmobiliario   latest    abc123def456   2 minutes ago   1.5GB
```

---

### PASO 7: DESPLEGAR EN PORTAINER

**Método A: Desde navegador (Más fácil)**

1. **Abrir Portainer en el navegador:**
   ```
   https://iagentekportainer.iagentek.com.mx
   ```

2. **Login:**
   - Usuario: admin
   - Password: tu_password_portainer

3. **Ir a:**
   ```
   Stacks → Add Stack
   ```

4. **Configurar:**
   ```
   Name: backend-inmobiliario
   ```

5. **Copy y paste del docker-compose.yml:**
   - En PuTTY: `cat docker-compose.yml`
   - Copia todo el contenido
   - Pega en Portainer en el campo "Compose file"

6. **Environment variables:**
   - NO necesitas agregar nada
   - Ya están configuradas en el docker-compose.yml

7. **Deploy:**
   - Click en "Deploy the stack"

8. **Verificar:**
   - Ir a "Services"
   - Verás `backend-inmobiliario_backend-api` corriendo

---

**Método B: Desde PuTTY (Línea de comandos)**

```bash
# Desplegar stack
docker stack deploy -c docker-compose.yml backend-inmobiliario

# Ver logs
docker service logs -f backend-inmobiliario_backend-api

# Presionar Ctrl+C para salir de los logs
```

---

### PASO 8: VERIFICAR QUE FUNCIONA

**En PuTTY:**

```bash
# Ver estado del servicio
docker service ls

# Ver logs (últimas 50 líneas)
docker service logs --tail 50 backend-inmobiliario_backend-api

# Ver health check
curl http://localhost:8000/health

# O probar desde tu PC (en PowerShell):
curl https://apiinmobiliario.iagentek.com.mx/health
```

**Deberías ver:**
```json
{"status": "ok"}
```

---

## ✅ CHECKLIST COMPLETO

### Herramientas:
- [ ] PuTTY instalado y configurado
- [ ] WinSCP instalado y configurado

### Conexión:
- [ ] Conectado al VPS con PuTTY
- [ ] Conectado al VPS con WinSCP

### Archivos:
- [ ] Directorio /root/backend-inmobiliario creado
- [ ] Archivos subidos con WinSCP
- [ ] .env incluido

### Docker:
- [ ] Imagen construida con éxito
- [ ] Stack desplegado en Portainer
- [ ] Servicio corriendo

### Verificación:
- [ ] Backend responde en /health
- [ ] Sin errores en logs

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Error: "Permission denied" al subir archivos

**Solución:**
```bash
# En PuTTY:
sudo chown -R $USER:$USER /root/backend-inmobiliario
```

### Error: "Cannot connect to database"

**Solución:**
```bash
# Verificar que .env esté correcto
cat /root/backend-inmobiliario/.env

# Verificar variables de entorno en docker
docker service inspect backend-inmobiliario_backend-api
```

### Error: "Traefik network not found"

**Solución:**
```bash
# Verificar redes
docker network ls

# Si no existe traefik_default:
docker network create --driver overlay traefik_default
```

### Error: "Image not found"

**Solución:**
```bash
# Reconstruir la imagen
cd /root/backend-inmobiliario
docker build -t backend-inmobiliario:latest .
```

---

## 📊 COMANDOS ÚTILES

### Ver logs en tiempo real:
```bash
docker service logs -f backend-inmobiliario_backend-api
```

### Reiniciar servicio:
```bash
docker service update --force backend-inmobiliario_backend-api
```

### Ver estado:
```bash
docker service ps backend-inmobiliario_backend-api
```

### Eliminar stack (si necesitas):
```bash
docker stack rm backend-inmobiliario
```

---

## 🎉 COMPLETADO

**Tu backend debería estar funcionando en:**
```
https://apiinmobiliario.iagentek.com.mx
```

**Verificar:**
```bash
curl https://apiinmobiliario.iagentek.com.mx/health
```

---

## 📞 SIGUIENTE PASO

**Desplegar Frontend en Hostinger**

Lee: `INSTRUCCIONES_SUBIR_HOSTINGER.md`

---

**¡Éxito con tu despliegue!** 🚀💪

