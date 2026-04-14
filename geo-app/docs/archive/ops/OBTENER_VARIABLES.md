# 🔐 OBTENER VARIABLES DE ENTORNO

## 📋 EN PUTTY

Ejecuta este comando para ver el contenido de .env:

```bash
cat /root/backend-inmobiliario/.env
```

---

## 📝 VARIABLES QUE NECESITAS

Copia estos valores y pégalos en Portainer:

### 1. SUPABASE_URL
```
https://iagenteksupabase.iagentek.com.mx
```

### 2. SUPABASE_KEY
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k
```

### 3. SUPABASE_SERVICE_ROLE_KEY
(Copiarlo del .env)

### 4. POSTGRES_HOST
```
iagenteksupabase.iagentek.com.mx
```

### 5. POSTGRES_PORT
```
5432
```

### 6. POSTGRES_DB
```
postgres
```

### 7. POSTGRES_USER
```
postgres
```

### 8. POSTGRES_PASSWORD
(Copiarlo del .env)

---

## 🚀 EN PORTAINER

Para cada variable, click en:
```
"+ Add an environment variable"
```

Agrega:
- **Name:** Nombre de la variable (ej: SUPABASE_URL)
- **Value:** El valor que copiaste

---

## ✅ DESPUÉS DE AGREGAR TODAS

Click en **"Deploy the stack"**

---

**Ejecuta `cat /root/backend-inmobiliario/.env` en PuTTY primero** 👀

