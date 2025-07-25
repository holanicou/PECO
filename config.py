import os
from typing import Dict, Any, Optional

# Rutas base
RUTA_BASE = os.getcwd()
RUTA_TRACKERS = os.path.join(RUTA_BASE, "03_Trackers")
RUTA_RECURSOS = os.path.join(RUTA_BASE, "static", "05_Templates_y_Recursos")
RUTA_REPORTES = os.path.join(RUTA_BASE, "06_Reportes")
RUTA_RESOLUCIONES = os.path.join(RUTA_BASE, "01_Resoluciones")
RUTA_LOGS = os.path.join(RUTA_BASE, "logs")

# Archivos de datos
CSV_GASTOS = os.path.join(RUTA_TRACKERS, "gastos_mensuales.csv")
XLSX_INVERSIONES = os.path.join(RUTA_TRACKERS, "inversiones.xlsx")
JSON_PRESUPUESTO = os.path.join(RUTA_RECURSOS, "presupuesto_base.json")
RUTA_CONFIG_JSON = os.path.join(RUTA_RECURSOS, 'config_mes.json')

# Configuración de plantillas
NOMBRE_PLANTILLA_RESOLUCION = "plantilla_resolucion.tex"
RUTA_PLANTILLA_RESOLUCION = os.path.join(RUTA_RECURSOS, NOMBRE_PLANTILLA_RESOLUCION)

# Archivos de recursos
LOGO_FILE = os.path.join(RUTA_RECURSOS, "logo.png")
FIRMA_FILE = os.path.join(RUTA_RECURSOS, "firma.png")

# ============================================================================
# SERVICE LAYER CONFIGURATION
# ============================================================================

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "log_dir": RUTA_LOGS,
    "console_level": "INFO",
    "file_level": "DEBUG"
}

# PDF Generation Configuration
PDF_CONFIG = {
    "latex_timeout": 60,  # seconds
    "temp_file_extensions": ['.aux', '.log', '.fls', '.fdb_latexmk', '.synctex.gz'],
    "auto_cleanup": True,
    "resource_files": ["logo.png", "firma.png"],
    "compilation_retries": 1
}

# Data Manager Configuration
DATA_CONFIG = {
    "csv_encoding": "utf-8",
    "excel_sheet_name": "Inversiones",
    "date_format": "%Y-%m-%d",
    "max_amount_threshold": 1000000,  # ARS
    "backup_enabled": False,
    "validation_enabled": True
}

# System Checker Configuration
SYSTEM_CONFIG = {
    "required_dependencies": ["pdflatex"],
    "python_min_version": (3, 7),
    "startup_validation": True,
    "auto_create_missing": True,
    "dependency_timeout": 10  # seconds
}

# Error Handling Configuration
ERROR_CONFIG = {
    "detailed_errors": True,
    "error_logging": True,
    "user_friendly_messages": True,
    "include_stack_trace": False  # Set to True for development
}

# Web Application Configuration
WEB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": False,  # Set to True for development
    "threaded": True,
    "request_timeout": 30,  # seconds
    "max_content_length": 16 * 1024 * 1024  # 16MB
}

# ============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATION
# ============================================================================

def get_environment() -> str:
    """
    Get current environment from environment variable.
    
    Returns:
        Environment name: 'development', 'testing', or 'production'
    """
    return os.environ.get('PECO_ENV', 'production').lower()

def get_config_for_environment(env: Optional[str] = None) -> Dict[str, Any]:
    """
    Get configuration settings for specific environment.
    
    Args:
        env: Environment name. If None, uses current environment.
        
    Returns:
        Dictionary with environment-specific configuration
    """
    if env is None:
        env = get_environment()
    
    base_config = {
        "logging": LOGGING_CONFIG.copy(),
        "pdf": PDF_CONFIG.copy(),
        "data": DATA_CONFIG.copy(),
        "system": SYSTEM_CONFIG.copy(),
        "error": ERROR_CONFIG.copy(),
        "web": WEB_CONFIG.copy()
    }
    
    if env == 'development':
        # Development-specific overrides
        base_config["logging"]["level"] = "DEBUG"
        base_config["logging"]["console_level"] = "DEBUG"
        base_config["web"]["debug"] = True
        base_config["error"]["include_stack_trace"] = True
        base_config["system"]["startup_validation"] = True
        
    elif env == 'testing':
        # Testing-specific overrides
        base_config["logging"]["level"] = "WARNING"
        base_config["data"]["backup_enabled"] = False
        base_config["pdf"]["auto_cleanup"] = True
        base_config["system"]["auto_create_missing"] = False
        
    elif env == 'production':
        # Production-specific overrides
        base_config["logging"]["level"] = "INFO"
        base_config["web"]["debug"] = False
        base_config["error"]["include_stack_trace"] = False
        base_config["data"]["backup_enabled"] = True
    
    return base_config

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_configuration() -> Dict[str, Any]:
    """
    Validate current configuration and return validation results.
    
    Returns:
        Dictionary with validation results and any issues found
    """
    issues = []
    warnings = []
    
    # Check if required directories exist
    required_dirs = [RUTA_TRACKERS, RUTA_RECURSOS, RUTA_REPORTES, RUTA_RESOLUCIONES, RUTA_LOGS]
    for directory in required_dirs:
        if not os.path.exists(directory):
            issues.append(f"Required directory missing: {directory}")
        elif not os.access(directory, os.W_OK):
            issues.append(f"No write permission for directory: {directory}")
    
    # Check if template file exists
    if not os.path.exists(RUTA_PLANTILLA_RESOLUCION):
        warnings.append(f"Template file missing: {RUTA_PLANTILLA_RESOLUCION}")
    
    # Check if resource files exist
    for resource_file in [LOGO_FILE, FIRMA_FILE]:
        if not os.path.exists(resource_file):
            warnings.append(f"Resource file missing: {resource_file}")
    
    # Validate configuration values
    if LOGGING_CONFIG["max_file_size"] < 1024 * 1024:  # Less than 1MB
        warnings.append("Log file size limit is very small")
    
    if PDF_CONFIG["latex_timeout"] < 10:
        warnings.append("LaTeX timeout is very short")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "checked_directories": required_dirs,
        "environment": get_environment()
    }

def create_default_directories() -> Dict[str, Any]:
    """
    Create default directory structure if it doesn't exist.
    
    Returns:
        Dictionary with creation results
    """
    created_dirs = []
    failed_dirs = []
    
    required_dirs = [RUTA_TRACKERS, RUTA_RECURSOS, RUTA_REPORTES, RUTA_RESOLUCIONES, RUTA_LOGS]
    
    for directory in required_dirs:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                created_dirs.append(directory)
        except Exception as e:
            failed_dirs.append((directory, str(e)))
    
    return {
        "created_directories": created_dirs,
        "failed_directories": failed_dirs,
        "success": len(failed_dirs) == 0
    }

# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

# Keep original variable names for backward compatibility
# These can be gradually phased out as the codebase is updated

# Legacy configuration access
def get_legacy_config():
    """Get configuration in legacy format for backward compatibility."""
    return {
        'RUTA_BASE': RUTA_BASE,
        'RUTA_TRACKERS': RUTA_TRACKERS,
        'RUTA_RECURSOS': RUTA_RECURSOS,
        'RUTA_REPORTES': RUTA_REPORTES,
        'RUTA_RESOLUCIONES': RUTA_RESOLUCIONES,
        'CSV_GASTOS': CSV_GASTOS,
        'XLSX_INVERSIONES': XLSX_INVERSIONES,
        'JSON_PRESUPUESTO': JSON_PRESUPUESTO,
        'RUTA_CONFIG_JSON': RUTA_CONFIG_JSON,
        'NOMBRE_PLANTILLA_RESOLUCION': NOMBRE_PLANTILLA_RESOLUCION
    }
