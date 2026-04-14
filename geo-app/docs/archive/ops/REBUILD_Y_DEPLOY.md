# 🔄 REBUILD Y DEPLOY - CORRECCIÓN MODELOS ML

## ✅ PROBLEMA IDENTIFICADO Y SOLUCIONADO

**Error:** Los modelos ML no se cargaban porque la ruta era relativa incorrecta.

**Solución:** Cambiada la ruta de carga de modelos a absoluta: `/app/ml_model/models`

---

## 📋 PASOS A SEGUIR

### **1️⃣ SUBIR CÓDIGO CORREGIDO AL VPS**

Conecta con **WinSCP** y sube el archivo actualizado:

```
Archivo a subir:
  geo-app/python_services/api/main.py

Destino en VPS:
  /root/analisis-inmobiliario/python_services/api/main.py
```

---

### **2️⃣ CONECTAR POR SSH (PuTTY)**

```bash
# Entrar al directorio del proyecto
cd /root/analisis-inmobiliario/python_services

# Verificar que el archivo se subió correctamente
cat api/main.py | grep -A 5 "models_dir ="
```

**Debe mostrar:**
```python
models_dir = base_dir / "ml_model" / "models"
```

---

### **3️⃣ RECONSTRUIR IMAGEN DOCKER**

```bash
# Estar en el directorio correcto
cd /root/analisis-inmobiliario/python_services

# Reconstruir imagen (tarda 3-5 minutos)
docker build -t backend-inmobiliario:latest .

# Verificar que se construyó
docker images | grep backend-inmobiliario

# Debe mostrar:
# backend-inmobiliario   latest   [new-id]   [just-now]   [size]
```

---

### **4️⃣ ACTUALIZAR STACK EN PORTAINER**

#### **Opción A: Actualizar stack existente (Recomendado)**

1. Abre Portainer: https://iagentekportainer.iagentek.com.mx
2. Login: admin / iagentek_123
3. Ve a: **Stacks** → **backend-inmobiliario** (o nombre que usaste)
4. Click: **Editor**
5. **NO CAMBIES EL YAML**, solo haz scroll abajo
6. Click: **Update the stack**
7. Espera 2-3 minutos

**¿Por qué funciona?**
- Portainer detecta automáticamente que la imagen cambió
- Reiniciará los contenedores con la nueva imagen

---

#### **Opción B: Recrear stack (si Opción A falla)**

1. Portainer → Stacks → **backend-inmobiliario**
2. Click: **Remove** (esto NO borra volúmenes)
3. Stack → **Add stack**
4. Name: `backend-inmobiliario`
5. Web editor: Pega el YAML de `DOCKER_COMPOSE_FINAL_YA_FUNCIONARA.yaml`
6. Click: **Deploy the stack**

---

### **5️⃣ VERIFICAR LOGS**

En Portainer:

1. Stacks → **backend-inmobiliario**
2. Click en el contenedor
3. Tab: **Logs**
4. Busca:

```
✅ Modelo cargado: plusvalia_model_v4.0_32_states.pkl
```

**O si no hay modelos:**

```
⚠️ No se encontró modelo pre-entrenado
```

---

### **6️⃣ PROBAR HEALTH CHECK**

```bash
# Desde PuTTY o curl
curl https://api.iainmobiliaria.iagentek.com.mx/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "v4.0_32_states",
  "api_version": "1.0.0",
  "timestamp": "2025-11-03T07:15:00.000Z"
}
```

---

### **7️⃣ SI NO HAY MODELOS: ENTRENAR**

Si `model_loaded: false`, ejecuta el endpoint de entrenamiento:

```bash
curl -X POST https://api.iainmobiliaria.iagentek.com.mx/train \
  -H "Content-Type: application/json" \
  -d '{
    "min_samples": 100,
    "force_retrain": true
  }'
```

**Tarda:** 5-15 minutos dependiendo de los datos.

---

## 🔍 VERIFICACIÓN FINAL

### **Checklist:**

```
✅ Código actualizado en VPS
✅ Imagen reconstruida
✅ Stack actualizado
✅ Backend corriendo
✅ Health check OK
✅ Models cargados o se pueden entrenar
✅ SSL funcionando (https://)
✅ CORS configurado
✅ API responde
```

---

## ❗ SI HAY ERRORES

### **Error: "Image not found"**

```bash
# Verificar imagen existe
docker images | grep backend-inmobiliario

# Si no existe, reconstruir
cd /root/analisis-inmobiliario/python_services
docker build -t backend-inmobiliario:latest .
```

### **Error: "Container keeps restarting"**

Ver logs en Portainer:

```
Portainer → Container → Logs
```

Busca líneas con `ERROR` o `Exception`.

### **Error: "Model directory still not found"**

Verificar estructura en contenedor:

```bash
docker exec -it [container-name] ls -la /app/ml_model/models
```

Si el directorio está vacío, copiar modelos manualmente o entrenar.

---

## 📞 COMANDOS ÚTILES

```bash
# Ver servicios corriendo
docker service ls

# Ver logs en tiempo real
docker service logs -f backend-inmobiliario_backend-api

# Reiniciar servicio
docker service update --force backend-inmobiliario_backend-api

# Ver recursos usados
docker stats
```

---

**¡Listo! Con esto el backend debería cargar los modelos correctamente.** 🚀

