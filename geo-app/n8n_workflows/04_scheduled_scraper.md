# 🕷️ Workflow 04: Scraper Programado (Scheduled Scraper)

Workflow para ejecutar automáticamente los scrapers de forma periódica y alimentar la base de datos con datos actualizados.

---

## 📋 Descripción

Este workflow:
1. ✅ Se ejecuta automáticamente (mensual o manual)
2. ✅ Llama al scraper Python unificado
3. ✅ Procesa los resultados CSV
4. ✅ Geocodifica direcciones
5. ✅ Inserta datos en Supabase
6. ✅ Actualiza grilla de precios
7. ✅ Crea snapshot de histórico

---

## 🏗️ Estructura del Workflow

```
┌─────────────────────────────┐
│  Trigger: Schedule (Monthly)│
│  or Manual Trigger          │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Execute Command Node       │
│  python scrapers/unified.py │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Read CSV File              │
│  (Output del scraper)       │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Loop: Each Row             │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Geocode if needed          │
│  (Nominatim fallback)       │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Supabase Insert            │
│  Table: comparables         │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Call /grid-build           │
│  (Recalcular grilla)        │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Execute SQL Function       │
│  insert_monthly_snapshot()  │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│  Notify Success (Email?)    │
└─────────────────────────────┘
```

---

## 🔧 Configuración de Nodos

### **Nodo 1: Schedule Trigger**

**Tipo**: `Schedule Trigger`

**Configuración**:
```json
{
  "rule": {
    "interval": [
      {
        "field": "months",
        "month": 1
      }
    ]
  },
  "triggerTimes": {
    "item": [
      {
        "hour": 2,
        "minute": 0
      }
    ]
  }
}
```

**Descripción**: Se ejecuta el día 1 de cada mes a las 2:00 AM.

---

### **Nodo 2: Execute Command**

**Tipo**: `Execute Command`

**Configuración**:
```json
{
  "command": "python",
  "arguments": "scrapers/unified_scraper.py",
  "cwd": "/ruta/a/python_services"
}
```

**Variables de entorno**:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SCRAPER_HEADLESS=true`

**Output**: Ruta al CSV generado (capturar desde stdout)

---

### **Nodo 3: Read CSV File**

**Tipo**: `Read/Write Files from Disk`

**Configuración**:
```json
{
  "operation": "read",
  "filePath": "={{ $json.csv_path }}",
  "options": {
    "encoding": "utf8"
  }
}
```

O usar el nodo **CSV** para parsear directamente:

```json
{
  "columns": {
    "mappingMode": "autoMapInputData"
  },
  "options": {
    "delimiter": ",",
    "fromLine": 1
  }
}
```

---

### **Nodo 4: Loop sobre filas**

**Tipo**: `Loop Over Items`

**Configuración**: Split cada fila del CSV.

---

### **Nodo 5: Geocode (Condicional)**

**Tipo**: `HTTP Request`

**Condición**: Si `lat` o `lon` están vacíos.

**Configuración**:
```json
{
  "method": "GET",
  "url": "https://nominatim.openstreetmap.org/search",
  "qs": {
    "q": "={{ $json.address }}, {{ $json.city }}, {{ $json.state }}",
    "format": "json",
    "limit": 1
  },
  "options": {
    "headers": {
      "User-Agent": "inmo-geo-mvp/1.0"
    }
  }
}
```

**Output**: Extraer `lat` y `lon` del resultado.

---

### **Nodo 6: Supabase Insert**

**Tipo**: `Supabase`

**Operación**: `Insert`

**Configuración**:
```json
{
  "table": "iainmobiliaria_comparables",
  "data": {
    "title": "={{ $json.title }}",
    "price_mxn": "={{ $json.price_mxn }}",
    "area_m2": "={{ $json.area_m2 }}",
    "address": "={{ $json.address }}",
    "city": "={{ $json.city }}",
    "state": "={{ $json.state }}",
    "lat": "={{ $json.lat }}",
    "lon": "={{ $json.lon }}",
    "source": "={{ $json.source }}",
    "source_url": "={{ $json.source_url }}",
    "collection_date": "={{ $now.format('YYYY-MM-DD') }}"
  },
  "options": {
    "onConflict": "ignore"
  }
}
```

**Credenciales**: `Supabase Inmobiliaria` (con `service_role_key`)

---

### **Nodo 7: Call Grid Build**

**Tipo**: `HTTP Request`

**Configuración**:
```json
{
  "method": "POST",
  "url": "https://iagentekn8nwebhook.iagentek.com.mx/grid-build",
  "body": {
    "step": 0.005
  },
  "options": {
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

---

### **Nodo 8: Create Monthly Snapshot**

**Tipo**: `Postgres`

**Operación**: `Execute Query`

**Configuración**:
```sql
SELECT insert_monthly_snapshot();
```

**Credenciales**: `PostgreSQL Supabase`

---

### **Nodo 9: Notification (Opcional)**

**Tipo**: `Email` o `Slack` o `Discord`

**Mensaje**:
```
✅ Scraping mensual completado

• Propiedades insertadas: {{ $json.inserted_count }}
• Grilla actualizada: {{ $json.tiles_count }} tiles
• Snapshot histórico creado

Fecha: {{ $now.format('YYYY-MM-DD HH:mm') }}
```

---

## 🚀 Implementación

### **Opción 1: Crear workflow manualmente**

1. Crear nuevo workflow en n8n
2. Agregar nodos según el diagrama
3. Configurar credenciales
4. Activar workflow

### **Opción 2: Usar código Python directamente** (Recomendado)

Simplificar usando un solo nodo **HTTP Request** que llame a un script Python:

```json
{
  "method": "POST",
  "url": "http://localhost:8000/scraper/run",
  "body": {
    "cities": ["Querétaro", "Guadalajara", "Monterrey"],
    "max_pages": 3
  }
}
```

**Ventaja**: Todo el procesamiento en Python (más fácil de mantener).

---

## 📊 Salida Esperada

**Response del workflow**:
```json
{
  "status": "success",
  "scraped_properties": 150,
  "inserted": 145,
  "duplicates": 5,
  "grid_tiles_updated": 320,
  "snapshot_created": true,
  "execution_time_seconds": 180,
  "sources": ["inmuebles24", "lamudi"],
  "cities": ["Querétaro", "Guadalajara", "Monterrey"]
}
```

---

## 🔄 Alternativa Simplificada

En lugar de crear un workflow complejo en n8n, **crear un endpoint en la API FastAPI**:

### **API Endpoint: `/scraper/run`**

```python
@app.post("/scraper/run")
async def run_scraper(
    cities: List[str],
    max_pages: int = 3,
    background: BackgroundTasks = None
):
    """
    Ejecuta el scraper unificado
    """
    # Ejecutar scraper
    scraper = UnifiedScraper()
    df = await scraper.scrape_all_sources(...)
    
    # Insertar en Supabase
    supabase.insert_batch(df)
    
    # Recalcular grilla
    rebuild_grid()
    
    # Crear snapshot
    create_snapshot()
    
    return {
        "status": "success",
        "scraped": len(df),
        ...
    }
```

**Workflow n8n simplificado**:
```
Schedule Trigger
    ↓
HTTP Request → POST /scraper/run
    ↓
Done ✅
```

---

## ⚠️ Consideraciones

### **Rate Limiting**

- Inmuebles24/Lamudi pueden bloquear si hay demasiadas peticiones
- **Solución**: Agregar delays entre peticiones (2-3 segundos)

### **Headless Browser**

- Playwright requiere Chromium instalado
- **Solución**: Ejecutar en servidor con `playwright install chromium`

### **Errores de Geocodificación**

- Nominatim tiene límite de 1 request/segundo
- **Solución**: Cachear coordenadas conocidas

### **Manejo de Duplicados**

- Usar `ON CONFLICT IGNORE` en Supabase
- O comparar por título + precio antes de insertar

---

## 📧 Notificaciones

### **Email de Resumen**

Enviar email al completar:

```
Asunto: ✅ Scraping Mensual Completado

Resumen:
• Inmuebles24: 75 propiedades
• Lamudi: 70 propiedades
• Total insertadas: 145
• Ciudades: Querétaro, Guadalajara, Monterrey

Próxima ejecución: 1 de Noviembre, 2025
```

---

## ✅ Checklist de Implementación

- [ ] Python services instalados y funcionando
- [ ] Credenciales de Supabase configuradas
- [ ] Playwright instalado (`playwright install chromium`)
- [ ] Workflows n8n activos
- [ ] Schedule configurado (mensual)
- [ ] Notificaciones configuradas (opcional)
- [ ] Logs de ejecución monitoreados

---

**Versión**: 1.0  
**Fecha**: Octubre 2025  
**Autor**: IAgentek

