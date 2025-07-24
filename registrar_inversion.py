# -*- coding: utf-8 -*-
import os
import pandas as pd
from datetime import datetime
import argparse

# --- CONFIGURACIÓN ---
RUTA_TRACKERS = "03_Trackers"
NOMBRE_XLSX = "inversiones.xlsx"
RUTA_XLSX = os.path.join(RUTA_TRACKERS, NOMBRE_XLSX)

# --- SETUP DEL PARSER DE ARGUMENTOS ---
parser = argparse.ArgumentParser(description="Registra una nueva inversion en el archivo de inversiones.")
parser.add_argument("-a", "--activo", type=str, required=True, help="El ticker o nombre del activo. Ej: SPY, AAPL")
parser.add_argument("-t", "--tipo", type=str, required=True, choices=['Compra', 'Venta'], help="El tipo de operacion: Compra o Venta.")
parser.add_argument("-m", "--monto", type=float, required=True, help="El monto de la operacion en ARS.")
args = parser.parse_args()

# --- LÓGICA PRINCIPAL ---
try:
    fecha = datetime.now().strftime("%Y-%m-%d")
    nueva_inversion = pd.DataFrame([{
        "Fecha": fecha,
        "Activo": args.activo,
        "Tipo": args.tipo,
        "Monto_ARS": args.monto
    }])

    # Verificar si el archivo existe para no sobreescribir los encabezados
    if os.path.exists(RUTA_XLSX):
        # Leer el archivo existente
        df_existente = pd.read_excel(RUTA_XLSX)
        # Concatenar el nuevo registro
        df_actualizado = pd.concat([df_existente, nueva_inversion], ignore_index=True)
    else:
        # Si el archivo no existe, el nuevo dataframe es el archivo completo
        df_actualizado = nueva_inversion
        # Asegurarse de que la carpeta de trackers exista
        if not os.path.exists(RUTA_TRACKERS):
            os.makedirs(RUTA_TRACKERS)

    # Guardar el DataFrame actualizado en el archivo Excel
    df_actualizado.to_excel(RUTA_XLSX, index=False)

    print("\n[OK] Inversion registrada con exito!")
    print(f"   - Fecha: {fecha}")
    print(f"   - Activo: {args.activo}")
    print(f"   - Tipo: {args.tipo}")
    print(f"   - Monto: ${args.monto:,.2f} ARS")

except Exception as e:
    print(f"\n[ERROR] Ocurrio un error inesperado: {e}")
