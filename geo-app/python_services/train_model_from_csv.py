# ================================================================
# ENTRENAMIENTO DE MODELO ML DESDE CSV
# ================================================================

import pandas as pd
from pathlib import Path
import sys
from loguru import logger

sys.path.append('.')
from ml_model.predictor import PlusvaliaPredictorModel
from config import DATA_DIR


def main():
    """
    Entrena el modelo ML con datos del CSV más reciente
    """
    logger.info("="*70)
    logger.info("ENTRENAMIENTO DE MODELO ML DESDE CSV")
    logger.info("="*70 + "\n")
    
    # Buscar el CSV más reciente
    csv_files = list(DATA_DIR.glob("synthetic_training_data_*.csv"))
    
    if not csv_files:
        logger.error("No se encontraron archivos CSV de entrenamiento")
        logger.info(f"Buscando en: {DATA_DIR}")
        return None
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Cargando datos desde: {latest_csv.name}")
    
    # Cargar datos
    df = pd.DataFrame(pd.read_csv(latest_csv))
    logger.success(f"Datos cargados: {len(df)} registros")
    
    # Estadísticas básicas
    logger.info(f"\nEstadisticas:")
    logger.info(f"   - Ciudades: {df['city'].nunique()}")
    logger.info(f"   - Precio promedio: ${df['price_mxn'].mean():,.0f} MXN")
    logger.info(f"   - Area promedio: {df['area_m2'].mean():,.0f} m2")
    logger.info(f"   - Precio/m2 promedio: ${df['price_m2'].mean():,.0f} MXN/m2")
    
    # Distribución por ciudad (Top 5)
    logger.info(f"\nTop 5 ciudades:")
    for city, count in df['city'].value_counts().head(5).items():
        logger.info(f"   - {city}: {count} propiedades")
    
    # Entrenar modelo
    logger.info("\n" + "-"*70)
    logger.info("ENTRENANDO MODELO ML")
    logger.info("-"*70 + "\n")
    
    model = PlusvaliaPredictorModel(model_version="2.0")
    
    try:
        metrics = model.train(df, target_col='price_m2', test_size=0.2)
        
        logger.success("\nENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        logger.info("\nMetricas del modelo:")
        logger.info(f"   - R2 (test): {metrics['test_r2']:.4f}")
        logger.info(f"   - MAE (test): ${metrics['test_mae']:,.0f} MXN/m2")
        logger.info(f"   - RMSE (test): ${metrics['test_rmse']:,.0f} MXN/m2")
        logger.info(f"   - Muestras: {metrics['n_samples']:,}")
        logger.info(f"   - Features: {metrics['n_features']}")
        
        # Pruebas de predicción
        logger.info("\n" + "="*70)
        logger.info("PRUEBAS DE PREDICCION")
        logger.info("="*70)
        
        # Prueba 1: Guadalajara
        logger.info("\nPRUEBA 1: Terreno en Guadalajara, Jalisco")
        pred1 = model.predict_price(
            lat=20.6597,
            lon=-103.3496,
            area_m2=500,
            city="Guadalajara",
            state="Jalisco"
        )
        logger.info(f"   - Ubicacion: Guadalajara, Jalisco")
        logger.info(f"   - Area: 500 m2")
        logger.info(f"   - Precio/m2: ${pred1['predicted_price_m2']:,.0f} MXN")
        logger.info(f"   - Precio total: ${pred1['predicted_total_price']:,.0f} MXN")
        logger.info(f"   - Score plusvalia: {pred1['plusvalia_score']:.1f}/100")
        logger.info(f"   - Potencial: {pred1['growth_potential']}")
        logger.info(f"   - Confianza: {pred1['confidence']:.1f}%")
        
        # Prueba 2: Zapopan
        logger.info("\nPRUEBA 2: Terreno en Zapopan, Jalisco")
        pred2 = model.predict_price(
            lat=20.7214,
            lon=-103.3918,
            area_m2=300,
            city="Zapopan",
            state="Jalisco"
        )
        logger.info(f"   - Ubicacion: Zapopan, Jalisco")
        logger.info(f"   - Area: 300 m2")
        logger.info(f"   - Precio/m2: ${pred2['predicted_price_m2']:,.0f} MXN")
        logger.info(f"   - Precio total: ${pred2['predicted_total_price']:,.0f} MXN")
        logger.info(f"   - Score plusvalia: {pred2['plusvalia_score']:.1f}/100")
        logger.info(f"   - Potencial: {pred2['growth_potential']}")
        
        # Prueba 3: Ciudad de México
        logger.info("\nPRUEBA 3: Terreno en Ciudad de Mexico")
        pred3 = model.predict_price(
            lat=19.4326,
            lon=-99.1332,
            area_m2=200,
            city="Ciudad de México",
            state="Ciudad de México"
        )
        logger.info(f"   - Ubicacion: Ciudad de Mexico")
        logger.info(f"   - Area: 200 m2")
        logger.info(f"   - Precio/m2: ${pred3['predicted_price_m2']:,.0f} MXN")
        logger.info(f"   - Precio total: ${pred3['predicted_total_price']:,.0f} MXN")
        logger.info(f"   - Score plusvalia: {pred3['plusvalia_score']:.1f}/100")
        logger.info(f"   - Potencial: {pred3['growth_potential']}")
        
        # Prueba 4: Monterrey
        logger.info("\nPRUEBA 4: Terreno en Monterrey, Nuevo Leon")
        pred4 = model.predict_price(
            lat=25.6866,
            lon=-100.3161,
            area_m2=400,
            city="Monterrey",
            state="Nuevo León"
        )
        logger.info(f"   - Ubicacion: Monterrey, Nuevo Leon")
        logger.info(f"   - Area: 400 m2")
        logger.info(f"   - Precio/m2: ${pred4['predicted_price_m2']:,.0f} MXN")
        logger.info(f"   - Precio total: ${pred4['predicted_total_price']:,.0f} MXN")
        logger.info(f"   - Score plusvalia: {pred4['plusvalia_score']:.1f}/100")
        logger.info(f"   - Potencial: {pred4['growth_potential']}")
        
        logger.info("\n" + "="*70)
        logger.success("ENTRENAMIENTO Y PRUEBAS COMPLETADAS")
        logger.info("="*70)
        logger.info("\nEl modelo esta listo para usar en la API!")
        logger.info("Los modelos estan guardados en: ml_model/models/")
        
        return model
        
    except (ValueError, KeyError, TypeError, RuntimeError) as e:
        logger.error(f"\nError durante el entrenamiento: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Ejecutar
    model = main()
    
    if model:
        logger.success("\n MODELO ML ENTRENADO EXITOSAMENTE!")
    else:
        logger.error("\n ERROR: No se pudo entrenar el modelo")

