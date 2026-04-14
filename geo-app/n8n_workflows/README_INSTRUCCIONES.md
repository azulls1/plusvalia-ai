# 📦 Workflows de N8N - Instrucciones de Importación

## 🎯 Workflows Creados:

1. **`01_ingest_csv.json`** - Subir y procesar archivos CSV
2. **`02_osm_amenities.json`** - Extraer amenidades de OpenStreetMap
3. **`03_grid_build.json`** - Recalcular grilla de precios

---

## 📋 Pasos para Importar en N8N:

### **Paso 1: Acceder a N8N**
1. Ve a: https://iagentekn8n.iagentek.com.mx/home/workflows
2. Inicia sesión con tus credenciales

---

### **Paso 2: Importar cada Workflow**

Para **cada uno de los 3 archivos JSON**:

1. **Click en el botón de menú** (3 líneas horizontales) arriba a la derecha
2. **Selecciona "Import from File"** o "Importar desde archivo"
3. **Selecciona el archivo JSON** correspondiente:
   - `01_ingest_csv.json`
   - `02_osm_amenities.json`
   - `03_grid_build.json`
4. **Click "Import"** o "Importar"

---

### **Paso 3: Configurar Credenciales de Supabase**

Después de importar, **DEBES configurar las credenciales**:

#### **A. Crear credencial de Supabase:**
1. En N8N, ve a **"Credentials"** en el menú lateral
2. Click en **"+ New Credential"**
3. Busca y selecciona **"Supabase API"**
4. Completa los campos:
   - **Name**: `Supabase Inmobiliaria`
   - **Host**: `iagenteksupabase.iagentek.com.mx`
   - **Service Role Secret**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogInNlcnZpY2Vfcm9sZSIsCiAgImlzcyI6ICJzdXBhYmFzZSIsCiAgImlhdCI6IDE3MTUwNTA4MDAsCiAgImV4cCI6IDE4NzI4MTcyMDAKfQ.82nFc9RPC-0tzN0svrqQrnHUHHe51bJkpCUiC_uTypo`
5. **Save**

#### **B. Crear credencial de PostgreSQL (para Workflow 3):**
1. Click en **"+ New Credential"**
2. Busca y selecciona **"Postgres"**
3. Completa los campos:
   - **Name**: `PostgreSQL Supabase`
   - **Host**: `iagenteksupabase.iagentek.com.mx`
   - **Port**: `5432`
   - **Database**: `postgres`
   - **User**: `postgres`
   - **Password**: (la contraseña de tu PostgreSQL en Supabase)
   - **SSL**: ✅ Activado
4. **Test Connection** → debe salir verde ✅
5. **Save**

---

### **Paso 4: Asignar Credenciales a los Workflows**

Para **cada workflow importado**:

#### **Workflow 1 y 2** (ingest-csv y osm-amenities):
1. Abre el workflow
2. Click en el nodo **"Insert to Supabase"** o **"Upsert to Supabase"**
3. En **"Credentials"**, selecciona: `Supabase Inmobiliaria`
4. **Save** el workflow

#### **Workflow 3** (grid-build):
1. Abre el workflow
2. Click en el nodo **"Call rebuild_grid Function"**
3. En **"Credentials"**, selecciona: `PostgreSQL Supabase`
4. **Save** el workflow

---

### **Paso 5: Activar los Workflows**

Para cada workflow:
1. Abre el workflow
2. Click en el **toggle** arriba a la derecha para activarlo (debe ponerse verde ✅)
3. El workflow ahora está **activo** y escuchando peticiones

---

### **Paso 6: Obtener las URLs de los Webhooks**

Para cada workflow:
1. Abre el workflow
2. Click en el nodo **"Webhook"**
3. Copia la **URL del webhook** (algo como: `https://iagentekn8nwebhook.iagentek.com.mx/webhook/...`)
4. **IMPORTANTE**: Debe tener el path correcto:
   - Workflow 1: `.../ingest-csv`
   - Workflow 2: `.../osm-amenities`
   - Workflow 3: `.../grid-build`

---

## 🧪 Paso 7: Probar los Webhooks

### **Test 1: Probar grid-build (el más simple)**

En tu terminal o Postman:
```bash
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/grid-build \
  -H "Content-Type: application/json" \
  -d '{"step": 0.005}'
```

**Respuesta esperada:**
```json
{
  "ok": true,
  "tiles": 10,
  "comparables_used": 10,
  "execution_time_ms": 1234.56,
  "message": "Grilla recalculada exitosamente"
}
```

---

### **Test 2: Probar osm-amenities**

```bash
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/osm-amenities \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Guadalajara",
    "state": "Jalisco",
    "types": "school,hospital"
  }'
```

**Respuesta esperada:**
```json
{
  "ok": true,
  "upserts": 245,
  "message": "Amenidades extraídas exitosamente"
}
```

---

### **Test 3: Probar ingest-csv**

Este requiere un archivo CSV. Usa el archivo de ejemplo:
```bash
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/ingest-csv \
  -F "file=@geo-app/data/samples/comparables_demo.csv"
```

---

## ⚠️ Problemas Comunes:

### **Error: "Credential not found"**
- Asegúrate de haber creado las credenciales de Supabase/PostgreSQL
- Asigna las credenciales a cada nodo que las necesite

### **Error: "Connection refused"**
- Verifica que la URL de Supabase sea correcta
- Verifica que el Service Role Key sea el correcto

### **Error: "Table not found"**
- Verifica que las tablas `iainmobiliaria_*` existan en Supabase
- Ejecuta los scripts SQL si no las has creado

### **Error en Nominatim: "429 Too Many Requests"**
- Estás haciendo demasiadas peticiones muy rápido
- Agrega un delay entre peticiones (1-2 segundos)

---

## 🔧 Configuración de CORS (si es necesario)

Si tienes errores de CORS desde el frontend:

1. En cada webhook, activa **"CORS Enabled"**
2. Agrega orígenes permitidos:
   - `http://localhost:4200`
   - `http://localhost:52130`
   - Tu dominio de producción

---

## 📊 Verificación Final:

Una vez todo configurado, verifica en la interfaz Angular:

1. **Subir CSV**: Usa el botón "Cargar Comparables"
2. **Extraer OSM**: Selecciona tipos de amenidad y click "Extraer OSM (Ciudad)"
3. **Recalcular Grilla**: Click "Recalcular Grilla"

Si todo funciona ✅, ¡tu proyecto está al 100%!

---

## 🆘 Soporte:

Si tienes problemas:
1. Revisa los logs de ejecución en N8N
2. Verifica las credenciales
3. Prueba con los comandos curl primero

---

**¡Éxito con la importación!** 🚀

