#!/usr/bin/env python3
"""Re-entrenar modelo con todos los datos y generar predicciones limpias"""
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

from loguru import logger
from supabase import create_client
import pandas as pd
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_COMPARABLES, TABLE_PREDICTIONS
from ml_model.predictor import PlusvaliaPredictorModel

def main():
    logger.info("="*70)
    logger.info("RE-ENTRENAR MODELO Y GENERAR PREDICCIONES COMPLETAS")
    logger.info("="*70)
    
    try:
        # 1. Conectar
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # 2. LIMPIAR PREDICCIONES ANTIGUAS
        logger.info("\nLimpiando predicciones antiguas...")
        supabase.table(TABLE_PREDICTIONS).delete().neq('id', 0).execute()
        logger.success("Predicciones antiguas eliminadas")
        
        # 3. Obtener TODAS las propiedades
        logger.info("\nObteniendo todas las propiedades...")
        response = supabase.table(TABLE_COMPARABLES).select('*').execute()
        df = pd.DataFrame(response.data)
        logger.info(f"Total propiedades: {len(df)}")
        
        # Calcular price_m2 si no viene
        if 'price_m2' not in df.columns:
            df['price_m2'] = df['price_mxn'] / df['area_m2']
        
        # 4. RE-ENTRENAR MODELO
        logger.info("\n" + "="*70)
        logger.info("FASE 1: RE-ENTRENANDO MODELO CON TODOS LOS DATOS")
        logger.info("="*70)
        
        model = PlusvaliaPredictorModel(model_version="4.0_completo")
        metrics = model.train(df, target_col='price_m2', test_size=0.2)
        
        logger.success("\nModelo entrenado exitosamente:")
        logger.info(f"  R² Score: {metrics['test_r2']:.4f}")
        logger.info(f"  MAE: ${metrics['test_mae']:,.0f} MXN/m²")
        logger.info(f"  RMSE: ${metrics['test_rmse']:,.0f} MXN/m²")
        logger.info(f"  Muestras entrenadas: {metrics['n_samples']}")
        logger.info(f"  Features utilizadas: {metrics['n_features']}")
        
        # Guardar modelo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = Path(__file__).parent / 'ml_model' / 'models' / f'plusvalia_model_v4.0_completo_{timestamp}.pkl'
        model.save_model(str(model_path))
        logger.success(f"Modelo con timestamp guardado: {model_path.name}")
        
        # Guardar versión principal
        main_path = Path(__file__).parent / 'ml_model' / 'models' / 'plusvalia_model_v4.0_completo.pkl'
        model.save_model(str(main_path))
        logger.success(f"Version principal guardada: plusvalia_model_v4.0_completo.pkl")
        
        # 5. GENERAR PREDICCIONES
        logger.info("\n" + "="*70)
        logger.info("FASE 2: GENERANDO PREDICCIONES PARA TODAS LAS PROPIEDADES")
        logger.info("="*70)
        
        predicciones = []
        
        for idx, row in df.iterrows():
            try:
                pred = model.predict_price(
                    lat=float(row['lat']),
                    lon=float(row['lon']),
                    area_m2=float(row['area_m2']),
                    city=row['city'],
                    state=row['state']
                )
                
                prediccion = {
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'city': row['city'],
                    'state': row['state'],
                    'predicted_price_m2': float(round(pred['predicted_price_m2'], 2)),
                    'plusvalia_score': float(round(pred['plusvalia_score'], 1)),
                    'growth_potential': pred['growth_potential'],
                    'risk_level': 'medio',
                    'model_version': 'v4.0_completo',
                    'model_confidence': float(round(pred['confidence'], 1))
                }
                
                predicciones.append(prediccion)
                
                if (idx + 1) % 500 == 0:
                    logger.info(f"  Progreso: {idx + 1}/{len(df)} predicciones generadas")
                    
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Error en propiedad {idx}: {str(e)[:80]}")
                continue
        
        logger.success(f"\nPredicciones generadas exitosamente: {len(predicciones)}")
        
        # 6. GUARDAR EN SUPABASE
        logger.info(f"\n" + "="*70)
        logger.info("FASE 3: GUARDANDO PREDICCIONES EN SUPABASE")
        logger.info("="*70)
        logger.info(f"Guardando {len(predicciones)} predicciones en lotes de 100...")
        
        saved = 0
        
        for i in range(0, len(predicciones), 100):
            batch = predicciones[i:i+100]
            try:
                supabase.table(TABLE_PREDICTIONS).insert(batch).execute()
                saved += len(batch)
                if (i + 100) % 1000 == 0 or saved == len(predicciones):
                    logger.info(f"  Guardadas {saved}/{len(predicciones)}")
            except Exception as e:  # Supabase client may raise various errors
                logger.error(f"Error guardando batch: {str(e)[:100]}")
        
        logger.success(f"\nTotal guardadas en BD: {saved} predicciones")
        
        # 7. Verificar
        logger.info("\nVerificando resultados en base de datos...")
        response = supabase.table(TABLE_PREDICTIONS).select('id', count='exact').execute()
        logger.success(f"Predicciones totales en BD: {response.count}")
        
        # Estadísticas por estado
        response_states = supabase.table(TABLE_PREDICTIONS).select('state').execute()
        if response_states.data:
            df_states = pd.DataFrame(response_states.data)
            states_count = df_states['state'].value_counts()
            logger.info("\nPredicciones por estado:")
            for state, count in states_count.items():
                logger.info(f"  {state}: {count}")
        
        logger.success("\n" + "="*70)
        logger.success("✅ PROCESO COMPLETADO EXITOSAMENTE")
        logger.success("="*70)
        logger.info(f"Modelo entrenado: {metrics['n_samples']} muestras")
        logger.info(f"R² Score: {metrics['test_r2']:.4f}")
        logger.info(f"Predicciones totales: {response.count}")
        logger.success("="*70)
        
        return 0
        
    except Exception as e:  # Intentional broad catch: top-level function handler
        logger.error(f"\nError fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
        colorize=False
    )
    
    exit_code = main()
    sys.exit(exit_code)

