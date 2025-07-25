# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from services.pdf_generator import PDFGenerator
from services.latex_processor import LaTeXProcessor
from services.exceptions import PECOError, LaTeXError, ConfigurationError
from services.logging_config import setup_logging, get_logger
from config import RUTA_CONFIG_JSON, RUTA_RECURSOS, NOMBRE_PLANTILLA_RESOLUCION, RUTA_RESOLUCIONES

# Setup logging
setup_logging()  # Initialize logging system
logger = get_logger("generar_resolucion" if __name__ == "__main__" else __name__)

# --- DICCIONARIO PARA MESES EN ROMANO ---
meses_romanos = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
    7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
}

def generar_resolucion():
    """
    Función principal que lee la configuración y genera la resolución PDF
    usando el PDFGenerator y LaTeXProcessor services.
    """
    print("--- [INFO] Iniciando generador de resoluciones PECO ---")
    
    try:
        # Load configuration
        try:
            with open(RUTA_CONFIG_JSON, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("[OK] Datos de config_mes.json cargados correctamente.")
            logger.info("Configuration loaded successfully from config_mes.json")
        except FileNotFoundError:
            raise ConfigurationError(
                f"No se encontró el archivo de configuración: {RUTA_CONFIG_JSON}",
                "CONFIG_FILE_NOT_FOUND"
            )
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Error al parsear el archivo JSON: {e}",
                "CONFIG_JSON_INVALID"
            )

        # Generate resolution code and date information
        try:
            fecha_actual = datetime.now()
            dia = fecha_actual.day
            mes_romano = meses_romanos[fecha_actual.month]
            año_corto = fecha_actual.strftime('%y')
            codigo_res = f"r{dia}e{mes_romano}s{año_corto}"
            nombre_archivo_base = f"{codigo_res} - {config.get('titulo_documento', 'Resolucion')}"
            
            # Add generated data to config
            config['codigo_res'] = codigo_res
            config['fecha_larga'] = fecha_actual.strftime(f'%d de {config.get("mes_nombre", "mes")} de %Y')
            
            logger.info(f"Resolution code generated: {codigo_res}")
        except KeyError as e:
            raise ConfigurationError(
                f"Falta una clave en el archivo de configuración: {e}",
                "CONFIG_MISSING_KEY"
            )

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
        
        # Validate template file exists
        if not os.path.exists(template_path):
            raise ConfigurationError(
                f"No se encontró la plantilla de resolución: {template_path}",
                "TEMPLATE_NOT_FOUND",
                details={'template_path': template_path, 'expected_location': RUTA_RECURSOS}
            )

        # Generate PDF using service layer with correct method signature
        result = pdf_generator.generate_resolution(
            template_path=template_path,
            data=config,
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
