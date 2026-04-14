# 👁️ MOSTRAR ARCHIVOS OCULTOS EN WINSCP

## 🔧 CONFIGURACIÓN NECESARIA

Los archivos que empiezan con `.` (como `.env`) están **ocultos** por defecto en WinSCP.

---

## ✅ ACTIVAR MOSTRAR ARCHIVOS OCULTOS

### En WinSCP:

1. **Ir a menú:**
   ```
   Opciones → Preferencias
   ```

2. **Sección:**
   ```
   Panel → Ver
   ```

3. **Buscar opción:**
   ```
   ✅ Marcar "Mostrar archivos ocultos"
   ```

4. **Click en "Aplicar" y "OK"**

5. **Actualizar la vista:**
   - Presiona `F5` en WinSCP
   - O haz click derecho → Actualizar

---

## ✅ AHORA DEBERÍAS VER

En el panel derecho del VPS:
```
/root/backend-inmobiliario/
├── .dockerignore     ← Archivo oculto
├── .env              ← Archivo oculto (IMPORTANTE)
├── .gitignore        ← Archivo oculto
├── api/
├── config.py
├── docker-compose.yml
├── Dockerfile
├── integrations/
├── ml_model/
├── requirements.txt
└── scrapers/
```

---

## 🎯 VERIFICAR QUE .env ESTÁ AHÍ

### Opción 1: En WinSCP

Después de activar "Mostrar archivos ocultos", busca:
```
.env (1 KB, Archivo ENV)
```

---

### Opción 2: En PuTTY

**Conectarte con PuTTY y ejecutar:**

```bash
# Ir al directorio
cd /root/backend-inmobiliario

# Listar TODOS los archivos (incluidos ocultos)
ls -la

# Buscar específicamente .env
ls -la | grep .env
```

**Deberías ver:**
```
-rw-r--r-- 1 root root 647 Nov  3 12:44 .env
```

---

## 🚀 SIGUIENTE PASO

Una vez que veas `.env`:

1. **Verifica que está subido correctamente**
2. **Continúa con:** Construir imagen Docker

En PuTTY:
```bash
cd /root/backend-inmobiliario
docker build -t backend-inmobiliario:latest .
```

---

**¡Dime cuando ya lo veas!** 👀

