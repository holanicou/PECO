# -*- coding: utf-8 -*-
"""
System dependency checker for PECO financial application.
Validates required dependencies and system requirements.
"""

import os
import subprocess
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from .base import Result
from .exceptions import ConfigurationError
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DependencyResult(Result):
    """Result class for dependency checking operations."""
    missing_dependencies: Optional[List[str]] = None
    installation_instructions: Optional[Dict[str, str]] = None


@dataclass
class ConfigurationResult(Result):
    """Result class for configuration validation operations."""
    missing_files: Optional[List[str]] = None
    missing_directories: Optional[List[str]] = None
    created_files: Optional[List[str]] = None
    created_directories: Optional[List[str]] = None


class SystemChecker:
    """
    System dependency checker that validates required dependencies
    and provides installation instructions for missing components.
    """
    
    # Installation instructions for missing dependencies
    INSTALLATION_INSTRUCTIONS = {
        'pdflatex': {
            'windows': 'Install MiKTeX from https://miktex.org/download or TeX Live from https://www.tug.org/texlive/',
            'linux': 'Install texlive-latex-base: sudo apt-get install texlive-latex-base texlive-latex-extra',
            'macos': 'Install MacTeX from https://www.tug.org/mactex/ or use Homebrew: brew install --cask mactex'
        },
        'python': {
            'windows': 'Install Python from https://www.python.org/downloads/',
            'linux': 'Install python3: sudo apt-get install python3 python3-pip',
            'macos': 'Install Python from https://www.python.org/downloads/ or use Homebrew: brew install python'
        }
    }
    
    def __init__(self):
        """Initialize the SystemChecker."""
        self.logger = get_logger(self.__class__.__name__)
    
    def check_all_dependencies(self) -> DependencyResult:
        """
        Check all required system dependencies.
        
        Returns:
            DependencyResult: Result containing missing dependencies and installation instructions
        """
        self.logger.info("Starting system dependency check")
        
        missing_deps = []
        installation_instructions = {}
        
        # Check LaTeX installation
        latex_result = self.check_latex_installation()
        if not latex_result.success:
            missing_deps.append('pdflatex')
            installation_instructions['pdflatex'] = self._get_installation_instruction('pdflatex')
        
        # Check Python installation (should always be available if we're running)
        python_result = self.check_python_installation()
        if not python_result.success:
            missing_deps.append('python')
            installation_instructions['python'] = self._get_installation_instruction('python')
        
        if missing_deps:
            self.logger.warning(f"Missing dependencies found: {missing_deps}")
            return DependencyResult(
                success=False,
                message=f"Missing required dependencies: {', '.join(missing_deps)}",
                missing_dependencies=missing_deps,
                installation_instructions=installation_instructions,
                error_code="MISSING_DEPENDENCIES"
            )
        
        self.logger.info("All system dependencies are available")
        return DependencyResult(
            success=True,
            message="All required dependencies are available"
        )
    
    def check_latex_installation(self) -> Result:
        """
        Check if pdflatex is available in the system.
        
        Returns:
            Result: Success if pdflatex is available, failure otherwise
        """
        try:
            # Check if pdflatex is in PATH
            pdflatex_path = shutil.which('pdflatex')
            if pdflatex_path:
                self.logger.info(f"pdflatex found at: {pdflatex_path}")
                
                # Try to run pdflatex to verify it works
                result = subprocess.run(
                    ['pdflatex', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version_info = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
                    self.logger.info(f"pdflatex is working: {version_info}")
                    return Result(
                        success=True,
                        message=f"pdflatex is available: {version_info}",
                        data={'path': pdflatex_path, 'version': version_info}
                    )
                else:
                    self.logger.error(f"pdflatex failed to run: {result.stderr}")
                    return Result(
                        success=False,
                        message=f"pdflatex is installed but not working properly: {result.stderr}",
                        error_code="LATEX_NOT_WORKING"
                    )
            else:
                self.logger.warning("pdflatex not found in PATH")
                return Result(
                    success=False,
                    message="pdflatex is not installed or not in PATH",
                    error_code="LATEX_NOT_FOUND"
                )
                
        except subprocess.TimeoutExpired:
            self.logger.error("pdflatex version check timed out")
            return Result(
                success=False,
                message="pdflatex version check timed out",
                error_code="LATEX_TIMEOUT"
            )
        except Exception as e:
            self.logger.error(f"Error checking pdflatex installation: {e}")
            return Result(
                success=False,
                message=f"Error checking pdflatex installation: {str(e)}",
                error_code="LATEX_CHECK_ERROR"
            )
    
    def check_python_installation(self) -> Result:
        """
        Check if Python is properly installed and accessible.
        
        Returns:
            Result: Success if Python is available, failure otherwise
        """
        try:
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            python_path = sys.executable
            
            self.logger.info(f"Python {python_version} found at: {python_path}")
            
            # Check if we have the minimum required version (3.7+)
            if sys.version_info >= (3, 7):
                return Result(
                    success=True,
                    message=f"Python {python_version} is available",
                    data={'version': python_version, 'path': python_path}
                )
            else:
                return Result(
                    success=False,
                    message=f"Python version {python_version} is too old. Minimum required: 3.7",
                    error_code="PYTHON_VERSION_TOO_OLD"
                )
                
        except Exception as e:
            self.logger.error(f"Error checking Python installation: {e}")
            return Result(
                success=False,
                message=f"Error checking Python installation: {str(e)}",
                error_code="PYTHON_CHECK_ERROR"
            )
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get basic system information for troubleshooting.
        
        Returns:
            Dict[str, str]: System information
        """
        import platform
        import sys
        
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'python_executable': str(Path(sys.executable)),
        }
        
        # Add PATH information
        path_env = os.environ.get('PATH', '')
        info['path_directories'] = len(path_env.split(os.pathsep))
        
        return info
    
    def _get_installation_instruction(self, dependency: str) -> str:
        """
        Get installation instruction for a specific dependency based on the current platform.
        
        Args:
            dependency: Name of the dependency
            
        Returns:
            str: Installation instruction
        """
        import platform
        
        system = platform.system().lower()
        if system == 'darwin':
            system = 'macos'
        elif system not in ['windows', 'linux', 'macos']:
            system = 'linux'  # Default to linux for unknown systems
        
        instructions = self.INSTALLATION_INSTRUCTIONS.get(dependency, {})
        return instructions.get(system, f"Please install {dependency} for your operating system")
    
    def validate_configuration(self) -> ConfigurationResult:
        """
        Validate all configuration files and directories, creating missing ones.
        
        Returns:
            ConfigurationResult: Result containing validation status and created items
        """
        self.logger.info("Starting comprehensive configuration validation")
        
        missing_files = []
        missing_directories = []
        created_files = []
        created_directories = []
        validation_errors = []
        
        # Import config to get paths
        try:
            import config
        except ImportError:
            self.logger.error("Could not import config module")
            return ConfigurationResult(
                success=False,
                message="Configuration module not found",
                error_code="CONFIG_MODULE_NOT_FOUND"
            )
        
        # Define required directories with descriptions
        required_directories = {
            config.RUTA_TRACKERS: "Data tracking directory",
            config.RUTA_RECURSOS: "Templates and resources directory", 
            config.RUTA_REPORTES: "Reports output directory",
            config.RUTA_RESOLUCIONES: "Resolutions output directory",
            os.path.join(config.RUTA_BASE, "logs"): "Application logs directory"
        }
        
        # Check and create directories
        for directory, description in required_directories.items():
            if not os.path.exists(directory):
                missing_directories.append(directory)
                try:
                    os.makedirs(directory, exist_ok=True)
                    created_directories.append(directory)
                    self.logger.info(f"Created {description}: {directory}")
                except Exception as e:
                    error_msg = f"Failed to create {description} {directory}: {str(e)}"
                    self.logger.error(error_msg)
                    validation_errors.append(error_msg)
            else:
                # Validate directory permissions
                if not os.access(directory, os.W_OK):
                    error_msg = f"No write permission for directory: {directory}"
                    self.logger.warning(error_msg)
                    validation_errors.append(error_msg)
        
        # Define required configuration files with their validation and default content
        config_files = {
            config.RUTA_CONFIG_JSON: {
                'description': 'Monthly configuration file',
                'validator': self._validate_config_mes_json,
                'default_content': self._get_default_config_mes(),
                'required': True
            },
            config.JSON_PRESUPUESTO: {
                'description': 'Base budget configuration file',
                'validator': self._validate_presupuesto_json,
                'default_content': self._get_default_presupuesto(),
                'required': True
            },
            config.CSV_GASTOS: {
                'description': 'Monthly expenses CSV file',
                'validator': self._validate_csv_structure,
                'default_content': self._get_default_csv_header(),
                'required': True
            },
            config.XLSX_INVERSIONES: {
                'description': 'Investments Excel file',
                'validator': self._validate_excel_structure,
                'default_content': None,  # Special handling for Excel
                'required': True
            }
        }
        
        # Template files (don't auto-create, but validate if they exist)
        template_files = {
            os.path.join(config.RUTA_RECURSOS, config.NOMBRE_PLANTILLA_RESOLUCION): {
                'description': 'LaTeX resolution template',
                'validator': self._validate_latex_template,
                'default_content': self._get_default_template(),
                'required': False  # Templates are not auto-created
            }
        }
        
        # Validate and create configuration files
        for file_path, file_info in config_files.items():
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                try:
                    if file_path.endswith('.xlsx'):
                        self._create_default_excel_file(file_path)
                    else:
                        self._create_file_with_content(file_path, file_info['default_content'])
                    created_files.append(file_path)
                    self.logger.info(f"Created {file_info['description']}: {file_path}")
                except Exception as e:
                    error_msg = f"Failed to create {file_info['description']} {file_path}: {str(e)}"
                    self.logger.error(error_msg)
                    validation_errors.append(error_msg)
            else:
                # Validate existing file structure
                try:
                    validation_result = file_info['validator'](file_path)
                    if not validation_result:
                        error_msg = f"Invalid structure in {file_info['description']}: {file_path}"
                        self.logger.warning(error_msg)
                        validation_errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Failed to validate {file_info['description']} {file_path}: {str(e)}"
                    self.logger.warning(error_msg)
                    validation_errors.append(error_msg)
        
        # Validate template files (don't auto-create)
        for file_path, file_info in template_files.items():
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                self.logger.warning(f"Missing {file_info['description']}: {file_path}")
            else:
                # Validate template structure
                try:
                    validation_result = file_info['validator'](file_path)
                    if not validation_result:
                        error_msg = f"Invalid structure in {file_info['description']}: {file_path}"
                        self.logger.warning(error_msg)
                        validation_errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Failed to validate {file_info['description']} {file_path}: {str(e)}"
                    self.logger.warning(error_msg)
                    validation_errors.append(error_msg)
        
        # Check for additional resource files (logos, signatures)
        resource_files = {
            os.path.join(config.RUTA_RECURSOS, "logo.png"): "Logo image file",
            os.path.join(config.RUTA_RECURSOS, "firma.png"): "Signature image file"
        }
        
        for file_path, description in resource_files.items():
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                self.logger.warning(f"Missing {description}: {file_path}")
        
        # Determine success status
        critical_missing = [f for f in missing_files if any(
            f == path and info['required'] 
            for path, info in {**config_files, **template_files}.items()
        )]
        
        success = len(validation_errors) == 0 and len(critical_missing) == 0
        
        # Build result message
        if success:
            message = "All configuration files and directories are valid"
            if created_files or created_directories:
                message += f" (created {len(created_files)} files, {len(created_directories)} directories)"
        else:
            message_parts = []
            if validation_errors:
                message_parts.append(f"{len(validation_errors)} validation errors")
            if critical_missing:
                message_parts.append(f"{len(critical_missing)} critical files missing")
            message = f"Configuration validation completed with {', '.join(message_parts)}"
        
        result = ConfigurationResult(
            success=success,
            message=message,
            missing_files=missing_files if missing_files else None,
            missing_directories=missing_directories if missing_directories else None,
            created_files=created_files if created_files else None,
            created_directories=created_directories if created_directories else None
        )
        
        # Add validation errors to result data
        if validation_errors:
            result.data = {'validation_errors': validation_errors}
        
        return result
    
    def _get_default_config_mes(self) -> str:
        """Get default content for config_mes.json."""
        from datetime import datetime, timedelta
        current_date = datetime.now()
        previous_month = (current_date.replace(day=1) - timedelta(days=1))
        
        default_config = {
            "titulo_documento": f"Presupuesto mensual de {current_date.strftime('%B').lower()}",
            "mes_nombre": current_date.strftime('%B').lower(),
            "mes_anterior": previous_month.strftime('%B').lower(),
            "mensualidad_anterior_monto": "0",
            "gastos_mes_anterior": [
                {
                    "descripcion": "Ejemplo de gasto",
                    "monto": "0"
                }
            ],
            "considerandos_adicionales": [
                "Que para el mes actual se proyecta un presupuesto inicial.",
                "Que se debe mantener un registro detallado de todos los gastos.",
                "Que este es un archivo de configuración generado automáticamente."
            ],
            "articulos": [
                "Aprobar el presupuesto mensual correspondiente al mes actual.",
                "Registrar todos los gastos y movimientos financieros del período.",
                "Mantener el control y seguimiento de las finanzas personales."
            ],
            "anexo": {}
        }
        
        return json.dumps(default_config, indent=2, ensure_ascii=False)
    
    def _get_default_presupuesto(self) -> str:
        """Get default content for presupuesto_base.json."""
        # Match the actual structure used in the existing file
        default_presupuesto = {
            "Comida": 25000,
            "Transporte": 8000,
            "Ocio": 15000,
            "Inversión": 50000,
            "Cuota Celular": 42416,
            "Regalos": 0
        }
        
        return json.dumps(default_presupuesto, indent=2, ensure_ascii=False)
    
    def _get_default_csv_header(self) -> str:
        """Get default CSV header for gastos_mensuales.csv."""
        return "Fecha,Categoria,Descripcion,Monto_ARS\n"
    
    def _get_default_template(self) -> str:
        """Get default LaTeX template content."""
        return """\\documentclass[12pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[spanish]{babel}
\\usepackage{geometry}
\\usepackage{graphicx}

\\geometry{margin=2.5cm}

\\begin{document}

\\begin{center}
\\textbf{\\Large {{ titulo }}}\\\\
\\vspace{0.5cm}
\\textbf{Mes: {{ mes_nombre }}}
\\end{center}

\\vspace{1cm}

\\section*{Consideraciones}
{% for consideracion in consideraciones_adicionales %}
\\item {{ consideracion }}
{% endfor %}

\\vspace{1cm}

\\section*{Artículos}
{% for articulo in articulos %}
{{ articulo }}\\\\
{% endfor %}

\\end{document}
"""
    
    def _create_file_with_content(self, file_path: str, content: str) -> None:
        """
        Create a file with the specified content.
        
        Args:
            file_path: Path to the file to create
            content: Content to write to the file
        """
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_default_excel_file(self, file_path: str) -> None:
        """
        Create a default Excel file for investments tracking.
        
        Args:
            file_path: Path to the Excel file to create
        """
        try:
            import pandas as pd
            
            # Create empty DataFrame with required columns
            df = pd.DataFrame(columns=['Fecha', 'Activo', 'Tipo', 'Monto'])
            
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Save to Excel
            df.to_excel(file_path, index=False, sheet_name='Inversiones')
            
        except ImportError:
            # If pandas is not available, create a simple CSV-like structure
            self.logger.warning("pandas not available, creating simple Excel alternative")
            content = "Fecha,Activo,Tipo,Monto\n"
            # Save as CSV with .xlsx extension (will be converted later if needed)
            with open(file_path.replace('.xlsx', '.csv'), 'w', encoding='utf-8') as f:
                f.write(content)
    
    def validate_startup_requirements(self) -> DependencyResult:
        """
        Validate all startup requirements and provide detailed feedback.
        This method should be called during application startup.
        
        Returns:
            DependencyResult: Comprehensive validation result
        """
        self.logger.info("Validating startup requirements")
        
        # Get system info for troubleshooting
        system_info = self.get_system_info()
        self.logger.info(f"System info: {system_info}")
        
        # Check all dependencies
        dependency_result = self.check_all_dependencies()
        
        # Check configuration
        config_result = self.validate_configuration()
        
        # Combine results
        all_success = dependency_result.success and config_result.success
        
        if not all_success:
            # Log detailed information for troubleshooting
            self.logger.error("Startup validation found issues")
            if not dependency_result.success:
                self.logger.error(f"Missing dependencies: {dependency_result.missing_dependencies}")
            if not config_result.success:
                self.logger.error(f"Configuration issues: {config_result.message}")
            
            # Combine error messages
            messages = []
            if not dependency_result.success:
                messages.append(dependency_result.message)
            if not config_result.success:
                messages.append(config_result.message)
            
            # Add system info to result for better error reporting
            dependency_result.data = {
                'system_info': system_info,
                'missing_dependencies': dependency_result.missing_dependencies,
                'installation_instructions': dependency_result.installation_instructions,
                'configuration_result': {
                    'success': config_result.success,
                    'message': config_result.message,
                    'missing_files': config_result.missing_files,
                    'created_files': config_result.created_files,
                    'created_directories': config_result.created_directories
                }
            }
            dependency_result.message = "; ".join(messages)
            dependency_result.success = all_success
        else:
            self.logger.info("All startup requirements validated successfully")
            dependency_result.data = {
                'system_info': system_info,
                'configuration_result': {
                    'success': config_result.success,
                    'message': config_result.message,
                    'created_files': config_result.created_files,
                    'created_directories': config_result.created_directories
                }
            }
        
        return dependency_result
    
    def validate_complete_system(self) -> DependencyResult:
        """
        Perform complete system validation including dependencies and configuration.
        This is the main method to call during application startup.
        
        Returns:
            DependencyResult: Comprehensive validation result
        """
        self.logger.info("Starting complete system validation")
        
        # Get system info for troubleshooting
        system_info = self.get_system_info()
        self.logger.info(f"System info: {system_info}")
        
        # Check all dependencies
        dependency_result = self.check_all_dependencies()
        
        # Check configuration regardless of dependency status
        config_result = self.validate_configuration()
        
        # Combine results
        all_success = dependency_result.success and config_result.success
        
        # Build comprehensive result
        messages = []
        if not dependency_result.success:
            messages.append(f"Dependencies: {dependency_result.message}")
        if not config_result.success:
            messages.append(f"Configuration: {config_result.message}")
        
        if all_success:
            message = "System validation completed successfully"
            if config_result.created_files or config_result.created_directories:
                created_items = []
                if config_result.created_files:
                    created_items.append(f"{len(config_result.created_files)} files")
                if config_result.created_directories:
                    created_items.append(f"{len(config_result.created_directories)} directories")
                message += f" (created {', '.join(created_items)})"
        else:
            message = "; ".join(messages)
        
        # Create comprehensive result
        result = DependencyResult(
            success=all_success,
            message=message,
            missing_dependencies=dependency_result.missing_dependencies,
            installation_instructions=dependency_result.installation_instructions,
            data={
                'system_info': system_info,
                'dependency_check': {
                    'success': dependency_result.success,
                    'message': dependency_result.message,
                    'missing_dependencies': dependency_result.missing_dependencies,
                    'installation_instructions': dependency_result.installation_instructions
                },
                'configuration_check': {
                    'success': config_result.success,
                    'message': config_result.message,
                    'missing_files': config_result.missing_files,
                    'missing_directories': config_result.missing_directories,
                    'created_files': config_result.created_files,
                    'created_directories': config_result.created_directories,
                    'validation_errors': (config_result.data or {}).get('validation_errors', []) if hasattr(config_result, 'data') else []
                }
            }
        )
        
        if all_success:
            self.logger.info("Complete system validation passed")
        else:
            self.logger.error(f"System validation issues found: {message}")
        
        return result
    
    def _validate_config_mes_json(self, file_path: str) -> bool:
        """
        Validate the structure of config_mes.json file.
        
        Args:
            file_path: Path to the config_mes.json file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Check required fields
            required_fields = [
                'titulo_documento', 'mes_nombre', 'mes_anterior', 
                'mensualidad_anterior_monto', 'gastos_mes_anterior',
                'considerandos_adicionales', 'articulos'
            ]
            
            for field in required_fields:
                if field not in config_data:
                    self.logger.warning(f"Missing required field '{field}' in config_mes.json")
                    return False
            
            # Validate gastos_mes_anterior structure
            if isinstance(config_data['gastos_mes_anterior'], list):
                for gasto in config_data['gastos_mes_anterior']:
                    if not isinstance(gasto, dict) or 'descripcion' not in gasto or 'monto' not in gasto:
                        self.logger.warning("Invalid structure in gastos_mes_anterior")
                        return False
            
            # Validate lists
            if not isinstance(config_data['considerandos_adicionales'], list):
                self.logger.warning("considerandos_adicionales must be a list")
                return False
                
            if not isinstance(config_data['articulos'], list):
                self.logger.warning("articulos must be a list")
                return False
            
            return True
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON in config_mes.json: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Error validating config_mes.json: {e}")
            return False
    
    def _validate_presupuesto_json(self, file_path: str) -> bool:
        """
        Validate the structure of presupuesto_base.json file.
        
        Args:
            file_path: Path to the presupuesto_base.json file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                presupuesto_data = json.load(f)
            
            # Check if it's a dictionary with category names as keys and amounts as values
            if not isinstance(presupuesto_data, dict):
                self.logger.warning("presupuesto_base.json must be a dictionary")
                return False
            
            # Validate that all values are numeric
            for categoria, monto in presupuesto_data.items():
                if not isinstance(monto, (int, float)):
                    self.logger.warning(f"Invalid amount for category '{categoria}': must be numeric")
                    return False
                if monto < 0:
                    self.logger.warning(f"Invalid amount for category '{categoria}': must be non-negative")
                    return False
            
            return True
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON in presupuesto_base.json: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Error validating presupuesto_base.json: {e}")
            return False
    
    def _validate_csv_structure(self, file_path: str) -> bool:
        """
        Validate the structure of the CSV expenses file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            
            # Check if header exists and has required columns
            expected_columns = ['Fecha', 'Categoria', 'Descripcion', 'Monto']
            header_columns = [col.strip() for col in first_line.split(',')]
            
            # Allow for different column orders and slight variations
            for expected_col in expected_columns:
                if not any(expected_col.lower() in col.lower() for col in header_columns):
                    self.logger.warning(f"Missing expected column '{expected_col}' in CSV header")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error validating CSV structure: {e}")
            return False
    
    def _validate_excel_structure(self, file_path: str) -> bool:
        """
        Validate the structure of the Excel investments file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Try to read with pandas first
            try:
                import pandas as pd
                df = pd.read_excel(file_path)
                
                # Check if required columns exist
                expected_columns = ['Fecha', 'Activo', 'Tipo', 'Monto']
                for expected_col in expected_columns:
                    if not any(expected_col.lower() in col.lower() for col in df.columns):
                        self.logger.warning(f"Missing expected column '{expected_col}' in Excel file")
                        return False
                
                return True
                
            except ImportError:
                # If pandas is not available, just check if file exists and is readable
                self.logger.info("pandas not available, performing basic Excel file validation")
                return os.path.exists(file_path) and os.path.getsize(file_path) > 0
                
        except Exception as e:
            self.logger.warning(f"Error validating Excel structure: {e}")
            return False
    
    def _validate_latex_template(self, file_path: str) -> bool:
        """
        Validate the structure of the LaTeX template file.
        
        Args:
            file_path: Path to the LaTeX template file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Check for basic LaTeX structure
            required_elements = [
                '\\documentclass',
                '\\begin{document}',
                '\\end{document}'
            ]
            
            for element in required_elements:
                if element not in template_content:
                    self.logger.warning(f"Missing required LaTeX element '{element}' in template")
                    return False
            
            # Check for Jinja2 template variables that are expected
            expected_variables = [
                '{{ titulo_documento }}',
                '{{ mes_nombre }}',
                '{{ gastos_mes_anterior }}',
                '{{ considerandos_adicionales }}',
                '{{ articulos }}'
            ]
            
            missing_variables = []
            for variable in expected_variables:
                if variable not in template_content:
                    missing_variables.append(variable)
            
            if missing_variables:
                self.logger.warning(f"Missing expected template variables: {missing_variables}")
                # Don't return False here as templates might have different variable names
                # Just log the warning
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error validating LaTeX template: {e}")
            return False