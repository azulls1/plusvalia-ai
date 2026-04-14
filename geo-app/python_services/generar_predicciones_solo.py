#!/usr/bin/env python3
"""
Script para generar predicciones usando el modelo ya entrenado
"""

import sys
from pathlib import Path
from loguru import logger
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_COMPARABLES, TABLE_PREDICTIONS
from ml_model.predictor import PlusvaliaPredictorModel
import pandas as pd

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:8}</level> | <level>{message}</level>",
    level="INFO"
)

def generar_predicciones():
    """
    Genera predicciones para todas las propiedades en comparables
    """
    try:
        logger.info("🚀 Iniciando generación de predicciones...")
        
        # 1. Cargar modelo entrenado (usar el más reciente)
        logger.info("📦 Buscando modelo entrenado...")
        models_dir = Path(__file__).parent / 'ml_model' / 'models'
        
        # Buscar el modelo más reciente
        model_files = list(models_dir.glob('plusvalia_model_*.pkl'))
        if not model_files:
            logger.error(f"❌ No se encontró ningún modelo en: {models_dir}")
            logger.info("💡 Primero debes entrenar el modelo ejecutando: python pipeline_entrenamiento_completo.py")
            return
        
        # Usar el modelo más reciente (último creado)
        model_path = max(model_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"📦 Usando modelo: {model_path.name}")
        
        # Crear instancia y cargar el modelo
        model = PlusvaliaPredictorModel()
        model.load_model(model_path.name)
        
        # 2. Conectar a Supabase
        logger.info("🔗 Conectando a Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # 3. Obtener comparables
        logger.info("📥 Obteniendo propiedades de Supabase...")
        response = supabase.table(TABLE_COMPARABLES).select("*").limit(5000).execute()
        df = pd.DataFrame(response.data)
        
        if len(df) == 0:
            logger.warning("⚠️ No hay propiedades en la tabla comparables")
            return
        
        logger.success(f"✅ {len(df)} propiedades cargadas")
        
        # 4. Generar predicciones
        logger.info(f"🔮 Generando predicciones para {len(df)} propiedades...")
        
        predictions_batch = []
        saved_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                prediction = model.predict_price(
                    lat=row['lat'],
                    lon=row['lon'],
                    area_m2=row['area_m2'],
                    city=row['city'],
                    state=row['state']
                )
                
                # Columnas según schema de Supabase
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
                    try:
                        supabase.table(TABLE_PREDICTIONS).insert(predictions_batch).execute()
                        saved_count += len(predictions_batch)
                        predictions_batch = []
                        logger.info(f"  ✓ Guardadas {saved_count} predicciones...")
                    except Exception as e:  # Supabase client may raise various errors
                        logger.error(f"  ✗ Error guardando lote: {e}")
                        error_count += len(predictions_batch)
                        predictions_batch = []
                
            except (ValueError, KeyError, TypeError) as e:
                error_count += 1
                if error_count <= 5:  # Solo mostrar los primeros 5 errores
                    logger.warning(f"  ⚠️ Error fila {idx}: {str(e)[:100]}")
        
        # Guardar últimas predicciones
        if predictions_batch:
            try:
                supabase.table(TABLE_PREDICTIONS).insert(predictions_batch).execute()
                saved_count += len(predictions_batch)
            except Exception as e:  # Supabase client may raise various errors
                logger.error(f"Error guardando últimas predicciones: {e}")
                error_count += len(predictions_batch)
        
        # 5. Resumen
        logger.info("\n" + "="*70)
        logger.info("RESUMEN DE PREDICCIONES")
        logger.info("="*70)
        logger.success(f"✅ Predicciones guardadas: {saved_count}")
        if error_count > 0:
            logger.warning(f"⚠️ Errores: {error_count}")
        logger.info(f"📊 Total procesadas: {len(df)}")
        logger.info(f"🎯 Tasa de éxito: {(saved_count/len(df)*100):.1f}%")
        logger.info("="*70)
        
    except Exception as e:  # Intentional broad catch: top-level function handler
        logger.error(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    generar_predicciones()

