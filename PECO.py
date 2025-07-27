# -*- coding: utf-8 -*-
import argparse
import sys

# Import SystemChecker for startup validation
from services.system_checker import SystemChecker
from services.logging_config import get_logger

# Direct imports for CLI commands (replacing subprocess calls)
from analisis_mensual import main as analisis_mensual_main
from generar_resolucion import generar_resolucion
from services.data_manager import DataManager
from services.exceptions import PECOError
from datetime import datetime

# Initialize logger
logger = get_logger(__name__)

def registrar_gasto_main(monto, categoria, desc):
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

def registrar_inversion_main(activo, tipo, monto):
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

# --- CONFIGURACIÓN DEL PARSER PRINCIPAL ---
parser = argparse.ArgumentParser(
    prog="peco",
    description="Herramienta central para gestionar tu proyecto de Economía Personal (PECO).",
    epilog="Usa 'peco <comando> --help' para obtener ayuda sobre un comando específico."
)

# Creamos los subparsers para cada comando
subparsers = parser.add_subparsers(dest="comando", required=True, help="Comandos disponibles")

# --- COMANDO: registrar ---
parser_registrar = subparsers.add_parser("registrar", help="Registra un nuevo gasto en el CSV.")
parser_registrar.add_argument("-m", "--monto", type=float, required=True, help="Monto del gasto.")
parser_registrar.add_argument("-c", "--categoria", type=str, required=True, help="Categoría del gasto.")
parser_registrar.add_argument("-d", "--desc", type=str, required=True, help="Descripción del gasto.")

# --- NUEVO COMANDO: invertir ---
parser_invertir = subparsers.add_parser("invertir", help="Registra una nueva inversion en el XLSX.")
parser_invertir.add_argument("-a", "--activo", type=str, required=True, help="Ticker del activo. Ej: SPY")
parser_invertir.add_argument("-t", "--tipo", type=str, required=True, choices=['Compra', 'Venta'], help="Tipo de operacion.")
parser_invertir.add_argument("-m", "--monto", type=float, required=True, help="Monto de la operacion.")

# --- COMANDO: generar ---
parser_generar = subparsers.add_parser("generar", help="Genera la resolución en PDF del mes actual.")

# --- COMANDO: analizar ---
parser_analizar = subparsers.add_parser("analizar", help="Analiza los gastos del mes y genera un reporte.")

# --- LÓGICA PRINCIPAL ---
if __name__ == "__main__":
    # Perform startup system validation
    logger.info("Starting PECO CLI application")
    system_checker = SystemChecker()
    
    logger.info("Performing startup system validation...")
    startup_result = system_checker.validate_startup_requirements()
    
    if not startup_result.success:
        logger.warning("System validation found issues during startup:")
        if startup_result.missing_dependencies:
            logger.warning(f"Missing dependencies: {startup_result.missing_dependencies}")
            print("[WARNING] Missing system dependencies detected:")
            for dep in startup_result.missing_dependencies:
                print(f"  - {dep}")
                if startup_result.installation_instructions and dep in startup_result.installation_instructions:
                    print(f"    Installation: {startup_result.installation_instructions[dep]}")
            print("\nSome features may not work properly until dependencies are installed.")
            print("The application will continue, but PDF generation may fail if pdflatex is missing.\n")
        else:
            logger.warning(f"Configuration issues: {startup_result.message}")
            print(f"[WARNING] Configuration issues detected: {startup_result.message}")
            print("The application will continue but some features may not work properly.\n")
    else:
        logger.info("All system dependencies validated successfully")
    
    args = parser.parse_args()

    try:
        if args.comando == "registrar":
            # Call registrar_gasto main function directly
            logger.info(f"Executing registrar command: monto={args.monto}, categoria={args.categoria}, desc={args.desc}")
            registrar_gasto_main(args.monto, args.categoria, args.desc)
        
        elif args.comando == "invertir":
            # Call registrar_inversion main function directly
            logger.info(f"Executing invertir command: activo={args.activo}, tipo={args.tipo}, monto={args.monto}")
            registrar_inversion_main(args.activo, args.tipo, args.monto)

        elif args.comando == "generar":
            # Call generar_resolucion function directly
            logger.info("Executing generar command")
            generar_resolucion()

        elif args.comando == "analizar":
            # Call analisis_mensual main function directly
            logger.info("Executing analizar command")
            analisis_mensual_main()
            
    except KeyboardInterrupt:
        logger.info("Command execution interrupted by user")
        print("\n[INFO] Operación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing command '{args.comando}': {e}", exc_info=True)
        print(f"\n[ERROR] Error ejecutando comando '{args.comando}': {e}")
        sys.exit(1)

