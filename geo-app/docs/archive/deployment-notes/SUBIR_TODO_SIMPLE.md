# 🚀 SUBIR TODO EN UNA SOLA CARPETA

## ✅ ESTRATEGIA SIMPLE

Vamos a subir TODOS los archivos del backend a `/root/backend-inmobiliario/` en una sola operación.

---

## 📋 PASO A PASO

### **PASO 1: Abrir WinSCP**

1. Abre **WinSCP**
2. Conecta al VPS:
   - Host: IP de tu VPS
   - Usuario: `root`
   - Password: Tu contraseña

---

### **PASO 2: Crear carpeta en VPS**

**Panel derecho (VPS):**

1. Navega a `/root/`
2. Click derecho → **"New"** → **"Directory"**
3. Nombre: `backend-inmobiliario`
4. Click **"OK"**

---

### **PASO 3: Subir TODOS los archivos**

**Panel izquierdo (tu PC):**
```
C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services\
```

**Panel derecho (VPS):**
```
/root/backend-inmobiliario/
```

**Acción:**

1. **Selecciona TODA la carpeta** `python_services` en WinSCP
   - Ctrl+A para seleccionar todo
2. **Arrastra** del panel izquierdo al derecho
3. **Espera** a que termine la transferencia (tarda 5-10 minutos)

**IMPORTANTE:** Sube TODA la carpeta `python_services`, incluyendo:
- ✅ `api/`
- ✅ `ml_model/`
- ✅ `integrations/`
- ✅ `scrapers/`
- ✅ `requirements.txt`
- ✅ `Dockerfile`
- ✅ `config.py`
- ✅ Todo lo demás

---

### **PASO 4: Verificar en PuTTY**

Abre PuTTY y escribe:

```bash
cd /root/backend-inmobiliario
ls -la
```

**Debe mostrar:**
```
api/
config.py
Dockerfile
ml_model/
requirements.txt
...etc
```

---

### **PASO 5: Verificar archivo corregido**

```bash
cat api/main.py | grep -A 2 "models_dir ="
```

**Debe mostrar:**
```python
models_dir = base_dir / "ml_model" / "models"
```

---

### **PASO 6: Construir Docker**

```bash
cd /root/backend-inmobiliario
docker build -t backend-inmobiliario:latest .
```

**Espera 3-5 minutos**

---

### **PASO 7: Portainer**

1. Abre: https://iagentekportainer.iagentek.com.mx
2. Login: `admin` / `iagentek_123`
3. Stacks → `backend-inmobiliario`
4. Update the stack

---

## ✅ ¡LISTO!

Con este método, subes TODO de una vez y evitas problemas de rutas.

---

**¿Tienes WinSCP abierto? Empieza con el PASO 1.**

