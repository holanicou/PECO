# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import subprocess
import sys
import os
import json

# --- INICIALIZACIÓN DE FLASK ---
# Le decimos a Flask que la carpeta 'static' es pública para poder acceder al logo.
app = Flask(__name__, template_folder='.', static_folder='static')

# --- RUTA AL ARCHIVO DE CONFIGURACIÓN DE RESOLUCIONES ---
# Esta ruta es necesaria para la funcionalidad de editar la resolución.
RUTA_CONFIG_JSON = os.path.join('static', '05_Templates_y_Recursos', 'config_mes.json')

def ejecutar_comando_ecop(comando_args):
    """
    Ejecuta el script ecop.py con los argumentos proporcionados y captura la salida.
    """
    try:
        # Usamos sys.executable para garantizar que se use el Python del entorno virtual
        comando_completo = [sys.executable, 'ecop.py'] + comando_args
        
        # Se ejecuta el subproceso forzando la codificación UTF-8
        resultado = subprocess.run(
            comando_completo,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8', # Forzamos UTF-8 para compatibilidad
            errors='ignore',
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Devolvemos la salida estándar del script si todo fue bien
        return resultado.stdout if resultado.stdout else "Comando ejecutado sin salida."
    except FileNotFoundError:
        return "Error: No se encontró el script 'ecop.py'."
    except subprocess.CalledProcessError as e:
        # Si el script termina con un error, devolvemos la salida de error
        return f"Error al ejecutar el script:\n{e.stdout}\n{e.stderr}"
    except Exception as e:
        return f"Ocurrió un error inesperado: {e}"

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    """ Sirve el archivo principal de tu interfaz, el index.html. """
    return render_template('index.html')

@app.route('/ejecutar', methods=['POST'])
def ejecutar():
    """ Recibe las acciones desde el frontend y ejecuta los scripts. """
    data = request.json
    comando = data.get('comando')
    args = data.get('args', {})
    
    comando_args = [comando]
    
    if comando == 'registrar':
        if not all([args.get('monto'), args.get('categoria'), args.get('desc')]):
            return jsonify({'salida': 'Error: Todos los campos de gasto son obligatorios.'}), 400
        comando_args.extend(['-m', str(args.get('monto')), '-c', args.get('categoria'), '-d', args.get('desc')])
    
    elif comando == 'invertir':
        if not all([args.get('activo'), args.get('tipo'), args.get('monto')]):
            return jsonify({'salida': 'Error: Todos los campos de inversion son obligatorios.'}), 400
        comando_args.extend(['-a', args.get('activo'), '-t', args.get('tipo'), '-m', str(args.get('monto'))])

    salida = ejecutar_comando_ecop(comando_args)
    return jsonify({'salida': salida})

@app.route('/get-config', methods=['GET'])
def get_config():
    """ Lee y devuelve el contenido del archivo config_mes.json. """
    try:
        with open(RUTA_CONFIG_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save-config', methods=['POST'])
def save_config():
    """ Recibe un JSON del frontend y lo guarda en config_mes.json. """
    try:
        nuevo_config = request.json
        with open(RUTA_CONFIG_JSON, 'w', encoding='utf-8') as f:
            json.dump(nuevo_config, f, indent=2, ensure_ascii=False)
        return jsonify({'salida': '[OK] Archivo de configuracion guardado con exito.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- INICIAR EL SERVIDOR ---
if __name__ == '__main__':
    print("🚀 Servidor ECOP iniciado. Abre http://127.0.0.1:5000 en tu navegador.")
    app.run(debug=True, port=5000)
