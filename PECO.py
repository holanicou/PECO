# -*- coding: utf-8 -*-
import argparse
import subprocess
import sys

# Import SystemChecker for startup validation
from services.system_checker import SystemChecker
from services.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def ejecutar_script(script_name, args_adicionales=[]):
    """
    Función genérica para ejecutar los otros scripts de Python.
    """
    # sys.executable se asegura de que usemos el mismo Python que está ejecutando PECO.py
    comando = [sys.executable, script_name] + args_adicionales
    try:
        # Se ejecuta el subproceso forzando la codificación UTF-8 para la salida
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return resultado.stdout, resultado.stderr
    except FileNotFoundError:
        return f"[ERROR] No se encontro el script '{script_name}'.", ""
    except subprocess.CalledProcessError as e:
        return f"[ERROR] El script '{script_name}' termino con un error:\n{e.stdout}\n{e.stderr}", ""
    except Exception as e:
        return f"[ERROR] Ocurrio un error inesperado: {e}", ""

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

    stdout_output = ""
    stderr_output = ""

    if args.comando == "registrar":
        args_para_script = ["--monto", str(args.monto), "--categoria", args.categoria, "--desc", args.desc]
        stdout_output, stderr_output = ejecutar_script("registrar_gasto.py", args_para_script)
    
    elif args.comando == "invertir":
        # Lógica para llamar al nuevo script de inversiones
        args_para_script = ["--activo", args.activo, "--tipo", args.tipo, "--monto", str(args.monto)]
        stdout_output, stderr_output = ejecutar_script("registrar_inversion.py", args_para_script)

    elif args.comando == "generar":
        stdout_output, stderr_output = ejecutar_script("generar_resolucion.py")

    elif args.comando == "analizar":
        stdout_output, stderr_output = ejecutar_script("analisis_mensual.py")
    
    if stdout_output:
        print(stdout_output)
    if stderr_output:
        print(stderr_output)

