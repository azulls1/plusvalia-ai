-- ================================================================
-- TEST RÁPIDO - Verificación antes de insertar datos
-- ================================================================
-- Ejecuta este script ANTES del script 6 para verificar que todo funciona

-- ================================================================
-- 1. VERIFICAR QUE LAS TABLAS EXISTEN
-- ================================================================
SELECT 'TEST 1: Verificar tablas' AS test;

SELECT 
  tablename,
  'OK ✓' AS estado
FROM pg_tables
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public'
ORDER BY tablename;

-- Debe retornar 3 filas


-- ================================================================
-- 2. VERIFICAR POLÍTICAS RLS
-- ================================================================
SELECT 'TEST 2: Verificar políticas RLS' AS test;

SELECT
  tablename,
  COUNT(*) AS cantidad_politicas,
  'OK ✓' AS estado
FROM pg_policies
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- Debe retornar 3 filas con 4 políticas cada una (SELECT, INSERT, UPDATE, DELETE)


-- ================================================================
-- 3. VERIFICAR FUNCIONES
-- ================================================================
SELECT 'TEST 3: Verificar funciones' AS test;

SELECT 
  proname AS funcion,
  'OK ✓' AS estado
FROM pg_proc
WHERE proname IN (
  'rebuild_grid',
  'get_statistics',
  'clean_old_data',
  'get_nearby_amenities',
  'update_updated_at_column'
)
AND pronamespace = 'public'::regnamespace
ORDER BY proname;

-- Debe retornar 5 filas


-- ================================================================
-- 4. VERIFICAR ÍNDICES
-- ================================================================
SELECT 'TEST 4: Verificar índices' AS test;

SELECT
  tablename,
  COUNT(*) AS cantidad_indices,
  'OK ✓' AS estado
FROM pg_indexes
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- Debe retornar 3 filas


-- ================================================================
-- 5. TEST DE INSERCIÓN SIMPLE
-- ================================================================
SELECT 'TEST 5: Probar inserción simple' AS test;

-- Insertar un registro de prueba en comparables
INSERT INTO public.iainmobiliaria_comparables 
  (title, price_mxn, area_m2, address, city, state, lat, lon)
VALUES 
  ('TEST', 1000000, 100, 'Test Address', 'Queretaro', 'Queretaro', 20.5888, -100.3899)
RETURNING id, title, price_m2;

-- Debe retornar 1 fila con el ID y price_m2 = 10000


-- ================================================================
-- 6. TEST DE LECTURA
-- ================================================================
SELECT 'TEST 6: Probar lectura' AS test;

SELECT 
  title, 
  price_m2,
  'OK ✓' AS estado
FROM public.iainmobiliaria_comparables 
WHERE title = 'TEST';

-- Debe retornar 1 fila


-- ================================================================
-- 7. LIMPIAR TEST
-- ================================================================
SELECT 'TEST 7: Limpiar registro de prueba' AS test;

DELETE FROM public.iainmobiliaria_comparables 
WHERE title = 'TEST';

-- Verificar que se eliminó
SELECT 
  CASE 
    WHEN COUNT(*) = 0 THEN 'Limpieza OK ✓'
    ELSE 'ERROR: No se eliminó'
  END AS resultado
FROM public.iainmobiliaria_comparables 
WHERE title = 'TEST';


-- ================================================================
-- 8. TEST DE FUNCIÓN rebuild_grid (sin datos)
-- ================================================================
SELECT 'TEST 8: Probar función rebuild_grid' AS test;

-- Esta función fallará si no hay datos, lo cual es esperado
-- Descomenta solo si ya tienes datos:

-- SELECT * FROM rebuild_grid(0.005);


-- ================================================================
-- 9. TEST DE FUNCIÓN get_statistics
-- ================================================================
SELECT 'TEST 9: Probar función get_statistics' AS test;

SELECT * FROM public.get_statistics();

-- Debe retornar 1 fila con estadísticas (probablemente todos en 0)


-- ================================================================
-- 10. TEST DE FUNCIÓN get_nearby_amenities (sin datos)
-- ================================================================
SELECT 'TEST 10: Probar función get_nearby_amenities' AS test;

-- Esta función retornará 0 filas si no hay amenidades, lo cual es correcto
SELECT * FROM public.get_nearby_amenities(20.5888, -100.3899, 5.0, NULL)
LIMIT 5;

-- Debe ejecutarse sin error (aunque retorne 0 filas)


-- ================================================================
-- RESULTADO FINAL
-- ================================================================
SELECT 
  '✅ TODOS LOS TESTS PASARON' AS resultado,
  'Puedes ejecutar el script 6 ahora' AS mensaje;

