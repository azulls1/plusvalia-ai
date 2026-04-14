-- ================================================================
-- MIGRATION 20: Feature Enrichment Tables for ML Model
-- Purpose: Transform 10-feature model into 50+ feature model
-- ================================================================

-- ==================== 1. NORMALIZE CITIES ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    lat FLOAT8,
    lon FLOAT8,
    municipality_code VARCHAR(10),
    zona_metropolitana VARCHAR(100),
    population INTEGER,
    UNIQUE(name, state)
);

-- ==================== 2. AMENITY-PROPERTY LINKAGE ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_amenity_distances (
    id BIGSERIAL PRIMARY KEY,
    comparable_id BIGINT NOT NULL,
    amenity_id BIGINT NOT NULL,
    distance_m FLOAT NOT NULL,
    amenity_type VARCHAR(50),
    amenity_name VARCHAR(200),
    UNIQUE(comparable_id, amenity_id)
);

CREATE INDEX IF NOT EXISTS idx_amenity_dist_comparable ON iainmobiliaria_amenity_distances(comparable_id);
CREATE INDEX IF NOT EXISTS idx_amenity_dist_type ON iainmobiliaria_amenity_distances(amenity_type);

-- ==================== 3. PRE-COMPUTED AMENITY COUNTS ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_amenity_counts (
    comparable_id BIGINT PRIMARY KEY,
    -- Counts at different radii
    total_500m INTEGER DEFAULT 0,
    total_1km INTEGER DEFAULT 0,
    total_2km INTEGER DEFAULT 0,
    total_5km INTEGER DEFAULT 0,
    -- By category at 1km
    schools_1km INTEGER DEFAULT 0,
    hospitals_1km INTEGER DEFAULT 0,
    restaurants_1km INTEGER DEFAULT 0,
    supermarkets_1km INTEGER DEFAULT 0,
    banks_1km INTEGER DEFAULT 0,
    parks_1km INTEGER DEFAULT 0,
    transport_1km INTEGER DEFAULT 0,
    commercial_1km INTEGER DEFAULT 0,
    -- Nearest distances
    nearest_school_m FLOAT,
    nearest_hospital_m FLOAT,
    nearest_supermarket_m FLOAT,
    nearest_park_m FLOAT,
    nearest_transport_m FLOAT,
    -- Composite scores
    walkability_score FLOAT DEFAULT 0, -- 0-100
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== 4. DISTANCE FEATURES ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_distance_features (
    comparable_id BIGINT PRIMARY KEY,
    distance_to_center_km FLOAT,
    distance_to_nearest_metro_km FLOAT,
    distance_to_nearest_highway_km FLOAT,
    distance_to_nearest_airport_km FLOAT,
    distance_to_coast_km FLOAT,
    distance_to_industrial_zone_km FLOAT,
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== 5. GEOGRAPHIC ENRICHMENT ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_geographic_enrichment (
    comparable_id BIGINT PRIMARY KEY,
    elevation_m INTEGER,
    slope_percent FLOAT,
    flood_risk_level VARCHAR(20) DEFAULT 'unknown', -- none, low, medium, high
    seismic_zone VARCHAR(5), -- A, B, C, D
    zoning_type VARCHAR(50), -- residential, commercial, mixed, industrial, rural
    annual_rainfall_mm FLOAT,
    avg_temperature_c FLOAT,
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== 6. DEMOGRAPHIC ENRICHMENT (REAL INEGI) ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_demographics (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    municipality_code VARCHAR(10),
    -- Population
    population INTEGER,
    population_density FLOAT,
    population_growth_5yr_pct FLOAT,
    median_age FLOAT,
    -- Economic
    pea_pct FLOAT, -- % economically active
    unemployment_rate FLOAT,
    avg_income_mxn FLOAT,
    grado_marginacion VARCHAR(20), -- muy_alto, alto, medio, bajo, muy_bajo
    indice_marginacion FLOAT,
    -- Education
    pct_education_superior FLOAT,
    avg_schooling_years FLOAT,
    -- Housing
    pct_owner_occupied FLOAT,
    pct_vacant_housing FLOAT,
    -- Infrastructure
    pct_water_access FLOAT,
    pct_electricity FLOAT,
    pct_drainage FLOAT,
    pct_internet FLOAT,
    -- Security
    homicide_rate_per_100k FLOAT,
    total_crime_rate FLOAT,
    security_perception_score FLOAT, -- 0-100
    -- Source tracking
    data_source VARCHAR(50) DEFAULT 'INEGI',
    data_year INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(city, state, data_year)
);

CREATE INDEX IF NOT EXISTS idx_demographics_city_state ON iainmobiliaria_demographics(city, state);

-- ==================== 7. NEIGHBORHOOD PROFILES ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_neighborhoods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    center_lat FLOAT8,
    center_lon FLOAT8,
    -- Price metrics
    median_price_m2 NUMERIC,
    avg_price_m2 NUMERIC,
    price_std_dev NUMERIC,
    price_growth_1yr_pct FLOAT,
    price_growth_3yr_pct FLOAT,
    -- Quality scores
    safety_score FLOAT, -- 0-100
    walkability_score FLOAT, -- 0-100
    school_quality_score FLOAT, -- 0-100
    infrastructure_score FLOAT, -- 0-100
    green_space_score FLOAT, -- 0-100
    -- Market activity
    avg_days_on_market INTEGER,
    listing_count INTEGER,
    demand_index FLOAT,
    -- Metadata
    sample_count INTEGER,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, city, state)
);

-- ==================== 8. MARKET INDICATORS ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_market_indicators (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    period_date DATE NOT NULL,
    -- Price indicators
    median_price_m2 NUMERIC,
    avg_price_m2 NUMERIC,
    price_change_mom_pct FLOAT, -- month over month
    price_change_yoy_pct FLOAT, -- year over year
    -- Volume
    listing_count INTEGER,
    sold_count INTEGER,
    absorption_rate FLOAT,
    avg_days_on_market INTEGER,
    -- Economic context
    shf_price_index FLOAT,
    mortgage_rate_pct FLOAT,
    inflation_rate_pct FLOAT,
    usd_exchange_rate FLOAT,
    -- Source
    data_source VARCHAR(50),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(city, state, period_date)
);

-- ==================== 9. PREDICTION VALIDATION ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_prediction_validation (
    id SERIAL PRIMARY KEY,
    prediction_id BIGINT,
    comparable_id BIGINT,
    predicted_price_m2 NUMERIC NOT NULL,
    actual_price_m2 NUMERIC,
    error_pct FLOAT,
    error_abs NUMERIC,
    validation_date DATE,
    validation_status VARCHAR(20), -- pending, accurate, within_10pct, within_20pct, outlier
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== 10. FEATURE STORE ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_feature_store (
    comparable_id BIGINT PRIMARY KEY,
    -- Core features
    area_m2 FLOAT,
    log_area FLOAT,
    price_m2 FLOAT,
    -- Location features
    distance_to_center_km FLOAT,
    lat FLOAT8,
    lon FLOAT8,
    -- Amenity features
    walkability_score FLOAT,
    nearest_school_m FLOAT,
    nearest_hospital_m FLOAT,
    nearest_transport_m FLOAT,
    amenity_count_1km INTEGER,
    -- Demographic features
    population_density FLOAT,
    avg_income_mxn FLOAT,
    unemployment_rate FLOAT,
    education_index FLOAT,
    security_score FLOAT,
    infrastructure_score FLOAT,
    -- Market features
    zone_median_price_m2 FLOAT,
    price_trend_1yr_pct FLOAT,
    -- Temporal
    month INTEGER,
    quarter INTEGER,
    -- Metadata
    feature_version VARCHAR(10) DEFAULT 'v2.0',
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== 11. MODEL FEATURE IMPORTANCE ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_model_features (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    importance_score FLOAT,
    rank INTEGER,
    shap_mean_abs FLOAT,
    trained_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_version, feature_name)
);

-- ==================== 12. DATA QUALITY TRACKING ====================
CREATE TABLE IF NOT EXISTS iainmobiliaria_data_quality (
    comparable_id BIGINT PRIMARY KEY,
    source_reliability FLOAT DEFAULT 50, -- 0-100
    data_freshness_days INTEGER,
    price_confidence FLOAT DEFAULT 50, -- 0-100
    location_accuracy_m FLOAT,
    completeness_pct FLOAT, -- % of non-null important fields
    is_outlier BOOLEAN DEFAULT FALSE,
    outlier_reason TEXT,
    validated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== ENABLE RLS ON ALL NEW TABLES ====================
ALTER TABLE iainmobiliaria_cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_amenity_distances ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_amenity_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_distance_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_geographic_enrichment ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_demographics ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_neighborhoods ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_market_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_prediction_validation ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_feature_store ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_model_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_data_quality ENABLE ROW LEVEL SECURITY;

-- Public read for all
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'iainmobiliaria_cities',
        'iainmobiliaria_amenity_distances',
        'iainmobiliaria_amenity_counts',
        'iainmobiliaria_distance_features',
        'iainmobiliaria_geographic_enrichment',
        'iainmobiliaria_demographics',
        'iainmobiliaria_neighborhoods',
        'iainmobiliaria_market_indicators',
        'iainmobiliaria_prediction_validation',
        'iainmobiliaria_feature_store',
        'iainmobiliaria_model_features',
        'iainmobiliaria_data_quality'
    ])
    LOOP
        EXECUTE format('CREATE POLICY "Public read %s" ON %I FOR SELECT TO anon, authenticated USING (true)', tbl, tbl);
        EXECUTE format('CREATE POLICY "Service write %s" ON %I FOR ALL TO service_role USING (true) WITH CHECK (true)', tbl, tbl);
    END LOOP;
END $$;

-- ==================== ADD COLUMNS TO EXISTING TABLES ====================
-- Comparables: add quality tracking
ALTER TABLE iainmobiliaria_comparables ADD COLUMN IF NOT EXISTS data_quality_score FLOAT;
ALTER TABLE iainmobiliaria_comparables ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- Predictions: add validation link
ALTER TABLE iainmobiliaria_predictions ADD COLUMN IF NOT EXISTS actual_sold_price NUMERIC;
ALTER TABLE iainmobiliaria_predictions ADD COLUMN IF NOT EXISTS prediction_error_pct FLOAT;
ALTER TABLE iainmobiliaria_predictions ADD COLUMN IF NOT EXISTS inference_ms FLOAT;

-- Grid tiles: add statistics
ALTER TABLE iainmobiliaria_grid_tiles ADD COLUMN IF NOT EXISTS price_m2_min NUMERIC;
ALTER TABLE iainmobiliaria_grid_tiles ADD COLUMN IF NOT EXISTS price_m2_max NUMERIC;
ALTER TABLE iainmobiliaria_grid_tiles ADD COLUMN IF NOT EXISTS price_m2_std NUMERIC;
ALTER TABLE iainmobiliaria_grid_tiles ADD COLUMN IF NOT EXISTS last_updated TIMESTAMPTZ DEFAULT NOW();
