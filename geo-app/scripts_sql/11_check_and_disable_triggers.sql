-- ===================================================================
-- SCRIPT 11: Verificar y deshabilitar triggers temporalmente
-- ===================================================================
-- Este script verifica triggers activos y los deshabilita temporalmente
-- para permitir la inserción de datos

-- Verificar triggers en la tabla iainmobiliaria_inegi_data
SELECT 
    tgname AS trigger_name,
    tgtype AS trigger_type,
    tgenabled AS enabled,
    pg_get_triggerdef(oid) AS trigger_definition
FROM pg_trigger
WHERE tgrelid = 'public.iainmobiliaria_inegi_data'::regclass
  AND tgname NOT LIKE 'RI_%'  -- Excluir triggers del sistema
ORDER BY tgname;

-- Deshabilitar triggers temporalmente en iainmobiliaria_inegi_data
ALTER TABLE public.iainmobiliaria_inegi_data DISABLE TRIGGER ALL;

-- Verificar estado después de deshabilitar
SELECT 
    tgname AS trigger_name,
    tgenabled AS enabled_status,
    CASE 
        WHEN tgenabled = 'O' THEN 'ENABLED (original)'
        WHEN tgenabled = 'D' THEN 'DISABLED'
        WHEN tgenabled = 'R' THEN 'REPLICA'
        WHEN tgenabled = 'A' THEN 'ALWAYS'
        ELSE 'UNKNOWN'
    END AS status_description
FROM pg_trigger
WHERE tgrelid = 'public.iainmobiliaria_inegi_data'::regclass
  AND tgname NOT LIKE 'RI_%'
ORDER BY tgname;

SELECT '✅ Triggers deshabilitados en iainmobiliaria_inegi_data' AS resultado;

