-- ================================================================
-- MIGRACIÓN 22: Tablas para features mejorados (Fases 1-4)
-- Fecha: 2026-03-31
-- Descripción: Agregados H3, features turísticos, espaciales mejorados, NDVI
-- ================================================================

-- ==================== 1. AGREGADOS HEXAGONALES H3 ====================
-- Métricas de precio agregadas por hexágono H3
-- Permite análisis espacial suave sin depender de límites administrativos
CREATE TABLE IF NOT EXISTS iainmobiliaria_h3_aggregates (
    id BIGSERIAL PRIMARY KEY,
    h3_index VARCHAR(20) NOT NULL,       -- Índice H3 del hexágono
    resolution INTEGER NOT NULL,          -- Resolución H3 (7=~5km, 9=~175m)
    -- Métricas de precio
    avg_price_m2 FLOAT,
    median_price_m2 FLOAT,
    min_price_m2 FLOAT,
    max_price_m2 FLOAT,
    stddev_price_m2 FLOAT,
    count INTEGER NOT NULL DEFAULT 0,     -- Número de comparables en el hexágono
    -- Tendencias
    price_trend_6m FLOAT,                -- Tendencia últimos 6 meses
    price_trend_1yr FLOAT,               -- Tendencia último año
    -- Métricas de área
    avg_area_m2 FLOAT,
    median_area_m2 FLOAT,
    -- Diversidad de uso
    property_type_diversity FLOAT,       -- Índice Shannon de tipos de propiedad
    -- Metadata
    center_lat FLOAT8,
    center_lon FLOAT8,
    parent_h3 VARCHAR(20),               -- Hexágono padre (resolución - 1)
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(h3_index, resolution)
);

CREATE INDEX IF NOT EXISTS idx_h3_index ON iainmobiliaria_h3_aggregates(h3_index);
CREATE INDEX IF NOT EXISTS idx_h3_resolution ON iainmobiliaria_h3_aggregates(resolution);
CREATE INDEX IF NOT EXISTS idx_h3_center_latlon ON iainmobiliaria_h3_aggregates(center_lat, center_lon);
CREATE INDEX IF NOT EXISTS idx_h3_count ON iainmobiliaria_h3_aggregates(count) WHERE count >= 5;

COMMENT ON TABLE iainmobiliaria_h3_aggregates IS 'Agregados por hexágono H3 — análisis espacial suavizado de precios y métricas';

-- ==================== 2. FEATURES TURÍSTICOS ====================
-- Score turístico por comparable, basado en proximidad a zonas turísticas
CREATE TABLE IF NOT EXISTS iainmobiliaria_tourism_features (
    id BIGSERIAL PRIMARY KEY,
    comparable_id BIGINT NOT NULL,
    -- Score turístico compuesto
    tourism_score FLOAT,                 -- 0-100 score general
    is_tourism_zone BOOLEAN DEFAULT FALSE, -- Dentro de zona turística definida
    -- Hotspot más cercano
    nearest_hotspot VARCHAR(100),        -- Nombre del destino turístico más cercano
    nearest_hotspot_distance_km FLOAT,   -- Distancia al hotspot en km
    -- Detalle por tipo de turismo
    beach_proximity_score FLOAT,         -- 0-100 proximidad a playas
    cultural_proximity_score FLOAT,      -- 0-100 proximidad a sitios culturales
    adventure_proximity_score FLOAT,     -- 0-100 proximidad a sitios de aventura
    -- Indicadores de demanda turística
    hotel_density_5km INTEGER,           -- Hoteles en radio de 5km
    restaurant_density_5km INTEGER,      -- Restaurantes en radio de 5km
    airbnb_density_estimate FLOAT,       -- Estimación de densidad Airbnb
    -- Estacionalidad
    seasonal_factor FLOAT,               -- Factor estacional (>1 = temporada alta)
    peak_season_months VARCHAR(20),      -- Meses de temporada alta, ej: "12,1,2,3"
    -- Metadata
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(comparable_id)
);

CREATE INDEX IF NOT EXISTS idx_tourism_comparable ON iainmobiliaria_tourism_features(comparable_id);
CREATE INDEX IF NOT EXISTS idx_tourism_score ON iainmobiliaria_tourism_features(tourism_score);
CREATE INDEX IF NOT EXISTS idx_tourism_zone ON iainmobiliaria_tourism_features(is_tourism_zone) WHERE is_tourism_zone = TRUE;

COMMENT ON TABLE iainmobiliaria_tourism_features IS 'Features turísticos por comparable — impacto del turismo en valorización';

-- ==================== 3. FEATURES ESPACIALES MEJORADOS ====================
-- Métricas espaciales avanzadas por comparable
CREATE TABLE IF NOT EXISTS iainmobiliaria_enhanced_spatial (
    id BIGSERIAL PRIMARY KEY,
    comparable_id BIGINT NOT NULL,
    -- Ratios de precio espacial
    price_ratio_1km_5km FLOAT,           -- Ratio precio local vs regional
    price_ratio_h3_state FLOAT,          -- Ratio precio hexágono vs estado
    price_std_1km FLOAT,                 -- Desviación estándar precios 1km
    price_std_5km FLOAT,                 -- Desviación estándar precios 5km
    -- Interpolación espacial
    idw_price FLOAT,                     -- Precio interpolado por IDW (Inverse Distance Weighting)
    kriging_price FLOAT,                 -- Precio interpolado por Kriging (si disponible)
    -- Percentiles
    price_percentile_city FLOAT,         -- Percentil de precio en la ciudad
    price_percentile_state FLOAT,        -- Percentil de precio en el estado
    price_percentile_h3 FLOAT,           -- Percentil de precio en hexágono H3
    -- Distancias geográficas
    distance_coast_km FLOAT,             -- Distancia a la costa más cercana
    distance_border_km FLOAT,            -- Distancia a frontera más cercana (US/Guatemala/Belize)
    distance_state_capital_km FLOAT,     -- Distancia a capital del estado
    -- Densidad
    comparables_count_1km INTEGER,       -- Número de comparables en 1km
    comparables_count_5km INTEGER,       -- Número de comparables en 5km
    -- Autocorrelación espacial
    morans_i_local FLOAT,               -- Indicador de Moran local (clusters de precio)
    spatial_lag_price FLOAT,             -- Precio rezagado espacialmente
    -- Metadata
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(comparable_id)
);

CREATE INDEX IF NOT EXISTS idx_enhanced_spatial_comparable ON iainmobiliaria_enhanced_spatial(comparable_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_spatial_coast ON iainmobiliaria_enhanced_spatial(distance_coast_km);

COMMENT ON TABLE iainmobiliaria_enhanced_spatial IS 'Features espaciales mejorados — ratios de precio, interpolación y autocorrelación espacial';

-- ==================== 4. NDVI / VEGETACIÓN ====================
-- Índice de vegetación por hexágono H3, derivado de imágenes satelitales
CREATE TABLE IF NOT EXISTS iainmobiliaria_ndvi_features (
    id BIGSERIAL PRIMARY KEY,
    h3_index VARCHAR(20) NOT NULL,       -- Índice H3 del hexágono
    -- NDVI (Normalized Difference Vegetation Index)
    ndvi_avg FLOAT,                      -- NDVI promedio (-1 a 1, típico 0-0.8)
    ndvi_min FLOAT,
    ndvi_max FLOAT,
    ndvi_std FLOAT,
    -- Categorización
    ndvi_category VARCHAR(20),           -- urban_dense, low_green, moderate, high_green
    green_space_pct FLOAT,               -- % de píxeles con NDVI > 0.3
    -- Score compuesto
    green_space_score FLOAT,             -- 0-100 score de espacios verdes
    -- Cambio temporal
    ndvi_change_1yr FLOAT,               -- Cambio NDVI vs año anterior
    urbanization_trend VARCHAR(20),      -- greening, stable, urbanizing
    -- Fecha de los datos satelitales
    data_date DATE NOT NULL,
    satellite_source VARCHAR(50) DEFAULT 'Sentinel-2',
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(h3_index, data_date)
);

CREATE INDEX IF NOT EXISTS idx_ndvi_h3 ON iainmobiliaria_ndvi_features(h3_index);
CREATE INDEX IF NOT EXISTS idx_ndvi_category ON iainmobiliaria_ndvi_features(ndvi_category);
CREATE INDEX IF NOT EXISTS idx_ndvi_date ON iainmobiliaria_ndvi_features(data_date);
CREATE INDEX IF NOT EXISTS idx_ndvi_score ON iainmobiliaria_ndvi_features(green_space_score);

COMMENT ON TABLE iainmobiliaria_ndvi_features IS 'NDVI por hexágono H3 — índice de vegetación y espacios verdes que impactan calidad de vida';

-- ==================== TRIGGER: updated_at automático ====================
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'iainmobiliaria_h3_aggregates',
        'iainmobiliaria_tourism_features',
        'iainmobiliaria_enhanced_spatial',
        'iainmobiliaria_ndvi_features'
    ])
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            tbl, tbl
        );
    END LOOP;
END $$;

-- ==================== ENABLE RLS EN TODAS LAS TABLAS NUEVAS ====================
ALTER TABLE iainmobiliaria_h3_aggregates ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_tourism_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_enhanced_spatial ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_ndvi_features ENABLE ROW LEVEL SECURITY;

-- Lectura pública, escritura solo service_role
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'iainmobiliaria_h3_aggregates',
        'iainmobiliaria_tourism_features',
        'iainmobiliaria_enhanced_spatial',
        'iainmobiliaria_ndvi_features'
    ])
    LOOP
        EXECUTE format('CREATE POLICY "Public read %s" ON %I FOR SELECT TO anon, authenticated USING (true)', tbl, tbl);
        EXECUTE format('CREATE POLICY "Service write %s" ON %I FOR ALL TO service_role USING (true) WITH CHECK (true)', tbl, tbl);
    END LOOP;
END $$;
