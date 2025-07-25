# -*- coding: utf-8 -*-
import os
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# Add services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.data_manager import DataManager
from services.exceptions import DataError, PECOError
from services.logging_config import get_logger
from config import RUTA_REPORTES

# Initialize logger
logger = get_logger(__name__)

FECHA_HOY = datetime.now()
MES_ACTUAL = FECHA_HOY.month
AÑO_ACTUAL = FECHA_HOY.year

def get_analysis_data(data_manager: DataManager, month: int, year: int):
    """
    Get comprehensive analysis data using DataManager service.
    
    Args:
        data_manager: DataManager instance
        month: Month number (1-12)
        year: Year
        
    Returns:
        AnalysisResult with financial data or None if error
    """
    try:
        logger.info(f"Getting analysis data for {month}/{year}")
        analysis_result = data_manager.get_monthly_analysis(month, year)
        
        if not analysis_result.success:
            logger.error(f"Failed to get analysis data: {analysis_result.message}")
            print(f"[ERROR] {analysis_result.message}")
            return None
            
        return analysis_result
        
    except Exception as e:
        logger.error(f"Unexpected error getting analysis data: {e}")
        print(f"[ERROR] Error inesperado al obtener datos de análisis: {e}")
        return None

def validate_chart_data(gastos_por_categoria):
    """
    Validate data completeness and quality before generating visualizations.
    
    Args:
        gastos_por_categoria: Dictionary with category expenses
        
    Returns:
        tuple: (is_valid, cleaned_data, validation_message)
    """
    if not gastos_por_categoria:
        return False, {}, "No hay datos de gastos proporcionados"
    
    if not isinstance(gastos_por_categoria, dict):
        return False, {}, "Los datos de gastos deben ser un diccionario"
    
    if len(gastos_por_categoria) == 0:
        return False, {}, "No hay categorías de gastos para mostrar"
    
    # Clean and validate data
    cleaned_data = {}
    total_amount = 0
    validation_warnings = []
    
    for categoria, monto in gastos_por_categoria.items():
        try:
            # Convert to float and validate
            amount = float(monto)
            
            # Check for reasonable amount ranges (0 to 10 million ARS)
            if amount > 10_000_000:
                validation_warnings.append(f"Monto muy alto para {categoria}: ${amount:,.2f} - posible error de datos")
                logger.warning(f"Extremely high amount for category {categoria}: {amount}")
                # Still include but cap at reasonable maximum
                amount = min(amount, 10_000_000)
            
            if amount > 0:
                cleaned_data[str(categoria)] = amount
                total_amount += amount
            elif amount < 0:
                validation_warnings.append(f"Monto negativo ignorado para {categoria}: ${amount:,.2f}")
                logger.warning(f"Negative amount found for category {categoria}: {amount}")
            else:
                validation_warnings.append(f"Monto cero ignorado para {categoria}")
                logger.info(f"Zero amount found for category {categoria}")
                
        except (ValueError, TypeError) as e:
            validation_warnings.append(f"Monto inválido para {categoria}: {monto}")
            logger.warning(f"Invalid amount for category {categoria}: {monto} - {e}")
            continue
    
    if not cleaned_data:
        return False, {}, "No hay montos válidos para mostrar en el gráfico"
    
    if total_amount == 0:
        return False, {}, "El total de gastos es cero"
    
    # Check for reasonable data distribution
    max_amount = max(cleaned_data.values())
    min_amount = min(cleaned_data.values())
    
    if max_amount / min_amount > 10000:  # Very skewed data
        validation_warnings.append("Datos muy desbalanceados - el gráfico puede ser difícil de leer")
        logger.warning("Data is highly skewed - chart may not be readable")
    
    # Check for too many categories (affects readability)
    if len(cleaned_data) > 15:
        validation_warnings.append(f"Muchas categorías ({len(cleaned_data)}) - considerando agrupar las menores")
        logger.warning(f"Too many categories for optimal chart readability: {len(cleaned_data)}")
    
    # Prepare validation message
    base_message = f"Datos validados: {len(cleaned_data)} categorías, total ${total_amount:,.2f}"
    if validation_warnings:
        warning_text = "; ".join(validation_warnings[:3])  # Limit to first 3 warnings
        validation_message = f"{base_message}. Advertencias: {warning_text}"
    else:
        validation_message = base_message
    
    return True, cleaned_data, validation_message


def create_fallback_chart(gastos_por_categoria, month: int, year: int, ruta_guardado: str):
    """
    Create a simple fallback chart when the main chart generation fails.
    
    Args:
        gastos_por_categoria: Dictionary with category expenses
        month: Month number
        year: Year
        ruta_guardado: Path where to save the chart
        
    Returns:
        str: Path to saved chart or None if failed
    """
    try:
        logger.info("Creating fallback chart with basic styling")
        
        # Ensure matplotlib backend is available
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
        except Exception as backend_error:
            logger.warning(f"Could not set matplotlib backend: {backend_error}")
        
        # Use basic matplotlib without seaborn
        plt.style.use('default')
        
        # Create figure with error handling
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
        except Exception as fig_error:
            logger.error(f"Failed to create matplotlib figure: {fig_error}")
            return None
        
        categories = list(gastos_por_categoria.keys())
        amounts = list(gastos_por_categoria.values())
        
        # Truncate category names if too long
        truncated_categories = [cat[:12] + '...' if len(cat) > 15 else cat for cat in categories]
        
        try:
            # Create simple bar chart as fallback
            bars = ax.bar(truncated_categories, amounts, color='steelblue', alpha=0.7)
            ax.set_title(f'Gastos por Categoría - {month:02d}/{year}', fontsize=14, fontweight='bold')
            ax.set_ylabel('Monto (ARS)', fontsize=12)
            
            # Rotate labels if too many categories
            if len(categories) > 5:
                plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars with error handling
            try:
                for bar, amount in zip(bars, amounts):
                    height = bar.get_height()
                    # Format amount based on size
                    if amount >= 1_000_000:
                        label = f'${amount/1_000_000:.1f}M'
                    elif amount >= 1_000:
                        label = f'${amount/1_000:.0f}K'
                    else:
                        label = f'${amount:,.0f}'
                    
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           label, ha='center', va='bottom', fontsize=9)
            except Exception as label_error:
                logger.warning(f"Could not add value labels to fallback chart: {label_error}")
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3, axis='y')
            
        except Exception as chart_error:
            logger.error(f"Error creating chart elements: {chart_error}")
            plt.close(fig)
            return None
        
        # Save with multiple attempts and error handling
        save_successful = False
        for attempt, (dpi, quality) in enumerate([(150, 'media'), (100, 'básica'), (75, 'mínima')], 1):
            try:
                plt.tight_layout()
                plt.savefig(ruta_guardado, dpi=dpi, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                save_successful = True
                logger.info(f"Fallback chart saved successfully with {quality} quality: {ruta_guardado}")
                break
            except Exception as save_error:
                logger.warning(f"Save attempt {attempt} failed with {quality} quality: {save_error}")
                if attempt == 3:  # Last attempt
                    logger.error(f"All fallback save attempts failed")
        
        plt.close(fig)
        
        if save_successful:
            return ruta_guardado
        else:
            return None
        
    except Exception as e:
        logger.error(f"Fallback chart generation failed completely: {e}")
        try:
            plt.close('all')
        except:
            pass
        return None


def validate_matplotlib_availability():
    """
    Validate that matplotlib is available and can create charts.
    
    Returns:
        tuple: (is_available, error_message)
    """
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        
        # Test basic functionality
        fig, ax = plt.subplots(figsize=(1, 1))
        ax.plot([1, 2], [1, 2])
        plt.close(fig)
        
        logger.debug("Matplotlib validation successful")
        return True, None
        
    except ImportError as e:
        error_msg = f"Matplotlib no está instalado: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error al validar matplotlib: {e}"
        logger.error(error_msg)
        return False, error_msg


def generar_grafico_gastos(gastos_por_categoria, month: int, year: int):
    """
    Generate expense chart with comprehensive error handling, validation, and fallback mechanisms.
    
    Args:
        gastos_por_categoria: Dictionary with category expenses
        month: Month number
        year: Year
        
    Returns:
        str: Path to saved chart or None if failed
    """
    print("\n[INFO] Generando gráfico de gastos...")
    logger.info(f"Starting chart generation for {month}/{year}")
    
    # Validate matplotlib availability first
    matplotlib_available, matplotlib_error = validate_matplotlib_availability()
    if not matplotlib_available:
        logger.error(f"Matplotlib validation failed: {matplotlib_error}")
        print(f"[ERROR] No se puede generar gráfico: {matplotlib_error}")
        return None
    
    # Validate data completeness before processing
    is_valid, cleaned_data, validation_message = validate_chart_data(gastos_por_categoria)
    
    if not is_valid:
        logger.warning(f"Data validation failed: {validation_message}")
        print(f"[WARNING] {validation_message}")
        return None
    
    logger.info(f"Data validation passed: {validation_message}")
    
    # Show validation warnings if any
    if "Advertencias:" in validation_message:
        print(f"[INFO] {validation_message}")
    else:
        print(f"[OK] {validation_message}")
    
    # Ensure reports directory exists with proper error handling
    try:
        if not os.path.exists(RUTA_REPORTES):
            os.makedirs(RUTA_REPORTES, exist_ok=True)
            logger.info(f"Created reports directory: {RUTA_REPORTES}")
    except OSError as e:
        logger.error(f"Failed to create reports directory: {e}")
        print(f"[ERROR] No se pudo crear el directorio de reportes: {e}")
        return None
    
    # Check write permissions
    try:
        test_file = os.path.join(RUTA_REPORTES, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except (OSError, IOError) as e:
        logger.error(f"No write permissions in reports directory: {e}")
        print(f"[ERROR] Sin permisos de escritura en el directorio de reportes: {e}")
        return None
    
    # Prepare file path
    nombre_grafico = f"reporte_gastos_{year}_{month:02d}.png"
    ruta_guardado = os.path.join(RUTA_REPORTES, nombre_grafico)
    
    # Try main chart generation with matplotlib
    try:
        logger.info("Attempting main chart generation")
        
        # Set up matplotlib style with fallback
        try:
            plt.style.use('seaborn-v0_8-deep')
            logger.debug("Using seaborn style")
        except (OSError, ValueError):
            try:
                plt.style.use('seaborn-deep')
                logger.debug("Using legacy seaborn style")
            except (OSError, ValueError):
                plt.style.use('default')
                logger.debug("Using default matplotlib style")
        
        # Create the main chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        categories = list(cleaned_data.keys())
        amounts = list(cleaned_data.values())
        
        # Create pie chart with error handling
        try:
            wedges, texts, autotexts = ax.pie(
                amounts, 
                autopct='%1.1f%%', 
                startangle=90, 
                pctdistance=0.85, 
                labels=categories,
                explode=[0.05 if i == amounts.index(max(amounts)) else 0 for i in range(len(amounts))]  # Explode largest slice
            )
            
            # Style the chart with error handling
            try:
                plt.setp(autotexts, size=10, weight="bold", color="white")
            except Exception:
                plt.setp(autotexts, size=10)  # Fallback without styling
            
            ax.set_title(f'Distribución de Gastos - {month:02d}/{year}', size=16, weight="bold")
            
        except Exception as pie_error:
            logger.warning(f"Pie chart creation failed, trying bar chart: {pie_error}")
            plt.close(fig)
            
            # Fallback to bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(categories, amounts)
            ax.set_title(f'Gastos por Categoría - {month:02d}/{year}', size=16, weight="bold")
            ax.set_ylabel('Monto (ARS)')
            
            # Rotate labels if needed
            if len(categories) > 5:
                plt.xticks(rotation=45, ha='right')
            
            # Add value labels
            for bar, amount in zip(bars, amounts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${amount:,.0f}', ha='center', va='bottom')
        
        # Save the chart with multiple format attempts
        save_successful = False
        for dpi, format_name in [(300, 'alta calidad'), (150, 'calidad media'), (75, 'calidad básica')]:
            try:
                plt.savefig(ruta_guardado, dpi=dpi, bbox_inches='tight', facecolor='white')
                save_successful = True
                logger.info(f"Chart saved successfully with {format_name}: {ruta_guardado}")
                print(f"[OK] Gráfico guardado con éxito en '{ruta_guardado}' ({format_name})!")
                break
            except Exception as save_error:
                logger.warning(f"Failed to save with {format_name} (DPI {dpi}): {save_error}")
                continue
        
        plt.close(fig)
        
        if save_successful:
            return ruta_guardado
        else:
            raise Exception("All save attempts failed")
            
    except Exception as main_error:
        logger.error(f"Main chart generation failed: {main_error}")
        print(f"[WARNING] Error en generación principal del gráfico: {main_error}")
        
        # Ensure any open figures are closed
        try:
            plt.close('all')
        except:
            pass
        
        # Try fallback chart generation
        print("[INFO] Intentando generar gráfico alternativo...")
        logger.info("Attempting fallback chart generation")
        
        fallback_result = create_fallback_chart(cleaned_data, month, year, ruta_guardado)
        
        if fallback_result:
            print(f"[OK] Gráfico alternativo guardado con éxito en '{fallback_result}'!")
            return fallback_result
        else:
            print("[ERROR] No se pudo generar ningún tipo de gráfico")
            logger.error("Both main and fallback chart generation failed")
            return None

def display_expense_summary(expenses_data, budget_data=None):
    """
    Display expense summary with budget comparison.
    
    Args:
        expenses_data: Dictionary with expense data
        budget_data: Optional budget data for comparison
    """
    if not expenses_data or expenses_data.get('total', 0) == 0:
        print("\n[INFO] No se encontraron gastos registrados para este mes.")
        return
    
    gastos_por_categoria = expenses_data.get('by_category', {})
    total_gastado = expenses_data.get('total', 0)
    
    print("\n[OK] Resumen de Gastos Mensuales:")
    print("-" * 40)
    
    for categoria, monto in gastos_por_categoria.items():
        porcentaje = (monto / total_gastado) * 100 if total_gastado else 0
        print(f"   - {categoria:<15}: ${monto:,.2f} ARS ({porcentaje:.1f}%)")
    
    print("-" * 40)
    print(f"   TOTAL GASTADO:{total_gastado: >22,.2f} ARS")
    print("-" * 40)
    
    # Budget comparison if available
    if budget_data and isinstance(budget_data, dict):
        print("\n[INFO] Análisis vs. Presupuesto:")
        print("-" * 40)
        
        for categoria, limite in budget_data.items():
            if isinstance(limite, (int, float)):
                gastado = gastos_por_categoria.get(categoria, 0)
                diferencia = limite - gastado
                estado = "[OK] Ahorro" if diferencia >= 0 else "[ALERTA] Exceso"
                print(f"   - {categoria:<15}: Gastado ${gastado:,.2f} de ${limite:,.2f}")
                print(f"     Diferencia: ${diferencia:,.2f} ({estado})")
        
        print("-" * 40)


def display_investment_summary(investments_data):
    """
    Display investment summary for the month with data validation and error handling.
    
    Args:
        investments_data: Dictionary with investment data
    """
    if not investments_data or investments_data.get('total_compras', 0) == 0:
        print("\n[INFO] No se encontraron inversiones (compras) registradas para este mes.")
        return
    
    by_asset = investments_data.get('by_asset', {})
    total_invertido = investments_data.get('total_compras', 0)
    
    # Validate investment data for extreme values
    validated_assets = {}
    data_warnings = []
    
    for activo, monto in by_asset.items():
        try:
            amount = float(monto)
            
            # Check for reasonable investment ranges
            if amount > 100_000_000:  # 100 million ARS seems unreasonable
                data_warnings.append(f"Monto extremadamente alto para {activo}: ${amount:,.2f} - verificar datos")
                logger.warning(f"Extremely high investment amount for {activo}: {amount}")
                # Cap at reasonable maximum for display
                amount = min(amount, 100_000_000)
            
            if amount > 0:  # Only show positive amounts (purchases)
                validated_assets[str(activo)] = amount
            elif amount < 0:
                data_warnings.append(f"Monto negativo para {activo}: ${amount:,.2f} - posible venta")
                logger.info(f"Negative amount (sale) for asset {activo}: {amount}")
                
        except (ValueError, TypeError) as e:
            data_warnings.append(f"Monto inválido para {activo}: {monto}")
            logger.warning(f"Invalid investment amount for {activo}: {monto} - {e}")
            continue
    
    if not validated_assets:
        print("\n[INFO] No se encontraron inversiones válidas para mostrar.")
        if data_warnings:
            print("[WARNING] Problemas encontrados en los datos:")
            for warning in data_warnings[:3]:  # Show first 3 warnings
                print(f"  - {warning}")
        return
    
    # Display warnings if any
    if data_warnings:
        print(f"\n[WARNING] Se encontraron {len(data_warnings)} problema(s) en los datos de inversiones:")
        for warning in data_warnings[:3]:  # Show first 3 warnings
            print(f"  - {warning}")
        if len(data_warnings) > 3:
            print(f"  ... y {len(data_warnings) - 3} problema(s) más (ver logs)")
    
    print("\n[INFO] Resumen de Inversiones (Compras del Mes):")
    print("-" * 40)
    
    # Sort by amount for better readability
    sorted_assets = sorted(validated_assets.items(), key=lambda x: x[1], reverse=True)
    
    for activo, monto in sorted_assets:
        # Format large numbers more readably
        if monto >= 1_000_000:
            formatted_amount = f"${monto/1_000_000:.2f}M ARS"
        elif monto >= 1_000:
            formatted_amount = f"${monto/1_000:.1f}K ARS"
        else:
            formatted_amount = f"${monto:,.2f} ARS"
        
        print(f"   - {activo:<15}: {formatted_amount}")
    
    print("-" * 40)
    
    # Format total with validation
    try:
        validated_total = float(total_invertido)
        if validated_total >= 1_000_000:
            formatted_total = f"{validated_total/1_000_000:.2f}M ARS"
        elif validated_total >= 1_000:
            formatted_total = f"{validated_total/1_000:.1f}K ARS"
        else:
            formatted_total = f"{validated_total:,.2f} ARS"
        
        print(f"   TOTAL INVERTIDO:{formatted_total: >20}")
        
        # Add data quality indicator
        if validated_total > 50_000_000:  # 50 million ARS
            print("   [WARNING] Total muy alto - verificar datos")
            
    except (ValueError, TypeError):
        print(f"   TOTAL INVERTIDO: [ERROR] Valor inválido")
        logger.error(f"Invalid total investment amount: {total_invertido}")
    
    print("-" * 40)


def main():
    """
    Main function using DataManager service for improved data handling and error recovery.
    """
    print(f"--- [INFO] INFORME FINANCIERO PECO: {MES_ACTUAL:02d}/{AÑO_ACTUAL} ---")
    logger.info(f"Starting financial analysis for {MES_ACTUAL}/{AÑO_ACTUAL}")
    
    analysis_successful = False
    chart_generated = False
    
    try:
        # Initialize DataManager with error handling
        try:
            data_manager = DataManager()
            logger.info("DataManager initialized successfully")
        except Exception as dm_error:
            logger.error(f"Failed to initialize DataManager: {dm_error}")
            print(f"[ERROR] No se pudo inicializar el gestor de datos: {dm_error}")
            return
        
        # Validate data integrity before analysis
        try:
            integrity_result = data_manager.validate_data_integrity()
            if not integrity_result.success:
                logger.warning(f"Data integrity issues found: {integrity_result.message}")
                print(f"[WARNING] Problemas de integridad detectados: {integrity_result.message}")
                if integrity_result.data and 'issues' in integrity_result.data:
                    for issue in integrity_result.data['issues']:
                        print(f"  - {issue}")
                print("[INFO] Continuando con el análisis...")
        except Exception as integrity_error:
            logger.warning(f"Data integrity check failed: {integrity_error}")
            print(f"[WARNING] No se pudo verificar la integridad de los datos: {integrity_error}")
        
        # Get comprehensive analysis data
        analysis_result = get_analysis_data(data_manager, MES_ACTUAL, AÑO_ACTUAL)
        
        if analysis_result is None:
            print("[ERROR] No se pudo obtener los datos de análisis")
            logger.error("Failed to get analysis data")
            return
        
        # Extract data from analysis result with error handling
        try:
            analysis_data = analysis_result.analysis_data
            expenses_data = analysis_data.get('expenses', {})
            investments_data = analysis_data.get('investments', {})
            budget_data = analysis_data.get('budget', {})
            
            # Check if we have any data to work with
            has_expense_data = expenses_data.get('total', 0) > 0
            has_investment_data = investments_data.get('total', 0) > 0
            
            if not has_expense_data and not has_investment_data:
                print("[INFO] No se encontraron datos financieros para este mes")
                logger.info("No financial data found for the specified month")
                return
            
        except Exception as data_error:
            logger.error(f"Error extracting analysis data: {data_error}")
            print(f"[ERROR] Error al procesar los datos de análisis: {data_error}")
            return
        
        # Display expense summary with error handling
        try:
            display_expense_summary(expenses_data, budget_data)
            analysis_successful = True
        except Exception as expense_error:
            logger.error(f"Error displaying expense summary: {expense_error}")
            print(f"[ERROR] Error al mostrar resumen de gastos: {expense_error}")
        
        # Generate expense chart if there's data - with comprehensive error handling
        gastos_por_categoria = expenses_data.get('by_category', {})
        if gastos_por_categoria:
            try:
                chart_path = generar_grafico_gastos(gastos_por_categoria, MES_ACTUAL, AÑO_ACTUAL)
                if chart_path:
                    logger.info(f"Chart generated successfully: {chart_path}")
                    chart_generated = True
                else:
                    logger.warning("Chart generation returned None")
                    print("[WARNING] No se pudo generar el gráfico de gastos")
            except Exception as chart_error:
                logger.error(f"Unexpected error during chart generation: {chart_error}")
                print(f"[ERROR] Error inesperado al generar gráfico: {chart_error}")
        else:
            logger.info("No expense data available for chart generation")
        
        # Display investment summary with error handling
        try:
            display_investment_summary(investments_data)
        except Exception as investment_error:
            logger.error(f"Error displaying investment summary: {investment_error}")
            print(f"[ERROR] Error al mostrar resumen de inversiones: {investment_error}")
        
        # Final status report
        if analysis_successful:
            logger.info("Financial analysis completed successfully")
            status_msg = f"\n[OK] Análisis financiero completado para {MES_ACTUAL:02d}/{AÑO_ACTUAL}"
            if chart_generated:
                status_msg += " (con gráfico)"
            else:
                status_msg += " (sin gráfico)"
            print(status_msg)
        else:
            print(f"\n[WARNING] Análisis completado con errores para {MES_ACTUAL:02d}/{AÑO_ACTUAL}")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        print("\n[INFO] Análisis interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        print(f"[ERROR] Error inesperado durante el análisis: {e}")
        print("Consulte los logs para más detalles.")
        
        # Try to provide helpful error context
        try:
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        except:
            pass

if __name__ == "__main__":
    main()
