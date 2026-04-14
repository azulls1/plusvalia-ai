-- ================================================================
-- SCRIPT: Desactivar RLS en Tablas de ML (para carga de datos)
-- ================================================================
-- Este script desactiva temporalmente Row Level Security (RLS)
-- en las tablas de ML para permitir inserciones desde Python
-- ================================================================

-- Desactivar RLS en todas las tablas de ML
ALTER TABLE public.iainmobiliaria_price_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_inegi_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_predictions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_amenities DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_grid_tiles DISABLE ROW LEVEL SECURITY;

-- Verificar estado de RLS
SELECT 
    tablename,
    CASE WHEN rowsecurity THEN 'RLS ACTIVADO ⚠️' ELSE 'RLS DESACTIVADO ✓' END as estado_rls
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename LIKE 'iainmobiliaria_%'
ORDER BY tablename;

SELECT '✅ RLS desactivado en todas las tablas de ML' AS resultado;

