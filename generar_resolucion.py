# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from services.pdf_generator import PDFGenerator
from services.latex_processor import LaTeXProcessor
from services.config_validator import ConfigValidator
from services.exceptions import PECOError, LaTeXError, ConfigurationError
from services.logging_config import setup_logging, get_logger
from config import RUTA_CONFIG_JSON, RUTA_RECURSOS, NOMBRE_PLANTILLA_RESOLUCION, RUTA_RESOLUCIONES

# Setup logging
setup_logging()  # Initialize logging system
logger = get_logger("generar_resolucion" if __name__ == "__main__" else __name__)


def check_existing_resolution_today(output_dir: str, current_codigo_res: str) -> dict:
    """
    Check if there's already a resolution generated today and return file paths for replacement.
    
    Args:
        output_dir: Directory where resolutions are stored
        current_codigo_res: Current resolution code being generated
        
    Returns:
        Dictionary with existing file paths or empty dict if none found
    """
    if not os.path.exists(output_dir):
        return {}
    
    # Extract day and month from current resolution code (format: rDDeMMsYY)
    if not current_codigo_res or len(current_codigo_res) < 8:
        return {}
    
    try:
        # Parse current resolution code to extract day pattern
        # Format: r{day}e{roman_month}s{year}
        day_part = current_codigo_res.split('e')[0][1:]  # Remove 'r' and get day
        month_year_part = current_codigo_res.split('e')[1]  # Get month and year part
        
        # Look for files with the same day pattern
        pattern_prefix = f"r{day_part}e{month_year_part}"
        
        existing_files = []
        for filename in os.listdir(output_dir):
            if filename.startswith(pattern_prefix) and filename != f"{current_codigo_res} - ":
                file_path = os.path.join(output_dir, filename)
                existing_files.append(file_path)
        
        if existing_files:
            # Find the main PDF file
            pdf_file = None
            tex_file = None
            all_files = []
            
            for file_path in existing_files:
                all_files.append(file_path)
                if file_path.endswith('.pdf'):
                    pdf_file = file_path
                elif file_path.endswith('.tex'):
                    tex_file = file_path
            
            return {
                'pdf_file': pdf_file,
                'tex_file': tex_file,
                'all_files': all_files
            }
    
    except Exception as e:
        logger.warning(f"Error checking for existing resolution: {e}")
    
    return {}



def generar_resolucion():
    """
    Función principal que lee la configuración y genera la resolución PDF
    usando el ConfigValidator, PDFGenerator y LaTeXProcessor services.
    """
    print("--- [INFO] Iniciando generador de resoluciones PECO ---")
    
    try:
        # Initialize configuration validator
        config_validator = ConfigValidator()
        
        # Load and validate configuration using the new validator
        print("[INFO] Cargando y validando configuración...")
        validation_result = config_validator.validate_and_load_config(RUTA_CONFIG_JSON)
        
        if not validation_result.success:
            print(f"[ERROR] Validación de configuración falló: {validation_result.message}")
            if validation_result.validation_errors:
                print("Errores encontrados:")
                for error in validation_result.validation_errors:
                    print(f"  - {error}")
            raise ConfigurationError(
                f"Configuration validation failed: {validation_result.message}",
                "CONFIG_VALIDATION_FAILED"
            )
        
        config = validation_result.data
        print("[OK] Configuración cargada y validada correctamente.")
        
        if validation_result.warnings:
            print("Advertencias:")
            for warning in validation_result.warnings:
                print(f"  - {warning}")
        
        logger.info("Configuration loaded and validated successfully")

        # Process configuration for template rendering
        print("[INFO] Procesando configuración para plantilla...")
        processing_result = config_validator.process_configuration_for_template(config)
        
        if not processing_result.success:
            print(f"[ERROR] Procesamiento de configuración falló: {processing_result.message}")
            raise ConfigurationError(
                f"Configuration processing failed: {processing_result.message}",
                "CONFIG_PROCESSING_FAILED"
            )
        
        processed_config = processing_result.data
        print("[OK] Configuración procesada correctamente.")
        
        # Generate filename base from processed config
        nombre_archivo_base = processed_config.get('titulo_documento', 'Resolucion')
        
        logger.info(f"Resolution code generated: {processed_config.get('codigo_res', 'N/A')}")
        logger.info(f"Configuration processing completed successfully")

        # Initialize services
        latex_processor = LaTeXProcessor()
        pdf_generator = PDFGenerator(latex_processor)
        
        # Check LaTeX availability
        if not pdf_generator.check_latex_availability():
            raise LaTeXError(
                "El comando 'pdflatex' no se encontró. Asegúrate de tener una distribución de LaTeX instalada.",
                "LATEX_NOT_FOUND"
            )

        # Prepare template and output paths
        template_path = os.path.join(RUTA_RECURSOS, NOMBRE_PLANTILLA_RESOLUCION)
        output_dir = RUTA_RESOLUCIONES
        
        # Check for existing resolution from today and handle replacement
        existing_files = check_existing_resolution_today(output_dir, processed_config.get('codigo_res', ''))
        if existing_files:
            print(f"[INFO] Se encontró resolución existente del día de hoy: {os.path.basename(existing_files['pdf_file']) if existing_files['pdf_file'] else 'archivos relacionados'}")
            print("[INFO] Reemplazando automáticamente...")
            
            # Remove existing files
            for file_path in existing_files['all_files']:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"[INFO] Archivo eliminado: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"[WARNING] No se pudo eliminar {file_path}: {e}")
        
        # Validate template file exists
        if not os.path.exists(template_path):
            raise ConfigurationError(
                f"No se encontró la plantilla de resolución: {template_path}",
                "TEMPLATE_NOT_FOUND",
                details={'template_path': template_path, 'expected_location': RUTA_RECURSOS}
            )

        # Generate PDF using service layer with processed configuration
        result = pdf_generator.generate_resolution(
            template_path=template_path,
            data=processed_config,
            output_dir=output_dir,
            filename_base=nombre_archivo_base
        )
        
        if result.success:
            print(f"\n[OK] PDF generado con éxito en: {result.pdf_path}")
            print(f"   Archivo LaTeX: {result.tex_path}")
            if result.details and result.details.get('cleanup_result'):
                cleanup = result.details['cleanup_result']
                if cleanup['total_cleaned'] > 0:
                    print(f"   Archivos temporales limpiados: {', '.join(cleanup['cleaned_files'])}")
                if cleanup['total_failed'] > 0:
                    print(f"   Advertencia: No se pudieron limpiar algunos archivos temporales")
            logger.info(f"PDF generated successfully: {result.pdf_path}")
        else:
            print(f"\n[ERROR] Falló la generación del PDF: {result.message}")
            if result.error_code:
                print(f"   Código de error: {result.error_code}")
            
            # Provide specific error guidance based on error code
            if result.error_code == "TEMPLATE_ERROR":
                print("   Sugerencia: Verifica que la plantilla LaTeX esté correctamente formateada")
                if result.details and 'template_path' in result.details:
                    print(f"   Plantilla utilizada: {result.details['template_path']}")
            elif result.error_code == "COMPILATION_ERROR" or result.error_code == "COMPILATION_FAILED":
                print("   Sugerencia: Revisa el log de compilación para errores específicos de LaTeX")
                if result.details and 'return_code' in result.details:
                    print(f"   Código de retorno de pdflatex: {result.details['return_code']}")
            elif result.error_code == "DIRECTORY_ERROR":
                print("   Sugerencia: Verifica permisos de escritura en el directorio de salida")
                print(f"   Directorio: {output_dir}")
            elif result.error_code == "FILE_WRITE_ERROR":
                print("   Sugerencia: Verifica permisos de escritura y espacio en disco")
                if result.details and 'tex_path' in result.details:
                    print(f"   Archivo problemático: {result.details['tex_path']}")
            
            # Show compilation log if available
            if result.compilation_log:
                print("\n--- Log de compilación LaTeX ---")
                # Show only the most relevant parts of the log
                log_lines = result.compilation_log.split('\n')
                error_lines = [line for line in log_lines if 'error' in line.lower() or 'failed' in line.lower()]
                if error_lines:
                    print("Errores encontrados:")
                    for line in error_lines[:5]:  # Show first 5 error lines
                        print(f"   {line.strip()}")
                else:
                    # Show last few lines which usually contain the summary
                    print("Últimas líneas del log:")
                    for line in log_lines[-5:]:
                        if line.strip():
                            print(f"   {line.strip()}")
            
            # Show additional details if available
            if result.details:
                if 'stderr' in result.details and result.details['stderr']:
                    print(f"\n--- Errores del sistema ---")
                    print(result.details['stderr'])
            
            logger.error(f"PDF generation failed: {result.message}", extra={
                'error_code': result.error_code,
                'details': result.details
            })

    except PECOError as e:
        print(f"\n[ERROR] {e.message}")
        if e.error_code:
            print(f"   Código de error: {e.error_code}")
        logger.error(f"PECO Error in resolution generation: {e.message}", extra={'error_code': e.error_code})
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error inesperado: {e}")
        logger.error(f"Unexpected error in resolution generation: {e}", exc_info=True)

if __name__ == "__main__":
    generar_resolucion()
