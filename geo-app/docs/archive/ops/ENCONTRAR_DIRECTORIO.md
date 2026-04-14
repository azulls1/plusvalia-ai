# 🔍 ENCONTRAR DIRECTORIO CORRECTO

El directorio `/root/analisis-inmobiliario/` no existe.

Necesitamos encontrar dónde están los archivos del proyecto.

---

## 📋 PASOS EN PuTTY

### **PASO 1: Buscar directorios**

En PuTTY, escribe:

```bash
cd /root
ls -la
```

Esto muestra todas las carpetas en `/root/`.

---

### **PASO 2: Buscar proyecto**

Busca carpetas que puedan ser tu proyecto. Ejemplos:

```
/root/analisis-mercado-evaluacion-terrenos/
/root/geo-app/
/root/python_services/
/root/backend-inmobiliario/
```

---

### **PASO 3: Entrar a la carpeta correcta**

Cuando encuentres una carpeta que parezca tu proyecto, escribe:

```bash
cd [nombre-carpeta]
ls -la
```

Ejemplo:
```bash
cd analisis-mercado-evaluacion-terrenos
ls -la
```

---

### **PASO 4: Buscar api/main.py**

Busca la carpeta que tenga `api/main.py`. Escribe:

```bash
find . -name "main.py" -path "*/api/*" 2>/dev/null
```

Esto encuentra el archivo `main.py` dentro de una carpeta `api/`.

---

## 💡 OPCIÓN ALTERNATIVA

Si no encuentras la carpeta, dime:

1. **¿Dónde subiste los archivos del backend?**
2. **¿Qué nombre tiene la carpeta principal del proyecto?**

Con esa información, te doy los comandos exactos.

---

**Envíame el resultado de `ls -la` en `/root/`** para ayudarte a encontrar la carpeta correcta.

