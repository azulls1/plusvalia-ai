# 🔧 CREAR RED TRAEFIK

## ❌ ERROR

```
network "traefik_default" is declared as external, but could not be found
```

---

## ✅ SOLUCIÓN

### En PuTTY, ejecuta:

```bash
# Crear la red
docker network create --driver overlay traefik_default

# Verificar que se creó
docker network ls | grep traefik
```

---

## 🚀 DESPUÉS

**Vuelve a Portainer:**
1. Ve a tu stack
2. Click en "Editor" 
3. Click en "Update the stack"

O simplemente:
1. Elimina el stack que falló
2. Crea uno nuevo
3. Pega el YAML otra vez
4. Deploy

---

**Ejecuta esos comandos en PuTTY primero** 🔧

