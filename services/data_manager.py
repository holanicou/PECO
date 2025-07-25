# -*- coding: utf-8 -*-
"""
DataManager service class for PECO financial application.
Handles expense and investment registration, data validation, and analysis.
Now uses SQLite database for improved performance and functionality.
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .base import Result, AnalysisResult
from .exceptions import DataError, ConfigurationError
from .logging_config import get_logger
from .database import DatabaseManager

logger = get_logger(__name__)


class DataManager:
    """
    Service class for managing financial data operations.
    Handles expense and investment registration, data validation, and analysis.
    Now uses SQLite database for improved performance and functionality.
    """
    
    def __init__(self, config_module=None, use_database=True):
        """
        Initialize DataManager with configuration.
        
        Args:
            config_module: Configuration module with file paths
            use_database: Whether to use SQLite database (True) or legacy files (False)
        """
        if config_module is None:
            import config as config_module
        
        self.config = config_module
        self.csv_gastos = config_module.CSV_GASTOS
        self.xlsx_inversiones = config_module.XLSX_INVERSIONES
        self.json_presupuesto = config_module.JSON_PRESUPUESTO
        self.ruta_trackers = config_module.RUTA_TRACKERS
        self.ruta_reportes = config_module.RUTA_REPORTES
        
        # Initialize database manager
        self.use_database = use_database
        if self.use_database:
            self.db_manager = DatabaseManager("peco.db")
            logger.info("DataManager initialized with SQLite database")
        else:
            self.db_manager = None
            logger.info("DataManager initialized with legacy file system")
        
        logger.info("DataManager initialized")
    
    def register_expense(self, amount: float, category: str, description: str) -> Result:
        """
        Register a new expense using SQLite database or legacy CSV file.
        
        Args:
            amount: Expense amount in ARS
            category: Expense category
            description: Expense description
            
        Returns:
            Result object indicating success or failure
        """
        try:
            logger.info(f"Registering expense: {amount} ARS, category: {category}")
            
            # Validate input data
            validation_result = self._validate_expense_data(amount, category, description)
            if not validation_result.success:
                return validation_result
            
            # Use SQLite database if enabled
            if self.use_database and self.db_manager:
                fecha = datetime.now().strftime("%Y-%m-%d")
                return self.db_manager.add_expense(fecha, category, description, amount)
            
            # Legacy CSV file method
            return self._register_expense_csv(amount, category, description)
            
        except Exception as e:
            logger.error(f"Error registering expense: {e}")
            return Result(
                success=False,
                message=f"Error al registrar gasto: {str(e)}",
                error_code="EXPENSE_REGISTRATION_ERROR"
            )
    
    def register_investment(self, asset: str, operation_type: str, amount: float) -> Result:
        """
        Register a new investment operation using SQLite database or legacy Excel file.
        
        Args:
            asset: Asset ticker or name
            operation_type: 'Compra' or 'Venta'
            amount: Operation amount in ARS
            
        Returns:
            Result object indicating success or failure
        """
        try:
            logger.info(f"Registering investment: {asset}, {operation_type}, {amount} ARS")
            
            # Validate input data
            validation_result = self._validate_investment_data(asset, operation_type, amount)
            if not validation_result.success:
                return validation_result
            
            # Use SQLite database if enabled
            if self.use_database and self.db_manager:
                fecha = datetime.now().strftime("%Y-%m-%d")
                return self.db_manager.add_investment(fecha, asset, operation_type, amount)
            
            # Legacy Excel file method
            return self._register_investment_excel(asset, operation_type, amount)
            
        except Exception as e:
            logger.error(f"Error registering investment: {e}")
            return Result(
                success=False,
                message=f"Error al registrar inversión: {str(e)}",
                error_code="INVESTMENT_REGISTRATION_ERROR"
            )  
  
    def get_monthly_analysis(self, month: int, year: int) -> AnalysisResult:
        """
        Get comprehensive monthly financial analysis using SQLite or legacy files.
        
        Args:
            month: Month number (1-12)
            year: Year
            
        Returns:
            AnalysisResult with financial analysis data
        """
        try:
            logger.info(f"Generating monthly analysis for {month}/{year}")
            
            # Validate month and year
            if not (1 <= month <= 12):
                return AnalysisResult(
                    success=False,
                    message="Mes inválido. Debe estar entre 1 y 12",
                    error_code="INVALID_MONTH"
                )
            
            if year < 2000 or year > datetime.now().year + 1:
                return AnalysisResult(
                    success=False,
                    message="Año inválido",
                    error_code="INVALID_YEAR"
                )
            
            # Use SQLite database if enabled
            if self.use_database and self.db_manager:
                return self._get_monthly_analysis_db(month, year)
            
            # Legacy file-based analysis
            return self._get_monthly_analysis_files(month, year)
            
        except Exception as e:
            logger.error(f"Error generating monthly analysis: {e}")
            return AnalysisResult(
                success=False,
                message=f"Error al generar análisis mensual: {str(e)}",
                error_code="ANALYSIS_ERROR"
            )
    
    def validate_data_integrity(self) -> Result:
        """
        Validate the integrity of data storage (SQLite database or legacy files).
        
        Returns:
            Result object with validation status
        """
        try:
            logger.info("Starting data integrity validation")
            
            # Use SQLite database validation if enabled
            if self.use_database and self.db_manager:
                return self._validate_database_integrity()
            
            # Legacy file validation
            return self._validate_files_integrity()
            
        except Exception as e:
            logger.error(f"Error during data integrity validation: {e}")
            return Result(
                success=False,
                message=f"Error durante validación de integridad: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
    
    def _validate_database_integrity(self) -> Result:
        """Validate SQLite database integrity."""
        try:
            issues = []
            validated_items = []
            
            # Check if database file exists
            if not os.path.exists("peco.db"):
                return Result(
                    success=False,
                    message="Base de datos SQLite no encontrada",
                    error_code="DATABASE_NOT_FOUND"
                )
            
            # Get database statistics
            stats_result = self.db_manager.get_database_stats()
            if not stats_result.success:
                issues.append(f"Error obteniendo estadísticas: {stats_result.message}")
            else:
                stats = stats_result.data
                validated_items.append(f"Base de datos: {stats['total_records']} registros")
                
                # Check if database has reasonable data
                if stats['total_records'] == 0:
                    issues.append("Base de datos vacía - no hay registros")
                
                if stats['database_size_bytes'] < 1024:  # Less than 1KB
                    issues.append("Base de datos muy pequeña - posible corrupción")
            
            # Test basic database operations
            try:
                # Try to get current month analysis
                current_month = datetime.now().month
                current_year = datetime.now().year
                analysis_result = self.db_manager.get_monthly_summary(current_year, current_month)
                if analysis_result.success:
                    validated_items.append("Consultas de análisis funcionando")
                else:
                    issues.append(f"Error en consultas: {analysis_result.message}")
            except Exception as e:
                issues.append(f"Error probando consultas: {str(e)}")
            
            # Check budget file (still used)
            budget_check = self._validate_budget_file()
            if budget_check.success:
                validated_items.append("Archivo de presupuesto")
            else:
                issues.append(f"Presupuesto: {budget_check.message}")
            
            # Check directory structure
            directories_check = self._validate_directory_structure()
            if directories_check.success:
                validated_items.append("Estructura de directorios")
            else:
                issues.append(f"Directorios: {directories_check.message}")
            
            if issues:
                return Result(
                    success=False,
                    message="Se encontraron problemas de integridad",
                    data={"issues": issues, "validated": validated_items},
                    error_code="DATA_INTEGRITY_ISSUES"
                )
            
            logger.info("Database integrity validation completed successfully")
            return Result(
                success=True,
                message="Base de datos SQLite íntegra y funcionando correctamente",
                data={"validated_items": validated_items}
            )
            
        except Exception as e:
            logger.error(f"Error validating database integrity: {e}")
            return Result(
                success=False,
                message=f"Error validando base de datos: {str(e)}",
                error_code="DATABASE_VALIDATION_ERROR"
            )
    
    def _validate_files_integrity(self) -> Result:
        """Validate legacy CSV/Excel files integrity."""
        try:
            issues = []
            
            # Check expenses file
            expenses_check = self._validate_expenses_file()
            if not expenses_check.success:
                issues.append(f"Gastos: {expenses_check.message}")
            
            # Check investments file
            investments_check = self._validate_investments_file()
            if not investments_check.success:
                issues.append(f"Inversiones: {investments_check.message}")
            
            # Check budget file
            budget_check = self._validate_budget_file()
            if not budget_check.success:
                issues.append(f"Presupuesto: {budget_check.message}")
            
            # Check directory structure
            directories_check = self._validate_directory_structure()
            if not directories_check.success:
                issues.append(f"Directorios: {directories_check.message}")
            
            if issues:
                return Result(
                    success=False,
                    message="Se encontraron problemas de integridad",
                    data={"issues": issues},
                    error_code="DATA_INTEGRITY_ISSUES"
                )
            
            logger.info("Files integrity validation completed successfully")
            return Result(
                success=True,
                message="Todos los archivos de datos están íntegros",
                data={"validated_files": ["gastos", "inversiones", "presupuesto", "directorios"]}
            )
            
        except Exception as e:
            logger.error(f"Error validating files integrity: {e}")
            return Result(
                success=False,
                message=f"Error validando archivos: {str(e)}",
                error_code="FILES_VALIDATION_ERROR"
            )
    
    # Private helper methods
    
    def _register_expense_csv(self, amount: float, category: str, description: str) -> Result:
        """Legacy method to register expense in CSV file."""
        try:
            # Ensure directory exists
            if not os.path.exists(self.ruta_trackers):
                os.makedirs(self.ruta_trackers)
                logger.info(f"Created directory: {self.ruta_trackers}")
            
            # Check if file exists and create headers if needed
            file_exists = os.path.isfile(self.csv_gastos)
            if not file_exists:
                with open(self.csv_gastos, "w", newline="", encoding="utf-8") as archivo:
                    writer = csv.writer(archivo)
                    writer.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
                logger.info(f"Created new expense file: {self.csv_gastos}")
            
            # Add new expense record
            fecha = datetime.now().strftime("%Y-%m-%d")
            nueva_fila = [fecha, category, description, amount]
            
            with open(self.csv_gastos, "a", newline="", encoding="utf-8") as archivo:
                writer = csv.writer(archivo)
                writer.writerow(nueva_fila)
            
            logger.info(f"Expense registered successfully: {fecha}, {category}, {amount}")
            
            return Result(
                success=True,
                message="Gasto registrado con éxito",
                data={
                    "fecha": fecha,
                    "categoria": category,
                    "descripcion": description,
                    "monto": amount
                }
            )
        except Exception as e:
            logger.error(f"Error registering expense to CSV: {e}")
            return Result(
                success=False,
                message=f"Error al registrar gasto: {str(e)}",
                error_code="CSV_WRITE_ERROR"
            )
    
    def _register_investment_excel(self, asset: str, operation_type: str, amount: float) -> Result:
        """Legacy method to register investment in Excel file."""
        try:
            # Ensure directory exists
            if not os.path.exists(self.ruta_trackers):
                os.makedirs(self.ruta_trackers)
                logger.info(f"Created directory: {self.ruta_trackers}")
            
            fecha = datetime.now().strftime("%Y-%m-%d")
            nueva_inversion = pd.DataFrame([{
                "Fecha": fecha,
                "Activo": asset,
                "Tipo": operation_type,
                "Monto_ARS": amount
            }])
            
            # Check if file exists and append or create
            if os.path.exists(self.xlsx_inversiones):
                df_existente = pd.read_excel(self.xlsx_inversiones)
                df_actualizado = pd.concat([df_existente, nueva_inversion], ignore_index=True)
            else:
                df_actualizado = nueva_inversion
                logger.info(f"Creating new investment file: {self.xlsx_inversiones}")
            
            # Save updated DataFrame
            df_actualizado.to_excel(self.xlsx_inversiones, index=False)
            
            logger.info(f"Investment registered successfully: {fecha}, {asset}, {operation_type}, {amount}")
            
            return Result(
                success=True,
                message="Inversión registrada con éxito",
                data={
                    "fecha": fecha,
                    "activo": asset,
                    "tipo": operation_type,
                    "monto": amount
                }
            )
        except Exception as e:
            logger.error(f"Error registering investment to Excel: {e}")
            return Result(
                success=False,
                message=f"Error al registrar inversión: {str(e)}",
                error_code="EXCEL_WRITE_ERROR"
            )
    
    def _get_monthly_analysis_db(self, month: int, year: int) -> AnalysisResult:
        """Get monthly analysis using SQLite database."""
        try:
            # Get monthly summary from database
            summary_result = self.db_manager.get_monthly_summary(year, month)
            if not summary_result.success:
                return AnalysisResult(
                    success=False,
                    message=summary_result.message,
                    error_code=summary_result.error_code
                )
            
            summary = summary_result.data
            
            # Get expenses by category
            categories_result = self.db_manager.get_expenses_by_category(year, month)
            expenses_by_category = {}
            if categories_result.success:
                for cat in categories_result.data:
                    expenses_by_category[cat['categoria']] = cat['total']
            
            # Load budget data
            budget_data = self._load_budget_data()
            
            # Compile analysis data
            analysis_data = {
                "month": month,
                "year": year,
                "expenses": {
                    "total": summary['total_expenses'],
                    "by_category": expenses_by_category,
                    "count": summary['expense_count']
                },
                "investments": {
                    "total": summary['total_purchases'],
                    "total_compras": summary['total_purchases'],
                    "total_ventas": summary['total_sales'],
                    "net_investment": summary['net_investment'],
                    "count": summary['investment_count']
                },
                "budget": budget_data,
                "generated_at": datetime.now().isoformat(),
                "data_source": "sqlite"
            }
            
            return AnalysisResult(
                success=True,
                message=f"Análisis mensual generado para {month}/{year} (SQLite)",
                total_expenses=summary['total_expenses'],
                expenses_by_category=expenses_by_category,
                total_investments=summary['total_purchases'],
                analysis_data=analysis_data
            )
            
        except Exception as e:
            logger.error(f"Error generating SQLite monthly analysis: {e}")
            return AnalysisResult(
                success=False,
                message=f"Error al generar análisis mensual: {str(e)}",
                error_code="DB_ANALYSIS_ERROR"
            )
    
    def _get_monthly_analysis_files(self, month: int, year: int) -> AnalysisResult:
        """Get monthly analysis using legacy CSV/Excel files."""
        try:
            # Load and analyze expenses
            expenses_data = self._load_and_analyze_expenses(month, year)
            
            # Load and analyze investments
            investments_data = self._load_and_analyze_investments(month, year)
            
            # Load budget data if available
            budget_data = self._load_budget_data()
            
            # Compile analysis results
            analysis_data = {
                "month": month,
                "year": year,
                "expenses": expenses_data,
                "investments": investments_data,
                "budget": budget_data,
                "generated_at": datetime.now().isoformat(),
                "data_source": "files"
            }
            
            return AnalysisResult(
                success=True,
                message=f"Análisis mensual generado para {month}/{year} (archivos)",
                total_expenses=expenses_data.get("total", 0),
                expenses_by_category=expenses_data.get("by_category", {}),
                total_investments=investments_data.get("total", 0),
                analysis_data=analysis_data
            )
            
        except Exception as e:
            logger.error(f"Error generating file-based monthly analysis: {e}")
            return AnalysisResult(
                success=False,
                message=f"Error al generar análisis mensual: {str(e)}",
                error_code="FILE_ANALYSIS_ERROR"
            )

    def _validate_expense_data(self, amount: float, category: str, description: str) -> Result:
        """Validate expense input data."""
        if amount <= 0:
            return Result(
                success=False,
                message="El monto debe ser mayor a 0",
                error_code="INVALID_AMOUNT"
            )
        
        if not category or not category.strip():
            return Result(
                success=False,
                message="La categoría es requerida",
                error_code="MISSING_CATEGORY"
            )
        
        if not description or not description.strip():
            return Result(
                success=False,
                message="La descripción es requerida",
                error_code="MISSING_DESCRIPTION"
            )
        
        # Check for reasonable limits
        if amount > 1000000:  # 1 million ARS
            return Result(
                success=False,
                message="El monto parece excesivamente alto. Verifique el valor",
                error_code="AMOUNT_TOO_HIGH"
            )
        
        return Result(success=True, message="Datos válidos")
    
    def _validate_investment_data(self, asset: str, operation_type: str, amount: float) -> Result:
        """Validate investment input data."""
        if amount <= 0:
            return Result(
                success=False,
                message="El monto debe ser mayor a 0",
                error_code="INVALID_AMOUNT"
            )
        
        if not asset or not asset.strip():
            return Result(
                success=False,
                message="El activo es requerido",
                error_code="MISSING_ASSET"
            )
        
        if operation_type not in ['Compra', 'Venta']:
            return Result(
                success=False,
                message="El tipo de operación debe ser 'Compra' o 'Venta'",
                error_code="INVALID_OPERATION_TYPE"
            )
        
        return Result(success=True, message="Datos válidos")
    
    def _load_and_analyze_expenses(self, month: int, year: int) -> Dict[str, Any]:
        """Load and analyze expenses for a specific month."""
        try:
            if not os.path.exists(self.csv_gastos):
                logger.warning(f"Expenses file not found: {self.csv_gastos}")
                return {"total": 0, "by_category": {}, "records": []}
            
            df = pd.read_csv(self.csv_gastos)
            if df.empty:
                return {"total": 0, "by_category": {}, "records": []}
            
            # Convert date column
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df = df.dropna(subset=['Fecha'])
            
            # Filter by month and year
            mask = (df['Fecha'].dt.month == month) & (df['Fecha'].dt.year == year)
            df_month = df[mask]
            
            if df_month.empty:
                return {"total": 0, "by_category": {}, "records": []}
            
            # Calculate totals by category
            by_category = df_month.groupby('Categoria')['Monto_ARS'].sum().to_dict()
            total = df_month['Monto_ARS'].sum()
            
            # Get individual records
            records = df_month.to_dict('records')
            
            return {
                "total": float(total),
                "by_category": {k: float(v) for k, v in by_category.items()},
                "records": records,
                "count": len(df_month)
            }
            
        except Exception as e:
            logger.error(f"Error loading expenses data: {e}")
            return {"total": 0, "by_category": {}, "records": [], "error": str(e)}
    
    def _load_and_analyze_investments(self, month: int, year: int) -> Dict[str, Any]:
        """Load and analyze investments for a specific month."""
        try:
            if not os.path.exists(self.xlsx_inversiones):
                logger.warning(f"Investments file not found: {self.xlsx_inversiones}")
                return {"total": 0, "by_asset": {}, "records": []}
            
            df = pd.read_excel(self.xlsx_inversiones)
            if df.empty:
                return {"total": 0, "by_asset": {}, "records": []}
            
            # Convert date column
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df = df.dropna(subset=['Fecha'])
            
            # Filter by month and year
            mask = (df['Fecha'].dt.month == month) & (df['Fecha'].dt.year == year)
            df_month = df[mask]
            
            if df_month.empty:
                return {"total": 0, "by_asset": {}, "records": []}
            
            # Separate purchases and sales
            compras = df_month[df_month['Tipo'].str.lower() == 'compra']
            ventas = df_month[df_month['Tipo'].str.lower() == 'venta']
            
            # Calculate totals
            total_compras = compras['Monto_ARS'].sum() if not compras.empty else 0
            total_ventas = ventas['Monto_ARS'].sum() if not ventas.empty else 0
            
            # Group by asset
            by_asset = df_month.groupby('Activo')['Monto_ARS'].sum().to_dict()
            
            # Get individual records
            records = df_month.to_dict('records')
            
            return {
                "total": float(total_compras),  # Total purchases for the month
                "total_compras": float(total_compras),
                "total_ventas": float(total_ventas),
                "by_asset": {k: float(v) for k, v in by_asset.items()},
                "records": records,
                "count": len(df_month)
            }
            
        except Exception as e:
            logger.error(f"Error loading investments data: {e}")
            return {"total": 0, "by_asset": {}, "records": [], "error": str(e)}
    
    def _load_budget_data(self) -> Dict[str, Any]:
        """Load budget configuration data."""
        try:
            if not os.path.exists(self.json_presupuesto):
                logger.warning(f"Budget file not found: {self.json_presupuesto}")
                return {}
            
            with open(self.json_presupuesto, 'r', encoding='utf-8') as f:
                budget_data = json.load(f)
            
            return budget_data
            
        except Exception as e:
            logger.error(f"Error loading budget data: {e}")
            return {"error": str(e)}
    
    def _validate_expenses_file(self) -> Result:
        """Validate expenses CSV file structure and data."""
        try:
            if not os.path.exists(self.csv_gastos):
                return Result(
                    success=False,
                    message="Archivo de gastos no encontrado",
                    error_code="FILE_NOT_FOUND"
                )
            
            df = pd.read_csv(self.csv_gastos)
            required_columns = ['Fecha', 'Categoria', 'Descripcion', 'Monto_ARS']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return Result(
                    success=False,
                    message=f"Columnas faltantes en archivo de gastos: {missing_columns}",
                    error_code="MISSING_COLUMNS"
                )
            
            # Check for data type issues
            if not df.empty:
                # Check if amounts are numeric
                non_numeric_amounts = df[~pd.to_numeric(df['Monto_ARS'], errors='coerce').notna()]
                if not non_numeric_amounts.empty:
                    return Result(
                        success=False,
                        message=f"Montos no numéricos encontrados en {len(non_numeric_amounts)} registros",
                        error_code="INVALID_AMOUNTS"
                    )
            
            return Result(success=True, message="Archivo de gastos válido")
            
        except Exception as e:
            return Result(
                success=False,
                message=f"Error validando archivo de gastos: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
    
    def _validate_investments_file(self) -> Result:
        """Validate investments Excel file structure and data."""
        try:
            if not os.path.exists(self.xlsx_inversiones):
                return Result(
                    success=False,
                    message="Archivo de inversiones no encontrado",
                    error_code="FILE_NOT_FOUND"
                )
            
            df = pd.read_excel(self.xlsx_inversiones)
            required_columns = ['Fecha', 'Activo', 'Tipo', 'Monto_ARS']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return Result(
                    success=False,
                    message=f"Columnas faltantes en archivo de inversiones: {missing_columns}",
                    error_code="MISSING_COLUMNS"
                )
            
            # Check for valid operation types
            if not df.empty:
                valid_types = ['Compra', 'Venta']
                invalid_types = df[~df['Tipo'].isin(valid_types)]
                if not invalid_types.empty:
                    return Result(
                        success=False,
                        message=f"Tipos de operación inválidos encontrados: {invalid_types['Tipo'].unique()}",
                        error_code="INVALID_OPERATION_TYPES"
                    )
            
            return Result(success=True, message="Archivo de inversiones válido")
            
        except Exception as e:
            return Result(
                success=False,
                message=f"Error validando archivo de inversiones: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
    
    def _validate_budget_file(self) -> Result:
        """Validate budget JSON file structure."""
        try:
            if not os.path.exists(self.json_presupuesto):
                return Result(
                    success=False,
                    message="Archivo de presupuesto no encontrado",
                    error_code="FILE_NOT_FOUND"
                )
            
            with open(self.json_presupuesto, 'r', encoding='utf-8') as f:
                budget_data = json.load(f)
            
            if not isinstance(budget_data, dict):
                return Result(
                    success=False,
                    message="Formato de presupuesto inválido. Debe ser un objeto JSON",
                    error_code="INVALID_FORMAT"
                )
            
            return Result(success=True, message="Archivo de presupuesto válido")
            
        except json.JSONDecodeError as e:
            return Result(
                success=False,
                message=f"Error de formato JSON en presupuesto: {str(e)}",
                error_code="JSON_ERROR"
            )
        except Exception as e:
            return Result(
                success=False,
                message=f"Error validando archivo de presupuesto: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
    
    def _validate_directory_structure(self) -> Result:
        """Validate that required directories exist."""
        try:
            required_dirs = [
                self.ruta_trackers,
                self.ruta_reportes,
                os.path.dirname(self.json_presupuesto)
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not os.path.exists(dir_path):
                    missing_dirs.append(dir_path)
            
            if missing_dirs:
                return Result(
                    success=False,
                    message=f"Directorios faltantes: {missing_dirs}",
                    error_code="MISSING_DIRECTORIES"
                )
            
            return Result(success=True, message="Estructura de directorios válida")
            
        except Exception as e:
            return Result(
                success=False,
                message=f"Error validando estructura de directorios: {str(e)}",
                error_code="VALIDATION_ERROR"
            )