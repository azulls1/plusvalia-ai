-- ================================================================
-- SCRIPT 6: DATOS DE PRUEBA (OPCIONAL)
-- Proyecto: Análisis de Mercado y Evaluación de Terrenos
-- Fecha: Octubre 2025
-- ================================================================

-- ⚠️ SOLO PARA PRUEBAS - NO EJECUTAR EN PRODUCCIÓN CON DATOS REALES

-- ================================================================
-- 1. INSERTAR COMPARABLES DE PRUEBA (Querétaro)
-- ================================================================

INSERT INTO public.iainmobiliaria_comparables 
  (title, price_mxn, area_m2, address, city, state, lat, lon)
VALUES
  ('Casa Residencial Juriquilla', 3500000, 150, 'Anillo Vial Fray Junípero Serra 5555, Juriquilla', 'Queretaro', 'Queretaro', 20.6969, -100.4461),
  ('Departamento Centro Histórico', 2800000, 85, 'Calle Corregidora 100, Centro', 'Queretaro', 'Queretaro', 20.5888, -100.3899),
  ('Casa Lomas de Querétaro', 5200000, 220, 'Av. Lomas 456, Lomas de Querétaro', 'Queretaro', 'Queretaro', 20.5628, -100.3903),
  ('Terreno Industrial El Marqués', 1800000, 500, 'Carretera 57 Km 180, El Marqués', 'El Marques', 'Queretaro', 20.6853, -100.2736),
  ('Casa en Zibatá', 4500000, 180, 'Blvd. Zibatá 789, Zibatá', 'El Marques', 'Queretaro', 20.7114, -100.2542),
  ('Departamento Milenio III', 1950000, 75, 'Av. Milenio III 321, Milenio III', 'Queretaro', 'Queretaro', 20.5571, -100.3653),
  ('Casa en La Vista', 6800000, 280, 'Privada La Vista 111, La Vista', 'Queretaro', 'Queretaro', 20.6421, -100.4217),
  ('Terreno en San Juan del Río', 850000, 300, 'Carretera San Juan del Río 200', 'San Juan del Rio', 'Queretaro', 20.3880, -99.9949),
  ('Casa Residencial Punta Juriquilla', 7500000, 320, 'Punta Juriquilla 555', 'Queretaro', 'Queretaro', 20.7083, -100.4653),
  ('Departamento Antea Lifestyle', 3200000, 95, 'Antea Lifestyle Center 789', 'Queretaro', 'Queretaro', 20.6344, -100.4556);

SELECT 'Comparables de prueba insertados: ' || COUNT(*) || ' registros'
FROM public.iainmobiliaria_comparables
WHERE city IN ('Queretaro', 'El Marques', 'San Juan del Rio');


-- ================================================================
-- 2. INSERTAR AMENIDADES DE PRUEBA (Querétaro)
-- ================================================================

INSERT INTO public.iainmobiliaria_amenities 
  (osm_id, name, amenity_type, lat, lon, city, state, tags)
VALUES
  (1001, 'Universidad Autónoma de Querétaro', 'university', 20.5888, -100.3899, 'Queretaro', 'Queretaro', '{"website": "www.uaq.mx"}'::jsonb),
  (1002, 'Hospital General de Querétaro', 'hospital', 20.5978, -100.3892, 'Queretaro', 'Queretaro', '{"emergency": "yes"}'::jsonb),
  (1003, 'CETYS Universidad Querétaro', 'university', 20.6969, -100.4461, 'Queretaro', 'Queretaro', '{"private": "yes"}'::jsonb),
  (1004, 'Walmart Juriquilla', 'marketplace', 20.6925, -100.4487, 'Queretaro', 'Queretaro', '{"brand": "Walmart"}'::jsonb),
  (1005, 'Escuela Primaria Benito Juárez', 'school', 20.5910, -100.3921, 'Queretaro', 'Queretaro', '{"level": "primary"}'::jsonb),
  (1006, 'Hospital Ángeles Querétaro', 'hospital', 20.6333, -100.4556, 'Queretaro', 'Queretaro', '{"private": "yes"}'::jsonb),
  (1007, 'Tecnológico de Monterrey Campus Querétaro', 'university', 20.7343, -100.4814, 'Queretaro', 'Queretaro', '{"students": "5000"}'::jsonb),
  (1008, 'Soriana Constituyentes', 'marketplace', 20.5800, -100.4100, 'Queretaro', 'Queretaro', '{"brand": "Soriana"}'::jsonb),
  (1009, 'Gasolinera Pemex Bernardo Quintana', 'fuel', 20.6110, -100.4020, 'Queretaro', 'Queretaro', '{"brand": "Pemex"}'::jsonb),
  (1010, 'Central de Autobuses Querétaro', 'bus_station', 20.5677, -100.4014, 'Queretaro', 'Queretaro', '{"operator": "ADO"}'::jsonb),
  (1011, 'Colegio Peterson Querétaro', 'school', 20.6921, -100.4433, 'Queretaro', 'Queretaro', '{"level": "high_school"}'::jsonb),
  (1012, 'Hospital Star Médica', 'hospital', 20.5766, -100.3811, 'Queretaro', 'Queretaro', '{"beds": "120"}'::jsonb),
  (1013, 'Parque Industrial Querétaro', 'industrial', 20.6588, -100.2822, 'El Marques', 'Queretaro', '{"type": "industrial_park"}'::jsonb),
  (1014, 'Aeropuerto Internacional de Querétaro', 'bus_station', 20.6173, -100.1858, 'Colon', 'Queretaro', '{"iata": "QRO"}'::jsonb),
  (1015, 'Universidad del Valle de México Campus Querétaro', 'university', 20.5555, -100.3666, 'Queretaro', 'Queretaro', '{"private": "yes"}'::jsonb);

SELECT 'Amenidades de prueba insertadas: ' || COUNT(*) || ' registros'
FROM public.iainmobiliaria_amenities
WHERE state = 'Queretaro';


-- ================================================================
-- 3. GENERAR GRILLA DE PRUEBA
-- ================================================================

-- Usar la función rebuild_grid para generar tiles desde los comparables
SELECT * FROM public.rebuild_grid(0.005);

SELECT 'Grilla de prueba generada: ' || COUNT(*) || ' tiles'
FROM public.iainmobiliaria_grid_tiles;


-- ================================================================
-- 4. VERIFICAR DATOS INSERTADOS
-- ================================================================

-- Resumen de datos
SELECT 
  'RESUMEN DE DATOS DE PRUEBA' AS seccion,
  '' AS detalle
UNION ALL
SELECT 
  'Comparables',
  COUNT(*)::TEXT || ' registros'
FROM public.iainmobiliaria_comparables
UNION ALL
SELECT 
  'Amenidades',
  COUNT(*)::TEXT || ' registros'
FROM public.iainmobiliaria_amenities
UNION ALL
SELECT 
  'Grid Tiles',
  COUNT(*)::TEXT || ' registros'
FROM public.iainmobiliaria_grid_tiles;


-- Estadísticas usando la función creada
SELECT * FROM public.get_statistics();


-- Ejemplo de consulta: amenidades cercanas al centro de Querétaro
SELECT 
  'AMENIDADES CERCANAS AL CENTRO (5 km)' AS titulo,
  name,
  amenity_type,
  ROUND(distance_km::NUMERIC, 2)::TEXT || ' km' AS distancia
FROM public.get_nearby_amenities(20.5888, -100.3899, 5.0)
ORDER BY distance_km
LIMIT 10;


-- ================================================================
-- 5. CONSULTAS DE EJEMPLO
-- ================================================================

-- Comparables ordenados por precio por m²
SELECT 
  title,
  ROUND(price_m2::NUMERIC, 2) AS precio_m2,
  city,
  area_m2
FROM public.iainmobiliaria_comparables
ORDER BY price_m2 DESC
LIMIT 5;


-- Conteo de amenidades por tipo
SELECT 
  amenity_type,
  COUNT(*) AS cantidad
FROM public.iainmobiliaria_amenities
GROUP BY amenity_type
ORDER BY cantidad DESC;


-- Tiles con mayor precio promedio
SELECT 
  ROUND(lat::NUMERIC, 4) AS latitud,
  ROUND(lon::NUMERIC, 4) AS longitud,
  ROUND(price_m2_avg::NUMERIC, 2) AS precio_promedio_m2,
  count_properties AS propiedades
FROM public.iainmobiliaria_grid_tiles
ORDER BY price_m2_avg DESC
LIMIT 5;


-- ================================================================
-- CONFIRMACIÓN FINAL
-- ================================================================
SELECT 
  '✅ DATOS DE PRUEBA INSERTADOS CORRECTAMENTE' AS status,
  'Puedes comenzar a usar la aplicación con estos datos' AS mensaje;


-- ================================================================
-- NOTA: LIMPIAR DATOS DE PRUEBA
-- ================================================================
-- Si necesitas eliminar estos datos de prueba, ejecuta:

-- DELETE FROM public.iainmobiliaria_comparables 
-- WHERE city IN ('Queretaro', 'El Marques', 'San Juan del Rio');

-- DELETE FROM public.iainmobiliaria_amenities 
-- WHERE state = 'Queretaro' AND osm_id BETWEEN 1001 AND 1015;

-- DELETE FROM public.iainmobiliaria_grid_tiles;

