-- ================================================================
-- SCRIPT 3: POLÍTICAS RLS (Row Level Security)
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================

-- ================================================================
-- HABILITAR RLS EN TODAS LAS TABLAS
-- ================================================================

ALTER TABLE public.iainmobiliaria_comparables ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_amenities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_grid_tiles ENABLE ROW LEVEL SECURITY;


-- ================================================================
-- POLÍTICAS PARA: iainmobiliaria_comparables
-- ================================================================

-- 1. Política de LECTURA pública (anon puede leer)
CREATE POLICY "Public read access for comparables" 
ON public.iainmobiliaria_comparables
FOR SELECT 
TO anon, authenticated
USING (true);

-- 2. Política de INSERCIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can insert comparables" 
ON public.iainmobiliaria_comparables
FOR INSERT 
TO authenticated, service_role
WITH CHECK (true);

-- 3. Política de ACTUALIZACIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can update comparables" 
ON public.iainmobiliaria_comparables
FOR UPDATE 
TO authenticated, service_role
USING (true)
WITH CHECK (true);

-- 4. Política de ELIMINACIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can delete comparables" 
ON public.iainmobiliaria_comparables
FOR DELETE 
TO authenticated, service_role
USING (true);


-- ================================================================
-- POLÍTICAS PARA: iainmobiliaria_amenities
-- ================================================================

-- 1. Política de LECTURA pública (anon puede leer)
CREATE POLICY "Public read access for amenities" 
ON public.iainmobiliaria_amenities
FOR SELECT 
TO anon, authenticated
USING (true);

-- 2. Política de INSERCIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can insert amenities" 
ON public.iainmobiliaria_amenities
FOR INSERT 
TO authenticated, service_role
WITH CHECK (true);

-- 3. Política de ACTUALIZACIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can update amenities" 
ON public.iainmobiliaria_amenities
FOR UPDATE 
TO authenticated, service_role
USING (true)
WITH CHECK (true);

-- 4. Política de ELIMINACIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can delete amenities" 
ON public.iainmobiliaria_amenities
FOR DELETE 
TO authenticated, service_role
USING (true);


-- ================================================================
-- POLÍTICAS PARA: iainmobiliaria_grid_tiles
-- ================================================================

-- 1. Política de LECTURA pública (anon puede leer)
CREATE POLICY "Public read access for grid_tiles" 
ON public.iainmobiliaria_grid_tiles
FOR SELECT 
TO anon, authenticated
USING (true);

-- 2. Política de INSERCIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can insert grid_tiles" 
ON public.iainmobiliaria_grid_tiles
FOR INSERT 
TO authenticated, service_role
WITH CHECK (true);

-- 3. Política de ACTUALIZACIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can update grid_tiles" 
ON public.iainmobiliaria_grid_tiles
FOR UPDATE 
TO authenticated, service_role
USING (true)
WITH CHECK (true);

-- 4. Política de ELIMINACIÓN (solo usuarios autenticados y service_role)
CREATE POLICY "Authenticated users can delete grid_tiles" 
ON public.iainmobiliaria_grid_tiles
FOR DELETE 
TO authenticated, service_role
USING (true);


-- ================================================================
-- ALTERNATIVA: POLÍTICAS MÁS PERMISIVAS (SOLO PARA DESARROLLO)
-- ================================================================
-- Descomentar estas líneas SOLO si necesitas desarrollo sin autenticación
-- y comentar las políticas anteriores

-- DROP POLICY IF EXISTS "Public read access for comparables" ON public.iainmobiliaria_comparables;
-- CREATE POLICY "Allow all operations for comparables" 
-- ON public.iainmobiliaria_comparables
-- FOR ALL 
-- TO public
-- USING (true)
-- WITH CHECK (true);

-- DROP POLICY IF EXISTS "Public read access for amenities" ON public.iainmobiliaria_amenities;
-- CREATE POLICY "Allow all operations for amenities" 
-- ON public.iainmobiliaria_amenities
-- FOR ALL 
-- TO public
-- USING (true)
-- WITH CHECK (true);

-- DROP POLICY IF EXISTS "Public read access for grid_tiles" ON public.iainmobiliaria_grid_tiles;
-- CREATE POLICY "Allow all operations for grid_tiles" 
-- ON public.iainmobiliaria_grid_tiles
-- FOR ALL 
-- TO public
-- USING (true)
-- WITH CHECK (true);


-- ================================================================
-- CONFIRMACIÓN
-- ================================================================
SELECT 'Políticas RLS creadas exitosamente' AS status;

-- Verificar políticas creadas
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename IN (
  'iainmobiliaria_comparables',
  'iainmobiliaria_amenities',
  'iainmobiliaria_grid_tiles'
)
AND schemaname = 'public'
ORDER BY tablename, cmd, policyname;

