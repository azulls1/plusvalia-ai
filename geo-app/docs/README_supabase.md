# Configuración de Supabase - Políticas RLS

Este documento describe las políticas de seguridad a nivel de fila (RLS) que deben configurarse en Supabase para el correcto funcionamiento de la aplicación.

## Tablas Requeridas

### 1. `grid_tiles`

Tabla que almacena las celdas de la grilla con precios promedio calculados.

**Columnas:**
- `id` (bigint, primary key)
- `lat` (float8) - Latitud del centro del tile
- `lon` (float8) - Longitud del centro del tile
- `price_m2_avg` (float8) - Precio promedio por m² en este tile
- `count_properties` (int4) - Cantidad de propiedades en este tile
- `created_at` (timestamp)

**Política RLS (Read-Only):**
```sql
-- Habilitar RLS en la tabla
ALTER TABLE grid_tiles ENABLE ROW LEVEL SECURITY;

-- Permitir lectura pública (anon key puede leer)
CREATE POLICY "Permitir lectura pública de grid_tiles"
ON grid_tiles
FOR SELECT
TO anon
USING (true);

-- Solo usuarios autenticados o service role pueden insertar/actualizar
CREATE POLICY "Solo service role puede modificar grid_tiles"
ON grid_tiles
FOR ALL
TO authenticated
USING (false)
WITH CHECK (false);
```

---

### 2. `amenities`

Tabla que almacena las amenidades extraídas de OpenStreetMap.

**Columnas:**
- `id` (bigint, primary key)
- `osm_id` (bigint) - ID de OSM (único)
- `name` (text) - Nombre de la amenidad
- `amenity_type` (text) - Tipo (school, hospital, etc.)
- `lat` (float8) - Latitud
- `lon` (float8) - Longitud
- `city` (text) - Ciudad
- `state` (text) - Estado
- `created_at` (timestamp)

**Política RLS (Read-Only):**
```sql
-- Habilitar RLS en la tabla
ALTER TABLE amenities ENABLE ROW LEVEL SECURITY;

-- Permitir lectura pública (anon key puede leer)
CREATE POLICY "Permitir lectura pública de amenities"
ON amenities
FOR SELECT
TO anon
USING (true);

-- Solo service role puede insertar/actualizar
CREATE POLICY "Solo service role puede modificar amenities"
ON amenities
FOR ALL
TO authenticated
USING (false)
WITH CHECK (false);
```

---

### 3. `comparables`

Tabla que almacena las propiedades comparables cargadas desde CSV.

**Columnas:**
- `id` (bigint, primary key)
- `title` (text)
- `price_mxn` (numeric)
- `area_m2` (numeric)
- `price_m2` (numeric) - Calculado: price_mxn / area_m2
- `address` (text)
- `city` (text)
- `state` (text)
- `lat` (float8) - Geocodificada por n8n
- `lon` (float8) - Geocodificada por n8n
- `created_at` (timestamp)

**Política RLS (Read-Only desde frontend):**
```sql
-- Habilitar RLS en la tabla
ALTER TABLE comparables ENABLE ROW LEVEL SECURITY;

-- Permitir lectura pública (anon key puede leer)
CREATE POLICY "Permitir lectura pública de comparables"
ON comparables
FOR SELECT
TO anon
USING (true);

-- Solo service role (n8n) puede insertar/actualizar
CREATE POLICY "Solo service role puede modificar comparables"
ON comparables
FOR ALL
TO authenticated
USING (false)
WITH CHECK (false);
```

---

## Notas Importantes

1. **Seguridad:** El frontend SOLO debe usar la `anon key`, NUNCA la `service_role key`.

2. **Escritura:** Todas las operaciones de escritura (INSERT, UPDATE, DELETE) deben hacerse desde n8n usando la `service_role key`.

3. **Lectura:** El frontend puede leer libremente con la `anon key` gracias a las políticas públicas de SELECT.

4. **Índices Recomendados:**
```sql
-- Para mejorar rendimiento en consultas geográficas
CREATE INDEX idx_grid_tiles_coords ON grid_tiles(lat, lon);
CREATE INDEX idx_amenities_coords ON amenities(lat, lon);
CREATE INDEX idx_amenities_type ON amenities(amenity_type);
CREATE INDEX idx_amenities_city_state ON amenities(city, state);
CREATE INDEX idx_comparables_coords ON comparables(lat, lon);

-- Índice único para evitar duplicados de OSM
CREATE UNIQUE INDEX idx_amenities_osm_id ON amenities(osm_id);
```

5. **Verificación:** Para verificar que las políticas están activas:
```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd 
FROM pg_policies 
WHERE tablename IN ('grid_tiles', 'amenities', 'comparables');
```

---

## Conexión desde n8n

Los workflows de n8n deben usar:
- **URL:** `https://iagenteksupabase.iagentek.com.mx`
- **Service Role Key:** (clave privada, SOLO en n8n, NO en frontend)

## Conexión desde Angular

La aplicación Angular usa:
- **URL:** `https://iagenteksupabase.iagentek.com.mx`
- **Anon Key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (configurada en `environment.ts`)

---

**Fecha:** Octubre 2025  
**Versión:** 1.0

