# 🔍 ERROR 404 - TRAEFIK NO ENCUENTRA EL SERVICIO

## ❓ POSIBLES CAUSAS

1. El servicio no está corriendo
2. Traefik no detecta los labels
3. DNS no está configurado
4. La red está mal conectada

---

## ✅ VERIFICAR PASO A PASO

### **1. Verificar que el servicio está corriendo**

En PuTTY:

```bash
docker service ls | grep backend-inmobiliario
```

**Debe mostrar:**
```
backend-inmobiliario_backend-api   replicated   1/1   backend-inmobiliario:latest
```

Si muestra **0/1** → El servicio no está corriendo

---

### **2. Ver logs del servicio**

```bash
docker service logs -f backend-inmobiliario_backend-api --tail 50
```

**Buscar:**
- "Started server process"
- "Application startup complete"
- Errores

---

### **3. Verificar Traefik detecta el servicio**

```bash
docker service logs -f traefik_traefik --tail 100 | grep backend-inmobiliario
```

**Debe mostrar logs de Traefik detectando el servicio**

---

### **4. Verificar DNS**

```bash
dig apiinmobiliario.iagentek.com.mx
```

**Debe mostrar la IP de tu VPS**

---

## 🔍 EJECUTA ESTOS COMANDOS Y DIME RESULTADOS

1. `docker service ls | grep backend-inmobiliario`
2. `docker service logs backend-inmobiliario_backend-api --tail 20`
3. `dig apiinmobiliario.iagentek.com.mx`

