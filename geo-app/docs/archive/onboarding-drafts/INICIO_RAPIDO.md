# 🚀 INICIO RÁPIDO - Guía de 5 Minutos

**Para arrancar el proyecto rápidamente cada vez que lo necesites.**

---

## ⚡ COMANDOS RÁPIDOS

### 1️⃣ Iniciar Backend (Terminal 1)

```powershell
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\python_services
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ **Verificar:** http://localhost:8000/health

---

### 2️⃣ Iniciar Frontend (Terminal 2)

```powershell
cd C:\Users\azull\OneDrive\Desktop\Analisis-mercado-evaluacion-terrenos\geo-app\app
ng serve
```

✅ **Abrir:** http://localhost:4200

---

## 🎯 URLS IMPORTANTES

| Componente | URL |
|------------|-----|
| **Frontend** | http://localhost:4200 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |
| **Supabase** | https://iagenteksupabase.iagentek.com.mx |
| **n8n Webhook** | https://iagentekn8nwebhook.iagentek.com.mx/webhook/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea |

---

## 🧪 PROBAR QUE TODO FUNCIONA

### ✅ Test 1: Backend
```powershell
curl http://localhost:8000/health
```
**Debe responder:** `{"status":"healthy"}`

### ✅ Test 2: Frontend
Abrir http://localhost:4200 - Debe cargar el mapa

### ✅ Test 3: Chatbot
1. Click en botón inferior izquierdo (Favier AI)
2. Escribir: "Hola"
3. Debe responder el AI

### ✅ Test 4: Predicciones ML
1. Click en "Predicciones ML"
2. Hacer zoom en Guadalajara
3. Click en cualquier punto del mapa
4. Debe mostrar predicciones cercanas

---

## 🔧 SOLUCIÓN RÁPIDA DE PROBLEMAS

### ❌ Backend no inicia: "Variables de entorno faltantes"

**Solución:**
```powershell
cd python_services
# Verificar que existe .env
Get-Content .env
# Si no existe, contactar al equipo
```

### ❌ Frontend: "NetworkError" o "CORS policy"

**Solución:**
1. Verificar que backend esté corriendo (puerto 8000)
2. Limpiar cache del navegador (Ctrl+Shift+Del)
3. Refrescar página (F5)

### ❌ Chatbot no responde

**Solución:**
1. Verificar n8n workflow esté ACTIVO (no test mode)
2. Ver browser console (F12) para errores
3. Verificar webhook URL en código

### ❌ Mapa no carga

**Solución:**
1. Verificar conexión a internet
2. Ver browser console (F12) para errores
3. Limpiar cache del navegador

---

## 📁 ESTRUCTURA DEL PROYECTO

```
geo-app/
├── python_services/          # Backend Python (FastAPI)
│   ├── api/main.py          # Servidor API
│   ├── config.py            # Configuración (lee .env)
│   ├── .env                 # ⚠️ Credenciales (NO subir a Git)
│   └── requirements.txt     # Dependencias Python
│
├── app/                     # Frontend Angular
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   └── ai-chatbot/  # Chatbot Favier AI
│   │   │   ├── pages/
│   │   │   │   └── mapa/        # Mapa principal
│   │   │   └── services/
│   │   │       ├── api.service.ts      # Conexión con backend
│   │   │       └── logger.service.ts   # Logging seguro
│   │   └── environments/
│   │       ├── environment.ts          # Config desarrollo
│   │       └── environment.prod.ts     # Config producción
│   └── package.json         # Dependencias Node
│
├── n8n_workflows/
│   └── FAVIER_AI_SYSTEM_PROMPT.md  # Prompt del chatbot
│
├── GUIA_SEGURIDAD_COMPLETA.md      # Guía técnica detallada
├── INSTRUCCIONES_DESPLIEGUE.md     # Despliegue a producción
├── RESUMEN_SEGURIDAD_Y_LIMPIEZA.md # Resumen ejecutivo
├── COMPLETADO_EXITOSAMENTE.md      # Estado final
└── INICIO_RAPIDO.md                # Esta guía
```

---

## 🔒 ARCHIVOS IMPORTANTES (NO TOCAR)

| Archivo | Descripción | ⚠️ |
|---------|-------------|---|
| `python_services/.env` | Credenciales sensibles | 🔴 NO SUBIR A GIT |
| `app/src/environments/environment.ts` | Config frontend | 🔴 NO SUBIR A GIT |
| `.gitignore` (todos) | Protección de archivos | ✅ Ya configurado |

---

## 📝 CAMBIOS COMUNES

### Cambiar puerto del backend:

**Archivo:** `python_services/.env`
```env
API_PORT=9000  # Cambiar de 8000 a 9000
```

### Cambiar URL del backend en frontend:

**Archivo:** `app/src/environments/environment.ts`
```typescript
mlApiBase: "http://localhost:9000"  // Cambiar puerto
```

### Actualizar prompt del chatbot:

**Archivo:** `n8n_workflows/FAVIER_AI_SYSTEM_PROMPT.md`
- Editar el prompt
- Copiar contenido completo
- Pegar en n8n → AI Agent → System Prompt
- Guardar workflow

---

## 🎓 DOCUMENTACIÓN COMPLETA

Para información detallada, consultar:

| Documento | Cuándo usarlo |
|-----------|---------------|
| **INICIO_RAPIDO.md** | Para arrancar el proyecto rápido |
| **GUIA_SEGURIDAD_COMPLETA.md** | Para entender la seguridad |
| **INSTRUCCIONES_DESPLIEGUE.md** | Para desplegar a producción |
| **RESUMEN_SEGURIDAD_Y_LIMPIEZA.md** | Para ver qué se hizo |
| **COMPLETADO_EXITOSAMENTE.md** | Para ver el estado final |

---

## ✅ CHECKLIST DIARIO

Antes de empezar a trabajar:

- [ ] Backend corriendo (puerto 8000)
- [ ] Frontend corriendo (puerto 4200)
- [ ] Navegador abierto en http://localhost:4200
- [ ] DevTools abierto (F12) para ver errores
- [ ] n8n workflow activo

Durante el trabajo:

- [ ] Guardar cambios frecuentemente
- [ ] Verificar errores en consola (F12)
- [ ] Probar chatbot después de cambios

Al terminar:

- [ ] Git status (verificar qué cambió)
- [ ] NO hacer commit del `.env`
- [ ] Cerrar terminales

---

## 🚨 EMERGENCIAS

### "¡Git detecta .env!"

```bash
git status
# Si aparece .env:
git reset HEAD python_services/.env
# NUNCA hacer commit de .env
```

### "¡Todo dejó de funcionar!"

1. **Cerrar todas las terminales**
2. **Reiniciar VSCode**
3. **Seguir "COMANDOS RÁPIDOS" arriba**
4. **Si persiste, consultar GUIA_SEGURIDAD_COMPLETA.md**

---

## 💡 TIPS ÚTILES

### Ver logs del backend:
```powershell
# En la terminal donde corre el backend
# Los logs aparecen automáticamente
```

### Ver logs del frontend:
- Abrir navegador → F12 → Console
- Ver errores en rojo
- Ver warnings en amarillo

### Reiniciar todo desde cero:
```powershell
# Terminal 1: Cerrar con Ctrl+C
# Terminal 2: Cerrar con Ctrl+C
# Luego seguir "COMANDOS RÁPIDOS"
```

---

## 🎯 COMANDOS ÚTILES

### Backend (Python):

```powershell
# Ver ayuda de uvicorn
python -m uvicorn --help

# Ver versión de Python
python --version

# Instalar dependencias
pip install -r requirements.txt

# Ver dependencias instaladas
pip list
```

### Frontend (Angular):

```powershell
# Ver versión de Angular
ng version

# Instalar dependencias
npm install

# Build de producción
ng build --configuration production

# Limpiar cache
Remove-Item -Recurse -Force .angular
```

---

## 🔄 WORKFLOW TÍPICO

1. **Abrir proyecto en VSCode**
2. **Abrir 2 terminales (Ctrl + Shift + ñ)**
3. **Terminal 1:** Arrancar backend
4. **Terminal 2:** Arrancar frontend
5. **Abrir navegador:** http://localhost:4200
6. **Trabajar y probar**
7. **Al terminar:** Ctrl+C en ambas terminales

---

**Proyecto listo para trabajar.** ⚡

Si algo falla, consultar **GUIA_SEGURIDAD_COMPLETA.md** o **INSTRUCCIONES_DESPLIEGUE.md**
