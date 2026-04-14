# ✅ ARCHIVOS SUBIDOS - SIGUIENTE PASO

## 🎉 VERIFICA TU WINSCP

Ya tienes subidos:
- ✅ api/
- ✅ integrations/
- ✅ ml_model/
- ✅ scrapers/
- ✅ Dockerfile
- ✅ docker-compose.yml
- ✅ requirements.txt
- ✅ config.py

---

## ⚠️ FALTA SUBIR

**IMPORTANTE:** Falta el archivo `.env` con tus credenciales.

### En WinSCP:

1. **Panel izquierdo (tu PC):**
   - Busca el archivo `.env` en la carpeta `python_services/`

2. **Selecciona `.env`**

3. **Arrastra y suelta** al panel derecho (VPS)

4. **Verifica** que ahora veas `.env` en el VPS

---

## ❌ NO SUBIR

**NO subas estos (no son necesarios):**
- ❌ `__pycache__/` (caché de Python)
- ❌ `data/` (datos temporales)
- ❌ `logs/` (logs temporales)
- ❌ `*.md` (documentos, no necesarios en producción)
- ❌ Otros archivos `.py` que no sean `config.py`

---

## ✅ VERIFICACIÓN FINAL

En WinSCP, panel derecho, deberías ver **EXACTAMENTE**:
```
/root/backend-inmobiliario/
├── api/
├── integrations/
├── ml_model/
├── scrapers/
├── config.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env  ← IMPORTANTE
```

---

## 🚀 SIGUIENTE PASO: CONSTRUIR CON DOCKER

### Abre PuTTY

1. **Abrir PuTTY**

2. **Conectarte:**
   ```
   Host: tu-ip-vps
   Port: 22
   ```

3. **Login:**
   ```
   Usuario: root
   Password: tu_password
   ```

---

### Ejecutar comandos en PuTTY:

```bash
# Ir al directorio
cd /root/backend-inmobiliario

# Verificar archivos
ls -la

# Deberías ver: api, integrations, ml_model, scrapers, .env, etc.

# Construir imagen Docker
docker build -t backend-inmobiliario:latest .

# Esto tomará varios minutos...
# Espera hasta ver "Successfully built"

# Verificar que se creó
docker images | grep backend-inmobiliario
```

---

## 🎯 DESPUÉS DE CONSTRUIR

Lee: `DESPLIEGUE_CON_PUTTY_WINSCP.md` → Sección "PASO 7: DESPLEGAR EN PORTAINER"

O simplemente:
1. Abre Portainer en navegador
2. Stacks → Add Stack
3. Copia el contenido de `docker-compose.yml`
4. Deploy

---

## 🆘 SI HAY ERROR

**Error: "Cannot find .env"**
→ Asegúrate de que `.env` esté subido

**Error: "Permission denied"**
```bash
# En PuTTY:
sudo chown -R $USER:$USER /root/backend-inmobiliario
```

---

**¡Sigue con PuTTY ahora!** 🚀

