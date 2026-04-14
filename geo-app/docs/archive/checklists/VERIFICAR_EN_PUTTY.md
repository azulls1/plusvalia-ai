# ✅ VERIFICAR ARCHIVOS EN PUTTY

## 🔍 MÉTODO MÁS FÁCIL

Puedes verificar que `.env` está en el VPS usando PuTTY:

---

## 📋 PASOS

### 1. Abrir PuTTY

**Conectarte:**
```
Host: 144.126.157.81
Puerto: 22
Usuario: root
```

---

### 2. Ejecutar estos comandos:

```bash
# Ir al directorio
cd /root/backend-inmobiliario

# Listar TODOS los archivos (incluidos ocultos)
ls -la
```

---

### 3. Buscar .env específicamente:

```bash
# Ver solo el archivo .env
ls -la | grep "\.env"

# O mejor, ver su contenido
cat .env
```

---

## ✅ RESULTADO ESPERADO

Deberías ver algo como:
```
-rw-r--r-- 1 root root 647 Nov  3 12:44 .env
```

O si ejecutas `cat .env`:
```
SUPABASE_URL=https://iagenteksupabase.iagentek.com.mx
SUPABASE_KEY=eyJhbGci...
...
```

---

## 🚀 SI .ENV ESTÁ AHÍ

**Continúa con:**

```bash
# Construir imagen Docker
docker build -t backend-inmobiliario:latest .

# Esto tomará varios minutos...
# Espera a ver "Successfully built"
```

---

## ❌ SI NO ESTÁ

**Volver a subir:**

1. En WinSCP, panel izquierdo
2. Selecciona `.env`
3. Arrastra al panel derecho
4. Confirma reemplazo si pregunta

---

**Ejecuta el comando `ls -la` en PuTTY y dime qué ves** 👀

