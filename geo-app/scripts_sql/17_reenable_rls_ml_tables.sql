-- ================================================================
-- SCRIPT 17: Re-enable RLS on ML Tables
-- ================================================================
-- This script reverses 10_disable_rls_ml_tables.sql by re-enabling
-- Row Level Security on all ML and data tables.
--
-- WHY: RLS was disabled for bulk data loading. In production, RLS
-- must be active to prevent unauthorized data access via the
-- Supabase anon key.
--
-- RUN THIS: Before every production deployment.
-- ================================================================

-- ==================== STEP 1: Enable RLS on all tables ====================

ALTER TABLE public.iainmobiliaria_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_inegi_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_amenities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_grid_tiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.iainmobiliaria_comparables ENABLE ROW LEVEL SECURITY;

-- ==================== STEP 2: Read policies for anon users ====================
-- Allow anon (frontend) to SELECT from all tables but not modify them.

-- Predictions: public read-only
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_read_predictions') THEN
        CREATE POLICY anon_read_predictions ON public.iainmobiliaria_predictions
            FOR SELECT
            TO anon
            USING (true);
    END IF;
END $$;

-- Price history: public read-only
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_read_price_history') THEN
        CREATE POLICY anon_read_price_history ON public.iainmobiliaria_price_history
            FOR SELECT
            TO anon
            USING (true);
    END IF;
END $$;

-- INEGI data: public read-only
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_read_inegi_data') THEN
        CREATE POLICY anon_read_inegi_data ON public.iainmobiliaria_inegi_data
            FOR SELECT
            TO anon
            USING (true);
    END IF;
END $$;

-- Amenities: public read-only
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_read_amenities') THEN
        CREATE POLICY anon_read_amenities ON public.iainmobiliaria_amenities
            FOR SELECT
            TO anon
            USING (true);
    END IF;
END $$;

-- Grid tiles: public read-only
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_read_grid_tiles') THEN
        CREATE POLICY anon_read_grid_tiles ON public.iainmobiliaria_grid_tiles
            FOR SELECT
            TO anon
            USING (true);
    END IF;
END $$;

-- Comparables: public read-only
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_read_comparables') THEN
        CREATE POLICY anon_read_comparables ON public.iainmobiliaria_comparables
            FOR SELECT
            TO anon
            USING (true);
    END IF;
END $$;

-- ==================== STEP 3: Write policies for service_role only ====================
-- Only the service_role (python backend) can INSERT, UPDATE, DELETE.

-- Predictions: service_role full access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'service_write_predictions') THEN
        CREATE POLICY service_write_predictions ON public.iainmobiliaria_predictions
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- Price history: service_role full access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'service_write_price_history') THEN
        CREATE POLICY service_write_price_history ON public.iainmobiliaria_price_history
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- INEGI data: service_role full access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'service_write_inegi_data') THEN
        CREATE POLICY service_write_inegi_data ON public.iainmobiliaria_inegi_data
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- Amenities: service_role full access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'service_write_amenities') THEN
        CREATE POLICY service_write_amenities ON public.iainmobiliaria_amenities
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- Grid tiles: service_role full access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'service_write_grid_tiles') THEN
        CREATE POLICY service_write_grid_tiles ON public.iainmobiliaria_grid_tiles
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- Comparables: service_role full access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'service_write_comparables') THEN
        CREATE POLICY service_write_comparables ON public.iainmobiliaria_comparables
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- ==================== STEP 4: Verify RLS status ====================

SELECT
    tablename,
    CASE WHEN rowsecurity THEN 'RLS ENABLED' ELSE 'RLS DISABLED (WARNING!)' END AS rls_status
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename LIKE 'iainmobiliaria_%'
ORDER BY tablename;

-- Verify policies exist
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
    AND tablename LIKE 'iainmobiliaria_%'
ORDER BY tablename, policyname;

SELECT 'RLS re-enabled and policies created on all ML tables' AS resultado;
