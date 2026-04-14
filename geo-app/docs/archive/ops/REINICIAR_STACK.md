# 🔄 REINICIAR STACK

## ⚠️ PROBLEMA

Los logs muestran la **imagen antigua** (del 07:00:53).

El update no aplicó el cambio.

---

## ✅ SOLUCIÓN

### **Opción 1: Reiniciar desde Portainer**

1. Portainer → Stacks → **backend-inmobiliario**
2. Click en el servicio: **backend-inmobiliario_backend-api**
3. Click botón **"Update/Recreate"**
4. Esperar 2-3 minutos

---

### **Opción 2: Force Update (más efectivo)**

1. Portainer → Stacks → **backend-inmobiliario**
2. Click botón **"Editor"** (arriba)
3. **NO CAMBIAR NADA**
4. Click **"Update the stack"**
5. **Marcar checkbox:** "Re-pull image" (si existe)
6. Click **"Update the stack"**
7. Esperar 2-3 minutos

---

### **Opción 3: Recreate Stack (si lo anterior falla)**

1. Portainer → Stacks → **backend-inmobiliario**
2. Click botón **"Remove"** (NO borra volúmenes)
3. **+ Add stack**
4. Name: **backend-inmobiliario**
5. Web editor: Pegar YAML de `DOCKER_COMPOSE_FINAL_YA_FUNCIONARA.yaml`
6. **Deploy the stack**

---

**Ejecuta Opción 1 primero** y dime qué pasa.

