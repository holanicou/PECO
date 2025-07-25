# -*- coding: utf-8 -*-
import argparse
from datetime import datetime
from services.data_manager import DataManager
from services.exceptions import PECOError
from services.logging_config import setup_logging

# Setup logging
logger = setup_logging("INFO")

def main(activo, tipo, monto):
    """
    Registra una nueva inversión usando el DataManager service.
    """
    try:
        # Instantiate DataManager service
        data_manager = DataManager()
        
        # Register investment using service layer
        result = data_manager.register_investment(activo, tipo, monto)
        
        if result.success:
            fecha = datetime.now().strftime("%Y-%m-%d")
            print("\n[OK] Inversion registrada con exito!")
            print(f"   - Fecha: {fecha}")
            print(f"   - Activo: {activo}")
            print(f"   - Tipo: {tipo}")
            print(f"   - Monto: ${monto:,.2f} ARS")
            logger.info(f"Investment registered successfully: {activo} - {tipo} - ${monto:,.2f}")
        else:
            print(f"\n[ERROR] {result.message}")
            logger.error(f"Failed to register investment: {result.message}")
            if result.error_code:
                print(f"   Codigo de error: {result.error_code}")

    except PECOError as e:
        print(f"\n[ERROR] {e.message}")
        if e.error_code:
            print(f"   Codigo de error: {e.error_code}")
        logger.error(f"PECO Error in investment registration: {e.message}", extra={'error_code': e.error_code})
    except Exception as e:
        print(f"\n[ERROR] Ocurrio un error inesperado: {e}")
        logger.error(f"Unexpected error in investment registration: {e}", exc_info=True)

if __name__ == "__main__":
    # --- SETUP DEL PARSER DE ARGUMENTOS ---
    parser = argparse.ArgumentParser(description="Registra una nueva inversion en el archivo de inversiones.")
    parser.add_argument("-a", "--activo", type=str, required=True, help="El ticker o nombre del activo. Ej: SPY, AAPL")
    parser.add_argument("-t", "--tipo", type=str, required=True, choices=['Compra', 'Venta'], help="El tipo de operacion: Compra o Venta.")
    parser.add_argument("-m", "--monto", type=float, required=True, help="El monto de la operacion en ARS.")
    args = parser.parse_args()
    
    main(args.activo, args.tipo, args.monto)
