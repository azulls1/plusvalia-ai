-- ================================================================
-- SCRIPT 7: TABLAS PARA ML E HISTÓRICO DE PRECIOS
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================

-- ==================== TABLA: HISTÓRICO DE PRECIOS ====================
-- Almacena snapshots mensuales de precios para análisis temporal
CREATE TABLE IF NOT EXISTS public.iainmobiliaria_price_history (
  id BIGSERIAL PRIMARY KEY,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  property_type TEXT DEFAULT 'terreno',
  price_m2_avg NUMERIC(10, 2) NOT NULL CHECK (price_m2_avg > 0),
  price_m2_median NUMERIC(10, 2),
  price_m2_min NUMERIC(10, 2),
  price_m2_max NUMERIC(10, 2),
  sample_count INT NOT NULL CHECK (sample_count > 0),
  collection_date DATE NOT NULL DEFAULT CURRENT_DATE,
  data_source TEXT DEFAULT 'scraping',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(city, state, property_type, collection_date)
);

COMMENT ON TABLE public.iainmobiliaria_price_history IS 'Histórico mensual de precios por ciudad para análisis de tendencias';
COMMENT ON COLUMN public.iainmobiliaria_price_history.collection_date IS 'Fecha de recolección de datos (mensual)';
COMMENT ON COLUMN public.iainmobiliaria_price_history.sample_count IS 'Número de propiedades usadas en el cálculo';

-- Índices para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_price_history_city_date 
  ON public.iainmobiliaria_price_history(city, state, collection_date DESC);

CREATE INDEX IF NOT EXISTS idx_price_history_date 
  ON public.iainmobiliaria_price_history(collection_date DESC);


-- ==================== TABLA: DATOS INEGI ====================
-- Almacena datos demográficos y socioeconómicos de INEGI por AGEB o municipio
CREATE TABLE IF NOT EXISTS public.iainmobiliaria_inegi_data (
  id BIGSERIAL PRIMARY KEY,
  geoid TEXT UNIQUE NOT NULL,
  geo_type TEXT NOT NULL CHECK (geo_type IN ('ageb', 'municipio', 'localidad')),
  name TEXT NOT NULL,
  state TEXT NOT NULL,
  municipality TEXT,
  
  -- Datos demográficos
  population INT,
  population_density NUMERIC(10, 2),
  households INT,
  avg_household_size NUMERIC(4, 2),
  
  -- Datos socioeconómicos
  economic_level TEXT CHECK (economic_level IN ('bajo', 'medio-bajo', 'medio', 'medio-alto', 'alto')),
  employed_population INT,
  unemployment_rate NUMERIC(5, 2),
  
  -- Infraestructura
  water_coverage_pct NUMERIC(5, 2),
  electricity_coverage_pct NUMERIC(5, 2),
  internet_coverage_pct NUMERIC(5, 2),
  
  -- Educación
  avg_schooling_years NUMERIC(4, 2),
  literacy_rate NUMERIC(5, 2),
  
  -- Vivienda
  total_dwellings INT,
  occupied_dwellings INT,
  avg_occupants_per_room NUMERIC(4, 2),
  
  -- Geolocalización (centroide del polígono)
  lat FLOAT8,
  lon FLOAT8,
  geometry JSONB,
  
  data_year INT DEFAULT 2020,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE public.iainmobiliaria_inegi_data IS 'Datos demográficos y socioeconómicos de INEGI';
COMMENT ON COLUMN public.iainmobiliaria_inegi_data.geoid IS 'Identificador único del AGEB o municipio';
COMMENT ON COLUMN public.iainmobiliaria_inegi_data.geometry IS 'Polígono en formato GeoJSON';

-- Índices geoespaciales
CREATE INDEX IF NOT EXISTS idx_inegi_state 
  ON public.iainmobiliaria_inegi_data(state);

CREATE INDEX IF NOT EXISTS idx_inegi_municipality 
  ON public.iainmobiliaria_inegi_data(municipality);

CREATE INDEX IF NOT EXISTS idx_inegi_geoid 
  ON public.iainmobiliaria_inegi_data(geoid);


-- ==================== TABLA: PREDICCIONES ML ====================
-- Almacena predicciones del modelo de ML
CREATE TABLE IF NOT EXISTS public.iainmobiliaria_predictions (
  id BIGSERIAL PRIMARY KEY,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  city TEXT,
  state TEXT,
  
  -- Predicciones
  predicted_price_m2 NUMERIC(10, 2) NOT NULL,
  plusvalia_score NUMERIC(5, 2) CHECK (plusvalia_score >= 0 AND plusvalia_score <= 100),
  growth_potential TEXT CHECK (growth_potential IN ('bajo', 'medio', 'alto', 'muy_alto')),
  risk_level TEXT CHECK (risk_level IN ('bajo', 'medio', 'alto')),
  
  -- Features usados en la predicción
  current_price_m2 NUMERIC(10, 2),
  distance_to_center_km NUMERIC(8, 2),
  amenities_count INT,
  population_density NUMERIC(10, 2),
  economic_level TEXT,
  
  -- Metadatos del modelo
  model_version TEXT NOT NULL,
  model_confidence NUMERIC(5, 2),
  prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE public.iainmobiliaria_predictions IS 'Predicciones de plusvalía generadas por el modelo ML';
COMMENT ON COLUMN public.iainmobiliaria_predictions.plusvalia_score IS 'Score de plusvalía esperada (0-100)';
COMMENT ON COLUMN public.iainmobiliaria_predictions.growth_potential IS 'Categoría de potencial de crecimiento';

-- Índices para consultas geográficas
CREATE INDEX IF NOT EXISTS idx_predictions_location 
  ON public.iainmobiliaria_predictions(lat, lon);

CREATE INDEX IF NOT EXISTS idx_predictions_score 
  ON public.iainmobiliaria_predictions(plusvalia_score DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_city 
  ON public.iainmobiliaria_predictions(city, state);


-- ==================== ACTUALIZAR TABLA COMPARABLES ====================
-- Agregar campos adicionales para ML y scraping

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
  END IF;
END $$;

-- Agregar comentarios
COMMENT ON COLUMN public.iainmobiliaria_comparables.collection_date IS 'Fecha de recolección para análisis histórico';
COMMENT ON COLUMN public.iainmobiliaria_comparables.source IS 'Fuente: manual, inmuebles24, lamudi, etc.';
COMMENT ON COLUMN public.iainmobiliaria_comparables.source_url IS 'URL original de la propiedad';

-- Crear índice para consultas temporales
CREATE INDEX IF NOT EXISTS idx_comparables_collection_date 
  ON public.iainmobiliaria_comparables(collection_date DESC);

CREATE INDEX IF NOT EXISTS idx_comparables_source 
  ON public.iainmobiliaria_comparables(source);


-- ==================== FUNCIONES AUXILIARES ====================

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


-- ==================== TRIGGERS ====================

-- Trigger para actualizar updated_at en inegi_data
CREATE OR REPLACE FUNCTION update_updated_at_inegi()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Eliminar trigger si existe antes de crearlo
DROP TRIGGER IF EXISTS trigger_update_inegi_updated_at ON public.iainmobiliaria_inegi_data;

CREATE TRIGGER trigger_update_inegi_updated_at
BEFORE UPDATE ON public.iainmobiliaria_inegi_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_inegi();


-- ==================== CONFIRMACIÓN ====================
SELECT 'Tablas ML e Histórico creadas exitosamente' AS status;

-- Verificar tablas creadas
SELECT 
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN (
  'iainmobiliaria_price_history',
  'iainmobiliaria_inegi_data',
  'iainmobiliaria_predictions'
)
ORDER BY tablename;

