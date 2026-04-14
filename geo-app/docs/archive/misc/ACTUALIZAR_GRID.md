# 🗺️ Actualizar Grid de Ubicaciones

## ¿Qué es el Grid?

El **Grid de Ubicaciones** (`iainmobiliaria_grid_tiles`) es una cuadrícula geográfica que agrega las propiedades en celdas espaciales. Cada celda contiene:
- Precio promedio por m²
- Cantidad de propiedades en esa zona
- Coordenadas del centro de la celda

Se usa para **visualizar mapas de calor** de precios inmobiliarios.

---

## ¿Cuándo actualizar?

Debes regenerar el grid cuando:
1. ✅ Agregas nuevas propiedades a `iainmobiliaria_comparables`
2. ✅ Actualizas precios de propiedades existentes
3. ✅ Cambias datos de ubicación (lat/lon) de propiedades

---

## ¿Cómo actualizar?

### Opción 1: Usando Python

```bash
cd geo-app/python_services
python -c "from supabase import create_client; from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY; supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY); result = supabase.rpc('rebuild_grid', {'step_deg': 0.005}).execute(); print(f'Grid actualizado: {result.data[0]}' if result.data else 'OK')"
```

### Opción 2: Usando SQL en Supabase

1. Ve a tu proyecto en https://supabase.com
2. Abre el **SQL Editor**
3. Ejecuta:

```sql
SELECT * FROM rebuild_grid(0.005);
```

**Resultado esperado:**
```
tiles_created | comparables_used | execution_time_ms
--------------+------------------+------------------
    363      |      800         |     50.23
```

---

## Parámetros

### `step_deg` (Tamaño de celda)

Controla el tamaño de cada celda del grid:

| step_deg | Tamaño aproximado | Uso recomendado |
|----------|-------------------|-----------------|
| 0.001    | ~111 m           | Ciudades densas |
| 0.005    | **~500 m** (DEFAULT) | **General** |
| 0.01     | ~1.1 km          | Áreas grandes |
| 0.02     | ~2.2 km          | Estados/regiones |

**Más pequeño = Más celdas = Más detalle (pero más lento)**

---

## Verificar Grid

Después de actualizar, verifica que se haya generado correctamente:

```sql
-- Ver estadísticas del grid
SELECT 
  COUNT(*) as total_celdas,
  AVG(price_m2_avg) as precio_promedio,
  MIN(price_m2_avg) as precio_minimo,
  MAX(price_m2_avg) as precio_maximo,
  AVG(count_properties) as props_por_celda
FROM iainmobiliaria_grid_tiles;
```

```sql
-- Ver muestra de celdas
SELECT 
  lat, 
  lon, 
  price_m2_avg, 
  count_properties
FROM iainmobiliaria_grid_tiles
ORDER BY price_m2_avg DESC
LIMIT 10;
```

---

## Estado Actual

**Última actualización:** 25 de Octubre de 2025

| Métrica | Valor |
|---------|-------|
| **Total de celdas** | 363 |
| **Propiedades usadas** | 800 |
| **Precio/m² promedio** | $44,337 MXN |
| **Precio/m² rango** | $10,613 - $137,265 MXN |
| **Propiedades por celda** | 2.2 (promedio) |
| **Tamaño de celda** | ~500m |

---

## Troubleshooting

### Error: "DELETE requires a WHERE clause"

**Causa:** RLS (Row Level Security) activado sin políticas adecuadas.

**Solución:**
```sql
-- Deshabilitar RLS temporalmente
ALTER TABLE iainmobiliaria_grid_tiles DISABLE ROW LEVEL SECURITY;

-- Regenerar grid
SELECT * FROM rebuild_grid(0.005);

-- Opcional: Volver a habilitar RLS
-- ALTER TABLE iainmobiliaria_grid_tiles ENABLE ROW LEVEL SECURITY;
```

### Error: "No hay comparables con coordenadas válidas"

**Causa:** Las propiedades no tienen `lat`, `lon` o `price_m2` válidos.

**Solución:**
```sql
-- Verificar propiedades con coordenadas
SELECT COUNT(*) 
FROM iainmobiliaria_comparables 
WHERE lat IS NOT NULL 
  AND lon IS NOT NULL 
  AND (price_mxn / NULLIF(area_m2, 0)) > 0;
```

Si es 0, necesitas agregar propiedades con coordenadas válidas.

---

## Uso en Frontend

Una vez generado el grid, puedes usarlo en el frontend para:

### Mapa de Calor (Heatmap)

```typescript
// En Angular/Leaflet
const gridData = await fetch('/api/grid-tiles').then(r => r.json());

const heatmapData = gridData.map(tile => [
  tile.lat,
  tile.lon,
  tile.price_m2_avg / 100000  // Normalizar
]);

L.heatLayer(heatmapData, {
  radius: 25,
  blur: 15,
  maxZoom: 17
}).addTo(map);
```

### Polígonos de Precios

```typescript
gridData.forEach(tile => {
  const bounds = calculateBounds(tile.lat, tile.lon, 0.005);
  
  L.rectangle(bounds, {
    color: getColorByPrice(tile.price_m2_avg),
    fillOpacity: 0.5,
    weight: 1
  })
  .bindPopup(`
    <b>$${tile.price_m2_avg.toLocaleString()}/m²</b><br>
    ${tile.count_properties} propiedades
  `)
  .addTo(map);
});
```

---

## API Endpoint (Recomendado)

Crea un endpoint en tu API para servir el grid:

```python
# En api/main.py
@app.get("/api/grid-tiles")
async def get_grid_tiles():
    """Obtiene el grid de precios"""
    result = supabase.table("iainmobiliaria_grid_tiles").select("*").execute()
    return result.data
```

---

**Última actualización:** 25 de Octubre de 2025  
**Grid actual:** 363 celdas | 800 propiedades | ~500m por celda

