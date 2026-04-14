# ✅ Checklist de Configuración Completa

Este checklist te ayudará a completar la configuración del proyecto paso a paso.

---

## 📦 FASE 1: Instalación Local (COMPLETO ✅)

- [x] Node.js instalado (v22.14.0+)
- [x] Estructura de proyecto creada
- [x] Archivos de configuración generados
- [x] Código fuente con comentarios inline
- [x] Documentación completa

**Estado:** ✅ COMPLETADO

---

## 🗄️ FASE 2: Configuración de Supabase

### 2.1 Crear Proyecto en Supabase

- [ ] Ir a https://supabase.com
- [ ] Crear cuenta o iniciar sesión
- [ ] Crear nuevo proyecto
- [ ] Anotar URL y claves

### 2.2 Crear Tablas

Ejecutar en el SQL Editor de Supabase:

#### Tabla: `comparables`
```sql
CREATE TABLE comparables (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  price_mxn NUMERIC NOT NULL,
  area_m2 NUMERIC NOT NULL,
  price_m2 NUMERIC GENERATED ALWAYS AS (price_mxn / NULLIF(area_m2, 0)) STORED,
  address TEXT,
  city TEXT,
  state TEXT,
  lat FLOAT8,
  lon FLOAT8,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Tabla: `amenities`
```sql
CREATE TABLE amenities (
  id BIGSERIAL PRIMARY KEY,
  osm_id BIGINT UNIQUE NOT NULL,
  name TEXT,
  amenity_type TEXT NOT NULL,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  city TEXT,
  state TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Tabla: `grid_tiles`
```sql
CREATE TABLE grid_tiles (
  id BIGSERIAL PRIMARY KEY,
  lat FLOAT8 NOT NULL,
  lon FLOAT8 NOT NULL,
  price_m2_avg FLOAT8 NOT NULL,
  count_properties INT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Checklist:**
- [ ] Tabla `comparables` creada
- [ ] Tabla `amenities` creada
- [ ] Tabla `grid_tiles` creada

### 2.3 Configurar RLS (Row Level Security)

```sql
-- Habilitar RLS en todas las tablas
ALTER TABLE comparables ENABLE ROW LEVEL SECURITY;
ALTER TABLE amenities ENABLE ROW LEVEL SECURITY;
ALTER TABLE grid_tiles ENABLE ROW LEVEL SECURITY;

-- Políticas de lectura pública (anon key)
CREATE POLICY "Lectura pública comparables" ON comparables FOR SELECT TO anon USING (true);
CREATE POLICY "Lectura pública amenities" ON amenities FOR SELECT TO anon USING (true);
CREATE POLICY "Lectura pública grid_tiles" ON grid_tiles FOR SELECT TO anon USING (true);
```

**Checklist:**
- [ ] RLS habilitado en las 3 tablas
- [ ] Políticas de lectura pública creadas

### 2.4 Crear Índices

```sql
-- Índices geográficos
CREATE INDEX idx_comparables_coords ON comparables(lat, lon);
CREATE INDEX idx_amenities_coords ON amenities(lat, lon);
CREATE INDEX idx_grid_tiles_coords ON grid_tiles(lat, lon);

-- Índices adicionales
CREATE INDEX idx_amenities_type ON amenities(amenity_type);
CREATE INDEX idx_amenities_city_state ON amenities(city, state);
CREATE UNIQUE INDEX idx_amenities_osm_id ON amenities(osm_id);
```

**Checklist:**
- [ ] Índices creados

### 2.5 Actualizar Variables de Entorno

Editar `app/src/environments/environment.ts` y `environment.prod.ts`:

```typescript
supabaseUrl: "TU_URL_DE_SUPABASE",
supabaseAnonKey: "TU_ANON_KEY_DE_SUPABASE",
```

**Checklist:**
- [ ] URLs actualizadas en `environment.ts`
- [ ] URLs actualizadas en `environment.prod.ts`

**Estado FASE 2:** ⏳ PENDIENTE

---

## 🔗 FASE 3: Configuración de n8n

### 3.1 Instalar n8n

```bash
# Opción 1: npm (recomendado para desarrollo)
npm install -g n8n

# Opción 2: Docker (recomendado para producción)
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

**Checklist:**
- [ ] n8n instalado
- [ ] n8n corriendo en puerto 5678 (o configurado)

### 3.2 Crear Workflows

Ver `docs/N8N_WEBHOOKS.md` para configuración detallada.

#### Workflow 1: Ingesta de CSV (`/ingest-csv`)

**Nodos necesarios:**
1. Webhook (ruta: `/ingest-csv`, método: POST)
2. Binary File Processor (parsear CSV)
3. Loop (iterar cada fila)
4. HTTP Request (Nominatim para geocodificar)
5. Set (calcular price_m2)
6. Supabase (insertar en `comparables`)
7. Respond to Webhook

**Checklist:**
- [ ] Workflow creado
- [ ] Webhook activado
- [ ] Service role key de Supabase configurada
- [ ] Probado con `data/samples/comparables_demo.csv`

#### Workflow 2: Extracción OSM (`/osm-amenities`)

**Nodos necesarios:**
1. Webhook (ruta: `/osm-amenities`, método: POST)
2. HTTP Request (Nominatim para bbox de ciudad)
3. Code (construir query Overpass)
4. HTTP Request (Overpass API)
5. Loop (iterar resultados)
6. Supabase (upsert en `amenities`)
7. Respond to Webhook

**Checklist:**
- [ ] Workflow creado
- [ ] Webhook activado
- [ ] Probado con ciudad "Queretaro"

#### Workflow 3: Reconstrucción de Grilla (`/grid-build`)

**Nodos necesarios:**
1. Webhook (ruta: `/grid-build`, método: POST)
2. Supabase (obtener todos los comparables)
3. Code (generar grilla y calcular promedios)
4. Supabase (limpiar `grid_tiles`)
5. Supabase (insertar nuevos tiles en batch)
6. Respond to Webhook

**Checklist:**
- [ ] Workflow creado
- [ ] Webhook activado
- [ ] Probado

### 3.3 Configurar CORS en n8n

Si frontend y n8n están en dominios diferentes:

```json
{
  "security": {
    "cors": {
      "enabled": true,
      "origins": [
        "http://localhost:4200",
        "https://tu-dominio-hostinger.com"
      ]
    }
  }
}
```

**Checklist:**
- [ ] CORS configurado

### 3.4 Actualizar Variables de Entorno

Editar `app/src/environments/environment.ts` y `environment.prod.ts`:

```typescript
n8nBase: "https://tu-url-de-n8n.com",
```

**Checklist:**
- [ ] URLs actualizadas

**Estado FASE 3:** ⏳ PENDIENTE

---

## 🚀 FASE 4: Pruebas Locales

### 4.1 Instalar Dependencias

```bash
cd geo-app/app
npm install
```

**Checklist:**
- [ ] Dependencias instaladas sin errores

### 4.2 Ejecutar en Desarrollo

```bash
npm start
```

**Checklist:**
- [ ] Aplicación inicia en http://localhost:4200
- [ ] Mapa se carga correctamente
- [ ] Panel de controles visible
- [ ] Sin errores en consola del navegador

### 4.3 Probar Funcionalidades

**Subir CSV:**
- [ ] Seleccionar `data/samples/comparables_demo.csv`
- [ ] Click en "Cargar Comparables"
- [ ] Verificar mensaje de éxito
- [ ] Verificar datos en Supabase tabla `comparables`

**Recalcular Grilla:**
- [ ] Click en "Recalcular Grilla"
- [ ] Confirmar acción
- [ ] Esperar mensaje de éxito
- [ ] Verificar heatmap actualizado
- [ ] Verificar datos en Supabase tabla `grid_tiles`

**Extraer OSM:**
- [ ] Ingresar ciudad: "Queretaro"
- [ ] Ingresar estado: "Queretaro"
- [ ] Seleccionar tipos (ej: school, hospital)
- [ ] Click en "Extraer OSM (Ciudad)"
- [ ] Esperar mensaje de éxito
- [ ] Verificar marcadores en el mapa
- [ ] Verificar datos en Supabase tabla `amenities`

**Aplicar Filtros:**
- [ ] Configurar filtros (ciudad, precio, tipos)
- [ ] Click en "Aplicar Filtros"
- [ ] Verificar mapa actualizado con datos filtrados

**Estado FASE 4:** ⏳ PENDIENTE

---

## 🌐 FASE 5: Despliegue en Hostinger

### 5.1 Build de Producción

```bash
cd geo-app/app
npm run build
```

**Checklist:**
- [ ] Build completado sin errores
- [ ] Carpeta `dist/app` generada

### 5.2 Configurar Variables de Producción

Verificar `app/src/environments/environment.prod.ts`:

```typescript
production: true,
supabaseUrl: "URL_REAL_DE_SUPABASE",
supabaseAnonKey: "ANON_KEY_REAL",
n8nBase: "URL_REAL_DE_N8N",
```

**Checklist:**
- [ ] URLs de producción configuradas

### 5.3 Subir a Hostinger

**Método: File Manager**
1. Acceder a cPanel de Hostinger
2. Ir a File Manager
3. Navegar a `public_html/`
4. Subir TODO el contenido de `dist/app/`
5. Subir `.htaccess` (importante para SPA routing)

**Método: FTP**
```bash
# Usar cliente FTP (FileZilla, WinSCP, etc.)
# Conectar con credenciales de Hostinger
# Subir contenido de dist/app/ a public_html/
```

**Checklist:**
- [ ] Archivos subidos a Hostinger
- [ ] `.htaccess` subido
- [ ] Permisos correctos (755 para directorios, 644 para archivos)

### 5.4 Verificar Despliegue

**Checklist:**
- [ ] Sitio accesible en navegador
- [ ] Mapa se carga correctamente
- [ ] Sin errores 404 al navegar
- [ ] Funcionalidades probadas (subir CSV, filtros, etc.)
- [ ] Verificar en múltiples navegadores

**Estado FASE 5:** ⏳ PENDIENTE

---

## 🔒 FASE 6: Seguridad y Optimización

### 6.1 Seguridad

**Checklist:**
- [ ] Verificar que SOLO `anon key` está en el frontend
- [ ] Verificar que `service_role key` SOLO está en n8n
- [ ] RLS habilitado en todas las tablas
- [ ] HTTPS habilitado en producción
- [ ] CORS configurado correctamente

### 6.2 Optimización

**Checklist:**
- [ ] Caché configurado en `.htaccess`
- [ ] GZIP activado
- [ ] Imágenes optimizadas
- [ ] Índices en base de datos creados

### 6.3 Monitoreo

**Checklist:**
- [ ] Configurar alertas en Supabase (si disponible)
- [ ] Monitorear logs de n8n
- [ ] Verificar rendimiento del mapa con muchos datos

**Estado FASE 6:** ⏳ PENDIENTE

---

## 📊 Resumen de Estado

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Instalación Local | ✅ COMPLETO |
| 2 | Configuración Supabase | ⏳ PENDIENTE |
| 3 | Configuración n8n | ⏳ PENDIENTE |
| 4 | Pruebas Locales | ⏳ PENDIENTE |
| 5 | Despliegue Hostinger | ⏳ PENDIENTE |
| 6 | Seguridad y Optimización | ⏳ PENDIENTE |

---

## 📚 Recursos Adicionales

- **Supabase Docs:** https://supabase.com/docs
- **n8n Docs:** https://docs.n8n.io
- **Leaflet Docs:** https://leafletjs.com
- **Angular Docs:** https://angular.io/docs
- **Tailwind Docs:** https://tailwindcss.com/docs

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisar consola del navegador (F12)
2. Revisar logs de n8n
3. Verificar datos en Supabase
4. Consultar documentación en `docs/`

📧 **Contacto:** contacto@iagentek.com.mx

---

**¡Éxito con tu proyecto! 🎉**

