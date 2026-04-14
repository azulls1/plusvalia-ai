-- ================================================================
-- VISTA PARA CHAT DE IA
-- ================================================================
-- Esta vista une todas las tablas necesarias para que el agente
-- de IA pueda responder preguntas con una sola consulta
-- ================================================================

-- Eliminar vista si existe
DROP VIEW IF EXISTS vw_predictions_chat_ai;

-- Crear vista enriquecida
CREATE OR REPLACE VIEW vw_predictions_chat_ai AS
SELECT 
  -- ============ IDENTIFICACIÓN ============
  p.id,
  p.lat,
  p.lon,
  p.city,
  p.state,
  
  -- ============ PREDICCIONES ML ============
  p.predicted_price_m2,
  p.plusvalia_score,
  p.growth_potential,
  p.risk_level,
  p.current_price_m2,
  p.model_confidence,
  p.model_version,
  p.prediction_date,
  
  -- ============ HISTÓRICO DE PRECIOS ============
  ph.price_m2_avg as historic_price_avg,
  ph.price_m2_median as historic_price_median,
  ph.collection_date as last_price_update,
  ph.data_source as historic_data_source,
  
  -- ============ DATOS DE ZONA (GRID) ============
  gt.price_m2_avg as zone_price_avg,
  gt.count_properties as zone_properties_count,
  
  -- ============ MÉTRICAS CALCULADAS ============
  
  -- Clasificación de inversión
  CASE
    WHEN p.plusvalia_score >= 80 AND p.risk_level = 'bajo' THEN 'Excelente'
    WHEN p.plusvalia_score >= 70 AND p.risk_level IN ('bajo', 'medio') THEN 'Muy Buena'
    WHEN p.plusvalia_score >= 60 THEN 'Buena'
    WHEN p.plusvalia_score >= 40 THEN 'Regular'
    ELSE 'Baja'
  END as investment_rating,
  
  -- Precio vs promedio de zona (%)
  CASE 
    WHEN gt.price_m2_avg > 0 THEN 
      ROUND(((p.predicted_price_m2 - gt.price_m2_avg) / gt.price_m2_avg * 100)::numeric, 2)
    ELSE 0 
  END as price_vs_zone_pct,
  
  -- Potencial de ganancia vs histórico (%)
  CASE 
    WHEN ph.price_m2_avg > 0 THEN 
      ROUND(((p.predicted_price_m2 - ph.price_m2_avg) / ph.price_m2_avg * 100)::numeric, 2)
    ELSE 0 
  END as potential_gain_pct,
  
  -- Diferencia absoluta vs zona
  CASE 
    WHEN gt.price_m2_avg > 0 THEN 
      p.predicted_price_m2 - gt.price_m2_avg
    ELSE 0 
  END as price_diff_vs_zone,
  
  -- Recomendación textual
  CASE
    WHEN p.plusvalia_score >= 75 AND p.risk_level = 'bajo' 
      THEN 'Altamente recomendado para inversión'
    WHEN p.plusvalia_score >= 65 AND p.growth_potential = 'alto' 
      THEN 'Buena oportunidad de inversión'
    WHEN p.plusvalia_score >= 50 
      THEN 'Opción viable con análisis adicional'
    ELSE 'No recomendado actualmente'
  END as recommendation,
  
  -- Score de confianza general (0-100)
  ROUND((
    (p.plusvalia_score * 0.4) + 
    (p.model_confidence * 100 * 0.3) + 
    (CASE WHEN gt.count_properties >= 10 THEN 100 
          WHEN gt.count_properties >= 5 THEN 70 
          ELSE 40 END * 0.3)
  )::numeric, 2) as confidence_score,
  
  -- ============ URLs Y METADATOS ============
  
  -- URL para ver en mapa
  'http://localhost:4200/?lat=' || p.lat || '&lon=' || p.lon as map_url,
  
  -- Resumen en una línea
  p.city || ', ' || p.state || ' - Score: ' || p.plusvalia_score || 
  '/100 - $' || TO_CHAR(p.predicted_price_m2, 'FM999,999') || '/m²' as summary

FROM iainmobiliaria_predictions p

-- JOIN con histórico de precios (último por ciudad)
LEFT JOIN LATERAL (
  SELECT 
    price_m2_avg, 
    price_m2_median, 
    collection_date,
    data_source
  FROM iainmobiliaria_price_history
  WHERE city = p.city AND state = p.state
  ORDER BY collection_date DESC
  LIMIT 1
) ph ON true

-- JOIN con grid (tile más cercano)
LEFT JOIN LATERAL (
  SELECT 
    price_m2_avg, 
    count_properties
  FROM iainmobiliaria_grid_tiles
  ORDER BY 
    -- Aproximación simple de distancia (sin PostGIS)
    (ABS(iainmobiliaria_grid_tiles.lat - p.lat) + 
     ABS(iainmobiliaria_grid_tiles.lon - p.lon))
  LIMIT 1
) gt ON true

ORDER BY p.plusvalia_score DESC;

-- ================================================================
-- ÍNDICES PARA MEJORAR RENDIMIENTO
-- ================================================================

-- Índice en predictions para city
CREATE INDEX IF NOT EXISTS idx_predictions_city 
ON iainmobiliaria_predictions(city);

-- Índice en predictions para plusvalia_score
CREATE INDEX IF NOT EXISTS idx_predictions_score 
ON iainmobiliaria_predictions(plusvalia_score DESC);

-- Índice compuesto para filtros comunes
CREATE INDEX IF NOT EXISTS idx_predictions_city_score 
ON iainmobiliaria_predictions(city, plusvalia_score DESC);

-- ================================================================
-- COMENTARIOS EN LA VISTA
-- ================================================================

COMMENT ON VIEW vw_predictions_chat_ai IS 
'Vista optimizada para el chat de IA con todos los datos necesarios para recomendaciones de inversión inmobiliaria';

-- ================================================================
-- VERIFICACIÓN
-- ================================================================

-- Contar registros en la vista
SELECT COUNT(*) as total_records FROM vw_predictions_chat_ai;

-- Ejemplo de consulta para el chat de IA
SELECT 
  city,
  summary,
  investment_rating,
  potential_gain_pct,
  recommendation,
  map_url
FROM vw_predictions_chat_ai
WHERE city = 'Guadalajara'
  AND investment_rating IN ('Excelente', 'Muy Buena')
ORDER BY plusvalia_score DESC
LIMIT 5;

-- ================================================================
-- FIN DEL SCRIPT
-- ================================================================

