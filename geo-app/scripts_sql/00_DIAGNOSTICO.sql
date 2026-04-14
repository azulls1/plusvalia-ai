-- ================================================================
-- DIAGNÓSTICO COMPLETO - Estado actual de la base de datos
-- ================================================================
-- Ejecuta este script para ver qué existe actualmente
-- NO modifica nada, solo consulta

-- ================================================================
-- 1. TABLAS EXISTENTES EN EL SCHEMA PUBLIC
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '1. TABLAS EXISTENTES' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

SELECT 
  schemaname,
  tablename,
  CASE 
    WHEN tablename LIKE 'iainmobiliaria_%' THEN '⚠️ PROYECTO INMOBILIARIA'
    ELSE '✓ Otra tabla'
  END AS tipo
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;


-- ================================================================
-- 2. VERIFICAR TABLAS DEL PROYECTO INMOBILIARIA
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '2. TABLAS DEL PROYECTO INMOBILIARIA' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

SELECT 
  tablename,
  CASE 
    WHEN tablename = 'iainmobiliaria_comparables' THEN '⚠️ YA EXISTE'
    WHEN tablename = 'iainmobiliaria_amenities' THEN '⚠️ YA EXISTE'
    WHEN tablename = 'iainmobiliaria_grid_tiles' THEN '⚠️ YA EXISTE'
    ELSE 'OK'
  END AS estado
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'iainmobiliaria_comparables',
    'iainmobiliaria_amenities',
    'iainmobiliaria_grid_tiles'
  );

-- Resultado esperado
SELECT 
  CASE 
    WHEN COUNT(*) = 0 THEN '✅ No hay tablas del proyecto - Podemos crear desde cero'
    WHEN COUNT(*) = 3 THEN '⚠️ Las 3 tablas ya existen - Necesitas limpiar primero'
    ELSE '⚠️ Algunas tablas existen - Estado inconsistente'
  END AS diagnostico
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'iainmobiliaria_comparables',
    'iainmobiliaria_amenities',
    'iainmobiliaria_grid_tiles'
  );


-- ================================================================
-- 3. FUNCIONES EXISTENTES DEL PROYECTO
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '3. FUNCIONES DEL PROYECTO INMOBILIARIA' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

SELECT 
  proname AS funcion,
  pg_get_function_arguments(oid) AS parametros,
  CASE 
    WHEN proname IN (
      'rebuild_grid',
      'get_statistics',
      'clean_old_data',
      'get_nearby_amenities'
    ) THEN '⚠️ PROYECTO INMOBILIARIA'
    WHEN proname = 'update_updated_at_column' THEN '⚠️ COMPARTIDA'
    ELSE '✓ Otra función'
  END AS tipo
FROM pg_proc
WHERE pronamespace = 'public'::regnamespace
  AND proname IN (
    'rebuild_grid',
    'get_statistics',
    'clean_old_data',
    'get_nearby_amenities',
    'update_updated_at_column'
  )
ORDER BY proname;


-- ================================================================
-- 4. VERIFICAR FUNCIÓN update_updated_at_column Y DEPENDENCIAS
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '4. FUNCIÓN update_updated_at_column Y SUS DEPENDENCIAS' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

-- Verificar si existe
SELECT 
  CASE 
    WHEN COUNT(*) > 0 THEN '⚠️ La función update_updated_at_column EXISTE'
    ELSE '✅ La función update_updated_at_column NO existe'
  END AS estado
FROM pg_proc
WHERE proname = 'update_updated_at_column'
  AND pronamespace = 'public'::regnamespace;

-- Verificar triggers que la usan
SELECT 
  tgname AS trigger_name,
  (SELECT relname FROM pg_class WHERE oid = tgrelid) AS tabla,
  CASE 
    WHEN (SELECT relname FROM pg_class WHERE oid = tgrelid) LIKE 'iainmobiliaria_%' 
      THEN '⚠️ PROYECTO INMOBILIARIA'
    ELSE '✓ Otra tabla'
  END AS tipo
FROM pg_trigger
WHERE tgname LIKE '%updated_at%'
  AND NOT tgisinternal
ORDER BY tgname;


-- ================================================================
-- 5. POLÍTICAS RLS DEL PROYECTO
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '5. POLÍTICAS RLS DEL PROYECTO INMOBILIARIA' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

SELECT
  tablename,
  COUNT(*) AS cantidad_politicas
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
    'iainmobiliaria_comparables',
    'iainmobiliaria_amenities',
    'iainmobiliaria_grid_tiles'
  )
GROUP BY tablename
ORDER BY tablename;

-- Resultado esperado
SELECT 
  CASE 
    WHEN COUNT(*) = 0 THEN '✅ No hay políticas - Listo para crear'
    WHEN COUNT(*) >= 12 THEN '⚠️ Políticas ya existen - Necesitas limpiar'
    ELSE '⚠️ Estado inconsistente'
  END AS diagnostico
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
    'iainmobiliaria_comparables',
    'iainmobiliaria_amenities',
    'iainmobiliaria_grid_tiles'
  );


-- ================================================================
-- 6. ÍNDICES DEL PROYECTO
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '6. ÍNDICES DEL PROYECTO INMOBILIARIA' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

SELECT
  tablename,
  COUNT(*) AS cantidad_indices
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
    'iainmobiliaria_comparables',
    'iainmobiliaria_amenities',
    'iainmobiliaria_grid_tiles'
  )
GROUP BY tablename
ORDER BY tablename;


-- ================================================================
-- 7. CONTEO DE DATOS EN TABLAS (si existen)
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '7. DATOS EN TABLAS DEL PROYECTO' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

-- Solo se ejecuta si las tablas existen
DO $$
DECLARE
  comparables_count INT := 0;
  amenities_count INT := 0;
  tiles_count INT := 0;
BEGIN
  -- Verificar iainmobiliaria_comparables
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'iainmobiliaria_comparables' AND schemaname = 'public') THEN
    SELECT COUNT(*) INTO comparables_count FROM public.iainmobiliaria_comparables;
    RAISE NOTICE 'iainmobiliaria_comparables: % registros', comparables_count;
  ELSE
    RAISE NOTICE 'iainmobiliaria_comparables: Tabla NO existe';
  END IF;

  -- Verificar iainmobiliaria_amenities
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'iainmobiliaria_amenities' AND schemaname = 'public') THEN
    SELECT COUNT(*) INTO amenities_count FROM public.iainmobiliaria_amenities;
    RAISE NOTICE 'iainmobiliaria_amenities: % registros', amenities_count;
  ELSE
    RAISE NOTICE 'iainmobiliaria_amenities: Tabla NO existe';
  END IF;

  -- Verificar iainmobiliaria_grid_tiles
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'iainmobiliaria_grid_tiles' AND schemaname = 'public') THEN
    SELECT COUNT(*) INTO tiles_count FROM public.iainmobiliaria_grid_tiles;
    RAISE NOTICE 'iainmobiliaria_grid_tiles: % registros', tiles_count;
  ELSE
    RAISE NOTICE 'iainmobiliaria_grid_tiles: Tabla NO existe';
  END IF;
END $$;


-- ================================================================
-- 8. VERIFICAR CONEXIÓN Y PERMISOS
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '8. INFORMACIÓN DE CONEXIÓN' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

SELECT 
  current_user AS usuario_actual,
  current_database() AS base_datos,
  current_schema() AS schema_actual,
  version() AS version_postgresql;


-- ================================================================
-- 9. RESUMEN Y RECOMENDACIONES
-- ================================================================
SELECT '═══════════════════════════════════════════════════' AS separador;
SELECT '9. RESUMEN Y RECOMENDACIONES' AS seccion;
SELECT '═══════════════════════════════════════════════════' AS separador;

DO $$
DECLARE
  tablas_count INT;
  funciones_count INT;
  politicas_count INT;
BEGIN
  -- Contar componentes del proyecto
  SELECT COUNT(*) INTO tablas_count
  FROM pg_tables
  WHERE schemaname = 'public'
    AND tablename IN ('iainmobiliaria_comparables', 'iainmobiliaria_amenities', 'iainmobiliaria_grid_tiles');

  SELECT COUNT(*) INTO funciones_count
  FROM pg_proc
  WHERE pronamespace = 'public'::regnamespace
    AND proname IN ('rebuild_grid', 'get_statistics', 'clean_old_data', 'get_nearby_amenities');

  SELECT COUNT(*) INTO politicas_count
  FROM pg_policies
  WHERE schemaname = 'public'
    AND tablename IN ('iainmobiliaria_comparables', 'iainmobiliaria_amenities', 'iainmobiliaria_grid_tiles');

  -- Diagnóstico
  RAISE NOTICE '';
  RAISE NOTICE '═══════════════════════════════════════════════════';
  RAISE NOTICE '           DIAGNÓSTICO FINAL';
  RAISE NOTICE '═══════════════════════════════════════════════════';
  RAISE NOTICE '';
  RAISE NOTICE 'Tablas del proyecto: %', tablas_count;
  RAISE NOTICE 'Funciones del proyecto: %', funciones_count;
  RAISE NOTICE 'Políticas RLS: %', politicas_count;
  RAISE NOTICE '';
  RAISE NOTICE '═══════════════════════════════════════════════════';
  
  -- Recomendación
  IF tablas_count = 0 AND funciones_count = 0 AND politicas_count = 0 THEN
    RAISE NOTICE '✅ RECOMENDACIÓN: Base de datos limpia';
    RAISE NOTICE '✅ Puedes ejecutar los scripts desde el inicio:';
    RAISE NOTICE '   1. Script 1: 01_crear_tablas.sql';
    RAISE NOTICE '   2. Script 2: 02_indices.sql';
    RAISE NOTICE '   3. Script 3: 03_rls_policies.sql';
    RAISE NOTICE '   4. Script 4: 04_funciones_utiles.sql';
    RAISE NOTICE '   5. Script 5: 00_TEST_RAPIDO.sql';
  ELSIF tablas_count > 0 OR funciones_count > 0 OR politicas_count > 0 THEN
    RAISE NOTICE '⚠️  RECOMENDACIÓN: Proyecto parcialmente instalado';
    RAISE NOTICE '⚠️  Necesitas ejecutar el script de limpieza primero';
    RAISE NOTICE '   Ejecuta: Script de limpieza (ver instrucciones)';
    RAISE NOTICE '   Luego continúa con los scripts normales';
  END IF;
  
  RAISE NOTICE '═══════════════════════════════════════════════════';
END $$;


-- ================================================================
-- FIN DEL DIAGNÓSTICO
-- ================================================================
SELECT '✅ DIAGNÓSTICO COMPLETO FINALIZADO' AS resultado;
SELECT 'Revisa los resultados arriba para ver el estado actual' AS mensaje;

