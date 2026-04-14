# 📋 VARIABLES PARA COPIAR EN PORTAINER

## ✅ COPIA Y PEGA ESTAS EN PORTAINER

En la sección "Environment variables" de Portainer, agrega estas 8 variables:

---

### Variable 1:
**Name:** `SUPABASE_URL`  
**Value:** `https://iagenteksupabase.iagentek.com.mx`

---

### Variable 2:
**Name:** `SUPABASE_KEY`  
**Value:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k`

---

### Variable 3:
**Name:** `SUPABASE_SERVICE_ROLE_KEY`  
**Value:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogInNlcnZpY2Vfcm9sZSIsCiAgImlzcyI6ICJzdXBhYmFzZSIsCiAgImlhdCI6IDE3MTUwNTA4MDAsCiAgImV4cCI6IDE4NzI4MTcyMDAKfQ.82nFc9RPC-0tzN0svrqQrnHUHHe51bJkpCUiC_uTypo`

---

### Variable 4:
**Name:** `POSTGRES_HOST`  
**Value:** `iagenteksupabase.iagentek.com.mx`

---

### Variable 5:
**Name:** `POSTGRES_PORT`  
**Value:** `5432`

---

### Variable 6:
**Name:** `POSTGRES_DB`  
**Value:** `postgres`

---

### Variable 7:
**Name:** `POSTGRES_USER`  
**Value:** `postgres.iagenteksupabase`

---

### Variable 8:
**Name:** `POSTGRES_PASSWORD`  
**Value:** `Iagentek_123root@vmi2851872`

---

## 🚀 DESPUÉS

Cuando tengas las 8 variables agregadas:

**Click en "Deploy the stack"** 🚀

---

## ✅ VERIFICACIÓN

Después del deploy, en PuTTY:

```bash
# Ver logs
docker service logs -f backend-inmobiliario_backend-api

# O verificar health
curl http://localhost:8000/health
```

