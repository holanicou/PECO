# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json

# --- CONFIGURACIÓN ---
RUTA_BASE = os.getcwd()
RUTA_TRACKERS = os.path.join(RUTA_BASE, "03_Trackers")
# CORRECCIÓN: La ruta a recursos ahora debe apuntar a la carpeta 'static'
RUTA_RECURSOS = os.path.join(RUTA_BASE, "static", "05_Templates_y_Recursos")
RUTA_REPORTES = os.path.join(RUTA_BASE, "06_Reportes")

CSV_GASTOS = os.path.join(RUTA_TRACKERS, "gastos_mensuales.csv")
XLSX_INVERSIONES = os.path.join(RUTA_TRACKERS, "inversiones.xlsx")
JSON_PRESUPUESTO = os.path.join(RUTA_RECURSOS, "presupuesto_base.json")

FECHA_HOY = datetime.now()
MES_ACTUAL = FECHA_HOY.month
AÑO_ACTUAL = FECHA_HOY.year

def cargar_y_preparar_datos(ruta_archivo, tipo='csv'):
    if not os.path.exists(ruta_archivo):
        return None
    try:
        df = pd.read_csv(ruta_archivo) if tipo == 'csv' else pd.read_excel(ruta_archivo)
        if 'Fecha' not in df.columns: return None
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df.dropna(subset=['Fecha'], inplace=True)
        return df
    except Exception as e:
        print(f"[ERROR] al cargar el archivo {os.path.basename(ruta_archivo)}: {e}")
        return None

def analizar_gastos(df_gastos):
    filtro_mes = (df_gastos['Fecha'].dt.month == MES_ACTUAL) & (df_gastos['Fecha'].dt.year == AÑO_ACTUAL)
    df_mes = df_gastos[filtro_mes]
    if df_mes.empty:
        print(f"No se encontraron gastos registrados en el mes {MES_ACTUAL}/{AÑO_ACTUAL}.")
        return None, 0
    gastos_por_categoria = df_mes.groupby('Categoria')['Monto_ARS'].sum()
    return gastos_por_categoria, df_mes['Monto_ARS'].sum()

def analizar_inversiones(df_inversiones):
    filtro_mes = (df_inversiones['Fecha'].dt.month == MES_ACTUAL) & (df_inversiones['Fecha'].dt.year == AÑO_ACTUAL)
    df_mes = df_inversiones[filtro_mes]
    if df_mes.empty: return None, 0
    compras = df_mes[df_mes['Tipo'].str.lower() == 'compra']
    return compras.groupby('Activo')['Monto_ARS'].sum(), compras['Monto_ARS'].sum()

def generar_grafico_gastos(gastos_por_categoria):
    print("\n[INFO] Generando grafico de gastos...")
    try:
        plt.style.use('seaborn-v0_8-deep')
        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(gastos_por_categoria, autopct='%1.1f%%', startangle=90, pctdistance=0.85, labels=gastos_por_categoria.index)
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.set_title(f'Distribucion de Gastos - {MES_ACTUAL}/{AÑO_ACTUAL}', size=16, weight="bold")
        if not os.path.exists(RUTA_REPORTES): os.makedirs(RUTA_REPORTES)
        nombre_grafico = f"reporte_gastos_{AÑO_ACTUAL}_{MES_ACTUAL:02d}.png"
        ruta_guardado = os.path.join(RUTA_REPORTES, nombre_grafico)
        plt.savefig(ruta_guardado)
        print(f"[OK] Grafico guardado con exito en '{ruta_guardado}'!")
    except Exception as e:
        print(f"[ERROR] Ocurrio un error al generar el grafico: {e}")

def main():
    print(f"--- [INFO] INFORME FINANCIERO ECOP: {MES_ACTUAL}/{AÑO_ACTUAL} ---")
    df_gastos = cargar_y_preparar_datos(CSV_GASTOS, 'csv')
    if df_gastos is not None:
        gastos_por_categoria, total_gastado = analizar_gastos(df_gastos)
        if gastos_por_categoria is not None:
            print("\n[OK] Resumen de Gastos Mensuales:")
            print("-" * 40)
            for categoria, monto in gastos_por_categoria.items():
                porcentaje = (monto / total_gastado) * 100 if total_gastado else 0
                print(f"   - {categoria:<15}: ${monto:,.2f} ARS ({porcentaje:.1f}%)")
            print("-" * 40)
            print(f"   TOTAL GASTADO:{total_gastado: >22,.2f} ARS")
            print("-" * 40)
            if os.path.exists(JSON_PRESUPUESTO):
                with open(JSON_PRESUPUESTO, 'r', encoding='utf-8') as f:
                    presupuesto = json.load(f)
                print("\n[INFO] Analisis vs. Presupuesto:")
                print("-" * 40)
                for categoria, limite in presupuesto.items():
                    gastado = gastos_por_categoria.get(categoria, 0)
                    diferencia = limite - gastado
                    estado = "[OK] Ahorro" if diferencia >= 0 else "[ALERTA] Exceso"
                    print(f"   - {categoria:<15}: Gastado ${gastado:,.2f} de ${limite:,.2f}")
                    print(f"     Diferencia: ${diferencia:,.2f} ({estado})")
                print("-" * 40)
            generar_grafico_gastos(gastos_por_categoria)
    df_inversiones = cargar_y_preparar_datos(XLSX_INVERSIONES, 'excel')
    if df_inversiones is not None:
        inversiones_por_activo, total_invertido = analizar_inversiones(df_inversiones)
        if inversiones_por_activo is not None and total_invertido > 0:
            print("\n[INFO] Resumen de Inversiones (Compras del Mes):")
            print("-" * 40)
            for activo, monto in inversiones_por_activo.items():
                print(f"   - {activo:<15}: ${monto:,.2f} ARS")
            print("-" * 40)
            print(f"   TOTAL INVERTIDO:{total_invertido: >20,.2f} ARS")
            print("-" * 40)

if __name__ == "__main__":
    main()
