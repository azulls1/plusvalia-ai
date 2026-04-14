# 📋 Instrucciones para Configurar Supabase

## Orden de Ejecución de Scripts SQL

Ejecuta los scripts en el **SQL Editor de Supabase** en el siguiente orden:

### ✅ Paso 1: Crear Tablas
```sql
-- Ejecutar: 01_crear_tablas.sql
```
Crea las 3 tablas principales:
- `iainmobiliaria_comparables`
- `iainmobiliaria_amenities`
- `iainmobiliaria_grid_tiles`

**Tiempo estimado:** 5 segundos

---

### ✅ Paso 2: Crear Índices
```sql
-- Ejecutar: 02_indices.sql
```
Crea todos los índices necesarios para optimización de consultas geográficas y filtros.

**Tiempo estimado:** 10 segundos

---

### ✅ Paso 3: Configurar Políticas RLS
```sql
-- Ejecutar: 03_rls_policies.sql
```
Configura Row Level Security (RLS) con políticas de:
- ✅ Lectura pública (anon puede leer)
- ✅ Escritura restringida (solo authenticated y service_role)

**Tiempo estimado:** 15 segundos

---

### ✅ Paso 4: Crear Funciones Útiles
```sql
-- Ejecutar: 04_funciones_utiles.sql
```
Crea funciones PostgreSQL para:
- `rebuild_grid()` - Recalcular grilla de precios
- `get_statistics()` - Obtener estadísticas generales
- `clean_old_data()` - Limpiar datos antiguos
- `get_nearby_amenities()` - Buscar amenidades cercanas
- Triggers para actualizar `updated_at` automáticamente

**Tiempo estimado:** 20 segundos

---

### ✅ Paso 5: Verificar Todo
```sql
-- Ejecutar: 05_verificacion.sql
```
Verifica que todo esté correctamente configurado:
- Tablas creadas ✓
- Índices creados ✓
- Políticas RLS activas ✓
- Funciones disponibles ✓
- Triggers funcionando ✓

**Tiempo estimado:** 5 segundos

---

## 🔐 Configuración de Seguridad

### Credenciales que necesitas:

1. **Supabase URL**: `https://iagenteksupabase.iagentek.com.mx`
2. **Anon Key** (para el frontend): Ya está en `environment.ts`
3. **Service Role Key** (para N8N): **NO compartir públicamente**

### Permisos configurados:

| Tabla | Anon (Frontend) | Authenticated | Service Role (N8N) |
|-------|-----------------|---------------|-------------------|
| **Lectura** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Escritura** | ❌ No | ✅ Sí | ✅ Sí |
| **Actualización** | ❌ No | ✅ Sí | ✅ Sí |
| **Eliminación** | ❌ No | ✅ Sí | ✅ Sí |

---

## 🎯 Modo Desarrollo (OPCIONAL)

Si necesitas permisos más permisivos durante desarrollo, descomenta las políticas alternativas en el script `03_rls_policies.sql` (sección "ALTERNATIVA: POLÍTICAS MÁS PERMISIVAS").

**⚠️ ADVERTENCIA:** No uses políticas permisivas en producción.

---

## 📊 Uso de Funciones

### Reconstruir grilla de precios:
```sql
SELECT * FROM rebuild_grid(0.005);
```

### Obtener estadísticas:
```sql
SELECT * FROM get_statistics();
```

### Limpiar datos antiguos (>90 días):
```sql
SELECT * FROM clean_old_data(90);
```

### Buscar amenidades cercanas:
```sql
SELECT * FROM get_nearby_amenities(20.5, -100.4, 5.0, 'school');
```

---

## 🧪 Testing

Después de ejecutar todos los scripts, prueba:

1. **Insertar un registro de prueba:**
```sql
INSERT INTO iainmobiliaria_comparables 
  (title, price_mxn, area_m2, address, city, state, lat, lon)
VALUES 
  ('Prueba', 1000000, 100, 'Calle Ejemplo 123', 'Queretaro', 'Queretaro', 20.5888, -100.3899);
```

2. **Leer el registro:**
```sql
SELECT * FROM iainmobiliaria_comparables WHERE title = 'Prueba';
```

3. **Eliminar el registro de prueba:**
```sql
DELETE FROM iainmobiliaria_comparables WHERE title = 'Prueba';
```

---

## 🔄 Actualizar Environment Variables

Después de configurar Supabase, actualiza `environment.ts` si es necesario:

```typescript
export const environment = {
  production: false,
  supabaseUrl: "https://iagenteksupabase.iagentek.com.mx",
  supabaseAnonKey: "TU_ANON_KEY_AQUI",
  // ... resto de la configuración
};
```

---

## 📞 Soporte

Si tienes problemas durante la configuración:
1. Verifica los mensajes de error en SQL Editor
2. Ejecuta el script `05_verificacion.sql` para diagnóstico
3. Contacta: contacto@iagentek.com.mx

---

## ✅ Checklist Final

- [ ] Script 1 ejecutado (Tablas creadas)
- [ ] Script 2 ejecutado (Índices creados)
- [ ] Script 3 ejecutado (RLS configurado)
- [ ] Script 4 ejecutado (Funciones creadas)
- [ ] Script 5 ejecutado (Verificación exitosa)
- [ ] Prueba de inserción/lectura exitosa
- [ ] Variables de entorno actualizadas en Angular

---

**¡Listo! Ahora puedes configurar los webhooks de N8N.**

