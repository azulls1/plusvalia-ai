-- ================================================================
-- SCRIPT 1: CREACIÓN DE TABLAS
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================

-- Tabla 1: iainmobiliaria_comparables
-- Almacena propiedades comparables cargadas desde CSV
CREATE TABLE IF NOT EXISTS public.iainmobiliaria_comparables (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  price_mxn NUMERIC(12, 2) NOT NULL CHECK (price_mxn > 0),
  area_m2 NUMERIC(10, 2) NOT NULL CHECK (area_m2 > 0),
  price_m2 NUMERIC(10, 2) GENERATED ALWAYS AS (price_mxn / area_m2) STORED,
  address TEXT NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  lat FLOAT8,
  lon FLOAT8,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comentarios descriptivos
COMMENT ON TABLE public.iainmobiliaria_comparables IS 'Propiedades comparables para análisis de mercado inmobiliario';
COMMENT ON COLUMN public.iainmobiliaria_comparables.price_m2 IS 'Precio por m² calculado automáticamente';
COMMENT ON COLUMN public.iainmobiliaria_comparables.lat IS 'Latitud geocodificada por n8n';
COMMENT ON COLUMN public.iainmobiliaria_comparables.lon IS 'Longitud geocodificada por n8n';


-- Tabla 2: iainmobiliaria_amenities
-- Almacena amenidades extraídas de OpenStreetMap
CREATE TABLE IF NOT EXISTS public.iainmobiliaria_amenities (
  id BIGSERIAL PRIMARY KEY,
  osm_id BIGINT UNIQUE NOT NULL,
  name TEXT,
  amenity_type TEXT NOT NULL,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  city TEXT,
  state TEXT,
  tags JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comentarios descriptivos
COMMENT ON TABLE public.iainmobiliaria_amenities IS 'Amenidades (escuelas, hospitales, etc.) extraídas de OpenStreetMap';
COMMENT ON COLUMN public.iainmobiliaria_amenities.osm_id IS 'ID único de OpenStreetMap para evitar duplicados';
COMMENT ON COLUMN public.iainmobiliaria_amenities.amenity_type IS 'Tipo: school, hospital, university, marketplace, etc.';
COMMENT ON COLUMN public.iainmobiliaria_amenities.tags IS 'Metadatos adicionales de OSM en formato JSON';


-- Tabla 3: iainmobiliaria_grid_tiles
-- Almacena grilla de precios promedio por zona
CREATE TABLE IF NOT EXISTS public.iainmobiliaria_grid_tiles (
  id BIGSERIAL PRIMARY KEY,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  price_m2_avg FLOAT8 NOT NULL CHECK (price_m2_avg > 0),
  count_properties INT NOT NULL CHECK (count_properties > 0),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(lat, lon)
);

-- Comentarios descriptivos
COMMENT ON TABLE public.iainmobiliaria_grid_tiles IS 'Grilla de precios promedio calculada desde comparables';
COMMENT ON COLUMN public.iainmobiliaria_grid_tiles.lat IS 'Latitud del centro del tile';
COMMENT ON COLUMN public.iainmobiliaria_grid_tiles.lon IS 'Longitud del centro del tile';
COMMENT ON COLUMN public.iainmobiliaria_grid_tiles.price_m2_avg IS 'Precio promedio por m² en este tile';
COMMENT ON COLUMN public.iainmobiliaria_grid_tiles.count_properties IS 'Cantidad de propiedades usadas en el cálculo';


-- ================================================================
-- CONFIRMACIÓN
-- ================================================================
SELECT 'Tablas creadas exitosamente' AS status;

-- Verificar tablas creadas
SELECT 
  schemaname,
  tablename,
  tableowner
FROM pg_tables
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
ORDER BY tablename;

