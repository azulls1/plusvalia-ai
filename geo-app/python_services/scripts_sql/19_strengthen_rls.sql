-- Drop overly permissive policies
DROP POLICY IF EXISTS "Authenticated users can insert comparables" ON iainmobiliaria_comparables;
DROP POLICY IF EXISTS "Authenticated users can update comparables" ON iainmobiliaria_comparables;
DROP POLICY IF EXISTS "Authenticated users can delete comparables" ON iainmobiliaria_comparables;

-- Recreate with service_role only for writes
CREATE POLICY "Service role can insert comparables"
ON iainmobiliaria_comparables FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Service role can update comparables"
ON iainmobiliaria_comparables FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role can delete comparables"
ON iainmobiliaria_comparables FOR DELETE TO service_role USING (true);

-- Same for amenities
DROP POLICY IF EXISTS "Authenticated users can insert amenities" ON iainmobiliaria_amenities;
DROP POLICY IF EXISTS "Authenticated users can update amenities" ON iainmobiliaria_amenities;
DROP POLICY IF EXISTS "Authenticated users can delete amenities" ON iainmobiliaria_amenities;

CREATE POLICY "Service role can insert amenities"
ON iainmobiliaria_amenities FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Service role can update amenities"
ON iainmobiliaria_amenities FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role can delete amenities"
ON iainmobiliaria_amenities FOR DELETE TO service_role USING (true);

-- Same for grid_tiles
DROP POLICY IF EXISTS "Authenticated users can insert grid_tiles" ON iainmobiliaria_grid_tiles;
DROP POLICY IF EXISTS "Authenticated users can update grid_tiles" ON iainmobiliaria_grid_tiles;
DROP POLICY IF EXISTS "Authenticated users can delete grid_tiles" ON iainmobiliaria_grid_tiles;

CREATE POLICY "Service role can insert grid_tiles"
ON iainmobiliaria_grid_tiles FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Service role can update grid_tiles"
ON iainmobiliaria_grid_tiles FOR UPDATE TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role can delete grid_tiles"
ON iainmobiliaria_grid_tiles FOR DELETE TO service_role USING (true);
