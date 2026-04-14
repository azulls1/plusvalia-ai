#!/usr/bin/env python3
"""
Script para corregir constraint y re-ejecutar fase 5
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv(Path(__file__).parent / '.env')

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_PREDICTIONS

def fix_constraint_via_api():
    """Corrige constraint usando direct SQL query"""
    print("Aplicando fix a growth_potential constraint...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    # Usar una query SQL directa a través de RPC si está disponible
    # O simplemente limpiar predicciones y regenerarlas
    
    try:
        # Verificar si hay predicciones guardadas
        result = supabase.table(TABLE_PREDICTIONS).select('id').limit(1).execute()
        print(f"Predicciones existentes: {len(result.data)}")
        
        # Necesitamos usar psycopg2 directo
        print("Nota: Necesitamos aplicar el fix manualmente en Supabase")
        print("Ejecuta este SQL en el editor SQL de Supabase:")
        print("""
ALTER TABLE public.ai_chat_predictions 
DROP CONSTRAINT IF EXISTS ai_chat_predictions_growth_potential_check;

ALTER TABLE public.ai_chat_predictions
ADD CONSTRAINT ai_chat_predictions_growth_potential_check 
CHECK (growth_potential IN ('bajo', 'medio', 'alto', 'muy_alto'));
        """)
        
        return False
        
    except Exception as e:  # Supabase client may raise various errors
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    fix_constraint_via_api()

