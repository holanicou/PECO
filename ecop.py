# -*- coding: utf-8 -*-
import argparse
import subprocess
import sys

def ejecutar_script(script_name, args_adicionales=[]):
    """
    Función genérica para ejecutar los otros scripts de Python.
    """
    # sys.executable se asegura de que usemos el mismo Python que está ejecutando ecop.py
    comando = [sys.executable, script_name] + args_adicionales
    try:
        # Se ejecuta el subproceso forzando la codificación UTF-8 para la salida
        subprocess.run(comando, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    except FileNotFoundError:
        # CAMBIO: Se reemplazó el emoji ❌ por texto simple.
        print(f"[ERROR] No se encontro el script '{script_name}'.")
    except subprocess.CalledProcessError as e:
        # CAMBIO: Se reemplazó el emoji ❌ por texto simple.
        print(f"[ERROR] El script '{script_name}' termino con un error:")
        print(e.stdout)
        print(e.stderr)
    except Exception as e:
        print(f"[ERROR] Ocurrio un error inesperado: {e}")

# --- CONFIGURACIÓN DEL PARSER PRINCIPAL ---
parser = argparse.ArgumentParser(
    prog="ecop",
    description="Herramienta central para gestionar tu proyecto de Economía Personal (ECOP).",
    epilog="Usa 'ecop <comando> --help' para obtener ayuda sobre un comando específico."
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
    args = parser.parse_args()

    if args.comando == "registrar":
        args_para_script = ["--monto", str(args.monto), "--categoria", args.categoria, "--desc", args.desc]
        ejecutar_script("registrar_gasto.py", args_para_script)
    
    elif args.comando == "invertir":
        # Lógica para llamar al nuevo script de inversiones
        args_para_script = ["--activo", args.activo, "--tipo", args.tipo, "--monto", str(args.monto)]
        ejecutar_script("registrar_inversion.py", args_para_script)

    elif args.comando == "generar":
        ejecutar_script("generar_resolucion.py")

    elif args.comando == "analizar":
        ejecutar_script("analisis_mensual.py")
