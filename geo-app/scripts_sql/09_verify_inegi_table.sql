-- Verificar estructura de la tabla iainmobiliaria_inegi_data

-- 1. Verificar que la tabla existe
SELECT 'Verificando tabla...' AS status;

-- 2. Ver todas las columnas de la tabla
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'iainmobiliaria_inegi_data'
ORDER BY ordinal_position;

-- 3. Verificar permisos (RLS)
SELECT 
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE tablename = 'iainmobiliaria_inegi_data';

-- 4. Ver políticas RLS si existen
SELECT 
    policyname,
    cmd,
    roles,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'iainmobiliaria_inegi_data';

-- 5. Contar registros actuales
SELECT 
    COUNT(*) as total_registros,
    COUNT(DISTINCT state) as estados_distintos,
    COUNT(DISTINCT municipality) as municipios_distintos
FROM iainmobiliaria_inegi_data;

