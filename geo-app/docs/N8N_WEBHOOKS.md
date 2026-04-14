# Configuración de Webhooks en n8n

Este documento describe los tres webhooks que deben configurarse en n8n para que la aplicación funcione correctamente.

## URL Base

Todas las rutas están bajo: `https://iagentekn8nwebhook.iagentek.com.mx`

---

## 1. Webhook: Ingesta de CSV (`/ingest-csv`)

### Propósito
Recibe un archivo CSV con comparables inmobiliarios, geocodifica las direcciones y los inserta en Supabase.

### Configuración

**Ruta:** `/ingest-csv`  
**Método:** `POST`  
**Content-Type:** `multipart/form-data`

### Flujo del Workflow

```
1. Webhook (recibe archivo CSV)
   ↓
2. CSV Parser (convierte CSV a JSON)
   ↓
3. Loop sobre cada fila
   ↓
4. Nominatim (geocodifica address → lat, lon)
   ↓
5. Calcular price_m2 = price_mxn / area_m2
   ↓
6. Supabase Insert (tabla: comparables)
   ↓
7. Responder: { ok: true, inserted: <n>, rejects: <m> }
```

### Campos Esperados en CSV

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| title | string | Sí | Título de la propiedad |
| price_mxn | number | Sí | Precio en pesos mexicanos |
| area_m2 | number | Sí | Área en metros cuadrados |
| address | string | Sí | Dirección completa |
| city | string | Sí | Ciudad |
| state | string | Sí | Estado |

### Respuesta Exitosa

```json
{
  "ok": true,
  "inserted": 10,
  "rejects": 0
}
```

### Respuesta con Errores

```json
{
  "ok": true,
  "inserted": 8,
  "rejects": 2,
  "errors": [
    { "row": 3, "error": "Geocoding failed" },
    { "row": 7, "error": "Invalid price" }
  ]
}
```

### Consideraciones

- Usar **service_role key** de Supabase (no anon key)
- Agregar retry logic para geocodificación
- Respetar rate limits de Nominatim (1 req/sec)
- Validar que price_mxn y area_m2 sean > 0
- Manejar casos donde geocodificación falle (guardar sin lat/lon o rechazar)

---

## 2. Webhook: Extracción OSM (`/osm-amenities`)

### Propósito
Extrae amenidades de OpenStreetMap para una ciudad/estado específica usando Overpass API.

### Configuración

**Ruta:** `/osm-amenities`  
**Método:** `POST`  
**Content-Type:** `application/json`

### Body Esperado

```json
{
  "city": "Queretaro",
  "state": "Queretaro",
  "types": "school,hospital,university,marketplace,bus_station,subway_entrance,fuel,industrial"
}
```

### Flujo del Workflow

```
1. Webhook (recibe city, state, types)
   ↓
2. Nominatim (obtiene bounding box de la ciudad)
   ↓
3. Construir query Overpass
   [bbox]
   (
     node["amenity"~"school|hospital|..."](bbox);
     way["amenity"~"school|hospital|..."](bbox);
     relation["amenity"~"school|hospital|..."](bbox);
   );
   out center;
   ↓
4. Overpass API (ejecuta query)
   ↓
5. Parsear resultados → extraer: osm_id, name, amenity_type, lat, lon
   ↓
6. Loop sobre resultados
   ↓
7. Supabase Upsert (tabla: amenities, clave: osm_id)
   ↓
8. Responder: { ok: true, upserts: <n> }
```

### Query Overpass Ejemplo

```
[out:json][timeout:60];
(
  node["amenity"~"^(school|hospital|university)$"](20.0,-100.5,21.0,-99.5);
  way["amenity"~"^(school|hospital|university)$"](20.0,-100.5,21.0,-99.5);
  relation["amenity"~"^(school|hospital|university)$"](20.0,-100.5,21.0,-99.5);
);
out center;
```

### Respuesta Exitosa

```json
{
  "ok": true,
  "upserts": 245
}
```

### Respuesta con Error

```json
{
  "ok": false,
  "error": "City not found in Nominatim"
}
```

### Consideraciones

- Usar **service_role key** de Supabase
- Bounding box: usar Nominatim para obtener límites de la ciudad
- Timeout Overpass: mínimo 60 segundos (ciudades grandes)
- Rate limit Overpass: ~2 queries/min (agregar delays si es necesario)
- Deduplicación: usar `osm_id` como clave única (UPSERT, no INSERT)
- Manejar amenidades sin nombre (name puede ser NULL)

---

## 3. Webhook: Reconstrucción de Grilla (`/grid-build`)

### Propósito
Recalcula la grilla de precios promedio dividiendo el área de cobertura en celdas y promediando el precio/m² de los comparables en cada celda.

### Configuración

**Ruta:** `/grid-build`  
**Método:** `POST`  
**Content-Type:** `application/json`

### Body Esperado

```json
{
  "step": 0.005
}
```

**Nota:** `step` es opcional. Por defecto usa `0.005` grados (~500m).

### Flujo del Workflow

```
1. Webhook (recibe step)
   ↓
2. Supabase Query (obtener todos los comparables con lat, lon, price_m2)
   ↓
3. Calcular bounding box de todos los comparables
   lat_min, lat_max, lon_min, lon_max
   ↓
4. Generar grilla
   for lat = lat_min to lat_max step 0.005:
     for lon = lon_min to lon_max step 0.005:
       crear tile: { lat_center, lon_center, lat_min, lat_max, lon_min, lon_max }
   ↓
5. Para cada tile, filtrar comparables dentro del bbox
   ↓
6. Calcular price_m2_avg y count_properties para ese tile
   ↓
7. Supabase Delete (limpiar tabla grid_tiles)
   ↓
8. Supabase Insert Batch (insertar nuevos tiles con datos)
   ↓
9. Responder: { ok: true, tiles: <n> }
```

### Algoritmo de Grilla (Pseudocódigo)

```javascript
function buildGrid(comparables, step = 0.005) {
  // 1. Obtener bounding box
  const latMin = Math.min(...comparables.map(c => c.lat));
  const latMax = Math.max(...comparables.map(c => c.lat));
  const lonMin = Math.min(...comparables.map(c => c.lon));
  const lonMax = Math.max(...comparables.map(c => c.lon));

  const tiles = [];

  // 2. Generar grilla
  for (let lat = latMin; lat <= latMax; lat += step) {
    for (let lon = lonMin; lon <= lonMax; lon += step) {
      const tileLatMin = lat;
      const tileLatMax = lat + step;
      const tileLonMin = lon;
      const tileLonMax = lon + step;
      
      const tileLatCenter = lat + step / 2;
      const tileLonCenter = lon + step / 2;

      // 3. Filtrar comparables en este tile
      const propsInTile = comparables.filter(c => 
        c.lat >= tileLatMin && c.lat < tileLatMax &&
        c.lon >= tileLonMin && c.lon < tileLonMax
      );

      // 4. Calcular promedio
      if (propsInTile.length > 0) {
        const avgPrice = propsInTile.reduce((sum, c) => sum + c.price_m2, 0) / propsInTile.length;
        
        tiles.push({
          lat: tileLatCenter,
          lon: tileLonCenter,
          price_m2_avg: avgPrice,
          count_properties: propsInTile.length
        });
      }
    }
  }

  return tiles;
}
```

### Respuesta Exitosa

```json
{
  "ok": true,
  "tiles": 1523
}
```

### Respuesta con Error

```json
{
  "ok": false,
  "error": "No comparables found in database"
}
```

### Consideraciones

- Usar **service_role key** de Supabase
- Esta operación puede ser costosa (muchas iteraciones)
- Para datasets grandes (>10,000 comparables), considerar:
  - Procesar en batches
  - Usar función de PostgreSQL (más eficiente)
  - Limitar a una región específica
- Limpiar tabla `grid_tiles` antes de insertar nuevos datos
- Insertar en batches de 100-500 tiles (no uno por uno)
- Considerar índices espaciales en PostgreSQL para optimización

### Optimización con PostgreSQL

Alternativa: crear una función SQL en Supabase que haga el cálculo:

```sql
CREATE OR REPLACE FUNCTION rebuild_grid(step_deg float DEFAULT 0.005)
RETURNS int AS $$
DECLARE
  tile_count int;
BEGIN
  -- Limpiar tabla
  DELETE FROM grid_tiles;
  
  -- Insertar tiles con precio promedio
  INSERT INTO grid_tiles (lat, lon, price_m2_avg, count_properties)
  SELECT
    ROUND((lat / step_deg)::numeric, 0) * step_deg + step_deg / 2 AS lat,
    ROUND((lon / step_deg)::numeric, 0) * step_deg + step_deg / 2 AS lon,
    AVG(price_m2) AS price_m2_avg,
    COUNT(*) AS count_properties
  FROM comparables
  WHERE lat IS NOT NULL AND lon IS NOT NULL AND price_m2 > 0
  GROUP BY ROUND((lat / step_deg)::numeric, 0), ROUND((lon / step_deg)::numeric, 0);
  
  GET DIAGNOSTICS tile_count = ROW_COUNT;
  RETURN tile_count;
END;
$$ LANGUAGE plpgsql;
```

Desde n8n, solo llamar a esta función.

---

## Configuración de CORS en n8n

Si los webhooks están en un dominio diferente al frontend, configurar CORS:

### En n8n (settings)

```json
{
  "security": {
    "cors": {
      "enabled": true,
      "origins": [
        "http://localhost:4200",
        "https://tu-dominio-en-hostinger.com"
      ]
    }
  }
}
```

### O en cada Webhook node

- Activar "CORS Enabled"
- Agregar orígenes permitidos

---

## Testing de Webhooks

### Test 1: /ingest-csv

```bash
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/ingest-csv \
  -F "file=@comparables_demo.csv"
```

### Test 2: /osm-amenities

```bash
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/osm-amenities \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Queretaro",
    "state": "Queretaro",
    "types": "school,hospital"
  }'
```

### Test 3: /grid-build

```bash
curl -X POST https://iagentekn8nwebhook.iagentek.com.mx/grid-build \
  -H "Content-Type: application/json" \
  -d '{ "step": 0.005 }'
```

---

## Monitoreo y Logs

Recomendaciones:
- Activar logging en n8n para cada workflow
- Monitorear tiempos de ejecución
- Alertas si un webhook falla
- Dashboard con métricas:
  - Cantidad de comparables procesados
  - Cantidad de amenidades extraídas
  - Tiempo promedio de ejecución
  - Tasa de errores

---

**Versión:** 1.0  
**Última actualización:** Octubre 2025

