# ✅ VERIFICAR Y CONSTRUIR

## 🎯 SITUACIÓN

✅ Archivos ya subidos a `/root/backend-inmobiliario/`  
✅ Imagen Docker ya existe  
❓ Solo falta verificar y reconstruir

---

## 📋 PASOS RÁPIDOS

### **PASO 1: Verificar archivo correcto**

En PuTTY:

```bash
cd /root/backend-inmobiliario/api
cat main.py | grep -A 2 "models_dir ="
```

**Debe mostrar:**
```python
models_dir = base_dir / "ml_model" / "models"
```

---

### **PASO 2: Construir Docker**

```bash
cd /root/backend-inmobiliario
docker build -t backend-inmobiliario:latest .
```

**Espera 3-5 minutos**

---

### **PASO 3: Portainer**

1. Abre: https://iagentekportainer.iagentek.com.mx
2. Login: `admin` / `iagentek_123`
3. Stacks → `backend-inmobiliario`
4. Update the stack
5. Esperar 2-3 minutos

---

### **PASO 4: Ver logs**

En Portainer → Stacks → `backend-inmobiliario` → Logs

Buscar:
```
✅ Modelo cargado: plusvalia_model_v4.0_32_states.pkl
```

---

## ✅ ¡LISTO!

**Ejecuta el PASO 1 primero** y dime qué muestra.

