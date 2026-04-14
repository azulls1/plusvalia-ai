-- ================================================================
-- SCRIPT 2: CREACIÓN DE ÍNDICES
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================

-- ================================================================
-- ÍNDICES PARA: iainmobiliaria_comparables
-- ================================================================

-- Índice para consultas geográficas (lat, lon)
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_comparables_coords 
ON public.iainmobiliaria_comparables(lat, lon)
WHERE lat IS NOT NULL AND lon IS NOT NULL;

-- Índice para filtros por ubicación
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_comparables_location 
ON public.iainmobiliaria_comparables(city, state);

-- Índice para filtros por precio
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_comparables_price 
ON public.iainmobiliaria_comparables(price_m2)
WHERE price_m2 IS NOT NULL;

-- Índice para ordenamiento por fecha
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_comparables_created 
ON public.iainmobiliaria_comparables(created_at DESC);


-- ================================================================
-- ÍNDICES PARA: iainmobiliaria_amenities
-- ================================================================

-- Índice para consultas geográficas (lat, lon)
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_amenities_coords 
ON public.iainmobiliaria_amenities(lat, lon);

-- Índice único para OSM ID (evitar duplicados)
CREATE UNIQUE INDEX IF NOT EXISTS idx_iainmobiliaria_amenities_osm_id 
ON public.iainmobiliaria_amenities(osm_id);

-- Índice para filtros por tipo de amenidad
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_amenities_type 
ON public.iainmobiliaria_amenities(amenity_type);

-- Índice para filtros por ubicación
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_amenities_location 
ON public.iainmobiliaria_amenities(city, state)
WHERE city IS NOT NULL AND state IS NOT NULL;

-- Índice compuesto para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_amenities_type_location 
ON public.iainmobiliaria_amenities(amenity_type, city, state);

-- Índice GIN para búsquedas en tags JSON
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_amenities_tags 
ON public.iainmobiliaria_amenities USING GIN(tags)
WHERE tags IS NOT NULL;


-- ================================================================
-- ÍNDICES PARA: iainmobiliaria_grid_tiles
-- ================================================================

-- Índice para consultas geográficas (lat, lon)
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_grid_tiles_coords 
ON public.iainmobiliaria_grid_tiles(lat, lon);

-- Índice único compuesto (lat, lon) - ya existe como constraint UNIQUE
-- pero lo creamos explícitamente para asegurar
CREATE UNIQUE INDEX IF NOT EXISTS idx_iainmobiliaria_grid_tiles_unique_coords 
ON public.iainmobiliaria_grid_tiles(lat, lon);

-- Índice para ordenar por precio promedio
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_grid_tiles_price 
ON public.iainmobiliaria_grid_tiles(price_m2_avg DESC);

-- Índice para filtrar por cantidad de propiedades
CREATE INDEX IF NOT EXISTS idx_iainmobiliaria_grid_tiles_count 
ON public.iainmobiliaria_grid_tiles(count_properties)
WHERE count_properties > 0;


-- ================================================================
-- ANÁLISIS DE TABLAS (Opcional - para optimización)
-- ================================================================
-- Ejecutar después de cargar datos para actualizar estadísticas

-- ANALYZE public.iainmobiliaria_comparables;
-- ANALYZE public.iainmobiliaria_amenities;
-- ANALYZE public.iainmobiliaria_grid_tiles;


-- ================================================================
-- CONFIRMACIÓN
-- ================================================================
SELECT 'Índices creados exitosamente' AS status;

-- Verificar índices creados
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
ORDER BY tablename, indexname;

