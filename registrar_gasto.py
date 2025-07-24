# -*- coding: utf-8 -*-
import csv
from datetime import datetime
import os
import argparse

# --- CONFIGURACIÓN ---
NOMBRE_CARPETA_TRACKERS = "03_Trackers"
NOMBRE_ARCHIVO_CSV = "gastos_mensuales.csv"
RUTA_CSV = os.path.join(NOMBRE_CARPETA_TRACKERS, NOMBRE_ARCHIVO_CSV)

# --- SETUP DEL PARSER DE ARGUMENTOS ---
parser = argparse.ArgumentParser(
    description="Registra un nuevo gasto en el archivo CSV de tu proyecto ECOP.",
    epilog="Ejemplo de uso: python registrar_gasto.py --monto 5000 --categoria Comida --desc \"Almuerzo de trabajo\""
)
parser.add_argument("-m", "--monto", type=float, required=True, help="El monto del gasto en ARS.")
parser.add_argument("-c", "--categoria", type=str, required=True, help="La categoría del gasto.")
parser.add_argument("-d", "--desc", type=str, required=True, help="Una descripción breve del gasto.")
args = parser.parse_args()

# --- LÓGICA PRINCIPAL ---
try:
    if not os.path.exists(NOMBRE_CARPETA_TRACKERS):
        os.makedirs(NOMBRE_CARPETA_TRACKERS)
    
    archivo_nuevo = not os.path.isfile(RUTA_CSV)
    if archivo_nuevo:
        with open(RUTA_CSV, "w", newline="", encoding="utf-8") as archivo:
            escritor_csv = csv.writer(archivo)
            escritor_csv.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])

    fecha = datetime.now().strftime("%Y-%m-%d")
    nueva_fila = [fecha, args.categoria, args.desc, args.monto]

    with open(RUTA_CSV, "a", newline="", encoding="utf-8") as archivo:
        escritor_csv = csv.writer(archivo)
        escritor_csv.writerow(nueva_fila)

    # CAMBIO: Se reemplazó el emoji ✅ por texto simple para evitar errores de codificación.
    print("\n[OK] Gasto registrado con exito!")
    print(f"   - Fecha: {fecha}")
    print(f"   - Categoria: {args.categoria}")
    print(f"   - Descripcion: {args.desc}")
    print(f"   - Monto: ${args.monto:,.2f} ARS")

except Exception as e:
    # CAMBIO: Se reemplazó el emoji ❌ por texto simple.
    print(f"\n[ERROR] Ocurrio un error inesperado: {e}")
