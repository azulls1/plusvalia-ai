#!/usr/bin/env python3
"""
Script temporal para corregir el constraint de growth_potential
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(Path(__file__).parent / '.env')

from config import DATABASE_URL
import psycopg2

def fix_constraint():
    """Corrige el constraint de growth_potential"""
    sql = """
    -- Eliminar constraint antiguo
    ALTER TABLE public.ai_chat_predictions 
    DROP CONSTRAINT IF EXISTS ai_chat_predictions_growth_potential_check;

    -- Agregar constraint nuevo con 'muy_alto'
    ALTER TABLE public.ai_chat_predictions
    ADD CONSTRAINT ai_chat_predictions_growth_potential_check 
    CHECK (growth_potential IN ('bajo', 'medio', 'alto', 'muy_alto'));
    """
    
    print("Aplicando fix al constraint...")
    
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()
        
        print("Constraint corregido exitosamente")
        return True
        
    except (psycopg2.Error, OSError, ConnectionError) as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_constraint()
    sys.exit(0 if success else 1)

