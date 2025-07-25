# -*- coding: utf-8 -*-
"""
Unit tests for DataManager service class.
"""

import unittest
import tempfile
import os
import csv
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.data_manager import DataManager
from services.base import Result, AnalysisResult


class TestDataManager(unittest.TestCase):
    """Test cases for DataManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config module
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        
        # Initialize DataManager with mock config
        self.data_manager = DataManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_register_expense_success(self):
        """Test successful expense registration."""
        result = self.data_manager.register_expense(1500.0, "Comida", "Almuerzo")
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Gasto registrado con éxito")
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data["monto"], 1500.0)
        self.assertEqual(result.data["categoria"], "Comida")
        
        # Verify file was created and contains data
        self.assertTrue(os.path.exists(self.mock_config.CSV_GASTOS))
        
        with open(self.mock_config.CSV_GASTOS, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)  # Header + 1 data row
            self.assertEqual(rows[0], ["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
            self.assertEqual(rows[1][1], "Comida")
            self.assertEqual(rows[1][2], "Almuerzo")
            self.assertEqual(float(rows[1][3]), 1500.0)
    
    def test_register_expense_validation_errors(self):
        """Test expense registration validation errors."""
        # Test negative amount
        result = self.data_manager.register_expense(-100.0, "Comida", "Test")
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNT")
        
        # Test zero amount
        result = self.data_manager.register_expense(0.0, "Comida", "Test")
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNT")
        
        # Test empty category
        result = self.data_manager.register_expense(100.0, "", "Test")
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_CATEGORY")
        
        # Test empty description
        result = self.data_manager.register_expense(100.0, "Comida", "")
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_DESCRIPTION")
        
        # Test excessive amount
        result = self.data_manager.register_expense(2000000.0, "Comida", "Test")
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "AMOUNT_TOO_HIGH")
    
    def test_register_investment_success(self):
        """Test successful investment registration."""
        result = self.data_manager.register_investment("AAPL", "Compra", 50000.0)
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Inversión registrada con éxito")
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data["activo"], "AAPL")
        self.assertEqual(result.data["tipo"], "Compra")
        self.assertEqual(result.data["monto"], 50000.0)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.mock_config.XLSX_INVERSIONES))
        
        # Read and verify Excel file
        df = pd.read_excel(self.mock_config.XLSX_INVERSIONES)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["Activo"], "AAPL")
        self.assertEqual(df.iloc[0]["Tipo"], "Compra")
        self.assertEqual(df.iloc[0]["Monto_ARS"], 50000.0)
    
    def test_register_investment_validation_errors(self):
        """Test investment registration validation errors."""
        # Test invalid amount
        result = self.data_manager.register_investment("AAPL", "Compra", -1000.0)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNT")
        
        # Test empty asset
        result = self.data_manager.register_investment("", "Compra", 1000.0)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "MISSING_ASSET")
        
        # Test invalid operation type
        result = self.data_manager.register_investment("AAPL", "Invalid", 1000.0)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_OPERATION_TYPE")
    
    def test_get_monthly_analysis_with_data(self):
        """Test monthly analysis with existing data."""
        # Create test expense data
        expense_data = [
            ["Fecha", "Categoria", "Descripcion", "Monto_ARS"],
            ["2025-07-15", "Comida", "Almuerzo", "1500"],
            ["2025-07-16", "Transporte", "Uber", "800"],
            ["2025-07-17", "Comida", "Cena", "2000"]
        ]
        
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(expense_data)
        
        # Create test investment data
        investment_data = pd.DataFrame([
            {"Fecha": "2025-07-15", "Activo": "AAPL", "Tipo": "Compra", "Monto_ARS": 50000},
            {"Fecha": "2025-07-16", "Activo": "GOOGL", "Tipo": "Compra", "Monto_ARS": 30000}
        ])
        investment_data.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        # Create budget data
        budget_data = {"Comida": 5000, "Transporte": 2000}
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            json.dump(budget_data, f)
        
        # Test analysis
        result = self.data_manager.get_monthly_analysis(7, 2025)
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_expenses, 4300.0)  # 1500 + 800 + 2000
        self.assertEqual(result.expenses_by_category["Comida"], 3500.0)  # 1500 + 2000
        self.assertEqual(result.expenses_by_category["Transporte"], 800.0)
        self.assertEqual(result.total_investments, 80000.0)  # 50000 + 30000
        self.assertIsNotNone(result.analysis_data)
    
    def test_get_monthly_analysis_invalid_month(self):
        """Test monthly analysis with invalid month."""
        result = self.data_manager.get_monthly_analysis(13, 2025)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_MONTH")
        
        result = self.data_manager.get_monthly_analysis(0, 2025)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_MONTH")
    
    def test_get_monthly_analysis_invalid_year(self):
        """Test monthly analysis with invalid year."""
        result = self.data_manager.get_monthly_analysis(7, 1999)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_YEAR")
        
        result = self.data_manager.get_monthly_analysis(7, 2030)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_YEAR")
    
    def test_validate_data_integrity_success(self):
        """Test data integrity validation with valid files."""
        # Create valid expense file
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
            writer.writerow(["2025-07-15", "Comida", "Test", "1500"])
        
        # Create valid investment file
        df = pd.DataFrame([{"Fecha": "2025-07-15", "Activo": "AAPL", "Tipo": "Compra", "Monto_ARS": 1000}])
        df.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        # Create valid budget file
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            json.dump({"Comida": 5000}, f)
        
        # Create reports directory
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
        
        result = self.data_manager.validate_data_integrity()
        self.assertTrue(result.success)
        self.assertIn("validated_files", result.data)
    
    def test_validate_data_integrity_missing_files(self):
        """Test data integrity validation with missing files."""
        result = self.data_manager.validate_data_integrity()
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "DATA_INTEGRITY_ISSUES")
        self.assertIn("issues", result.data)
        self.assertTrue(len(result.data["issues"]) > 0)
    
    def test_load_and_analyze_expenses_empty_file(self):
        """Test expense analysis with empty file."""
        # Create empty CSV file with headers
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
        
        result = self.data_manager._load_and_analyze_expenses(7, 2025)
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["by_category"], {})
        self.assertEqual(result["records"], [])
    
    def test_load_and_analyze_investments_empty_file(self):
        """Test investment analysis with empty file."""
        # Create empty Excel file with headers
        df = pd.DataFrame(columns=["Fecha", "Activo", "Tipo", "Monto_ARS"])
        df.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        result = self.data_manager._load_and_analyze_investments(7, 2025)
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["by_asset"], {})
        self.assertEqual(result["records"], [])


if __name__ == '__main__':
    unittest.main()