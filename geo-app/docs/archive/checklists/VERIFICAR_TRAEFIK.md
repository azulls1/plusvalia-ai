# 🔍 VERIFICAR TRAEFIK

## ✅ BACKEND OK

**El backend está funcionando perfectamente:**
```
✅ Modelo cargado: plusvalia_model_v4.0_completo_20251102_232313.pkl
Application startup complete
Health check: 200 OK
```

**El problema es routing de Traefik.**

---

## 🔍 VERIFICAR TRAEFIK

### **1. Ver logs de Traefik**

En PuTTY:

```bash
docker service logs -f traefik_traefik --tail 100 | grep -i backend
```

**Buscar:** Si Traefik detecta el servicio

---

### **2. Verificar DNS**

En tu navegador, abre:

```
https://apiinmobiliario.iagentek.com.mx/
```

**¿Qué error muestra?**
- 404 Not Found → Traefik no encuentra el servicio
- Connection refused → DNS no está configurado
- Sin respuesta → Problema de red

---

### **3. Probar desde dentro del VPS**

En PuTTY:

```bash
curl http://localhost:8000/health
```

**Si funciona** → El problema es Traefik

---

### **4. Verificar labels de Traefik**

En PuTTY:

```bash
docker service inspect backend-inmobiliario_backend-api --format '{{json .Spec.TaskTemplate.ContainerSpec.Labels}}' | jq
```

**Debe mostrar los labels de Traefik**

---

## 📋 DIME:

1. **¿Qué dice el grep de Traefik logs?**
2. **¿Qué error muestra en el navegador?**
3. **¿Funciona el curl localhost:8000?**

