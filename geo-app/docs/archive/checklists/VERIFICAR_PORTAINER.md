# 🔍 VERIFICAR EN PORTAINER

## ❓ PROBLEMA

404 + CORS = El servicio no está corriendo o no se actualizó correctamente.

---

## ✅ VERIFICAR EN PORTAINER

### **1. Abrir Portainer**

```
https://iagentekportainer.iagentek.com.mx
```

### **2. Ver Stacks**

1. Menú → **Stacks**
2. Buscar: **`backend-inmobiliario`**
3. ¿Existe el stack?

---

### **3. Si NO existe el stack:**

Necesitas **crearlo**:

1. **+ Add stack**
2. Name: `backend-inmobiliario`
3. Web editor: Pegar YAML completo
4. Deploy

---

### **4. Si SÍ existe el stack:**

Verificar estado:

1. Click en **`backend-inmobiliario`**
2. Ver columna **"Running"**
3. ¿Dice "1" o "0"?

**Si dice "0":**
- El stack está detenido
- Click **Start**

**Si dice "1":**
- El stack está corriendo
- Verificar logs

---

### **5. Ver Logs**

1. Stack → **`backend-inmobiliario`**
2. Click en el contenedor
3. Tab **"Logs"**
4. Buscar errores

---

## 📋 DIME:

1. **¿Existe el stack `backend-inmobiliario`?** (Sí/No)
2. **¿Cuántos contenedores dice "Running"?** (0/1)
3. **¿Qué muestran los logs?**

