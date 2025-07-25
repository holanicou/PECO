# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
from config import RUTA_CONFIG_JSON

# Import service layer
from services.data_manager import DataManager
from services.pdf_generator import PDFGenerator
from services.latex_processor import LaTeXProcessor
from services.system_checker import SystemChecker
from services.exceptions import PECOError, LaTeXError, DataError, ConfigurationError
from services.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# --- INICIALIZACIÓN DE FLASK ---
# Le decimos a Flask que la carpeta 'static' es pública para poder acceder al logo.
app = Flask(__name__, template_folder='.', static_folder='static')

# Initialize service layer
data_manager = DataManager()
latex_processor = LaTeXProcessor()
pdf_generator = PDFGenerator(latex_processor)
system_checker = SystemChecker()

# Perform startup validation
logger.info("Performing startup system validation...")
startup_result = system_checker.validate_startup_requirements()

if not startup_result.success:
    logger.warning("System validation found issues during startup:")
    logger.warning(f"Missing dependencies: {startup_result.missing_dependencies}")
    for dep, instruction in (startup_result.installation_instructions or {}).items():
        logger.warning(f"To install {dep}: {instruction}")
    logger.warning("Application will continue but some features may not work properly")
else:
    logger.info("All system dependencies validated successfully")

logger.info("Flask application initialized with service layer")

# --- ERROR HANDLERS ---

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    logger.warning(f"Bad request: {error}")
    return jsonify({
        'success': False,
        'message': 'Solicitud inválida - verifique los datos enviados',
        'error_code': 'BAD_REQUEST',
        'details': {'description': str(error.description) if hasattr(error, 'description') else 'Solicitud malformada'}
    }), 400

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    logger.warning(f"Resource not found: {error}")
    return jsonify({
        'success': False,
        'message': 'Recurso no encontrado',
        'error_code': 'NOT_FOUND',
        'details': {'description': 'El recurso solicitado no existe'}
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors."""
    logger.warning(f"Method not allowed: {error}")
    return jsonify({
        'success': False,
        'message': 'Método HTTP no permitido para este endpoint',
        'error_code': 'METHOD_NOT_ALLOWED',
        'details': {'allowed_methods': error.valid_methods if hasattr(error, 'valid_methods') else []}
    }), 405

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle 413 Request Entity Too Large errors."""
    logger.warning(f"Request too large: {error}")
    return jsonify({
        'success': False,
        'message': 'Los datos enviados son demasiado grandes',
        'error_code': 'REQUEST_TOO_LARGE',
        'details': {'description': 'Reduzca el tamaño de los datos y vuelva a intentar'}
    }), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'message': 'Error interno del servidor - contacte al administrador',
        'error_code': 'INTERNAL_SERVER_ERROR',
        'details': {'description': 'Se ha producido un error inesperado en el servidor'}
    }), 500

@app.errorhandler(PECOError)
def handle_peco_error(error):
    """Handle custom PECO application errors."""
    logger.error(f"PECO error: {error}")
    
    # Determine appropriate HTTP status code based on error type
    if isinstance(error, ConfigurationError):
        status_code = 500  # Server configuration issue
    elif isinstance(error, DataError):
        status_code = 400  # Client data issue
    elif isinstance(error, LaTeXError):
        status_code = 422  # Unprocessable entity (LaTeX compilation issue)
    else:
        status_code = 500  # Generic server error
    
    return jsonify({
        'success': False,
        'message': error.message,
        'error_code': error.error_code,
        'details': error.details,
        'suggestions': _get_error_suggestions(error)
    }), status_code

def _get_error_suggestions(error: PECOError) -> list:
    """
    Get helpful suggestions based on the error type and code.
    
    Args:
        error: The PECO error instance
        
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    if isinstance(error, LaTeXError):
        suggestions.extend([
            'Verifique que pdflatex esté instalado correctamente',
            'Instale MiKTeX o TeX Live para Windows',
            'Revise que no haya caracteres especiales problemáticos en el texto'
        ])
    elif isinstance(error, DataError):
        if 'MISSING_' in error.error_code:
            suggestions.append('Complete todos los campos requeridos')
        elif 'INVALID_AMOUNT' in error.error_code:
            suggestions.append('Ingrese un monto numérico válido mayor a 0')
        elif 'FILE_NOT_FOUND' in error.error_code:
            suggestions.extend([
                'Verifique que los archivos de datos existan',
                'Ejecute la aplicación desde el directorio correcto'
            ])
    elif isinstance(error, ConfigurationError):
        suggestions.extend([
            'Verifique la configuración del sistema',
            'Asegúrese de tener permisos de escritura en los directorios',
            'Revise que todos los archivos de plantilla estén presentes'
        ])
    
    # Add general suggestions if no specific ones were found
    if not suggestions:
        suggestions.extend([
            'Revise los logs para más detalles',
            'Contacte al administrador si el problema persiste'
        ])
    
    return suggestions

# --- REQUEST VALIDATION MIDDLEWARE ---

def validate_json_request():
    """Validate that the request contains valid JSON data."""
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'Content-Type debe ser application/json',
            'error_code': 'INVALID_CONTENT_TYPE',
            'suggestions': ['Asegúrese de enviar datos JSON con Content-Type: application/json']
        }), 400
    
    try:
        # This will raise an exception if JSON is malformed
        request.get_json(force=True)
        return None
    except Exception as e:
        logger.warning(f"Invalid JSON in request: {e}")
        return jsonify({
            'success': False,
            'message': 'Formato JSON inválido en la solicitud',
            'error_code': 'MALFORMED_JSON',
            'details': {'error': str(e)},
            'suggestions': ['Verifique que el JSON esté bien formado', 'Use comillas dobles para strings', 'Revise que no falten comas o llaves']
        }), 400

def validate_required_fields(data: dict, required_fields: list, context: str = "operación") -> tuple:
    """
    Validate that all required fields are present and not empty.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context description for error messages
        
    Returns:
        Tuple of (is_valid: bool, error_response: dict or None)
    """
    if not data:
        return False, {
            'success': False,
            'message': f'No se recibieron datos para {context}',
            'error_code': 'NO_DATA',
            'suggestions': [f'Envíe los datos requeridos para {context}']
        }
    
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            empty_fields.append(field)
    
    if missing_fields or empty_fields:
        error_fields = missing_fields + empty_fields
        return False, {
            'success': False,
            'message': f'Campos requeridos faltantes o vacíos para {context}: {", ".join(error_fields)}',
            'error_code': 'MISSING_REQUIRED_FIELDS',
            'details': {
                'missing_fields': missing_fields,
                'empty_fields': empty_fields,
                'required_fields': required_fields
            },
            'suggestions': [f'Complete todos los campos requeridos: {", ".join(required_fields)}']
        }
    
    return True, None

def validate_numeric_field(value, field_name: str, min_value: float = None, max_value: float = None) -> tuple:
    """
    Validate that a field contains a valid numeric value.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        Tuple of (is_valid: bool, converted_value: float or None, error_response: dict or None)
    """
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return False, None, {
            'success': False,
            'message': f'El campo {field_name} debe ser un número válido',
            'error_code': 'INVALID_NUMERIC_VALUE',
            'details': {'field': field_name, 'value': str(value)},
            'suggestions': [f'Ingrese un valor numérico válido para {field_name}', 'Use punto (.) como separador decimal']
        }
    
    if min_value is not None and numeric_value < min_value:
        return False, None, {
            'success': False,
            'message': f'El campo {field_name} debe ser mayor o igual a {min_value}',
            'error_code': 'VALUE_TOO_LOW',
            'details': {'field': field_name, 'value': numeric_value, 'min_value': min_value},
            'suggestions': [f'Ingrese un valor mayor o igual a {min_value} para {field_name}']
        }
    
    if max_value is not None and numeric_value > max_value:
        return False, None, {
            'success': False,
            'message': f'El campo {field_name} debe ser menor o igual a {max_value}',
            'error_code': 'VALUE_TOO_HIGH',
            'details': {'field': field_name, 'value': numeric_value, 'max_value': max_value},
            'suggestions': [f'Ingrese un valor menor o igual a {max_value} para {field_name}']
        }
    
    return True, numeric_value, None

def create_success_response(message: str, data: dict = None, legacy_field: str = None) -> dict:
    """
    Create a standardized success response.
    
    Args:
        message: Success message
        data: Optional data payload
        legacy_field: Optional legacy field name for backward compatibility
        
    Returns:
        Standardized success response dictionary
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data:
        response['data'] = data
    
    # Add legacy field for backward compatibility
    if legacy_field:
        response[legacy_field] = message
    
    return response

def create_error_response(message: str, error_code: str, status_code: int = 400, 
                         details: dict = None, suggestions: list = None, legacy_field: str = None) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_code: Error code for programmatic handling
        status_code: HTTP status code
        details: Optional error details
        suggestions: Optional list of suggestions
        legacy_field: Optional legacy field name for backward compatibility
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': False,
        'message': message,
        'error_code': error_code,
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        response['details'] = details
    
    if suggestions:
        response['suggestions'] = suggestions
    
    # Add legacy field for backward compatibility
    if legacy_field:
        response[legacy_field] = message
    
    return response, status_code

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    """ Sirve el archivo principal de tu interfaz, el index_modular.html. """
    return render_template('index_modular.html')

@app.route('/ejecutar', methods=['POST'])
def ejecutar():
    """ Recibe las acciones desde el frontend y ejecuta las operaciones usando el service layer. """
    # Validate JSON request
    json_validation = validate_json_request()
    if json_validation:
        return json_validation
    
    try:
        data = request.json
        comando = data.get('comando')
        args = data.get('args', {})
        
        logger.info(f"Processing command: {comando} with args: {args}")
        
        if comando == 'registrar':
            # Validate required fields using improved validation
            is_valid, error_response = validate_required_fields(
                args, 
                ['monto', 'categoria', 'desc'], 
                'registro de gasto'
            )
            if not is_valid:
                return jsonify({**error_response, 'salida': error_response['message']}), 400
            
            # Validate numeric amount with range checking
            is_valid, monto_float, error_response = validate_numeric_field(
                args.get('monto'), 
                'monto', 
                min_value=0.01, 
                max_value=1000000
            )
            if not is_valid:
                return jsonify({**error_response, 'salida': error_response['message']}), 400
            
            # Register expense using service layer
            result = data_manager.register_expense(monto_float, args.get('categoria'), args.get('desc'))
            
            if result.success:
                return jsonify(create_success_response(
                    result.message, 
                    result.data, 
                    'salida'
                ))
            else:
                error_response, status_code = create_error_response(
                    result.message,
                    result.error_code or 'EXPENSE_REGISTRATION_ERROR',
                    400,
                    legacy_field='salida'
                )
                return jsonify(error_response), status_code
        
        elif comando == 'invertir':
            # Validate required fields using improved validation
            is_valid, error_response = validate_required_fields(
                args, 
                ['activo', 'tipo', 'monto'], 
                'registro de inversión'
            )
            if not is_valid:
                return jsonify({**error_response, 'salida': error_response['message']}), 400
            
            # Validate investment type
            tipo = args.get('tipo')
            if tipo not in ['Compra', 'Venta']:
                error_response, status_code = create_error_response(
                    'El tipo de operación debe ser "Compra" o "Venta"',
                    'INVALID_INVESTMENT_TYPE',
                    400,
                    details={'valid_types': ['Compra', 'Venta'], 'received': tipo},
                    suggestions=['Use "Compra" para compras de activos', 'Use "Venta" para ventas de activos'],
                    legacy_field='salida'
                )
                return jsonify(error_response), status_code
            
            # Validate numeric amount with range checking
            is_valid, monto_float, error_response = validate_numeric_field(
                args.get('monto'), 
                'monto', 
                min_value=0.01, 
                max_value=10000000
            )
            if not is_valid:
                return jsonify({**error_response, 'salida': error_response['message']}), 400
            
            # Register investment using service layer
            result = data_manager.register_investment(args.get('activo'), tipo, monto_float)
            
            if result.success:
                return jsonify(create_success_response(
                    result.message, 
                    result.data, 
                    'salida'
                ))
            else:
                error_response, status_code = create_error_response(
                    result.message,
                    result.error_code or 'INVESTMENT_REGISTRATION_ERROR',
                    400,
                    legacy_field='salida'
                )
                return jsonify(error_response), status_code
        
        elif comando == 'analizar':
            # Get month and year from args or use current month
            month = args.get('mes', datetime.now().month)
            year = args.get('año', datetime.now().year)
            
            # Validate month
            is_valid, month_int, error_response = validate_numeric_field(
                month, 
                'mes', 
                min_value=1, 
                max_value=12
            )
            if not is_valid:
                return jsonify({**error_response, 'salida': error_response['message']}), 400
            
            # Validate year
            current_year = datetime.now().year
            is_valid, year_int, error_response = validate_numeric_field(
                year, 
                'año', 
                min_value=2000, 
                max_value=current_year + 1
            )
            if not is_valid:
                return jsonify({**error_response, 'salida': error_response['message']}), 400
            
            # Generate analysis using service layer
            result = data_manager.get_monthly_analysis(int(month_int), int(year_int))
            
            if result.success:
                analysis_data = {
                    'total_expenses': result.total_expenses,
                    'expenses_by_category': result.expenses_by_category,
                    'total_investments': result.total_investments,
                    'analysis_data': result.analysis_data
                }
                return jsonify(create_success_response(
                    result.message, 
                    analysis_data, 
                    'salida'
                ))
            else:
                error_response, status_code = create_error_response(
                    result.message,
                    result.error_code or 'ANALYSIS_ERROR',
                    400,
                    legacy_field='salida'
                )
                return jsonify(error_response), status_code
        
        else:
            error_response, status_code = create_error_response(
                f'Comando no reconocido: {comando}',
                'UNKNOWN_COMMAND',
                400,
                details={'received_command': comando, 'valid_commands': ['registrar', 'invertir', 'analizar']},
                suggestions=['Use "registrar" para gastos', 'Use "invertir" para inversiones', 'Use "analizar" para análisis mensual'],
                legacy_field='salida'
            )
            return jsonify(error_response), status_code
    
    except PECOError as e:
        logger.error(f"PECO error in /ejecutar: {e}")
        error_response, status_code = create_error_response(
            str(e),
            e.error_code,
            500,
            details=e.details,
            suggestions=_get_error_suggestions(e),
            legacy_field='salida'
        )
        return jsonify(error_response), status_code
    
    except Exception as e:
        logger.error(f"Unexpected error in /ejecutar: {e}")
        error_response, status_code = create_error_response(
            f'Error interno del servidor: {str(e)}',
            'INTERNAL_ERROR',
            500,
            details={'error': str(e)},
            suggestions=['Revise los logs del servidor', 'Contacte al administrador si el problema persiste'],
            legacy_field='salida'
        )
        return jsonify(error_response), status_code

@app.route('/get-config', methods=['GET'])
def get_config():
    """ Lee y devuelve el contenido del archivo config_mes.json con mejor manejo de errores. """
    try:
        logger.info("Loading configuration file")
        
        if not os.path.exists(RUTA_CONFIG_JSON):
            logger.warning(f"Configuration file not found: {RUTA_CONFIG_JSON}")
            return jsonify({
                'success': False,
                'message': 'Archivo de configuración no encontrado',
                'error_code': 'CONFIG_NOT_FOUND',
                'error': 'Archivo de configuración no encontrado'  # For backward compatibility
            }), 404
        
        with open(RUTA_CONFIG_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info("Configuration loaded successfully")
        return jsonify({
            'success': True,
            'data': data,
            **data  # For backward compatibility - merge data into root
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in configuration file: {e}")
        return jsonify({
            'success': False,
            'message': f'Error de formato en archivo de configuración: {str(e)}',
            'error_code': 'JSON_DECODE_ERROR',
            'error': f'Error de formato JSON: {str(e)}'  # For backward compatibility
        }), 400
    
    except PermissionError as e:
        logger.error(f"Permission error reading configuration: {e}")
        return jsonify({
            'success': False,
            'message': 'Sin permisos para leer el archivo de configuración',
            'error_code': 'PERMISSION_ERROR',
            'error': 'Sin permisos para leer el archivo'  # For backward compatibility
        }), 403
    
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Error cargando configuración: {str(e)}',
            'error_code': 'CONFIG_LOAD_ERROR',
            'error': str(e)  # For backward compatibility
        }), 500

@app.route('/save-config', methods=['POST'])
def save_config():
    """ Recibe un JSON del frontend y lo guarda en config_mes.json con validación mejorada. """
    try:
        logger.info("Saving configuration file")
        
        nuevo_config = request.json
        if not nuevo_config:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos de configuración',
                'error_code': 'NO_CONFIG_DATA',
                'error': 'No se recibieron datos'  # For backward compatibility
            }), 400
        
        # Validate that it's a valid JSON object
        if not isinstance(nuevo_config, dict):
            return jsonify({
                'success': False,
                'message': 'Los datos de configuración deben ser un objeto JSON válido',
                'error_code': 'INVALID_CONFIG_FORMAT',
                'error': 'Formato de configuración inválido'  # For backward compatibility
            }), 400
        
        # Ensure directory exists
        config_dir = os.path.dirname(RUTA_CONFIG_JSON)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            logger.info(f"Created configuration directory: {config_dir}")
        
        # Save configuration with proper formatting
        with open(RUTA_CONFIG_JSON, 'w', encoding='utf-8') as f:
            json.dump(nuevo_config, f, indent=2, ensure_ascii=False)
        
        logger.info("Configuration saved successfully")
        return jsonify({
            'success': True,
            'message': 'Archivo de configuración guardado con éxito',
            'salida': '[OK] Archivo de configuracion guardado con exito.'  # For backward compatibility
        })
        
    except PermissionError as e:
        logger.error(f"Permission error saving configuration: {e}")
        return jsonify({
            'success': False,
            'message': 'Sin permisos para guardar el archivo de configuración',
            'error_code': 'PERMISSION_ERROR',
            'error': 'Sin permisos para guardar el archivo'  # For backward compatibility
        }), 403
    
    except OSError as e:
        logger.error(f"OS error saving configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Error del sistema guardando configuración: {str(e)}',
            'error_code': 'OS_ERROR',
            'error': str(e)  # For backward compatibility
        }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error saving configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Error guardando configuración: {str(e)}',
            'error_code': 'CONFIG_SAVE_ERROR',
            'error': str(e)  # For backward compatibility
        }), 500

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    """ Genera un PDF de resolución usando el service layer. """
    try:
        logger.info("Starting PDF generation")
        
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos para generar el PDF',
                'error_code': 'NO_PDF_DATA'
            }), 400
        
        # Validate required fields for PDF generation
        required_fields = ['titulo', 'mes_nombre', 'mes_anterior']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Campos requeridos faltantes: {", ".join(missing_fields)}',
                'error_code': 'MISSING_PDF_FIELDS'
            }), 400
        
        # Set up template path and output directory
        import config
        template_path = os.path.join(config.RUTA_TEMPLATES, 'resolucion_template.tex')
        output_dir = config.RUTA_RESOLUCIONES
        
        # Generate filename based on current date and title
        fecha_actual = datetime.now()
        filename_base = f"r{fecha_actual.day}e{fecha_actual.strftime('%b').upper()}s{fecha_actual.strftime('%y')} - {data.get('titulo', 'Resolucion')}"
        
        # Clean filename for filesystem compatibility
        filename_base = "".join(c for c in filename_base if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Generate PDF using service layer
        pdf_result = pdf_generator.generate_resolution(
            template_path=template_path,
            data=data,
            output_dir=output_dir,
            filename_base=filename_base
        )
        
        if pdf_result.success:
            logger.info(f"PDF generated successfully: {pdf_result.pdf_path}")
            return jsonify({
                'success': True,
                'message': pdf_result.message,
                'data': {
                    'pdf_path': pdf_result.pdf_path,
                    'tex_path': pdf_result.tex_path,
                    'filename': filename_base
                },
                'salida': pdf_result.message  # For backward compatibility
            })
        else:
            logger.error(f"PDF generation failed: {pdf_result.message}")
            return jsonify({
                'success': False,
                'message': pdf_result.message,
                'error_code': pdf_result.error_code,
                'details': pdf_result.details,
                'salida': pdf_result.message  # For backward compatibility
            }), 400
    
    except ConfigurationError as e:
        logger.error(f"Configuration error in PDF generation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error de configuración: {str(e)}',
            'error_code': e.error_code,
            'details': e.details,
            'salida': str(e)  # For backward compatibility
        }), 500
    
    except LaTeXError as e:
        logger.error(f"LaTeX error in PDF generation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error de LaTeX: {str(e)}',
            'error_code': e.error_code,
            'details': e.details,
            'salida': str(e)  # For backward compatibility
        }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in PDF generation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno generando PDF: {str(e)}',
            'error_code': 'PDF_GENERATION_ERROR',
            'salida': f'Error interno generando PDF: {str(e)}'  # For backward compatibility
        }), 500

@app.route('/validar-sistema', methods=['GET'])
def validar_sistema():
    """ Valida la integridad del sistema y dependencias usando SystemChecker. """
    try:
        logger.info("Starting comprehensive system validation")
        
        # Use SystemChecker for comprehensive validation
        dependency_result = system_checker.check_all_dependencies()
        data_integrity = data_manager.validate_data_integrity()
        system_info = system_checker.get_system_info()
        latex_result = system_checker.check_latex_installation()
        
        validation_results = {
            'dependencies': {
                'success': dependency_result.success,
                'message': dependency_result.message,
                'missing_dependencies': dependency_result.missing_dependencies or [],
                'installation_instructions': dependency_result.installation_instructions or {}
            },
            'data_integrity': {
                'success': data_integrity.success,
                'message': data_integrity.message
            },
            'system_info': system_info,
            'latex_available': latex_result.success,
            'system_status': 'ok'
        }
        
        # Check if there are any critical issues
        critical_issues = []
        warnings = []
        
        if not dependency_result.success:
            for dep in dependency_result.missing_dependencies or []:
                critical_issues.append(f'{dep} no está disponible')
                instruction = dependency_result.installation_instructions.get(dep, f'Instale {dep}')
                warnings.append(f'Para instalar {dep}: {instruction}')
        
        if not data_integrity.success:
            critical_issues.append(f"Problemas de integridad de datos: {data_integrity.message}")
        
        if critical_issues:
            validation_results['system_status'] = 'warning' if not dependency_result.missing_dependencies else 'error'
            validation_results['issues'] = critical_issues
            validation_results['warnings'] = warnings
        
        return jsonify({
            'success': True,
            'message': 'Validación del sistema completada',
            'data': validation_results
        })
    
    except Exception as e:
        logger.error(f"Error during system validation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error validando sistema: {str(e)}',
            'error_code': 'SYSTEM_VALIDATION_ERROR'
        }), 500

# --- INICIAR EL SERVIDOR ---
if __name__ == '__main__':
    print("🚀 Servidor PECO iniciado. Abre http://127.0.0.1:5000 en tu navegador.")
    app.run(debug=True, port=5000)
