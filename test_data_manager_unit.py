# -*- coding: utf-8 -*-
"""
Unit tests for DataManager service class.
Tests expense and investment registration, data validation, and analysis functionality.
"""

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import os
import csv
import json
import pandas as pd
from datetime import datetime
from io import StringIO

from services.data_manager import DataManager
from services.base import Result, AnalysisResult
from services.exceptions import DataError, ConfigurationError


class TestDataManager(unittest.TestCase):
    """Test cases for DataManager service class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock configuration module
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = "test_gastos.csv"
        self.mock_config.XLSX_INVERSIONES = "test_inversiones.xlsx"
        self.mock_config.JSON_PRESUPUESTO = "test_presupuesto.json"
        self.mock_config.RUTA_TRACKERS = "test_trackers"
        self.mock_config.RUTA_REPORTES = "test_reportes"
        
        # Create DataManager instance with mock config
        self.data_manager = DataManager(config_module=self.mock_config)
    
    def test_init_with_default_config(self):
        """Test DataManager initialization with default config."""
        # This test verifies that DataManager can be initialized without a config_module parameter
        # and will import the default config module
        with patch('builtins.__import__') as mock_import:
            mock_config = Mock()
            mock_config.CSV_GASTOS = "default_gastos.csv"
            mock_config.XLSX_INVERSIONES = "default_inversiones.xlsx"
            mock_config.JSON_PRESUPUESTO = "default_presupuesto.json"
            mock_config.RUTA_TRACKERS = "default_trackers"
            mock_config.RUTA_REPORTES = "default_reportes"
            
            mock_import.return_value = mock_config
            
            dm = DataManager()
            self.assertEqual(dm.csv_gastos, "default_gastos.csv")
    
    def test_init_with_custom_config(self):
        """Test DataManager initialization with custom config."""
        self.assertEqual(self.data_manager.csv_gastos, "test_gastos.csv")
        self.assertEqual(self.data_manager.xlsx_inversiones, "test_inversiones.xlsx")
        self.assertEqual(self.data_manager.json_presupuesto, "test_presupuesto.json")
    
    @patch('services.data_manager.os.makedirs')
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    def test_register_expense_success(self, mock_file, mock_isfile, mock_exists, mock_makedirs):
        """Test successful expense registration."""
        # Setup mocks
        mock_exists.return_value = True  # Directory exists
        mock_isfile.return_value = True  # File exists
        
        # Mock CSV writer
        mock_writer = Mock()
        with patch('services.data_manager.csv.writer', return_value=mock_writer):
            result = self.data_manager.register_expense(100.50, "Food", "Lunch at restaurant")
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Gasto registrado con éxito")
        self.assertIn("fecha", result.data)
        self.assertEqual(result.data["categoria"], "Food")
        self.assertEqual(result.data["descripcion"], "Lunch at restaurant")
        self.assertEqual(result.data["monto"], 100.50)
        
        # Verify file operations
        mock_file.assert_called()
        mock_writer.writerow.assert_called()
    
    @patch('services.data_manager.os.makedirs')
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    def test_register_expense_creates_file_with_headers(self, mock_file, mock_isfile, mock_exists, mock_makedirs):
        """Test expense registration creates file with headers when file doesn't exist."""
        # Setup mocks
        mock_exists.return_value = True  # Directory exists
        mock_isfile.return_value = False  # File doesn't exist
        
        # Mock CSV writer
        mock_writer = Mock()
        with patch('services.data_manager.csv.writer', return_value=mock_writer):
            result = self.data_manager.register_expense(50.0, "Transport", "Bus fare")
        
        # Assertions
        self.assertTrue(result.success)
        
        # Verify headers were written
        expected_calls = [
            unittest.mock.call(["Fecha", "Categoria", "Descripcion", "Monto_ARS"]),
            unittest.mock.call([unittest.mock.ANY, "Transport", "Bus fare", 50.0])
        ]
        mock_writer.writerow.assert_has_calls(expected_calls)
    
    @patch('services.data_manager.os.makedirs')
    @patch('services.data_manager.os.path.exists')
    def test_register_expense_creates_directory(self, mock_exists, mock_makedirs):
        """Test expense registration creates directory when it doesn't exist."""
        # Setup mocks
        mock_exists.side_effect = [False, True]  # Directory doesn't exist, then exists after creation
        
        with patch('services.data_manager.os.path.isfile', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('services.data_manager.csv.writer'):
            
            result = self.data_manager.register_expense(25.0, "Utilities", "Internet bill")
        
        # Verify directory creation
        mock_makedirs.assert_called_once_with("test_trackers")
        self.assertTrue(result.success)
    
    def test_register_expense_validation_negative_amount(self):
        """Test expense registration validation for negative amount."""
        result = self.data_manager.register_expense(-10.0, "Food", "Invalid expense")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNT")
        self.assertIn("mayor a 0", result.message)
    
    def test_register_expense_validation_zero_amount(self):
        """Test expense registration validation for zero amount."""
        result = self.data_manager.register_expense(0.0, "Food", "Invalid expense")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNT")
    
    def test_register_expense_validation_empty_category(self):
        """Test expense registration validation for empty category."""
        result = self.data_manager.register_expense(10.0, "", "Valid description")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_CATEGORY")
        self.assertIn("categoría es requerida", result.message)
    
    def test_register_expense_validation_whitespace_category(self):
        """Test expense registration validation for whitespace-only category."""
        result = self.data_manager.register_expense(10.0, "   ", "Valid description")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_CATEGORY")
    
    def test_register_expense_validation_empty_description(self):
        """Test expense registration validation for empty description."""
        result = self.data_manager.register_expense(10.0, "Food", "")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_DESCRIPTION")
        self.assertIn("descripción es requerida", result.message)
    
    def test_register_expense_validation_excessive_amount(self):
        """Test expense registration validation for excessive amount."""
        result = self.data_manager.register_expense(2000000.0, "Food", "Very expensive meal")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "AMOUNT_TOO_HIGH")
        self.assertIn("excesivamente alto", result.message)
    
    @patch('services.data_manager.os.makedirs')
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_excel')
    @patch('services.data_manager.pd.DataFrame.to_excel')
    def test_register_investment_success_new_file(self, mock_to_excel, mock_read_excel, mock_exists, mock_makedirs):
        """Test successful investment registration with new file creation."""
        # Setup mocks
        mock_exists.side_effect = [True, False]  # Directory exists, file doesn't exist
        
        result = self.data_manager.register_investment("AAPL", "Compra", 1500.0)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Inversión registrada con éxito")
        self.assertIn("fecha", result.data)
        self.assertEqual(result.data["activo"], "AAPL")
        self.assertEqual(result.data["tipo"], "Compra")
        self.assertEqual(result.data["monto"], 1500.0)
        
        # Verify Excel operations
        mock_read_excel.assert_not_called()  # File doesn't exist, so no read
        mock_to_excel.assert_called_once()
    
    @patch('services.data_manager.os.makedirs')
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_excel')
    @patch('services.data_manager.pd.DataFrame.to_excel')
    @patch('services.data_manager.pd.concat')
    def test_register_investment_success_existing_file(self, mock_concat, mock_to_excel, mock_read_excel, mock_exists, mock_makedirs):
        """Test successful investment registration with existing file."""
        # Setup mocks
        mock_exists.side_effect = [True, True]  # Directory and file exist
        mock_existing_df = pd.DataFrame([{"Fecha": "2025-01-01", "Activo": "GOOGL", "Tipo": "Compra", "Monto_ARS": 1000.0}])
        mock_read_excel.return_value = mock_existing_df
        mock_concat.return_value = mock_existing_df  # Simplified return
        
        result = self.data_manager.register_investment("MSFT", "Venta", 800.0)
        
        # Assertions
        self.assertTrue(result.success)
        
        # Verify Excel operations
        mock_read_excel.assert_called_once_with("test_inversiones.xlsx")
        mock_concat.assert_called_once()
        mock_to_excel.assert_called_once()
    
    def test_register_investment_validation_negative_amount(self):
        """Test investment registration validation for negative amount."""
        result = self.data_manager.register_investment("AAPL", "Compra", -100.0)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNT")
    
    def test_register_investment_validation_empty_asset(self):
        """Test investment registration validation for empty asset."""
        result = self.data_manager.register_investment("", "Compra", 100.0)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_ASSET")
        self.assertIn("activo es requerido", result.message)
    
    def test_register_investment_validation_invalid_operation_type(self):
        """Test investment registration validation for invalid operation type."""
        result = self.data_manager.register_investment("AAPL", "Hold", 100.0)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_OPERATION_TYPE")
        self.assertIn("'Compra' o 'Venta'", result.message)
    
    def test_get_monthly_analysis_invalid_month(self):
        """Test monthly analysis with invalid month."""
        result = self.data_manager.get_monthly_analysis(13, 2025)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_MONTH")
        self.assertIn("entre 1 y 12", result.message)
    
    def test_get_monthly_analysis_invalid_year(self):
        """Test monthly analysis with invalid year."""
        result = self.data_manager.get_monthly_analysis(1, 1999)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_YEAR")
        self.assertIn("Año inválido", result.message)
    
    @patch('services.data_manager.DataManager._load_and_analyze_expenses')
    @patch('services.data_manager.DataManager._load_and_analyze_investments')
    @patch('services.data_manager.DataManager._load_budget_data')
    def test_get_monthly_analysis_success(self, mock_budget, mock_investments, mock_expenses):
        """Test successful monthly analysis."""
        # Setup mock returns
        mock_expenses.return_value = {
            "total": 1500.0,
            "by_category": {"Food": 800.0, "Transport": 700.0},
            "records": []
        }
        mock_investments.return_value = {
            "total": 2000.0,
            "by_asset": {"AAPL": 2000.0},
            "records": []
        }
        mock_budget.return_value = {"monthly_limit": 2000.0}
        
        result = self.data_manager.get_monthly_analysis(7, 2025)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.total_expenses, 1500.0)
        self.assertEqual(result.expenses_by_category, {"Food": 800.0, "Transport": 700.0})
        self.assertEqual(result.total_investments, 2000.0)
        self.assertIn("analysis_data", result.__dict__)
    
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_csv')
    def test_load_and_analyze_expenses_file_not_found(self, mock_read_csv, mock_exists):
        """Test expense analysis when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.data_manager._load_and_analyze_expenses(7, 2025)
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["by_category"], {})
        self.assertEqual(result["records"], [])
        mock_read_csv.assert_not_called()
    
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_csv')
    def test_load_and_analyze_expenses_empty_file(self, mock_read_csv, mock_exists):
        """Test expense analysis with empty file."""
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame()  # Empty DataFrame
        
        result = self.data_manager._load_and_analyze_expenses(7, 2025)
        
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["by_category"], {})
        self.assertEqual(result["records"], [])
    
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_csv')
    def test_load_and_analyze_expenses_with_data(self, mock_read_csv, mock_exists):
        """Test expense analysis with actual data."""
        mock_exists.return_value = True
        
        # Create test DataFrame
        test_data = pd.DataFrame([
            {"Fecha": "2025-07-15", "Categoria": "Food", "Descripcion": "Lunch", "Monto_ARS": 500.0},
            {"Fecha": "2025-07-16", "Categoria": "Transport", "Descripcion": "Bus", "Monto_ARS": 200.0},
            {"Fecha": "2025-07-17", "Categoria": "Food", "Descripcion": "Dinner", "Monto_ARS": 800.0},
            {"Fecha": "2025-06-15", "Categoria": "Food", "Descripcion": "Previous month", "Monto_ARS": 300.0}  # Different month
        ])
        mock_read_csv.return_value = test_data
        
        result = self.data_manager._load_and_analyze_expenses(7, 2025)
        
        # Should only include July 2025 data
        self.assertEqual(result["total"], 1500.0)  # 500 + 200 + 800
        self.assertEqual(result["by_category"], {"Food": 1300.0, "Transport": 200.0})
        self.assertEqual(result["count"], 3)
    
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_excel')
    def test_load_and_analyze_investments_with_data(self, mock_read_excel, mock_exists):
        """Test investment analysis with actual data."""
        mock_exists.return_value = True
        
        # Create test DataFrame
        test_data = pd.DataFrame([
            {"Fecha": "2025-07-15", "Activo": "AAPL", "Tipo": "Compra", "Monto_ARS": 1000.0},
            {"Fecha": "2025-07-16", "Activo": "GOOGL", "Tipo": "Compra", "Monto_ARS": 1500.0},
            {"Fecha": "2025-07-17", "Activo": "AAPL", "Tipo": "Venta", "Monto_ARS": 800.0},
            {"Fecha": "2025-06-15", "Activo": "MSFT", "Tipo": "Compra", "Monto_ARS": 500.0}  # Different month
        ])
        mock_read_excel.return_value = test_data
        
        result = self.data_manager._load_and_analyze_investments(7, 2025)
        
        # Should only include July 2025 data
        self.assertEqual(result["total"], 2500.0)  # Total purchases: 1000 + 1500
        self.assertEqual(result["total_compras"], 2500.0)
        self.assertEqual(result["total_ventas"], 800.0)
        self.assertEqual(result["by_asset"], {"AAPL": 1800.0, "GOOGL": 1500.0})  # 1000 + 800, 1500
        self.assertEqual(result["count"], 3)
    
    @patch('services.data_manager.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"monthly_limit": 2000.0, "categories": ["Food", "Transport"]}')
    def test_load_budget_data_success(self, mock_file, mock_exists):
        """Test successful budget data loading."""
        mock_exists.return_value = True
        
        result = self.data_manager._load_budget_data()
        
        self.assertEqual(result["monthly_limit"], 2000.0)
        self.assertEqual(result["categories"], ["Food", "Transport"])
    
    @patch('services.data_manager.os.path.exists')
    def test_load_budget_data_file_not_found(self, mock_exists):
        """Test budget data loading when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.data_manager._load_budget_data()
        
        self.assertEqual(result, {})
    
    @patch('services.data_manager.DataManager._validate_expenses_file')
    @patch('services.data_manager.DataManager._validate_investments_file')
    @patch('services.data_manager.DataManager._validate_budget_file')
    @patch('services.data_manager.DataManager._validate_directory_structure')
    def test_validate_data_integrity_success(self, mock_dir, mock_budget, mock_investments, mock_expenses):
        """Test successful data integrity validation."""
        # All validations pass
        mock_expenses.return_value = Result(success=True, message="Valid")
        mock_investments.return_value = Result(success=True, message="Valid")
        mock_budget.return_value = Result(success=True, message="Valid")
        mock_dir.return_value = Result(success=True, message="Valid")
        
        result = self.data_manager.validate_data_integrity()
        
        self.assertTrue(result.success)
        self.assertIn("íntegros", result.message)
        self.assertEqual(len(result.data["validated_files"]), 4)
    
    @patch('services.data_manager.DataManager._validate_expenses_file')
    @patch('services.data_manager.DataManager._validate_investments_file')
    @patch('services.data_manager.DataManager._validate_budget_file')
    @patch('services.data_manager.DataManager._validate_directory_structure')
    def test_validate_data_integrity_with_issues(self, mock_dir, mock_budget, mock_investments, mock_expenses):
        """Test data integrity validation with issues."""
        # Some validations fail
        mock_expenses.return_value = Result(success=False, message="Expenses file corrupted")
        mock_investments.return_value = Result(success=True, message="Valid")
        mock_budget.return_value = Result(success=False, message="Budget file missing")
        mock_dir.return_value = Result(success=True, message="Valid")
        
        result = self.data_manager.validate_data_integrity()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "DATA_INTEGRITY_ISSUES")
        self.assertEqual(len(result.data["issues"]), 2)
        self.assertIn("Gastos: Expenses file corrupted", result.data["issues"])
        self.assertIn("Presupuesto: Budget file missing", result.data["issues"])
    
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_csv')
    def test_validate_expenses_file_missing_columns(self, mock_read_csv, mock_exists):
        """Test expenses file validation with missing columns."""
        mock_exists.return_value = True
        # DataFrame missing required columns
        mock_read_csv.return_value = pd.DataFrame([{"Fecha": "2025-01-01", "Monto": 100.0}])
        
        result = self.data_manager._validate_expenses_file()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_COLUMNS")
        self.assertIn("Columnas faltantes", result.message)
    
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_csv')
    def test_validate_expenses_file_invalid_amounts(self, mock_read_csv, mock_exists):
        """Test expenses file validation with invalid amounts."""
        mock_exists.return_value = True
        # DataFrame with non-numeric amounts
        test_data = pd.DataFrame([
            {"Fecha": "2025-01-01", "Categoria": "Food", "Descripcion": "Lunch", "Monto_ARS": "invalid"},
            {"Fecha": "2025-01-02", "Categoria": "Transport", "Descripcion": "Bus", "Monto_ARS": 100.0}
        ])
        mock_read_csv.return_value = test_data
        
        result = self.data_manager._validate_expenses_file()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNTS")
        self.assertIn("no numéricos", result.message)
    
    @patch('services.data_manager.os.path.exists')
    def test_validate_expenses_file_not_found(self, mock_exists):
        """Test expenses file validation when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.data_manager._validate_expenses_file()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "FILE_NOT_FOUND")
    
    @patch('services.data_manager.os.path.exists')
    @patch('services.data_manager.pd.read_excel')
    def test_validate_investments_file_invalid_operation_types(self, mock_read_excel, mock_exists):
        """Test investments file validation with invalid operation types."""
        mock_exists.return_value = True
        # DataFrame with invalid operation types
        test_data = pd.DataFrame([
            {"Fecha": "2025-01-01", "Activo": "AAPL", "Tipo": "Hold", "Monto_ARS": 1000.0},
            {"Fecha": "2025-01-02", "Activo": "GOOGL", "Tipo": "Compra", "Monto_ARS": 1500.0}
        ])
        mock_read_excel.return_value = test_data
        
        result = self.data_manager._validate_investments_file()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_OPERATION_TYPES")
        self.assertIn("inválidos", result.message)
    
    @patch('services.data_manager.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_validate_budget_file_json_error(self, mock_file, mock_exists):
        """Test budget file validation with JSON error."""
        mock_exists.return_value = True
        
        result = self.data_manager._validate_budget_file()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "JSON_ERROR")
        self.assertIn("formato JSON", result.message)
    
    @patch('services.data_manager.os.path.exists')
    def test_validate_directory_structure_missing_directories(self, mock_exists):
        """Test directory structure validation with missing directories."""
        mock_exists.return_value = False  # All directories missing
        
        result = self.data_manager._validate_directory_structure()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_DIRECTORIES")
        self.assertIn("faltantes", result.message)


if __name__ == '__main__':
    unittest.main()