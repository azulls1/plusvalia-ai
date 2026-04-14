-- ================================================================
-- SCRIPT 4: FUNCIONES ÚTILES
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================

-- ================================================================
-- FUNCIÓN 1: Reconstruir grilla de precios
-- ================================================================
-- Esta función recalcula todos los tiles de la grilla desde cero
-- Uso: SELECT rebuild_grid(0.005);

CREATE OR REPLACE FUNCTION public.rebuild_grid(
  step_deg FLOAT DEFAULT 0.005
)
RETURNS TABLE(
  tiles_created INT,
  comparables_used INT,
  execution_time_ms FLOAT
) AS $$
DECLARE
  start_time TIMESTAMP;
  end_time TIMESTAMP;
  tile_count INT;
  comp_count INT;
BEGIN
  start_time := clock_timestamp();
  
  -- Contar comparables válidos
  SELECT COUNT(*) INTO comp_count
  FROM public.iainmobiliaria_comparables
  WHERE lat IS NOT NULL 
    AND lon IS NOT NULL 
    AND price_m2 > 0;
  
  -- Verificar que hay datos
  IF comp_count = 0 THEN
    RAISE EXCEPTION 'No hay comparables con coordenadas válidas';
  END IF;
  
  -- Limpiar tabla de tiles
  DELETE FROM public.iainmobiliaria_grid_tiles;
  
  -- Insertar nuevos tiles con precios promedio
  INSERT INTO public.iainmobiliaria_grid_tiles (lat, lon, price_m2_avg, count_properties)
  SELECT
    ROUND((lat / step_deg)::NUMERIC, 0) * step_deg + step_deg / 2 AS lat,
    ROUND((lon / step_deg)::NUMERIC, 0) * step_deg + step_deg / 2 AS lon,
    AVG(price_m2) AS price_m2_avg,
    COUNT(*)::INT AS count_properties
  FROM public.iainmobiliaria_comparables
  WHERE lat IS NOT NULL 
    AND lon IS NOT NULL 
    AND price_m2 > 0
  GROUP BY 
    ROUND((lat / step_deg)::NUMERIC, 0), 
    ROUND((lon / step_deg)::NUMERIC, 0);
  
  GET DIAGNOSTICS tile_count = ROW_COUNT;
  
  end_time := clock_timestamp();
  
  -- Retornar estadísticas
  RETURN QUERY SELECT 
    tile_count,
    comp_count,
    (EXTRACT(EPOCH FROM (end_time - start_time)) * 1000)::FLOAT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.rebuild_grid IS 'Reconstruye la grilla de precios desde los comparables';


-- ================================================================
-- FUNCIÓN 2: Obtener estadísticas generales
-- ================================================================
-- Uso: SELECT * FROM get_statistics();

CREATE OR REPLACE FUNCTION public.get_statistics()
RETURNS TABLE(
  total_comparables BIGINT,
  total_amenities BIGINT,
  total_grid_tiles BIGINT,
  avg_price_m2 NUMERIC,
  min_price_m2 NUMERIC,
  max_price_m2 NUMERIC,
  cities_count BIGINT,
  states_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    (SELECT COUNT(*) FROM public.iainmobiliaria_comparables),
    (SELECT COUNT(*) FROM public.iainmobiliaria_amenities),
    (SELECT COUNT(*) FROM public.iainmobiliaria_grid_tiles),
    (SELECT ROUND(AVG(price_m2), 2) FROM public.iainmobiliaria_comparables WHERE price_m2 > 0),
    (SELECT ROUND(MIN(price_m2), 2) FROM public.iainmobiliaria_comparables WHERE price_m2 > 0),
    (SELECT ROUND(MAX(price_m2), 2) FROM public.iainmobiliaria_comparables WHERE price_m2 > 0),
    (SELECT COUNT(DISTINCT city) FROM public.iainmobiliaria_comparables WHERE city IS NOT NULL),
    (SELECT COUNT(DISTINCT state) FROM public.iainmobiliaria_comparables WHERE state IS NOT NULL);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.get_statistics IS 'Retorna estadísticas generales del sistema';


-- ================================================================
-- FUNCIÓN 3: Limpiar datos antiguos
-- ================================================================
-- Elimina registros más antiguos que X días
-- Uso: SELECT clean_old_data(90); -- elimina datos de hace más de 90 días

CREATE OR REPLACE FUNCTION public.clean_old_data(
  days_old INT DEFAULT 90
)
RETURNS TABLE(
  comparables_deleted INT,
  amenities_deleted INT,
  tiles_deleted INT
) AS $$
DECLARE
  comp_deleted INT;
  amen_deleted INT;
  tiles_deleted_count INT;
  cutoff_date TIMESTAMP;
BEGIN
  cutoff_date := NOW() - (days_old || ' days')::INTERVAL;
  
  -- Eliminar comparables antiguos
  DELETE FROM public.iainmobiliaria_comparables
  WHERE created_at < cutoff_date;
  GET DIAGNOSTICS comp_deleted = ROW_COUNT;
  
  -- Eliminar amenidades antiguas
  DELETE FROM public.iainmobiliaria_amenities
  WHERE created_at < cutoff_date;
  GET DIAGNOSTICS amen_deleted = ROW_COUNT;
  
  -- Eliminar tiles antiguos
  DELETE FROM public.iainmobiliaria_grid_tiles
  WHERE created_at < cutoff_date;
  GET DIAGNOSTICS tiles_deleted_count = ROW_COUNT;
  
  RETURN QUERY SELECT comp_deleted, amen_deleted, tiles_deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.clean_old_data IS 'Elimina registros más antiguos que X días';


-- ================================================================
-- FUNCIÓN 4: Obtener amenidades cercanas a una coordenada
-- ================================================================
-- Retorna amenidades dentro de un radio (en km)
-- Uso: SELECT * FROM get_nearby_amenities(20.5, -100.4, 5.0, 'school');

CREATE OR REPLACE FUNCTION public.get_nearby_amenities(
  target_lat FLOAT,
  target_lon FLOAT,
  radius_km FLOAT DEFAULT 5.0,
  amenity_filter TEXT DEFAULT NULL
)
RETURNS TABLE(
  id BIGINT,
  name TEXT,
  amenity_type TEXT,
  lat FLOAT8,
  lon FLOAT8,
  distance_km FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    subquery.id,
    subquery.name,
    subquery.amenity_type,
    subquery.lat,
    subquery.lon,
    subquery.distance_km
  FROM (
    SELECT
      a.id,
      a.name,
      a.amenity_type,
      a.lat,
      a.lon,
      -- Fórmula Haversine simplificada para distancia aproximada
      (6371 * acos(
        cos(radians(target_lat)) * cos(radians(a.lat)) *
        cos(radians(a.lon) - radians(target_lon)) +
        sin(radians(target_lat)) * sin(radians(a.lat))
      ))::FLOAT AS distance_km
    FROM public.iainmobiliaria_amenities a
    WHERE (amenity_filter IS NULL OR a.amenity_type = amenity_filter)
      -- Pre-filtro por bounding box (más eficiente)
      AND a.lat BETWEEN target_lat - (radius_km / 111.0) AND target_lat + (radius_km / 111.0)
      AND a.lon BETWEEN target_lon - (radius_km / 111.0) AND target_lon + (radius_km / 111.0)
  ) AS subquery
  WHERE subquery.distance_km <= get_nearby_amenities.radius_km
  ORDER BY subquery.distance_km ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.get_nearby_amenities IS 'Retorna amenidades cercanas a una coordenada dentro de un radio en km';


-- ================================================================
-- FUNCIÓN 5: Trigger para actualizar updated_at
-- ================================================================
-- Actualiza automáticamente la columna updated_at

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a todas las tablas
DROP TRIGGER IF EXISTS update_comparables_updated_at ON public.iainmobiliaria_comparables;
CREATE TRIGGER update_comparables_updated_at
  BEFORE UPDATE ON public.iainmobiliaria_comparables
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_amenities_updated_at ON public.iainmobiliaria_amenities;
CREATE TRIGGER update_amenities_updated_at
  BEFORE UPDATE ON public.iainmobiliaria_amenities
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_grid_tiles_updated_at ON public.iainmobiliaria_grid_tiles;
CREATE TRIGGER update_grid_tiles_updated_at
  BEFORE UPDATE ON public.iainmobiliaria_grid_tiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();


-- ================================================================
-- CONFIRMACIÓN
-- ================================================================
SELECT 'Funciones y triggers creados exitosamente' AS status;

-- Verificar funciones creadas
SELECT 
  n.nspname AS schema,
  p.proname AS function_name,
  pg_get_functiondef(p.oid) AS definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
    'rebuild_grid',
    'get_statistics',
    'clean_old_data',
    'get_nearby_amenities',
    'update_updated_at_column'
  )
ORDER BY p.proname;

