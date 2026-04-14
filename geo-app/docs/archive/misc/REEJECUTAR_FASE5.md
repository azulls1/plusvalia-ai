# 🎯 RE-EJECUTAR FASE 5 DESPUÉS DEL FIX

## ⚠️ PROBLEMA IDENTIFICADO

El pipeline falló en la Fase 5 porque el modelo genera `growth_potential = 'muy_alto'` pero la tabla `ai_chat_predictions` solo acepta `'bajo', 'medio', 'alto'`.

## ✅ SOLUCIÓN

### Paso 1: Aplicar Fix en Supabase

**Ve a:** https://iagenteksupabase.iagentek.com.mx/project/default/editor

**Ejecuta este SQL:**

```sql
-- Eliminar constraint antiguo
ALTER TABLE public.ai_chat_predictions 
DROP CONSTRAINT IF EXISTS ai_chat_predictions_growth_potential_check;

-- Agregar constraint nuevo con 'muy_alto'
ALTER TABLE public.ai_chat_predictions
ADD CONSTRAINT ai_chat_predictions_growth_potential_check 
CHECK (growth_potential IN ('bajo', 'medio', 'alto', 'muy_alto'));
```

**Luego haz clic en "RUN".**

### Paso 2: Verificar que el fix se aplicó

```sql
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conname = 'ai_chat_predictions_growth_potential_check';
```

**Deberías ver:** `(growth_potential IN ('bajo'::text, 'medio'::text, 'alto'::text, 'muy_alto'::text))`

### Paso 3: Re-ejecutar solo la Fase 5

```bash
cd geo-app/python_services
python pipeline_32_states_mexico.py --solo-fase5
```

O si no tienes ese flag, simplemente ejecuta todo de nuevo:

```bash
python pipeline_32_states_mexico.py
```

## 📊 ESTADO ACTUAL

✅ **Fase 1:** 2,800 propiedades generadas
✅ **Fase 2:** Scraping completado (sin amenities por limitación OSM)
✅ **Fase 3:** 134 grid tiles generados
✅ **Fase 4:** Modelo entrenado con 800 muestras
❌ **Fase 5:** Falla por constraint

## 🚀 DESPUÉS DEL FIX

- El pipeline debería completar exitosamente
- Se generarán todas las predicciones
- Todo quedará guardado en Supabase

