# ================================================================
# SUBIR DATOS A SUPABASE
# Este script sube los datos sintéticos generados a Supabase
# ================================================================

import pandas as pd
from pathlib import Path
import sys
from loguru import logger
from datetime import datetime

sys.path.append('.')
from config import DATA_DIR, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_COMPARABLES


def upload_csv_to_supabase(csv_file: Path):
    """
    Sube datos del CSV a Supabase
    """
    try:
        from supabase import create_client
        
        logger.info(f"Conectando a Supabase: {SUPABASE_URL}")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        logger.info(f"Cargando datos desde: {csv_file.name}")
        df = pd.read_csv(csv_file)
        logger.success(f"Datos cargados: {len(df)} registros")
        
        # Preparar datos para inserción - solo columnas que existen en Supabase
        # La tabla tiene: title, price_mxn, area_m2, address, city, state, lat, lon
        # price_m2 es calculado automáticamente, no se envía
        columns_to_keep = ['title', 'price_mxn', 'area_m2', 'address', 'city', 'state', 'lat', 'lon']
        df_clean = df[columns_to_keep].copy()
        
        records = df_clean.to_dict('records')
        saved_count = 0
        error_count = 0
        
        logger.info(f"Subiendo {len(records)} registros a Supabase...")
        logger.info(f"Tabla destino: {TABLE_COMPARABLES}")
        
        # Insertar por lotes de 50 registros
        batch_size = 50
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            try:
                # Insertar lote
                response = supabase.table(TABLE_COMPARABLES).insert(batch).execute()
                saved_count += len(batch)
                
                if batch_num % 10 == 0 or batch_num == total_batches:
                    logger.info(f"   Progreso: {saved_count}/{len(records)} registros ({saved_count*100//len(records)}%)")
                
            except Exception as e:  # Supabase client may raise various errors
                error_count += len(batch)
                error_msg = str(e)[:150]
                logger.warning(f"   Error en lote {batch_num}: {error_msg}")
        
        logger.success(f"\nRESULTADO:")
        logger.info(f"   - Registros exitosos: {saved_count}")
        logger.info(f"   - Registros con error: {error_count}")
        logger.info(f"   - Tasa de exito: {saved_count*100//len(records)}%")
        
        # Verificar datos en Supabase
        logger.info(f"\nVerificando datos en Supabase...")
        count_response = supabase.table(TABLE_COMPARABLES).select('id', count='exact').execute()
        total_in_db = count_response.count if hasattr(count_response, 'count') else 'N/A'
        logger.success(f"Total de registros en {TABLE_COMPARABLES}: {total_in_db}")
        
        return saved_count
        
    except (FileNotFoundError, IOError, ValueError, KeyError) as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """
    Función principal
    """
    logger.info("="*70)
    logger.info("SUBIR DATOS SINTETICOS A SUPABASE")
    logger.info("="*70 + "\n")
    
    # Buscar el CSV más reciente
    csv_files = list(DATA_DIR.glob("synthetic_training_data_*.csv"))
    
    if not csv_files:
        logger.error("No se encontraron archivos CSV de entrenamiento")
        logger.info(f"Buscando en: {DATA_DIR}")
        return False
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Archivo a subir: {latest_csv.name}")
    logger.info(f"Tamaño: {latest_csv.stat().st_size / 1024:.1f} KB")
    
    # Subir a Supabase
    saved_count = upload_csv_to_supabase(latest_csv)
    
    if saved_count > 0:
        logger.success("\n" + "="*70)
        logger.success("DATOS SUBIDOS EXITOSAMENTE A SUPABASE")
        logger.success("="*70)
        logger.info(f"\nAhora puedes:")
        logger.info(f"   1. Ver los datos en Supabase -> {TABLE_COMPARABLES}")
        logger.info(f"   2. Entrenar el modelo directamente desde Supabase")
        logger.info(f"   3. Usar la API para hacer predicciones")
        return True
    else:
        logger.error("\nNo se pudieron subir datos a Supabase")
        return False


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Ejecutar
    success = main()
    
    if success:
        logger.success("\n PROCESO COMPLETADO!")
    else:
        logger.error("\n ERROR EN EL PROCESO")

