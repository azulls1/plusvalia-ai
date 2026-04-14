# 🔐 VARIABLES DE ENTORNO PARA PORTAINER

## ⚠️ IMPORTANTE

Necesitas agregar las variables de entorno en Portainer porque el docker-compose.yml usa `${VARIABLE}`.

---

## 📋 PASO A PASO

### 1. En Portainer, cuando estés en "Add Stack"

Después de pegar el docker-compose.yml:

### 2. Baja hasta ver "Environment variables"

### 3. Agrega CADA UNA de estas variables:

```
SUPABASE_URL = https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k
SUPABASE_SERVICE_ROLE_KEY = TU_SERVICE_ROLE_KEY_AQUI
POSTGRES_HOST = iagenteksupabase.iagentek.com.mx
POSTGRES_PORT = 5432
POSTGRES_DB = postgres
POSTGRES_USER = postgres
POSTGRES_PASSWORD = TU_PASSWORD_AQUI
```

---

## 🔍 OBTENER LOS VALORES

### En PuTTY:

```bash
# Ver el contenido de .env
cat /root/backend-inmobiliario/.env
```

**Copia los valores** de ahí y pégalos en Portainer.

---

**⚠️ REEMPLAZA:**
- `TU_SERVICE_ROLE_KEY_AQUI` → Tu service role key real
- `TU_PASSWORD_AQUI` → Tu password de PostgreSQL

---

**¡Agrega las variables en Portainer antes de hacer Deploy!** 🔐

