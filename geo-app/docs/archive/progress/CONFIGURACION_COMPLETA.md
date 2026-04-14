# 🎯 Configuración Completa del Proyecto

## ✅ Estado Actual (25 de Octubre 2025)

### Frontend Angular
- ✅ **Servidor corriendo** en puerto 52130
- ✅ **HTML corregido** (eliminados comentarios mal colocados)
- ✅ **Componentes funcionando**:
  - Panel de carga de CSV
  - Panel de filtros
  - Mapa Leaflet
- ✅ **Servicio API actualizado** para usar tablas con prefijo `iainmobiliaria_`

---

## 📋 Scripts SQL Creados

Se han generado **7 scripts SQL** listos para ejecutar en Supabase:

### 📁 Carpeta: `scripts_sql/`

1. **`00_INSTRUCCIONES.md`** - Guía completa de ejecución
2. **`01_crear_tablas.sql`** - Crea las 3 tablas principales
3. **`02_indices.sql`** - Crea índices para optimización
4. **`03_rls_policies.sql`** - Configura políticas RLS de seguridad
5. **`04_funciones_utiles.sql`** - Funciones PostgreSQL útiles
6. **`05_verificacion.sql`** - Verifica que todo esté correcto
7. **`06_datos_prueba.sql`** - (Opcional) Datos de ejemplo para testing

---

## 🗄️ Tablas Configuradas

Todas las tablas usan el prefijo **`iainmobiliaria_`**:

### 1. `iainmobiliaria_comparables`
- Propiedades comparables cargadas desde CSV
- Columnas: id, title, price_mxn, area_m2, price_m2, address, city, state, lat, lon
- **price_m2** se calcula automáticamente

### 2. `iainmobiliaria_amenities`
- Amenidades de OpenStreetMap (escuelas, hospitales, etc.)
- Columnas: id, osm_id, name, amenity_type, lat, lon, city, state, tags
- **osm_id** es único para evitar duplicados

### 3. `iainmobiliaria_grid_tiles`
- Grilla de precios promedio por zona
- Columnas: id, lat, lon, price_m2_avg, count_properties
- **lat, lon** son únicos (no duplicados)

---

## 🔐 Seguridad RLS Configurada

### Permisos por Rol:

| Operación | anon (Frontend) | authenticated | service_role (N8N) |
|-----------|-----------------|---------------|-------------------|
| **SELECT** | ✅ Sí | ✅ Sí | ✅ Sí |
| **INSERT** | ❌ No | ✅ Sí | ✅ Sí |
| **UPDATE** | ❌ No | ✅ Sí | ✅ Sí |
| **DELETE** | ❌ No | ✅ Sí | ✅ Sí |

**Seguridad:**
- ✅ Frontend usa `anon key` (solo lectura)
- ✅ N8N usa `service_role key` (lectura/escritura)
- ✅ Datos públicos de solo lectura
- ✅ Escrituras protegidas

---

## 📊 Funciones PostgreSQL Creadas

### 1. `rebuild_grid(step_deg)`
Recalcula toda la grilla de precios desde los comparables.
```sql
SELECT * FROM rebuild_grid(0.005);
```

### 2. `get_statistics()`
Retorna estadísticas generales del sistema.
```sql
SELECT * FROM get_statistics();
```

### 3. `clean_old_data(days_old)`
Elimina registros más antiguos que X días.
```sql
SELECT * FROM clean_old_data(90);
```

### 4. `get_nearby_amenities(lat, lon, radius_km, type)`
Busca amenidades cercanas a una coordenada.
```sql
SELECT * FROM get_nearby_amenities(20.5888, -100.3899, 5.0, 'school');
```

### 5. Triggers `update_updated_at`
Actualiza automáticamente la columna `updated_at` en cada UPDATE.

---

## 🚀 Próximos Pasos

### PASO 1: Ejecutar Scripts en Supabase ⚡

1. Acceder a **Supabase Dashboard** → **SQL Editor**
2. Ejecutar scripts en orden:
   - ✅ `01_crear_tablas.sql`
   - ✅ `02_indices.sql`
   - ✅ `03_rls_policies.sql`
   - ✅ `04_funciones_utiles.sql`
   - ✅ `05_verificacion.sql` (verificar que todo está OK)
   - 📦 `06_datos_prueba.sql` (opcional, para testing)

**Tiempo total:** ~1 minuto

---

### PASO 2: Configurar Webhooks en N8N 🔗

Necesitas crear **3 workflows** en N8N:

#### Workflow 1: `/ingest-csv`
**Propósito:** Recibe CSV → Geocodifica → Inserta en `iainmobiliaria_comparables`

**Flujo:**
```
Webhook POST /ingest-csv
  ↓ (recibe archivo CSV)
CSV Parser
  ↓ (convierte a JSON)
Loop sobre filas
  ↓
Nominatim (geocodificar)
  ↓
Supabase Insert (tabla: iainmobiliaria_comparables)
  ↓
Responder: { ok: true, inserted: N, rejects: M }
```

**Configuración:**
- Ruta: `/ingest-csv`
- Método: `POST`
- Content-Type: `multipart/form-data`
- Supabase: usar **service_role key**

---

#### Workflow 2: `/osm-amenities`
**Propósito:** Extrae amenidades de OpenStreetMap

**Flujo:**
```
Webhook POST /osm-amenities
  ↓ (recibe { city, state, types })
Nominatim (obtener bounding box)
  ↓
Construir query Overpass
  ↓
Overpass API (ejecutar query)
  ↓
Loop sobre resultados
  ↓
Supabase Upsert (tabla: iainmobiliaria_amenities)
  ↓
Responder: { ok: true, upserts: N }
```

**Body esperado:**
```json
{
  "city": "Queretaro",
  "state": "Queretaro",
  "types": "school,hospital,university,marketplace"
}
```

**Configuración:**
- Ruta: `/osm-amenities`
- Método: `POST`
- Content-Type: `application/json`
- Supabase: usar **service_role key**

---

#### Workflow 3: `/grid-build`
**Propósito:** Recalcula grilla de precios

**Opción A - Usar función PostgreSQL (Recomendado):**
```
Webhook POST /grid-build
  ↓ (recibe { step })
Supabase: SELECT rebuild_grid(step)
  ↓
Responder: { ok: true, tiles: N }
```

**Opción B - Procesar en N8N:**
```
Webhook POST /grid-build
  ↓
Supabase Query (obtener todos los comparables)
  ↓
Function Node (calcular grilla en JavaScript)
  ↓
Supabase Delete (limpiar grid_tiles)
  ↓
Supabase Insert Batch (insertar nuevos tiles)
  ↓
Responder: { ok: true, tiles: N }
```

**Body esperado:**
```json
{
  "step": 0.005
}
```

**Configuración:**
- Ruta: `/grid-build`
- Método: `POST`
- Content-Type: `application/json`
- Supabase: usar **service_role key**

---

### PASO 3: Configurar CORS en N8N 🌐

Si los webhooks están en dominio diferente:

```json
{
  "security": {
    "cors": {
      "enabled": true,
      "origins": [
        "http://localhost:4200",
        "http://localhost:52130",
        "https://tu-dominio-hostinger.com"
      ]
    }
  }
}
```

O activar en cada **Webhook node**: CORS Enabled ✓

---

### PASO 4: Testing 🧪

#### Test con cURL:

```bash
# Test 1: Subir CSV
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/ingest-csv \
  -F "file=@data/samples/comparables_demo.csv"

# Test 2: Extraer OSM
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/osm-amenities \
  -H "Content-Type: application/json" \
  -d '{"city":"Queretaro","state":"Queretaro","types":"school,hospital"}'

# Test 3: Recalcular grilla
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/grid-build \
  -H "Content-Type: application/json" \
  -d '{"step":0.005}'
```

#### Test en Frontend:
1. Abrir `http://localhost:52130/mapa`
2. Cargar archivo CSV de prueba
3. Aplicar filtros
4. Extraer OSM
5. Recalcular grilla

---

## 📝 Notas Importantes

### Variables de Entorno
Las credenciales ya están configuradas en:
- `src/environments/environment.ts` (desarrollo)
- `src/environments/environment.prod.ts` (producción)

### Claves de Supabase
- **Anon Key**: Ya configurada en environment.ts (segura para frontend)
- **Service Role Key**: Solo para N8N (NO incluir en frontend)

### Nomenclatura de Tablas
Todas las tablas usan el prefijo **`iainmobiliaria_`** para:
- ✅ Evitar conflictos con otras apps
- ✅ Identificar fácilmente las tablas del proyecto
- ✅ Mejor organización en Supabase

---

## 🐛 Solución de Problemas

### Error: "relation iainmobiliaria_comparables does not exist"
**Solución:** Ejecutar `01_crear_tablas.sql` en Supabase

### Error: "permission denied for table"
**Solución:** Ejecutar `03_rls_policies.sql` para configurar permisos

### Error: "function rebuild_grid does not exist"
**Solución:** Ejecutar `04_funciones_utiles.sql`

### Mapa no muestra datos
**Solución:** 
1. Verificar que hay datos: `SELECT COUNT(*) FROM iainmobiliaria_grid_tiles;`
2. Verificar políticas RLS: `05_verificacion.sql`
3. Ver consola del navegador (F12) para errores

### N8N webhooks no responden
**Solución:**
1. Verificar que workflows estén activos
2. Verificar CORS configurado
3. Probar con cURL primero

---

## 📧 Soporte

**Email:** contacto@iagentek.com.mx  
**Documentación:** Ver carpeta `docs/` y `scripts_sql/`

---

## ✅ Checklist Final

### Supabase:
- [ ] Script 1 ejecutado (Tablas creadas)
- [ ] Script 2 ejecutado (Índices creados)
- [ ] Script 3 ejecutado (RLS configurado)
- [ ] Script 4 ejecutado (Funciones creadas)
- [ ] Script 5 ejecutado (Verificación OK)
- [ ] Script 6 ejecutado (Datos prueba - opcional)

### N8N:
- [ ] Workflow `/ingest-csv` creado y activo
- [ ] Workflow `/osm-amenities` creado y activo
- [ ] Workflow `/grid-build` creado y activo
- [ ] CORS configurado
- [ ] Service Role Key configurada
- [ ] Tests con cURL exitosos

### Frontend:
- [ ] Servidor corriendo (puerto 4200 o 52130)
- [ ] Interfaz carga correctamente
- [ ] Mapa se muestra
- [ ] No hay errores en consola

---

**🎉 ¡Todo listo para comenzar a usar la aplicación!**

**Versión:** 1.0  
**Última actualización:** 25 de Octubre 2025

