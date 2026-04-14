-- ================================================================
-- SCRIPT SEGURO: Actualizar Triggers y Funciones (Idempotente)
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================
-- Este script puede ejecutarse múltiples veces sin errores
-- ================================================================

-- ==================== FUNCIÓN: update_updated_at ====================
-- Función auxiliar para actualizar automáticamente el campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column IS 'Función genérica para actualizar updated_at automáticamente';


-- ==================== FUNCIÓN: update_updated_at_inegi ====================
CREATE OR REPLACE FUNCTION update_updated_at_inegi()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ==================== TRIGGERS (CON DROP IF EXISTS) ====================

-- Trigger para iainmobiliaria_inegi_data
DROP TRIGGER IF EXISTS trigger_update_inegi_updated_at ON public.iainmobiliaria_inegi_data;

CREATE TRIGGER trigger_update_inegi_updated_at
BEFORE UPDATE ON public.iainmobiliaria_inegi_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_inegi();


-- ==================== FUNCIONES DE NEGOCIO ====================

-- Función: Calcular histórico de precios mensual
CREATE OR REPLACE FUNCTION calculate_monthly_price_history()
RETURNS TABLE(
  city TEXT,
  state TEXT,
  avg_price_m2 NUMERIC,
  median_price_m2 NUMERIC,
  count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    c.city,
    c.state,
    AVG(c.price_m2)::NUMERIC(10,2) as avg_price_m2,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY c.price_m2)::NUMERIC(10,2) as median_price_m2,
    COUNT(*)::BIGINT as count
  FROM public.iainmobiliaria_comparables c
  WHERE c.collection_date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY c.city, c.state
  HAVING COUNT(*) >= 5;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_monthly_price_history IS 'Calcula estadísticas mensuales de precios por ciudad';


-- Función: Obtener tendencia de precios
CREATE OR REPLACE FUNCTION get_price_trend(
  p_city TEXT,
  p_state TEXT,
  p_months INT DEFAULT 12
)
RETURNS TABLE(
  collection_date DATE,
  avg_price_m2 NUMERIC,
  change_pct NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  WITH monthly_prices AS (
    SELECT 
      ph.collection_date,
      ph.price_m2_avg,
      LAG(ph.price_m2_avg) OVER (ORDER BY ph.collection_date) as prev_price
    FROM public.iainmobiliaria_price_history ph
    WHERE ph.city = p_city 
      AND ph.state = p_state
      AND ph.collection_date >= CURRENT_DATE - (p_months || ' months')::INTERVAL
    ORDER BY ph.collection_date
  )
  SELECT 
    mp.collection_date,
    mp.price_m2_avg,
    CASE 
      WHEN mp.prev_price IS NOT NULL AND mp.prev_price > 0 
      THEN ((mp.price_m2_avg - mp.prev_price) / mp.prev_price * 100)::NUMERIC(5,2)
      ELSE 0::NUMERIC(5,2)
    END as change_pct
  FROM monthly_prices mp;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_price_trend IS 'Obtiene tendencia de precios con cambio porcentual mensual';


-- Función: Insertar snapshot mensual
CREATE OR REPLACE FUNCTION insert_monthly_snapshot()
RETURNS INT AS $$
DECLARE
  inserted_count INT := 0;
BEGIN
  INSERT INTO public.iainmobiliaria_price_history (
    city,
    state,
    property_type,
    price_m2_avg,
    price_m2_median,
    price_m2_min,
    price_m2_max,
    sample_count,
    collection_date,
    data_source
  )
  SELECT 
    city,
    state,
    'terreno' as property_type,
    AVG(price_m2)::NUMERIC(10,2) as price_m2_avg,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_m2)::NUMERIC(10,2) as price_m2_median,
    MIN(price_m2)::NUMERIC(10,2) as price_m2_min,
    MAX(price_m2)::NUMERIC(10,2) as price_m2_max,
    COUNT(*)::INT as sample_count,
    CURRENT_DATE,
    'automated_snapshot'
  FROM public.iainmobiliaria_comparables
  WHERE collection_date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY city, state
  HAVING COUNT(*) >= 5
  ON CONFLICT (city, state, property_type, collection_date) 
  DO UPDATE SET
    price_m2_avg = EXCLUDED.price_m2_avg,
    price_m2_median = EXCLUDED.price_m2_median,
    price_m2_min = EXCLUDED.price_m2_min,
    price_m2_max = EXCLUDED.price_m2_max,
    sample_count = EXCLUDED.sample_count;
  
  GET DIAGNOSTICS inserted_count = ROW_COUNT;
  RETURN inserted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION insert_monthly_snapshot IS 'Crea snapshot mensual de precios promedio por ciudad';


-- ==================== AGREGAR COLUMNAS FALTANTES ====================

-- Agregar columna de fecha de recolección si no existe
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'iainmobiliaria_comparables' 
    AND column_name = 'collection_date'
  ) THEN
    ALTER TABLE public.iainmobiliaria_comparables 
    ADD COLUMN collection_date DATE DEFAULT CURRENT_DATE;
    
    RAISE NOTICE 'Columna collection_date agregada a iainmobiliaria_comparables';
  ELSE
    RAISE NOTICE 'Columna collection_date ya existe en iainmobiliaria_comparables';
  END IF;
END $$;

-- Agregar columna de fuente de datos
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'iainmobiliaria_comparables' 
    AND column_name = 'source'
  ) THEN
    ALTER TABLE public.iainmobiliaria_comparables 
    ADD COLUMN source TEXT DEFAULT 'manual';
    
    RAISE NOTICE 'Columna source agregada a iainmobiliaria_comparables';
  ELSE
    RAISE NOTICE 'Columna source ya existe en iainmobiliaria_comparables';
  END IF;
END $$;

-- Agregar columna de URL fuente
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'iainmobiliaria_comparables' 
    AND column_name = 'source_url'
  ) THEN
    ALTER TABLE public.iainmobiliaria_comparables 
    ADD COLUMN source_url TEXT;
    
    RAISE NOTICE 'Columna source_url agregada a iainmobiliaria_comparables';
  ELSE
    RAISE NOTICE 'Columna source_url ya existe en iainmobiliaria_comparables';
  END IF;
END $$;


-- ==================== AGREGAR COMENTARIOS ====================
COMMENT ON COLUMN public.iainmobiliaria_comparables.collection_date IS 'Fecha de recolección para análisis histórico';
COMMENT ON COLUMN public.iainmobiliaria_comparables.source IS 'Fuente: manual, inmuebles24, lamudi, etc.';
COMMENT ON COLUMN public.iainmobiliaria_comparables.source_url IS 'URL original de la propiedad';


-- ==================== CREAR ÍNDICES ====================
CREATE INDEX IF NOT EXISTS idx_comparables_collection_date 
  ON public.iainmobiliaria_comparables(collection_date DESC);

CREATE INDEX IF NOT EXISTS idx_comparables_source 
  ON public.iainmobiliaria_comparables(source);


-- ==================== CONFIRMACIÓN ====================
SELECT 'Triggers y funciones actualizados exitosamente' AS status;

-- Verificar tablas y su tamaño
SELECT 
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = tablename) AS num_columns
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE 'iainmobiliaria_%'
ORDER BY tablename;

