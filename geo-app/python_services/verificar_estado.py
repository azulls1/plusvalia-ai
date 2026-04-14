#!/usr/bin/env python3
"""Verificar estado actual del sistema"""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

try:
    from supabase import create_client
    import os
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Variables de entorno no configuradas")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("="*60)
    print("ESTADO ACTUAL DEL SISTEMA")
    print("="*60)
    
    # Propiedades
    result = supabase.table('iainmobiliaria_comparables').select('state', count='exact').execute()
    from collections import Counter
    states = Counter([r['state'] for r in result.data])
    
    print(f"\nPropiedades: {result.count}")
    print(f"Estados unicos: {len(states)}")
    print(f"\nEstados con datos:")
    for state, count in sorted(states.items()):
        print(f"  - {state}: {count} propiedades")
    
    # Amenities
    result = supabase.table('iainmobiliaria_amenities').select('*', count='exact').execute()
    print(f"\nAmenities: {result.count}")
    
    # Grid tiles
    result = supabase.table('iainmobiliaria_grid_tiles').select('*', count='exact').execute()
    print(f"Grid tiles: {result.count}")
    
    # INEGI data
    result = supabase.table('iainmobiliaria_inegi_data').select('*', count='exact').execute()
    print(f"INEGI data: {result.count}")
    
    # Predicciones
    result = supabase.table('iainmobiliaria_predictions').select('*', count='exact').execute()
    print(f"Predicciones: {result.count}")
    
    print("="*60)
    
except Exception as e:  # Intentional broad catch: top-level script handler
    print(f"Error: {e}")
    sys.exit(1)

