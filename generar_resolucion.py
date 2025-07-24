# -*- coding: utf-8 -*-
import os
import json
import subprocess
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURACIÓN DE RUTAS ---
RUTA_BASE = os.getcwd()
RUTA_TEMPLATES = os.path.join(RUTA_BASE, "static", "05_Templates_y_Recursos")
RUTA_RESOLUCIONES = os.path.join(RUTA_BASE, "01_Resoluciones")
RUTA_CONFIG = os.path.join(RUTA_TEMPLATES, "config_mes.json")
NOMBRE_PLANTILLA = "plantilla_resolucion.tex"

# --- DICCIONARIO PARA MESES EN ROMANO ---
meses_romanos = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
    7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
}

def limpiar_archivos_temporales(ruta_base):
    """
    Busca y elimina los archivos .aux y .log correspondientes
    a la resolución que se acaba de generar.
    """
    print("[INFO] Realizando limpieza de archivos temporales...")
    extensiones_a_borrar = ['.aux', '.log']
    for ext in extensiones_a_borrar:
        try:
            ruta_archivo = ruta_base + ext
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
                print(f"   - Archivo eliminado: {os.path.basename(ruta_archivo)}")
        except Exception as e:
            print(f"   - No se pudo eliminar {os.path.basename(ruta_archivo)}: {e}")

def generar_resolucion():
    """
    Función principal que lee la configuración, rellena la plantilla LaTeX
    y compila el PDF final.
    """
    # CAMBIO: Se reemplazaron emojis por texto simple
    print("--- [INFO] Iniciando generador de resoluciones ECOP ---")
    try:
        with open(RUTA_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("[OK] Datos de config_mes.json cargados correctamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el archivo de configuracion: {e}")
        return

    try:
        fecha_actual = datetime.now()
        dia = fecha_actual.day
        mes_romano = meses_romanos[fecha_actual.month]
        año_corto = fecha_actual.strftime('%y')
        codigo_res = f"r{dia}e{mes_romano}s{año_corto}"
        nombre_archivo_base = f"{codigo_res} - {config.get('titulo_documento', 'Resolucion')}"
        config['codigo_res'] = codigo_res
        config['fecha_larga'] = fecha_actual.strftime(f'%d de {config.get("mes_nombre", "mes")} de %Y')
    except KeyError as e:
        print(f"[ERROR] Falta una clave en el archivo de configuracion: {e}")
        return

    try:
        env = Environment(loader=FileSystemLoader(RUTA_TEMPLATES))
        template = env.get_template(NOMBRE_PLANTILLA)
        contenido_tex = template.render(config)
        print("[OK] Plantilla .tex rellenada con los datos del mes.")
    except Exception as e:
        print(f"[ERROR] al procesar la plantilla Jinja2: {e}")
        return

    if not os.path.exists(RUTA_RESOLUCIONES):
        os.makedirs(RUTA_RESOLUCIONES)
    ruta_tex_salida = os.path.join(RUTA_RESOLUCIONES, f"{nombre_archivo_base}.tex")
    ruta_base_salida = os.path.join(RUTA_RESOLUCIONES, nombre_archivo_base)

    try:
        with open(ruta_tex_salida, 'w', encoding='utf-8') as f:
            f.write(contenido_tex)
        print(f"[INFO] Archivo .tex guardado en: {ruta_tex_salida}")
        print("[INFO] Compilando PDF...")
        proceso = subprocess.run(
            ['pdflatex', '-output-directory', RUTA_RESOLUCIONES, ruta_tex_salida],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        if proceso.returncode == 0:
            print(f"\n[OK] Resolucion generada con exito!")
            print(f"   PDF guardado en: {ruta_base_salida}.pdf")
            limpiar_archivos_temporales(ruta_base_salida)
        else:
            print("[ERROR] durante la compilacion de LaTeX.")
            print("   Revisa el archivo de log para mas detalles.")
    except FileNotFoundError:
        print("[ERROR] El comando 'pdflatex' no se encontro.")
        print("   Asegurate de tener una distribucion de LaTeX instalada en tu sistema.")
    except Exception as e:
        print(f"[ERROR] al guardar o compilar el archivo: {e}")

if __name__ == "__main__":
    generar_resolucion()
