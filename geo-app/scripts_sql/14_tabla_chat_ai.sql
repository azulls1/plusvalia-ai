-- ================================================================
-- TABLA FÍSICA PARA CHAT DE IA (reemplaza la vista)
-- ================================================================
-- Esta tabla contiene datos pre-calculados para que el agente
-- de IA de n8n pueda consultarlos directamente
-- ================================================================

-- ================================================================
-- PASO 1: ELIMINAR VISTA Y CREAR TABLA
-- ================================================================

-- Eliminar vista si existe (ya no la necesitamos)
DROP VIEW IF EXISTS vw_predictions_chat_ai;

-- Crear tabla física
DROP TABLE IF EXISTS public.ai_chat_predictions CASCADE;

CREATE TABLE public.ai_chat_predictions (
  -- ============ IDENTIFICACIÓN ============
  id BIGSERIAL PRIMARY KEY,
  prediction_id BIGINT REFERENCES public.iainmobiliaria_predictions(id) ON DELETE CASCADE,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  
  -- ============ PREDICCIONES ML ============
  predicted_price_m2 FLOAT8 NOT NULL,
  plusvalia_score FLOAT8 NOT NULL CHECK (plusvalia_score >= 0 AND plusvalia_score <= 100),
  growth_potential TEXT NOT NULL CHECK (growth_potential IN ('bajo', 'medio', 'alto')),
  risk_level TEXT NOT NULL CHECK (risk_level IN ('bajo', 'medio', 'alto')),
  current_price_m2 FLOAT8,
  model_confidence FLOAT8,
  model_version TEXT,
  prediction_date TIMESTAMP WITH TIME ZONE,
  
  -- ============ HISTÓRICO DE PRECIOS ============
  historic_price_avg FLOAT8,
  historic_price_median FLOAT8,
  last_price_update DATE,
  historic_data_source TEXT,
  
  -- ============ DATOS DE ZONA (GRID) ============
  zone_price_avg FLOAT8,
  zone_properties_count INT,
  
  -- ============ MÉTRICAS CALCULADAS ============
  investment_rating TEXT CHECK (investment_rating IN ('Excelente', 'Muy Buena', 'Buena', 'Regular', 'Baja')),
  price_vs_zone_pct FLOAT8,
  potential_gain_pct FLOAT8,
  price_diff_vs_zone FLOAT8,
  recommendation TEXT,
  confidence_score FLOAT8,
  
  -- ============ METADATOS ============
  summary TEXT,
  map_url TEXT,
  
  -- ============ CONTROL ============
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Índice único para evitar duplicados
  UNIQUE(prediction_id)
);

-- Comentarios
COMMENT ON TABLE public.ai_chat_predictions IS 
'Tabla optimizada para el chat de IA con datos pre-calculados de todas las predicciones';

COMMENT ON COLUMN public.ai_chat_predictions.investment_rating IS 
'Calificación de inversión: Excelente > Muy Buena > Buena > Regular > Baja';

COMMENT ON COLUMN public.ai_chat_predictions.plusvalia_score IS 
'Score de plusvalía (0-100), mayor es mejor';

COMMENT ON COLUMN public.ai_chat_predictions.confidence_score IS 
'Score de confianza general del análisis (0-100)';

-- ================================================================
-- PASO 2: FUNCIÓN PARA ACTUALIZAR LA TABLA
-- ================================================================

CREATE OR REPLACE FUNCTION public.refresh_ai_chat_predictions()
RETURNS TABLE (
  inserted_count INT,
  updated_count INT,
  deleted_count INT,
  execution_time_ms NUMERIC
) 
LANGUAGE plpgsql
AS $$
DECLARE
  start_time TIMESTAMP;
  ins_count INT := 0;
  upd_count INT := 0;
  del_count INT := 0;
BEGIN
  start_time := clock_timestamp();
  
  -- Eliminar predicciones que ya no existen
  DELETE FROM public.ai_chat_predictions
  WHERE prediction_id NOT IN (SELECT id FROM public.iainmobiliaria_predictions);
  GET DIAGNOSTICS del_count = ROW_COUNT;
  
  -- Insertar o actualizar todas las predicciones
  INSERT INTO public.ai_chat_predictions (
    prediction_id, lat, lon, city, state,
    predicted_price_m2, plusvalia_score, growth_potential, risk_level,
    current_price_m2, model_confidence, model_version, prediction_date,
    historic_price_avg, historic_price_median, last_price_update, historic_data_source,
    zone_price_avg, zone_properties_count,
    investment_rating, price_vs_zone_pct, potential_gain_pct, 
    price_diff_vs_zone, recommendation, confidence_score,
    summary, map_url
  )
  SELECT 
    -- Identificación
    p.id as prediction_id,
    p.lat, p.lon, p.city, p.state,
    
    -- Predicciones ML
    p.predicted_price_m2, p.plusvalia_score, p.growth_potential, p.risk_level,
    p.current_price_m2, p.model_confidence, p.model_version, p.prediction_date,
    
    -- Histórico de precios
    ph.price_m2_avg, ph.price_m2_median, ph.collection_date, ph.data_source,
    
    -- Datos de zona
    gt.price_m2_avg, gt.count_properties,
    
    -- Clasificación de inversión
    CASE
      WHEN p.plusvalia_score >= 80 AND p.risk_level = 'bajo' THEN 'Excelente'
      WHEN p.plusvalia_score >= 70 AND p.risk_level IN ('bajo', 'medio') THEN 'Muy Buena'
      WHEN p.plusvalia_score >= 60 THEN 'Buena'
      WHEN p.plusvalia_score >= 40 THEN 'Regular'
      ELSE 'Baja'
    END,
    
    -- Precio vs zona
    CASE 
      WHEN gt.price_m2_avg > 0 THEN 
        ROUND(((p.predicted_price_m2 - gt.price_m2_avg) / gt.price_m2_avg * 100)::NUMERIC, 2)
      ELSE 0 
    END,
    
    -- Potencial de ganancia
    CASE 
      WHEN ph.price_m2_avg > 0 THEN 
        ROUND(((p.predicted_price_m2 - ph.price_m2_avg) / ph.price_m2_avg * 100)::NUMERIC, 2)
      ELSE 0 
    END,
    
    -- Diferencia vs zona
    CASE 
      WHEN gt.price_m2_avg > 0 THEN p.predicted_price_m2 - gt.price_m2_avg
      ELSE 0 
    END,
    
    -- Recomendación
    CASE
      WHEN p.plusvalia_score >= 75 AND p.risk_level = 'bajo' 
        THEN 'Altamente recomendado para inversión'
      WHEN p.plusvalia_score >= 65 AND p.growth_potential = 'alto' 
        THEN 'Buena oportunidad de inversión'
      WHEN p.plusvalia_score >= 50 
        THEN 'Opción viable con análisis adicional'
      ELSE 'No recomendado actualmente'
    END,
    
    -- Score de confianza
    ROUND((
      (p.plusvalia_score * 0.4) + 
      (p.model_confidence * 100 * 0.3) + 
      (CASE WHEN gt.count_properties >= 10 THEN 100 
            WHEN gt.count_properties >= 5 THEN 70 
            ELSE 40 END * 0.3)
    )::NUMERIC, 2),
    
    -- Summary
    p.city || ', ' || p.state || ' - Score: ' || p.plusvalia_score || 
    '/100 - $' || TO_CHAR(p.predicted_price_m2, 'FM999,999') || '/m²',
    
    -- Map URL
    'http://localhost:4200/?lat=' || p.lat || '&lon=' || p.lon
    
  FROM public.iainmobiliaria_predictions p
  
  -- JOIN con histórico
  LEFT JOIN LATERAL (
    SELECT price_m2_avg, price_m2_median, collection_date, data_source
    FROM public.iainmobiliaria_price_history
    WHERE city = p.city AND state = p.state
    ORDER BY collection_date DESC
    LIMIT 1
  ) ph ON true
  
  -- JOIN con grid
  LEFT JOIN LATERAL (
    SELECT price_m2_avg, count_properties
    FROM public.iainmobiliaria_grid_tiles
    ORDER BY (ABS(iainmobiliaria_grid_tiles.lat - p.lat) + ABS(iainmobiliaria_grid_tiles.lon - p.lon))
    LIMIT 1
  ) gt ON true
  
  ON CONFLICT (prediction_id) 
  DO UPDATE SET
    lat = EXCLUDED.lat,
    lon = EXCLUDED.lon,
    city = EXCLUDED.city,
    state = EXCLUDED.state,
    predicted_price_m2 = EXCLUDED.predicted_price_m2,
    plusvalia_score = EXCLUDED.plusvalia_score,
    growth_potential = EXCLUDED.growth_potential,
    risk_level = EXCLUDED.risk_level,
    current_price_m2 = EXCLUDED.current_price_m2,
    model_confidence = EXCLUDED.model_confidence,
    model_version = EXCLUDED.model_version,
    prediction_date = EXCLUDED.prediction_date,
    historic_price_avg = EXCLUDED.historic_price_avg,
    historic_price_median = EXCLUDED.historic_price_median,
    last_price_update = EXCLUDED.last_price_update,
    historic_data_source = EXCLUDED.historic_data_source,
    zone_price_avg = EXCLUDED.zone_price_avg,
    zone_properties_count = EXCLUDED.zone_properties_count,
    investment_rating = EXCLUDED.investment_rating,
    price_vs_zone_pct = EXCLUDED.price_vs_zone_pct,
    potential_gain_pct = EXCLUDED.potential_gain_pct,
    price_diff_vs_zone = EXCLUDED.price_diff_vs_zone,
    recommendation = EXCLUDED.recommendation,
    confidence_score = EXCLUDED.confidence_score,
    summary = EXCLUDED.summary,
    map_url = EXCLUDED.map_url,
    updated_at = NOW();
  
  GET DIAGNOSTICS ins_count = ROW_COUNT;
  
  -- Retornar estadísticas
  RETURN QUERY SELECT 
    ins_count,
    upd_count,
    del_count,
    EXTRACT(EPOCH FROM (clock_timestamp() - start_time)) * 1000;
END;
$$;

COMMENT ON FUNCTION public.refresh_ai_chat_predictions IS 
'Actualiza la tabla ai_chat_predictions con los últimos datos de predicciones';

-- ================================================================
-- PASO 3: ÍNDICES PARA OPTIMIZAR CONSULTAS
-- ================================================================

-- Índice por ciudad (consulta más común)
CREATE INDEX IF NOT EXISTS idx_ai_chat_city 
ON public.ai_chat_predictions(city);

-- Índice por plusvalia_score (para ordenar)
CREATE INDEX IF NOT EXISTS idx_ai_chat_score 
ON public.ai_chat_predictions(plusvalia_score DESC);

-- Índice compuesto (ciudad + score)
CREATE INDEX IF NOT EXISTS idx_ai_chat_city_score 
ON public.ai_chat_predictions(city, plusvalia_score DESC);

-- Índice por investment_rating
CREATE INDEX IF NOT EXISTS idx_ai_chat_rating 
ON public.ai_chat_predictions(investment_rating);

-- Índice por coordenadas (para búsquedas geográficas)
CREATE INDEX IF NOT EXISTS idx_ai_chat_coords 
ON public.ai_chat_predictions(lat, lon);

-- ================================================================
-- PASO 4: POBLAR LA TABLA INICIALMENTE
-- ================================================================

SELECT public.refresh_ai_chat_predictions();

-- ================================================================
-- PASO 5: RLS (Row Level Security) - ACCESO PÚBLICO PARA LECTURA
-- ================================================================

-- Habilitar RLS
ALTER TABLE public.ai_chat_predictions ENABLE ROW LEVEL SECURITY;

-- Política de lectura pública
CREATE POLICY "Public read access for ai_chat" 
ON public.ai_chat_predictions
FOR SELECT 
TO anon, authenticated
USING (true);

-- Política de escritura (solo service_role)
CREATE POLICY "Service role full access for ai_chat" 
ON public.ai_chat_predictions
FOR ALL 
TO service_role
USING (true)
WITH CHECK (true);

-- ================================================================
-- PASO 6: TRIGGER AUTOMÁTICO (OPCIONAL)
-- ================================================================
-- Este trigger actualiza la tabla automáticamente cuando hay cambios
-- en iainmobiliaria_predictions

CREATE OR REPLACE FUNCTION public.trigger_refresh_ai_chat()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Actualizar solo el registro afectado
  PERFORM public.refresh_ai_chat_predictions();
  RETURN NULL;
END;
$$;

-- Trigger después de INSERT/UPDATE/DELETE en predictions
DROP TRIGGER IF EXISTS auto_refresh_ai_chat ON public.iainmobiliaria_predictions;
CREATE TRIGGER auto_refresh_ai_chat
  AFTER INSERT OR UPDATE OR DELETE ON public.iainmobiliaria_predictions
  FOR EACH STATEMENT
  EXECUTE FUNCTION public.trigger_refresh_ai_chat();

-- ================================================================
-- PASO 7: VERIFICACIÓN
-- ================================================================

-- Contar registros
SELECT COUNT(*) as total_records FROM public.ai_chat_predictions;

-- Ver ejemplos de las mejores inversiones
SELECT 
  city, state,
  summary,
  investment_rating,
  potential_gain_pct,
  confidence_score,
  recommendation
FROM public.ai_chat_predictions
WHERE investment_rating IN ('Excelente', 'Muy Buena')
ORDER BY plusvalia_score DESC
LIMIT 10;

-- Estadísticas por ciudad
SELECT 
  city,
  COUNT(*) as predictions_count,
  ROUND(AVG(plusvalia_score)::NUMERIC, 2) as avg_score,
  ROUND(AVG(predicted_price_m2)::NUMERIC, 2) as avg_price_m2,
  COUNT(CASE WHEN investment_rating IN ('Excelente', 'Muy Buena') THEN 1 END) as top_investments
FROM public.ai_chat_predictions
GROUP BY city
ORDER BY avg_score DESC;

-- ================================================================
-- INSTRUCCIONES DE USO
-- ================================================================

-- Para actualizar manualmente la tabla:
-- SELECT public.refresh_ai_chat_predictions();

-- Para consultar desde n8n:
-- SELECT * FROM ai_chat_predictions 
-- WHERE city = 'Guadalajara' 
--   AND investment_rating = 'Excelente'
-- ORDER BY plusvalia_score DESC
-- LIMIT 10;

-- ================================================================
-- FIN DEL SCRIPT
-- ================================================================

