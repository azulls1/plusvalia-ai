-- ===================================================================
-- SCRIPT 15: Refresh del esquema de PostgREST para ai_chat_predictions
-- ===================================================================
-- Este script fuerza la recarga del esquema en PostgREST
-- para que reconozca la tabla ai_chat_predictions correctamente
-- ===================================================================

-- 1. Verificar que la tabla existe
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename = 'ai_chat_predictions'
  AND schemaname = 'public';

-- 2. Verificar columnas de la tabla
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'ai_chat_predictions'
ORDER BY ordinal_position
LIMIT 20;

-- 3. Verificar permisos en la tabla
SELECT 
    grantee,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
  AND table_name = 'ai_chat_predictions';

-- 4. Otorgar permisos explícitos (si no existen)
GRANT ALL ON public.ai_chat_predictions TO postgres;
GRANT ALL ON public.ai_chat_predictions TO service_role;
GRANT SELECT ON public.ai_chat_predictions TO anon;
GRANT SELECT ON public.ai_chat_predictions TO authenticated;

-- 5. Otorgar permisos en la secuencia
GRANT USAGE, SELECT ON SEQUENCE public.ai_chat_predictions_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE public.ai_chat_predictions_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.ai_chat_predictions_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE public.ai_chat_predictions_id_seq TO authenticated;

-- 6. Verificar que RLS esté configurado correctamente
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'ai_chat_predictions' 
  AND schemaname = 'public';

-- 7. Verificar políticas RLS
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename = 'ai_chat_predictions'
  AND schemaname = 'public';

-- 8. Forzar notificación a PostgREST (esto recarga el schema cache)
NOTIFY pgrst, 'reload schema';

-- 9. Verificación final
SELECT '✅ Schema actualizado. La tabla ai_chat_predictions debería estar disponible ahora en PostgREST' AS resultado;

-- ===================================================================
-- NOTAS IMPORTANTES:
-- ===================================================================
-- Después de ejecutar este script:
-- 1. Espera 10-15 segundos
-- 2. Recarga n8n (F5)
-- 3. Abre el nodo de Supabase
-- 4. En "Table Name or ID", busca "ai_chat_predictions" (sin rpc/)
-- 5. Debería aparecer como una tabla normal
-- ===================================================================

