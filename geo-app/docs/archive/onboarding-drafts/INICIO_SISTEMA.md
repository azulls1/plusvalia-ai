# ⚡ INICIO RÁPIDO DEL SISTEMA

**Sistema de Análisis de Mercado Inmobiliario con ML**  
**Versión:** 2.0 (Con Integración Frontend-Backend)

---

## 🚀 **INICIO EN 3 PASOS**

### ✅ Paso 1: Iniciar Backend (API Python)

Abre una **terminal** y ejecuta:

```bash
cd geo-app/python_services
python api/main.py
```

**Salida esperada:**
```
🚀 Iniciando servidor en 0.0.0.0:8000
✅ Modelo cargado: model_20251025_045127.joblib
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **Backend listo en:** http://localhost:8000  
📚 **Documentación API:** http://localhost:8000/docs

---

### ✅ Paso 2: Iniciar Frontend (Angular)

Abre una **segunda terminal** y ejecuta:

```bash
cd geo-app/app
ng serve
```

**Salida esperada:**
```
✔ Browser application bundle generation complete.
Initial Chunk Files   | Names         |  Size
...
✔ Compiled successfully.
** Angular Live Development Server is listening on localhost:4200 **
```

✅ **Frontend listo en:** http://localhost:4200

---

### ✅ Paso 3: Abrir en el Navegador

```
http://localhost:4200
```

**¡Listo!** Deberías ver el mapa con **10,561 predicciones ML** cargadas. 🎉

---

## 🎯 **GUÍA RÁPIDA DE USO**

### 1. **Ver Mapa de Calor de Plusvalía** (por defecto)
- El mapa muestra automáticamente las **10,561 predicciones**
- Colores:
  - 🔴 Rojo = Alta plusvalía (score > 66)
  - 🟡 Amarillo = Media plusvalía (score 33-66)
  - 🟢 Verde = Baja plusvalía (score < 33)

### 2. **Hacer Click en el Mapa**
- Click en cualquier parte del mapa
- Ve la predicción más cercana con:
  - Precio estimado/m²
  - Score de plusvalía
  - Potencial de crecimiento
  - Distancia

### 3. **Filtrar por Ciudad**
- Panel lateral → "Filtrar por Ciudad"
- Selecciona: Ciudad de México, Guadalajara, Monterrey o Zapopan
- El mapa se centra y filtra automáticamente

### 4. **Ver Ranking de Ciudades**
- Panel lateral → "Ranking de Ciudades"
- Ve estadísticas de cada ciudad:
  - Número de predicciones
  - Precio promedio/m²
  - Score promedio
- Click en una ciudad para filtrar

### 5. **Cambiar a Modo Precios**
- Panel lateral → "Modo de Visualización"
- Click en "💰 Precios"
- Ve el mapa de calor de precios (sistema antiguo)

---

## 📊 **ENDPOINTS DE LA API**

Una vez iniciado el backend, puedes acceder a:

### Documentación Interactiva:
```
http://localhost:8000/docs
```

### Endpoints principales:

| Endpoint | Descripción |
|----------|-------------|
| `GET /` | Info general de la API |
| `GET /health` | Health check del sistema |
| `GET /stats` | Estadísticas generales |
| `GET /predictions/heatmap` | Datos para heatmap (10,561 puntos) |
| `GET /predictions/nearby` | Búsqueda de predicciones cercanas |
| `GET /predictions/bbox` | Predicciones en área rectangular |
| `GET /predictions/stats-by-city` | Estadísticas por ciudad |
| `POST /predict` | Crear una nueva predicción |

---

## 🛠️ **RESOLUCIÓN DE PROBLEMAS**

### ❌ Error: "ModuleNotFoundError" en Python

**Solución:**
```bash
cd geo-app/python_services
pip install -r requirements.txt
```

---

### ❌ Error: "ng: command not found"

**Solución:**
```bash
npm install -g @angular/cli
```

---

### ❌ Error: "node_modules not found" en Angular

**Solución:**
```bash
cd geo-app/app
npm install
```

---

### ❌ Error: CORS en el navegador

**Verificar que la API esté corriendo** en `http://localhost:8000`

**Si persiste, verificar en `python_services/api/main.py`:**
```python
allow_origins=["http://localhost:4200"]  # Debe estar configurado
```

---

### ❌ Error: "No se cargan las predicciones"

**Verificar en `app/src/environments/environment.ts`:**
```typescript
mlApiBase: 'http://localhost:8000'  // Debe apuntar al backend
```

---

## 📦 **ESTADO DEL SISTEMA**

### Datos Disponibles:
- ✅ **10,561 predicciones ML** (grid denso 250m)
- ✅ **800 propiedades** (índices SHF Oct 2024)
- ✅ **13,309 amenidades** (OpenStreetMap)
- ✅ **414 datos INEGI** (Censo 2020)
- ✅ **110 registros históricos** (SHF 2023-2024)
- ✅ **363 tiles de grid** (calculados)

### Modelo ML:
- ✅ **Random Forest** entrenado
- ✅ **MAE:** $15,478
- ✅ **R²:** 0.6196 (62% de varianza explicada)
- ✅ **RMSE:** $20,607

---

## 🔧 **COMANDOS ÚTILES**

### Reiniciar Backend:
```bash
# En la terminal del backend, presiona Ctrl+C
# Luego:
python api/main.py
```

### Reiniciar Frontend:
```bash
# En la terminal del frontend, presiona Ctrl+C
# Luego:
ng serve
```

### Ver logs del Backend:
Los logs se muestran en la terminal donde ejecutaste `python api/main.py`

### Ver logs del Frontend:
Los logs se muestran en la consola del navegador (F12)

---

## 📱 **ACCESO DESDE OTROS DISPOSITIVOS**

Si quieres acceder desde otro dispositivo en tu red local:

### 1. Obtén tu IP local:

**Windows:**
```bash
ipconfig
# Busca "IPv4 Address"
```

**Mac/Linux:**
```bash
ifconfig
# Busca "inet"
```

### 2. Configura Angular:

```bash
cd geo-app/app
ng serve --host 0.0.0.0
```

### 3. Accede desde otro dispositivo:

```
http://TU_IP_LOCAL:4200
```

Por ejemplo: `http://192.168.1.100:4200`

---

## 📚 **DOCUMENTACIÓN ADICIONAL**

- **Integración Frontend-Backend:** `INTEGRACION_FRONTEND_BACKEND.md`
- **Resultado Opción A:** `python_services/RESULTADO_OPCION_A.md`
- **Resumen Final:** `python_services/RESUMEN_FINAL_COMPLETO.md`
- **Estado de Datos:** `python_services/RESUMEN_DATOS_REALES.md`

---

## 🎊 **¡TODO LISTO!**

Si seguiste los 3 pasos, ahora deberías tener:

✅ Backend corriendo en puerto 8000  
✅ Frontend corriendo en puerto 4200  
✅ Mapa interactivo con 10,561 predicciones  
✅ Click en mapa para ver detalles  
✅ Filtros por ciudad  
✅ Ranking de ciudades  

**¡Disfruta del sistema!** 🚀

---

**¿Necesitas ayuda?** Revisa la sección de "Resolución de Problemas" arriba.

**Última actualización:** 25 de Octubre de 2025, 05:25 AM

