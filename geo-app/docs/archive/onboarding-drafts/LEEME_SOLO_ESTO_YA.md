# 🚀 CORRECCIÓN MODELOS ML - PASOS RÁPIDOS

## ❗ PROBLEMA

Los modelos ML no se cargaban por una ruta incorrecta.

## ✅ SOLUCIÓN APLICADA

Ya está corregido en el código. Solo necesitas subir el archivo actualizado al VPS.

---

## 📋 HACER ESTO:

### **1. Subir archivo con WinSCP**

```
Sube este archivo:
  geo-app/python_services/api/main.py

Al VPS:
  /root/analisis-inmobiliario/python_services/api/main.py
```

---

### **2. Conectar con PuTTY y reconstruir:**

```bash
cd /root/analisis-inmobiliario/python_services
docker build -t backend-inmobiliario:latest .
```

---

### **3. En Portainer:**

```
Stacks → backend-inmobiliario → Update the stack
```

---

### **4. Verificar logs:**

En Portainer, logs deben mostrar:

```
✅ Modelo cargado: plusvalia_model_v4.0_32_states.pkl
```

---

**¡Listo! Con esto funcionará.** 🎉

Lee el archivo `REBUILD_Y_DEPLOY.md` si necesitas más detalles.

