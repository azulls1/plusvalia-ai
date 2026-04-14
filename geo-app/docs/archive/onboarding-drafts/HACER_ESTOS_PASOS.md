# ✅ PASOS EXACTOS A SEGUIR

## 🎯 SITUACIÓN ACTUAL

✅ Código corregido localmente  
❌ Código NO subido al VPS todavía  
❌ Imagen Docker NO reconstruida todavía

---

## 📋 PASOS (UNO POR UNO)

### **PASO 1: Abrir WinSCP**

1. Abre **WinSCP** en tu computadora
2. Conecta al VPS:
   - Host: Tu IP del VPS
   - Usuario: `root`
   - Password: Tu contraseña

---

### **PASO 2: Subir archivo API**

**Panel izquierdo (tu PC):**
```
C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services\api\
```

**Panel derecho (VPS):**
```
/root/analisis-inmobiliario/python_services/api/
```

**Acción:**
1. Arrastra el archivo `main.py` del panel izquierdo al derecho
2. Reemplazar si pregunta

---

### **PASO 3: Abrir PuTTY**

1. Abre **PuTTY**
2. Conecta al VPS (misma IP)
3. Login: `root`

---

### **PASO 4: Verificar archivo subido**

En PuTTY, escribe:

```bash
cd /root/analisis-inmobiliario/python_services/api
cat main.py | grep -A 2 "models_dir ="
```

**Debe mostrar:**
```python
models_dir = base_dir / "ml_model" / "models"
```

Si no muestra eso, el archivo no se subió bien. Volver al PASO 2.

---

### **PASO 5: Reconstruir Docker**

En PuTTY, escribe:

```bash
cd /root/analisis-inmobiliario/python_services
docker build -t backend-inmobiliario:latest .
```

**Espera 3-5 minutos** hasta que diga:
```
Successfully tagged backend-inmobiliario:latest
```

---

### **PASO 6: Abrir Portainer**

1. Abre navegador
2. Ve a: https://iagentekportainer.iagentek.com.mx
3. Login:
   - Usuario: `admin`
   - Password: `iagentek_123`

---

### **PASO 7: Actualizar Stack**

En Portainer:

1. Menú izquierdo: Click **"Stacks"**
2. Busca: `backend-inmobiliario`
3. Click en el nombre
4. Click botón **"Editor"** (arriba)
5. **NO CAMBIAR NADA**, solo scroll abajo
6. Click **"Update the stack"** (azul, abajo)
7. **Esperar 2-3 minutos**

---

### **PASO 8: Verificar Logs**

En Portainer:

1. Stacks → `backend-inmobiliario`
2. Click en el contenedor
3. Tab **"Logs"**
4. Buscar línea que diga:

```
✅ Modelo cargado: plusvalia_model_v4.0_32_states.pkl
```

**Si ves eso → ¡Éxito! ✅**

Si ves:

```
⚠️ No se encontró modelo pre-entrenado
```

No hay problema, los modelos se entrenan después.

---

### **PASO 9: Probar API**

En PuTTY o en tu navegador:

```bash
curl https://apiinmobiliario.iagentek.com.mx/health
```

**Debe responder:**
```json
{"status":"healthy","model_loaded":true o false,...}
```

---

## ✅ ¡COMPLETADO!

Si ves "✅ Modelo cargado" en los logs, **todo funciona**.

Si ves "⚠️ No se encontró modelo", el backend funciona pero necesita entrenar el modelo.

---

## ❓ ¿PROBLEMAS?

Dime en qué paso te quedaste y qué error viste.

