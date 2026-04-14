# 🔍 VERIFICAR ERROR 404

## ⚠️ PROBLEMA

Sigue mostrando **404** → Traefik no encuentra el servicio

---

## 📋 PASOS

### **1. Ver Logs del Backend**

1. Portainer → Stacks → **backend-inmobiliario**
2. Click en **backend-inmobiliario_backend-api**
3. Tab **Logs**
4. **Buscar líneas nuevas** (de hace 1-2 minutos)

**¿Qué debe mostrar?**
```
INFO: Started server process
🚀 Iniciando API de Predicciones ML
Application startup complete
```

**Si muestra "⚠️ Directorio de modelos no existe":**
→ La imagen NO se actualizó

---

### **2. Probar Health Directo**

En PuTTY:

```bash
curl http://localhost:8000/health
```

**Si funciona** → El backend está vivo, pero Traefik no lo ve

---

### **3. Verificar Red**

En PuTTY:

```bash
docker network inspect iagenteknet | grep -A 10 "backend"
```

**Debe mostrar el contenedor conectado.**

---

## 🔍 DIME:

1. **¿Qué muestran los logs nuevos?**
2. **¿Qué dice el curl de health?**
3. **¿Qué muestra el inspect de red?**

