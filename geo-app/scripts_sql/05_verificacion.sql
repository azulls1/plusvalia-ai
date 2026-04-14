-- ================================================================
-- SCRIPT 5: VERIFICACIÓN COMPLETA
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================

-- ================================================================
-- 1. VERIFICAR TABLAS CREADAS
-- ================================================================
SELECT 
  '1. VERIFICACIÓN DE TABLAS' AS seccion,
  '' AS detalle
UNION ALL
SELECT 
  'Tabla',
  tablename
FROM pg_tables
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
ORDER BY seccion, detalle;


-- ================================================================
-- 2. VERIFICAR COLUMNAS DE CADA TABLA
-- ================================================================
SELECT 
  '2. COLUMNAS - iainmobiliaria_comparables' AS seccion,
  column_name || ' (' || data_type || ')' AS detalle
FROM information_schema.columns
WHERE table_name = 'iainmobiliaria_comparables'
  AND table_schema = 'public'
ORDER BY ordinal_position;

SELECT 
  '2. COLUMNAS - iainmobiliaria_amenities' AS seccion,
  column_name || ' (' || data_type || ')' AS detalle
FROM information_schema.columns
WHERE table_name = 'iainmobiliaria_amenities'
  AND table_schema = 'public'
ORDER BY ordinal_position;

SELECT 
  '2. COLUMNAS - iainmobiliaria_grid_tiles' AS seccion,
  column_name || ' (' || data_type || ')' AS detalle
FROM information_schema.columns
WHERE table_name = 'iainmobiliaria_grid_tiles'
  AND table_schema = 'public'
ORDER BY ordinal_position;


-- ================================================================
-- 3. VERIFICAR ÍNDICES
-- ================================================================
SELECT
  '3. ÍNDICES' AS seccion,
  tablename || ' -> ' || indexname AS detalle
FROM pg_indexes
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public'
ORDER BY tablename, indexname;


-- ================================================================
-- 4. VERIFICAR POLÍTICAS RLS
-- ================================================================
SELECT
  '4. POLÍTICAS RLS' AS seccion,
  tablename || ' [' || cmd || '] -> ' || policyname AS detalle
FROM pg_policies
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public'
ORDER BY tablename, cmd, policyname;


-- ================================================================
-- 5. VERIFICAR RLS HABILITADO
-- ================================================================
SELECT
  '5. RLS HABILITADO' AS seccion,
  tablename || ' -> ' || 
  CASE 
    WHEN rowsecurity THEN 'ENABLED ✓'
    ELSE 'DISABLED ✗'
  END AS detalle
FROM pg_tables
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public';


-- ================================================================
-- 6. VERIFICAR FUNCIONES
-- ================================================================
SELECT 
  '6. FUNCIONES' AS seccion,
  proname || '(' || pg_get_function_arguments(oid) || ')' AS detalle
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


-- ================================================================
-- 7. VERIFICAR TRIGGERS
-- ================================================================
SELECT
  '7. TRIGGERS' AS seccion,
  tgname || ' ON ' || 
  (SELECT relname FROM pg_class WHERE oid = tgrelid) AS detalle
FROM pg_trigger
WHERE tgname IN (
  'update_comparables_updated_at',
  'update_amenities_updated_at',
  'update_grid_tiles_updated_at'
)
ORDER BY tgname;


-- ================================================================
-- 8. VERIFICAR CONSTRAINTS
-- ================================================================
SELECT
  '8. CONSTRAINTS' AS seccion,
  conname || ' ON ' || 
  (SELECT relname FROM pg_class WHERE oid = conrelid) AS detalle
FROM pg_constraint
WHERE conrelid IN (
  'iainmobiliaria_comparables'::regclass,
  'iainmobiliaria_amenities'::regclass,
  'iainmobiliaria_grid_tiles'::regclass
)
ORDER BY conname;


-- ================================================================
-- 9. VERIFICAR TAMAÑO DE TABLAS
-- ================================================================
SELECT
  '9. TAMAÑO DE TABLAS' AS seccion,
  tablename || ' -> ' || pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS detalle
FROM pg_tables
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public'
ORDER BY tablename;


-- ================================================================
-- 10. CONTEO DE REGISTROS
-- ================================================================
SELECT
  '10. CONTEO DE REGISTROS' AS seccion,
  'iainmobiliaria_comparables -> ' || COUNT(*)::TEXT AS detalle
FROM public.iainmobiliaria_comparables
UNION ALL
SELECT
  '10. CONTEO DE REGISTROS',
  'iainmobiliaria_amenities -> ' || COUNT(*)::TEXT
FROM public.iainmobiliaria_amenities
UNION ALL
SELECT
  '10. CONTEO DE REGISTROS',
  'iainmobiliaria_grid_tiles -> ' || COUNT(*)::TEXT
FROM public.iainmobiliaria_grid_tiles;


-- ================================================================
-- 11. PERMISOS DE ROLES
-- ================================================================
SELECT
  '11. PERMISOS' AS seccion,
  grantee || ' -> ' || privilege_type || ' ON ' || table_name AS detalle
FROM information_schema.role_table_grants
WHERE table_name IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND table_schema = 'public'
ORDER BY table_name, grantee, privilege_type;


-- ================================================================
-- 12. RESUMEN FINAL
-- ================================================================
SELECT
  '12. RESUMEN FINAL' AS seccion,
  'Total de tablas: ' || COUNT(DISTINCT tablename)::TEXT AS detalle
FROM pg_tables
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
UNION ALL
SELECT
  '12. RESUMEN FINAL',
  'Total de índices: ' || COUNT(*)::TEXT
FROM pg_indexes
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
UNION ALL
SELECT
  '12. RESUMEN FINAL',
  'Total de políticas RLS: ' || COUNT(*)::TEXT
FROM pg_policies
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
UNION ALL
SELECT
  '12. RESUMEN FINAL',
  'Total de funciones: ' || COUNT(*)::TEXT
FROM pg_proc
WHERE proname IN (
  'rebuild_grid',
  'get_statistics',
  'clean_old_data',
  'get_nearby_amenities',
  'update_updated_at_column'
)
UNION ALL
SELECT
  '12. RESUMEN FINAL',
  'Total de triggers: ' || COUNT(*)::TEXT
FROM pg_trigger
WHERE tgname IN (
  'update_comparables_updated_at',
  'update_amenities_updated_at',
  'update_grid_tiles_updated_at'
);


-- ================================================================
-- CONFIRMACIÓN FINAL
-- ================================================================
SELECT 
  '✅ VERIFICACIÓN COMPLETA' AS status,
  'Todas las tablas, índices, políticas y funciones han sido verificadas' AS mensaje;

