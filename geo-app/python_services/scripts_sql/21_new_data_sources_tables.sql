-- ================================================================
-- MIGRACIÓN 21: Tablas para nuevas fuentes de datos
-- Fecha: 2026-03-31
-- Descripción: CONAPO, DENUE, SESNSP, SHF, CENAPRED, SEDATU, CONAVI, INFONAVIT
-- ================================================================

-- ==================== 1. CONAPO Índice de Marginación ====================
-- Fuente: Consejo Nacional de Población
-- Nivel: AGEB (Área Geoestadística Básica) o municipio
CREATE TABLE IF NOT EXISTS iainmobiliaria_conapo_marginacion (
    id BIGSERIAL PRIMARY KEY,
    cve_ent VARCHAR(2) NOT NULL,          -- Clave entidad federativa
    cve_mun VARCHAR(5) NOT NULL,          -- Clave municipio
    cve_ageb VARCHAR(13),                 -- Clave AGEB (opcional, nivel municipal si es NULL)
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200) NOT NULL,
    marginalization_index FLOAT,          -- Índice de marginación original
    marginalization_grade VARCHAR(20),    -- Muy Alto/Alto/Medio/Bajo/Muy Bajo
    marginalization_score FLOAT,          -- 0-100 normalizado para ML
    population INTEGER,
    pct_illiterate FLOAT,                 -- % población analfabeta 15+
    pct_no_primary FLOAT,                 -- % sin primaria completa 15+
    pct_no_plumbing FLOAT,               -- % viviendas sin agua entubada
    pct_no_electricity FLOAT,            -- % viviendas sin energía eléctrica
    pct_no_drainage FLOAT,              -- % viviendas sin drenaje
    pct_dirt_floor FLOAT,               -- % viviendas con piso de tierra
    pct_overcrowded FLOAT,              -- % viviendas con hacinamiento
    pct_small_locality FLOAT,           -- % población en localidades < 5000 hab
    data_year INTEGER DEFAULT 2020,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conapo_state ON iainmobiliaria_conapo_marginacion(state);
CREATE INDEX IF NOT EXISTS idx_conapo_municipality ON iainmobiliaria_conapo_marginacion(municipality);
CREATE INDEX IF NOT EXISTS idx_conapo_cve_mun ON iainmobiliaria_conapo_marginacion(cve_mun);
CREATE INDEX IF NOT EXISTS idx_conapo_cve_ageb ON iainmobiliaria_conapo_marginacion(cve_ageb);
CREATE INDEX IF NOT EXISTS idx_conapo_grade ON iainmobiliaria_conapo_marginacion(marginalization_grade);

COMMENT ON TABLE iainmobiliaria_conapo_marginacion IS 'Índice de marginación CONAPO por AGEB/municipio — indica nivel socioeconómico de la zona';

-- ==================== 2. DENUE Negocios ====================
-- Fuente: Directorio Estadístico Nacional de Unidades Económicas (INEGI)
-- Establecimientos comerciales geolocalizados
CREATE TABLE IF NOT EXISTS iainmobiliaria_denue_businesses (
    id BIGSERIAL PRIMARY KEY,
    denue_id VARCHAR(20),                -- ID original DENUE
    business_name VARCHAR(300),
    naics_code VARCHAR(10) NOT NULL,     -- Código SCIAN (Sistema de Clasificación Industrial)
    naics_sector INTEGER,                -- Sector SCIAN (2 dígitos): 46=comercio, 52=financiero, etc.
    naics_description VARCHAR(200),
    employees_range VARCHAR(20),         -- Rango de personal: 0-5, 6-10, 11-30, etc.
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200) NOT NULL,
    locality VARCHAR(200),
    lat FLOAT8 NOT NULL,
    lon FLOAT8 NOT NULL,
    phone VARCHAR(50),
    activity_type VARCHAR(100),          -- Tipo de actividad económica
    data_year INTEGER DEFAULT 2024,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_denue_state ON iainmobiliaria_denue_businesses(state);
CREATE INDEX IF NOT EXISTS idx_denue_municipality ON iainmobiliaria_denue_businesses(municipality);
CREATE INDEX IF NOT EXISTS idx_denue_naics_sector ON iainmobiliaria_denue_businesses(naics_sector);
CREATE INDEX IF NOT EXISTS idx_denue_latlon ON iainmobiliaria_denue_businesses(lat, lon);
CREATE INDEX IF NOT EXISTS idx_denue_denue_id ON iainmobiliaria_denue_businesses(denue_id);

COMMENT ON TABLE iainmobiliaria_denue_businesses IS 'Establecimientos económicos DENUE/INEGI — densidad comercial y tipo de actividad por zona';

-- ==================== 3. SESNSP Estadísticas de Criminalidad ====================
-- Fuente: Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública
-- Incidencia delictiva por municipio y mes
CREATE TABLE IF NOT EXISTS iainmobiliaria_crime_stats (
    id BIGSERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200) NOT NULL,
    period_date DATE NOT NULL,           -- Primer día del mes reportado
    -- Delitos de alto impacto (tasa por 100k habitantes)
    homicide_rate FLOAT,
    robbery_rate FLOAT,
    vehicle_theft_rate FLOAT,
    extortion_rate FLOAT,
    kidnapping_rate FLOAT,
    -- Totales absolutos
    total_crimes INTEGER,
    property_crimes INTEGER,
    violent_crimes INTEGER,
    -- Indicadores calculados
    crime_trend FLOAT,                   -- Tendencia 12 meses: positivo=incremento
    safety_score FLOAT,                  -- 0-100 normalizado (100=más seguro)
    yoy_change_pct FLOAT,               -- Cambio interanual %
    -- Metadata
    population_base INTEGER,             -- Población usada para cálculo de tasas
    data_source VARCHAR(50) DEFAULT 'SESNSP',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(state, municipality, period_date)
);

CREATE INDEX IF NOT EXISTS idx_crime_state ON iainmobiliaria_crime_stats(state);
CREATE INDEX IF NOT EXISTS idx_crime_municipality ON iainmobiliaria_crime_stats(municipality);
CREATE INDEX IF NOT EXISTS idx_crime_period ON iainmobiliaria_crime_stats(period_date);
CREATE INDEX IF NOT EXISTS idx_crime_safety ON iainmobiliaria_crime_stats(safety_score);

COMMENT ON TABLE iainmobiliaria_crime_stats IS 'Incidencia delictiva SESNSP — tasas de criminalidad y score de seguridad por municipio/mes';

-- ==================== 4. SHF Índice de Precios de Vivienda ====================
-- Fuente: Sociedad Hipotecaria Federal
-- Índice de precios y tendencias por estado/municipio
CREATE TABLE IF NOT EXISTS iainmobiliaria_shf_price_index (
    id BIGSERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200),           -- NULL para nivel estatal
    period_date DATE NOT NULL,           -- Trimestre (primer día)
    -- Índices
    price_index FLOAT NOT NULL,          -- Índice de precios SHF (base=100)
    price_index_residential FLOAT,       -- Índice vivienda residencial
    price_index_social FLOAT,            -- Índice vivienda social
    -- Tendencias calculadas
    price_trend_1yr FLOAT,               -- Cambio % últimos 12 meses
    price_trend_3yr FLOAT,               -- Cambio % últimos 3 años
    price_momentum FLOAT,                -- Aceleración del cambio de precios
    -- Volumen
    transactions_count INTEGER,          -- Número de transacciones en período
    avg_price_mxn NUMERIC,              -- Precio promedio reportado
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'SHF',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(state, municipality, period_date)
);

CREATE INDEX IF NOT EXISTS idx_shf_state ON iainmobiliaria_shf_price_index(state);
CREATE INDEX IF NOT EXISTS idx_shf_municipality ON iainmobiliaria_shf_price_index(municipality);
CREATE INDEX IF NOT EXISTS idx_shf_period ON iainmobiliaria_shf_price_index(period_date);

COMMENT ON TABLE iainmobiliaria_shf_price_index IS 'Índice de precios de vivienda SHF — tendencias macro del mercado inmobiliario';

-- ==================== 5. CENAPRED Zonas de Riesgo ====================
-- Fuente: Centro Nacional de Prevención de Desastres
-- Zonas de riesgo sísmico, inundación y otros peligros
CREATE TABLE IF NOT EXISTS iainmobiliaria_risk_zones (
    id BIGSERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200) NOT NULL,
    lat FLOAT8,
    lon FLOAT8,
    -- Riesgo sísmico
    seismic_zone VARCHAR(5),             -- A (menor), B, C, D (mayor)
    seismic_zone_score FLOAT,            -- 0-1 normalizado
    -- Riesgo de inundación
    flood_risk VARCHAR(20),              -- none, low, medium, high, very_high
    flood_risk_score FLOAT,              -- 0-1 normalizado
    -- Riesgo volcánico
    volcanic_risk VARCHAR(20),
    volcanic_risk_score FLOAT,
    -- Riesgo de deslizamiento
    landslide_risk VARCHAR(20),
    landslide_risk_score FLOAT,
    -- Score compuesto
    risk_score FLOAT,                    -- 0-100 compuesto de todos los riesgos
    risk_category VARCHAR(20),           -- bajo, medio, alto, muy_alto
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'CENAPRED',
    data_year INTEGER DEFAULT 2024,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_state ON iainmobiliaria_risk_zones(state);
CREATE INDEX IF NOT EXISTS idx_risk_municipality ON iainmobiliaria_risk_zones(municipality);
CREATE INDEX IF NOT EXISTS idx_risk_latlon ON iainmobiliaria_risk_zones(lat, lon);
CREATE INDEX IF NOT EXISTS idx_risk_category ON iainmobiliaria_risk_zones(risk_category);

COMMENT ON TABLE iainmobiliaria_risk_zones IS 'Zonas de riesgo CENAPRED — riesgos naturales que impactan valor de propiedad';

-- ==================== 6. SEDATU Contención Urbana ====================
-- Fuente: Secretaría de Desarrollo Agrario, Territorial y Urbano
-- Perímetros de contención urbana (U1=intraurbano, U2=primer contorno, U3=periurbano)
CREATE TABLE IF NOT EXISTS iainmobiliaria_urban_containment (
    id BIGSERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200) NOT NULL,
    lat FLOAT8,
    lon FLOAT8,
    -- Clasificación urbana
    urban_zone VARCHAR(10) NOT NULL,     -- U1, U2, U3, rural
    urban_zone_description VARCHAR(100), -- Intraurbano, Primer Contorno, Periurbano, Rural
    urban_zone_score FLOAT,              -- 1.0=U1, 0.75=U2, 0.5=U3, 0.25=rural
    -- Infraestructura disponible
    has_public_transport BOOLEAN DEFAULT FALSE,
    has_paved_roads BOOLEAN DEFAULT FALSE,
    has_public_services BOOLEAN DEFAULT FALSE,
    proximity_employment_km FLOAT,       -- Distancia a fuentes de empleo
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'SEDATU',
    data_year INTEGER DEFAULT 2024,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_urban_state ON iainmobiliaria_urban_containment(state);
CREATE INDEX IF NOT EXISTS idx_urban_municipality ON iainmobiliaria_urban_containment(municipality);
CREATE INDEX IF NOT EXISTS idx_urban_latlon ON iainmobiliaria_urban_containment(lat, lon);
CREATE INDEX IF NOT EXISTS idx_urban_zone ON iainmobiliaria_urban_containment(urban_zone);

COMMENT ON TABLE iainmobiliaria_urban_containment IS 'Contención urbana SEDATU — clasificación U1/U2/U3 que afecta plusvalía y acceso a servicios';

-- ==================== 7. CONAVI RUV Vivienda ====================
-- Fuente: Comisión Nacional de Vivienda / Registro Único de Vivienda
-- Oferta de vivienda nueva registrada
CREATE TABLE IF NOT EXISTS iainmobiliaria_conavi_ruv (
    id BIGSERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200) NOT NULL,
    period_date DATE NOT NULL,           -- Mes de registro
    -- Oferta de vivienda
    registered_units INTEGER,            -- Viviendas registradas en RUV
    social_units INTEGER,                -- Vivienda social/económica
    medium_units INTEGER,                -- Vivienda media
    residential_units INTEGER,           -- Vivienda residencial
    -- Precios promedio por segmento
    avg_price_social NUMERIC,
    avg_price_medium NUMERIC,
    avg_price_residential NUMERIC,
    -- Indicadores
    supply_index FLOAT,                  -- Índice de oferta relativo a demanda
    absorption_rate_months FLOAT,        -- Meses para absorber inventario
    -- Desarrolladores activos
    active_developers INTEGER,
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'CONAVI-RUV',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(state, municipality, period_date)
);

CREATE INDEX IF NOT EXISTS idx_conavi_state ON iainmobiliaria_conavi_ruv(state);
CREATE INDEX IF NOT EXISTS idx_conavi_municipality ON iainmobiliaria_conavi_ruv(municipality);
CREATE INDEX IF NOT EXISTS idx_conavi_period ON iainmobiliaria_conavi_ruv(period_date);

COMMENT ON TABLE iainmobiliaria_conavi_ruv IS 'Registro Único de Vivienda CONAVI — oferta de vivienda nueva y precios por segmento';

-- ==================== 8. INFONAVIT Datos de Avalúos ====================
-- Fuente: Instituto del Fondo Nacional de la Vivienda para los Trabajadores
-- Avalúos y datos de créditos hipotecarios
CREATE TABLE IF NOT EXISTS iainmobiliaria_infonavit_data (
    id BIGSERIAL PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    municipality VARCHAR(200) NOT NULL,
    zip_code VARCHAR(5),
    period_date DATE NOT NULL,           -- Trimestre de reporte
    -- Avalúos
    avg_appraisal_value NUMERIC,         -- Valor promedio de avalúo
    median_appraisal_value NUMERIC,
    appraisal_count INTEGER,
    avg_price_m2 NUMERIC,                -- Precio promedio por m²
    -- Créditos
    credits_granted INTEGER,             -- Créditos otorgados en período
    avg_credit_amount NUMERIC,
    avg_worker_income NUMERIC,           -- Ingreso promedio del trabajador
    -- Demanda
    demand_index FLOAT,                  -- Índice de demanda (créditos/oferta)
    default_rate FLOAT,                  -- Tasa de morosidad
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'INFONAVIT',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(state, municipality, period_date)
);

CREATE INDEX IF NOT EXISTS idx_infonavit_state ON iainmobiliaria_infonavit_data(state);
CREATE INDEX IF NOT EXISTS idx_infonavit_municipality ON iainmobiliaria_infonavit_data(municipality);
CREATE INDEX IF NOT EXISTS idx_infonavit_zip ON iainmobiliaria_infonavit_data(zip_code);
CREATE INDEX IF NOT EXISTS idx_infonavit_period ON iainmobiliaria_infonavit_data(period_date);

COMMENT ON TABLE iainmobiliaria_infonavit_data IS 'Datos INFONAVIT — avalúos y demanda hipotecaria como indicador de mercado';

-- ==================== TRIGGER: updated_at automático ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'iainmobiliaria_conapo_marginacion',
        'iainmobiliaria_denue_businesses',
        'iainmobiliaria_crime_stats',
        'iainmobiliaria_shf_price_index',
        'iainmobiliaria_risk_zones',
        'iainmobiliaria_urban_containment',
        'iainmobiliaria_conavi_ruv',
        'iainmobiliaria_infonavit_data'
    ])
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            tbl, tbl
        );
    END LOOP;
END $$;

-- ==================== ENABLE RLS EN TODAS LAS TABLAS NUEVAS ====================
ALTER TABLE iainmobiliaria_conapo_marginacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_denue_businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_crime_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_shf_price_index ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_risk_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_urban_containment ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_conavi_ruv ENABLE ROW LEVEL SECURITY;
ALTER TABLE iainmobiliaria_infonavit_data ENABLE ROW LEVEL SECURITY;

-- Lectura pública, escritura solo service_role
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'iainmobiliaria_conapo_marginacion',
        'iainmobiliaria_denue_businesses',
        'iainmobiliaria_crime_stats',
        'iainmobiliaria_shf_price_index',
        'iainmobiliaria_risk_zones',
        'iainmobiliaria_urban_containment',
        'iainmobiliaria_conavi_ruv',
        'iainmobiliaria_infonavit_data'
    ])
    LOOP
        EXECUTE format('CREATE POLICY "Public read %s" ON %I FOR SELECT TO anon, authenticated USING (true)', tbl, tbl);
        EXECUTE format('CREATE POLICY "Service write %s" ON %I FOR ALL TO service_role USING (true) WITH CHECK (true)', tbl, tbl);
    END LOOP;
END $$;
