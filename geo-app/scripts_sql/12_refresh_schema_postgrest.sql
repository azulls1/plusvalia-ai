-- ===================================================================
-- SCRIPT 12: Refresh del esquema de PostgREST
-- ===================================================================
-- Este script fuerza la recarga del esquema en PostgREST
-- para que reconozca las tablas recién creadas

-- 1. Verificar que la tabla existe
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename = 'iainmobiliaria_inegi_data';

-- 2. Verificar columnas de la tabla
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'iainmobiliaria_inegi_data'
ORDER BY ordinal_position;

-- 3. Verificar permisos en la tabla
SELECT 
    grantee,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
  AND table_name = 'iainmobiliaria_inegi_data';

-- 4. Otorgar permisos explícitos (si no existen)
GRANT ALL ON public.iainmobiliaria_inegi_data TO postgres;
GRANT ALL ON public.iainmobiliaria_inegi_data TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.iainmobiliaria_inegi_data TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.iainmobiliaria_inegi_data TO authenticated;

-- 5. Otorgar permisos en la secuencia
GRANT USAGE, SELECT ON SEQUENCE public.iainmobiliaria_inegi_data_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE public.iainmobiliaria_inegi_data_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.iainmobiliaria_inegi_data_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE public.iainmobiliaria_inegi_data_id_seq TO authenticated;

-- 6. Forzar notificación a PostgREST (esto recarga el schema cache)
NOTIFY pgrst, 'reload schema';

-- 7. Verificación final
SELECT '✅ Schema actualizado. Permisos otorgados en iainmobiliaria_inegi_data' AS resultado;

