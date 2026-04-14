-- ================================================================
-- SCRIPT 16: CORREGIR CONSTRAINT GROWTH_POTENTIAL
-- ================================================================
-- El modelo ML genera 'muy_alto' pero la tabla ai_chat_predictions
-- solo acepta 'bajo', 'medio', 'alto'. Necesitamos agregar 'muy_alto'
-- ================================================================

-- Eliminar constraint antiguo
ALTER TABLE public.ai_chat_predictions 
DROP CONSTRAINT IF EXISTS ai_chat_predictions_growth_potential_check;

-- Agregar constraint nuevo con 'muy_alto'
ALTER TABLE public.ai_chat_predictions
ADD CONSTRAINT ai_chat_predictions_growth_potential_check 
CHECK (growth_potential IN ('bajo', 'medio', 'alto', 'muy_alto'));

-- Verificación
SELECT 'Constraint growth_potential actualizado correctamente' AS status;

