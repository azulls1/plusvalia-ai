#!/usr/bin/env python3
"""
Generar predicciones guardándolas directamente en iainmobiliaria_predictions
sin pasar por ai_chat_predictions (que tiene el constraint problemático)
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv(Path(__file__).parent / '.env')

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_COMPARABLES, TABLE_PREDICTIONS
from supabase import create_client
from ml_model.predictor import PlusvaliaPredictorModel
from loguru import logger

def main():
    """Genera predicciones guardándolas en la tabla correcta"""
    logger.info("Cargando modelo...")
    
    try:
        # Cargar modelo entrenado (el más reciente)
        model_dir = Path(__file__).parent / 'ml_model' / 'models'
        model_files = list(model_dir.glob('plusvalia_model_v4.0_32_states*.pkl'))
        
        if not model_files:
            logger.error("No se encontró el modelo entrenado.")
            return 1
        
        model_path = max(model_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Usando modelo: {model_path.name}")
        
        model = PlusvaliaPredictorModel(model_version="4.0_32_states")
        model.load_model(str(model_path))
        logger.info(f"Modelo cargado: versión {model.model_version}")
        
        # Conectar a Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Obtener propiedades
        logger.info("Obteniendo propiedades desde Supabase...")
        response = supabase.table(TABLE_COMPARABLES).select('*').execute()
        df = pd.DataFrame(response.data)
        
        logger.info(f"Total propiedades: {len(df)}")
        
        # Generar predicciones
        predictions_batch = []
        saved_count = 0
        
        logger.info("Generando predicciones...")
        
        for idx, row in df.iterrows():
            try:
                prediction = model.predict_price(
                    lat=row['lat'], lon=row['lon'],
                    area_m2=row['area_m2'],
                    city=row['city'], state=row['state']
                )
                
                pred_record = {
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'city': row['city'],
                    'state': row['state'],
                    'predicted_price_m2': float(prediction['predicted_price_m2']),
                    'plusvalia_score': float(prediction['plusvalia_score']),
                    'growth_potential': prediction['growth_potential'],
                    'risk_level': 'medio',
                    'current_price_m2': float(row.get('price_m2', 0)),
                    'model_version': prediction['model_version'],
                    'model_confidence': float(prediction['confidence'])
                }
                
                predictions_batch.append(pred_record)
                
                # Guardar en lotes de 100
                if len(predictions_batch) >= 100:
                    supabase.table(TABLE_PREDICTIONS).insert(predictions_batch).execute()
                    saved_count += len(predictions_batch)
                    logger.info(f"Guardadas {saved_count} predicciones...")
                    predictions_batch = []
                    
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Error en fila {idx}: {str(e)[:100]}")
        
        # Guardar último lote
        if predictions_batch:
            supabase.table(TABLE_PREDICTIONS).insert(predictions_batch).execute()
            saved_count += len(predictions_batch)
        
        logger.success(f"Total predicciones guardadas: {saved_count}")
        
    except Exception as e:  # Intentional broad catch: top-level function handler
        logger.error(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<level>{level: <8}</level> | {message}")
    
    sys.exit(main())

