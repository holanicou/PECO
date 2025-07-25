# -*- coding: utf-8 -*-
import argparse
from datetime import datetime
from services.data_manager import DataManager
from services.exceptions import PECOError
from services.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

def main(monto, categoria, desc):
    """
    Registra un nuevo gasto usando el DataManager service.
    """
    try:
        # Instantiate DataManager service
        data_manager = DataManager()
        
        # Register expense using service layer
        result = data_manager.register_expense(monto, categoria, desc)
        
        if result.success:
            fecha = datetime.now().strftime("%Y-%m-%d")
            print("\n[OK] Gasto registrado con exito!")
            print(f"   - Fecha: {fecha}")
            print(f"   - Categoria: {categoria}")
            print(f"   - Descripcion: {desc}")
            print(f"   - Monto: ${monto:,.2f} ARS")
            logger.info(f"Expense registered successfully: {categoria} - ${monto:,.2f}")
        else:
            print(f"\n[ERROR] {result.message}")
            logger.error(f"Failed to register expense: {result.message}")
            if result.error_code:
                print(f"   Codigo de error: {result.error_code}")

    except PECOError as e:
        print(f"\n[ERROR] {e.message}")
        if e.error_code:
            print(f"   Codigo de error: {e.error_code}")
        logger.error(f"PECO Error in expense registration: {e.message}", extra={'error_code': e.error_code})
    except Exception as e:
        print(f"\n[ERROR] Ocurrio un error inesperado: {e}")
        logger.error(f"Unexpected error in expense registration: {e}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Registra un nuevo gasto en el archivo CSV de tu proyecto PECO.",
        epilog="Ejemplo de uso: python registrar_gasto.py --monto 5000 --categoria Comida --desc \"Almuerzo de trabajo\""
    )
    parser.add_argument("-m", "--monto", type=float, required=True, help="El monto del gasto en ARS.")
    parser.add_argument("-c", "--categoria", type=str, required=True, help="La categoría del gasto.")
    parser.add_argument("-d", "--desc", type=str, required=True, help="Una descripción breve del gasto.")
    args = parser.parse_args()
    main(args.monto, args.categoria, args.desc)
