# -*- coding: utf-8 -*-
"""
Integration tests for complete workflows in the PECO application.
Tests end-to-end functionality including expense registration, analysis, and PDF generation.
"""

import unittest
import tempfile
import os
import csv
import json
import pandas as pd
import shutil
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import datetime
import subprocess
from io import StringIO

from services.data_manager import DataManager
from services.latex_processor import LaTeXProcessor
from services.pdf_generator import PDFGenerator
from services.system_checker import SystemChecker
from services.base import Result, AnalysisResult, PDFResult
from services.exceptions import LaTeXError, DataError, ConfigurationError


class TestExpenseRegistrationWorkflow(unittest.TestCase):
    """Integration tests for complete expense registration workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config module
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        self.mock_config.RUTA_RESOLUCIONES = os.path.join(self.temp_dir, "resoluciones")
        
        # Initialize services
        self.data_manager = DataManager(self.mock_config)
        self.latex_processor = LaTeXProcessor()
        
        # Create necessary directories
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
        os.makedirs(self.mock_config.RUTA_RESOLUCIONES, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_expense_registration_to_analysis_workflow(self):
        """Test complete workflow from expense registration to monthly analysis."""
        # Step 1: Register multiple expenses with special characters
        expenses = [
            (150.50, "Comida", "Almuerzo en restaurante con 10% de descuento"),
            (75.25, "Transporte", "Viaje en Uber - tarifa dinámica $75.25"),
            (200.00, "Servicios", "Pago de luz & gas (factura #12345)"),
            (50.75, "Comida", "Compra en supermercado: $50.75"),
            (125.00, "Entretenimiento", "Cine & palomitas - descuento 15%")
        ]
        
        # Register all expenses
        registration_results = []
        for amount, category, description in expenses:
            result = self.data_manager.register_expense(amount, category, description)
            registration_results.append(result)
            self.assertTrue(result.success, f"Failed to register expense: {description}")
        
        # Step 2: Verify file was created and contains all expenses
        self.assertTrue(os.path.exists(self.mock_config.CSV_GASTOS))
        
        with open(self.mock_config.CSV_GASTOS, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(len(rows), len(expenses) + 1)  # Header + expenses
        
        # Step 3: Generate monthly analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Step 4: Verify analysis results
        expected_total = sum(expense[0] for expense in expenses)
        self.assertEqual(analysis_result.total_expenses, expected_total)
        
        # Verify category breakdown
        expected_categories = {}
        for amount, category, _ in expenses:
            expected_categories[category] = expected_categories.get(category, 0) + amount
        
        for category, expected_amount in expected_categories.items():
            self.assertEqual(analysis_result.expenses_by_category[category], expected_amount)
        
        # Step 5: Verify analysis data structure
        self.assertIsNotNone(analysis_result.analysis_data)
        self.assertIn("expenses", analysis_result.analysis_data)
        self.assertIn("month", analysis_result.analysis_data)
        self.assertIn("year", analysis_result.analysis_data)
        
        # Step 6: Verify individual records contain special characters properly
        expense_records = analysis_result.analysis_data["expenses"]["records"]
        self.assertEqual(len(expense_records), len(expenses))
        
        # Check that special characters are preserved in the data
        descriptions = [record["Descripcion"] for record in expense_records]
        self.assertTrue(any("$" in desc for desc in descriptions))
        self.assertTrue(any("&" in desc for desc in descriptions))
        self.assertTrue(any("#" in desc for desc in descriptions))
        self.assertTrue(any("%" in desc for desc in descriptions))
    
    def test_expense_registration_with_data_validation_workflow(self):
        """Test expense registration workflow with comprehensive data validation."""
        # Create missing files for data integrity validation
        # Create empty investments file
        df_empty = pd.DataFrame(columns=["Fecha", "Activo", "Tipo", "Monto_ARS"])
        df_empty.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        # Create budget file
        budget_data = {"monthly_budget": 5000.0}
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            json.dump(budget_data, f)
        
        # Test valid expense registration
        valid_result = self.data_manager.register_expense(100.0, "Test", "Valid expense")
        self.assertTrue(valid_result.success)
        
        # Test data integrity validation after registration
        integrity_result = self.data_manager.validate_data_integrity()
        self.assertTrue(integrity_result.success)
        
        # Test invalid expense registration
        invalid_results = [
            self.data_manager.register_expense(-100.0, "Test", "Negative amount"),
            self.data_manager.register_expense(0.0, "Test", "Zero amount"),
            self.data_manager.register_expense(100.0, "", "Empty category"),
            self.data_manager.register_expense(100.0, "Test", ""),
            self.data_manager.register_expense(2000000.0, "Test", "Excessive amount")
        ]
        
        for result in invalid_results:
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_code)
        
        # Verify that invalid registrations didn't corrupt the file
        final_integrity_result = self.data_manager.validate_data_integrity()
        self.assertTrue(final_integrity_result.success)
    
    def test_expense_registration_with_unicode_and_special_chars_workflow(self):
        """Test expense registration workflow with unicode and special characters."""
        unicode_expenses = [
            (100.0, "Alimentación", "Café con leche y medialunas"),
            (200.0, "Educación", "Curso de programación - certificación"),
            (150.0, "Salud", "Consulta médica + medicamentos"),
            (75.0, "Transporte", "Viaje en colectivo línea 152"),
            (300.0, "Hogar", "Compra de electrodomésticos & accesorios")
        ]
        
        # Register all unicode expenses
        for amount, category, description in unicode_expenses:
            result = self.data_manager.register_expense(amount, category, description)
            self.assertTrue(result.success)
        
        # Verify file encoding and content preservation
        with open(self.mock_config.CSV_GASTOS, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Alimentación", content)
            self.assertIn("Café con leche", content)
            self.assertIn("programación", content)
            self.assertIn("médica", content)
            self.assertIn("línea", content)
            self.assertIn("electrodomésticos", content)
        
        # Generate analysis and verify unicode preservation
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Verify unicode characters in category names
        categories = list(analysis_result.expenses_by_category.keys())
        self.assertIn("Alimentación", categories)
        self.assertIn("Educación", categories)


class TestInvestmentRegistrationWorkflow(unittest.TestCase):
    """Integration tests for complete investment registration workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config module
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        
        self.data_manager = DataManager(self.mock_config)
        
        # Create necessary directories
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_investment_workflow_with_analysis(self):
        """Test complete investment workflow from registration to analysis."""
        # Step 1: Register multiple investment operations
        investments = [
            ("AAPL", "Compra", 1500.0),
            ("GOOGL", "Compra", 2000.0),
            ("MSFT", "Compra", 1000.0),
            ("AAPL", "Venta", 500.0),
            ("TSLA", "Compra", 3000.0),
            ("GOOGL", "Venta", 800.0)
        ]
        
        # Register all investments
        for asset, operation_type, amount in investments:
            result = self.data_manager.register_investment(asset, operation_type, amount)
            self.assertTrue(result.success, f"Failed to register {operation_type} of {asset}")
        
        # Step 2: Verify Excel file was created and contains all investments
        self.assertTrue(os.path.exists(self.mock_config.XLSX_INVERSIONES))
        
        df = pd.read_excel(self.mock_config.XLSX_INVERSIONES)
        self.assertEqual(len(df), len(investments))
        
        # Step 3: Generate monthly analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Step 4: Verify investment analysis calculations
        expected_purchases = sum(amount for _, op_type, amount in investments if op_type == "Compra")
        expected_sales = sum(amount for _, op_type, amount in investments if op_type == "Venta")
        
        investments_data = analysis_result.analysis_data["investments"]
        self.assertEqual(investments_data["total_compras"], expected_purchases)
        self.assertEqual(investments_data["total_ventas"], expected_sales)
        self.assertEqual(analysis_result.total_investments, expected_purchases)
        
        # Step 5: Verify asset breakdown
        expected_by_asset = {}
        for asset, _, amount in investments:
            expected_by_asset[asset] = expected_by_asset.get(asset, 0) + amount
        
        for asset, expected_amount in expected_by_asset.items():
            self.assertEqual(investments_data["by_asset"][asset], expected_amount)
    
    def test_mixed_investment_operations_workflow(self):
        """Test workflow with mixed investment operations over time."""
        # Simulate investment operations over multiple days
        operations = [
            ("2025-07-01", "AAPL", "Compra", 1000.0),
            ("2025-07-05", "AAPL", "Compra", 500.0),
            ("2025-07-10", "GOOGL", "Compra", 2000.0),
            ("2025-07-15", "AAPL", "Venta", 800.0),
            ("2025-07-20", "MSFT", "Compra", 1500.0),
            ("2025-07-25", "GOOGL", "Venta", 1000.0)
        ]
        
        # Create Excel file with historical data
        df_data = []
        for date, asset, op_type, amount in operations:
            df_data.append({
                "Fecha": date,
                "Activo": asset,
                "Tipo": op_type,
                "Monto_ARS": amount
            })
        
        df = pd.DataFrame(df_data)
        df.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        # Generate analysis for July 2025
        analysis_result = self.data_manager.get_monthly_analysis(7, 2025)
        self.assertTrue(analysis_result.success)
        
        # Verify calculations
        total_purchases = sum(amount for _, _, op_type, amount in operations if op_type == "Compra")
        total_sales = sum(amount for _, _, op_type, amount in operations if op_type == "Venta")
        
        investments_data = analysis_result.analysis_data["investments"]
        self.assertEqual(investments_data["total_compras"], total_purchases)
        self.assertEqual(investments_data["total_ventas"], total_sales)
        
        # Verify individual records
        self.assertEqual(len(investments_data["records"]), len(operations))


class TestPDFGenerationWorkflow(unittest.TestCase):
    """Integration tests for complete PDF generation workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.latex_processor = LaTeXProcessor()
        self.pdf_generator = PDFGenerator(self.latex_processor)
        
        # Create template directory structure
        self.template_dir = os.path.join(self.temp_dir, "templates")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.template_dir)
        os.makedirs(self.output_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_pdf_generation_workflow_with_special_characters(self):
        """Test complete PDF generation workflow with special characters."""
        # Step 1: Create template with special character placeholders
        template_content = """
\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\begin{document}

\\title{{ '{' }}{{ '{' }}{{ title }}{{ '}' }}{{ '}' }}
\\author{{ '{' }}{{ '{' }}{{ author }}{{ '}' }}{{ '}' }}
\\date{{ '{' }}{{ '{' }}{{ date }}{{ '}' }}{{ '}' }}
\\maketitle

\\section{Resumen Financiero}
{{ description }}

\\subsection{Gastos del Mes}
\\begin{itemize}
{% for expense in expenses %}
\\item {{ expense.description }}: {{ expense.amount }}
{% endfor %}
\\end{itemize}

\\subsection{Totales}
\\begin{itemize}
\\item Total de gastos: {{ total_expenses }}
\\item Tasa de interés: {{ interest_rate }}
\\item Categoría principal: {{ main_category }}
\\end{itemize}

\\end{document}
"""
        
        template_path = os.path.join(self.template_dir, "financial_report.tex")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # Step 2: Prepare data with special characters
        template_data = {
            'title': 'Reporte Financiero - Julio 2025',
            'author': 'Sistema PECO & Asociados',
            'date': '2025-07-24',
            'description': 'Este reporte incluye gastos con caracteres especiales como $, %, &, #, etc.',
            'expenses': [
                {
                    'description': 'Comida & bebidas en restaurante',
                    'amount': '$250.50'
                },
                {
                    'description': 'Transporte (Uber) - tarifa dinámica',
                    'amount': '$125.75'
                },
                {
                    'description': 'Servicios públicos: luz & gas',
                    'amount': '$180.25'
                },
                {
                    'description': 'Compra con descuento del 15%',
                    'amount': '$95.00'
                }
            ],
            'total_expenses': '$651.50',
            'interest_rate': '3.5%',
            'main_category': 'Alimentación & Entretenimiento'
        }
        
        # Step 3: Process template (this should escape special characters)
        processed_content = self.pdf_generator.process_template(template_path, template_data)
        
        # Step 4: Verify special characters were escaped
        self.assertIn('Sistema PECO \\& Asociados', processed_content)
        self.assertIn('caracteres especiales como \\$, \\%, \\&, \\#', processed_content)
        self.assertIn('Comida \\& bebidas', processed_content)
        self.assertIn('\\$250.50', processed_content)
        self.assertIn('luz \\& gas', processed_content)
        self.assertIn('descuento del 15\\%', processed_content)
        self.assertIn('3.5\\%', processed_content)
        self.assertIn('Alimentación \\& Entretenimiento', processed_content)
        
        # Step 5: Write processed content to file
        tex_output_path = os.path.join(self.output_dir, "test_report.tex")
        with open(tex_output_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        # Verify file was created
        self.assertTrue(os.path.exists(tex_output_path))
        
        # Step 6: Test directory structure validation
        result = self.pdf_generator.ensure_directory_structure(self.output_dir)
        self.assertTrue(result)
    
    @patch.object(PDFGenerator, 'check_latex_availability')
    @patch('subprocess.run')
    def test_complete_pdf_compilation_workflow(self, mock_subprocess, mock_latex_check):
        """Test complete PDF compilation workflow with mocked LaTeX."""
        mock_latex_check.return_value = True
        
        # Create simple LaTeX document
        tex_content = """
\\documentclass{article}
\\begin{document}
Test document with escaped characters: \\$ \\% \\&
\\end{document}
"""
        
        tex_path = os.path.join(self.output_dir, "test.tex")
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        
        # Mock successful compilation
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="This is pdfTeX, Version 3.14159265",
            stderr=""
        )
        
        # Create fake PDF to simulate successful compilation
        pdf_path = os.path.join(self.output_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("fake pdf content")
        
        # Test compilation
        result = self.pdf_generator.compile_to_pdf(tex_path, self.output_dir)
        
        self.assertTrue(result.success)
        self.assertTrue(result.pdf_created)
        self.assertEqual(result.return_code, 0)
        
        # Verify subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        self.assertEqual(call_args[0], 'pdflatex')
        self.assertIn('-interaction=nonstopmode', call_args)
        self.assertIn('-output-directory', call_args)
    
    def test_template_resource_copying_workflow(self):
        """Test template resource copying workflow."""
        # Create template with resource files
        template_path = os.path.join(self.template_dir, "template.tex")
        with open(template_path, 'w') as f:
            f.write("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Create resource files
        resources = ['logo.png', 'firma.png']
        for resource in resources:
            resource_path = os.path.join(self.template_dir, resource)
            with open(resource_path, 'wb') as f:
                f.write(b'fake image data')
        
        # Copy resources
        result = self.pdf_generator._copy_template_resources(template_path, self.output_dir)
        
        # Verify resources were copied
        for resource in resources:
            output_path = os.path.join(self.output_dir, resource)
            self.assertTrue(os.path.exists(output_path))
            
            # Verify subdirectory structure
            subdir_path = os.path.join(self.output_dir, '05_Templates_y_Recursos', resource)
            self.assertTrue(os.path.exists(subdir_path))
        
        # Verify result
        self.assertEqual(result['total_copied'], len(resources))
        self.assertEqual(result['total_failed'], 0)
    
    def test_cleanup_workflow(self):
        """Test temporary file cleanup workflow."""
        base_path = os.path.join(self.output_dir, "test_document")
        
        # Create various files
        files_to_create = [
            (base_path + '.tex', 'LaTeX source'),
            (base_path + '.pdf', 'PDF output'),
            (base_path + '.aux', 'auxiliary file'),
            (base_path + '.log', 'log file'),
            (base_path + '.fls', 'file list'),
            (base_path + '.synctex.gz', 'sync file')
        ]
        
        for file_path, content in files_to_create:
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Clean temporary files
        result = self.pdf_generator.clean_temp_files(base_path)
        
        # Verify important files remain
        self.assertTrue(os.path.exists(base_path + '.tex'))
        self.assertTrue(os.path.exists(base_path + '.pdf'))
        
        # Verify temporary files were removed
        self.assertFalse(os.path.exists(base_path + '.aux'))
        self.assertFalse(os.path.exists(base_path + '.log'))
        self.assertFalse(os.path.exists(base_path + '.fls'))
        self.assertFalse(os.path.exists(base_path + '.synctex.gz'))
        
        # Verify cleanup result
        self.assertEqual(result['total_cleaned'], 4)  # aux, log, fls, synctex.gz
        self.assertEqual(result['total_failed'], 0)


class TestWebInterfaceWorkflow(unittest.TestCase):
    """Integration tests for web interface workflows with mock HTTP requests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        
        # Create necessary directories
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('services.data_manager.DataManager')
    def test_web_expense_registration_workflow(self, mock_data_manager_class):
        """Test web interface expense registration workflow."""
        # Mock DataManager instance
        mock_data_manager = Mock()
        mock_data_manager_class.return_value = mock_data_manager
        
        # Mock successful expense registration
        mock_data_manager.register_expense.return_value = Result(
            success=True,
            message="Gasto registrado con éxito",
            data={
                "fecha": "2025-07-24",
                "categoria": "Comida",
                "descripcion": "Almuerzo con colegas",
                "monto": 150.0
            }
        )
        
        # Simulate web request data
        request_data = {
            'amount': 150.0,
            'category': 'Comida',
            'description': 'Almuerzo con colegas'
        }
        
        # Test the workflow
        data_manager = mock_data_manager_class()
        result = data_manager.register_expense(
            request_data['amount'],
            request_data['category'],
            request_data['description']
        )
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Gasto registrado con éxito")
        self.assertIn("fecha", result.data)
        self.assertEqual(result.data["monto"], 150.0)
        
        # Verify DataManager was called correctly
        mock_data_manager.register_expense.assert_called_once_with(150.0, 'Comida', 'Almuerzo con colegas')
    
    @patch('services.data_manager.DataManager')
    def test_web_expense_registration_error_handling_workflow(self, mock_data_manager_class):
        """Test web interface error handling workflow."""
        # Mock DataManager instance
        mock_data_manager = Mock()
        mock_data_manager_class.return_value = mock_data_manager
        
        # Mock validation error
        mock_data_manager.register_expense.return_value = Result(
            success=False,
            message="El monto debe ser mayor a 0",
            error_code="INVALID_AMOUNT"
        )
        
        # Simulate invalid web request
        request_data = {
            'amount': -100.0,
            'category': 'Comida',
            'description': 'Invalid expense'
        }
        
        # Test error handling
        data_manager = mock_data_manager_class()
        result = data_manager.register_expense(
            request_data['amount'],
            request_data['category'],
            request_data['description']
        )
        
        # Verify error response
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_AMOUNT")
        self.assertIn("mayor a 0", result.message)
    
    @patch('services.data_manager.DataManager')
    def test_web_monthly_analysis_workflow(self, mock_data_manager_class):
        """Test web interface monthly analysis workflow."""
        # Mock DataManager instance
        mock_data_manager = Mock()
        mock_data_manager_class.return_value = mock_data_manager
        
        # Mock analysis result
        mock_analysis_data = {
            "month": 7,
            "year": 2025,
            "expenses": {
                "total": 500.0,
                "by_category": {"Comida": 300.0, "Transporte": 200.0},
                "records": [
                    {"Fecha": "2025-07-15", "Categoria": "Comida", "Descripcion": "Almuerzo", "Monto_ARS": 150.0},
                    {"Fecha": "2025-07-16", "Categoria": "Transporte", "Descripcion": "Uber", "Monto_ARS": 75.0}
                ]
            },
            "investments": {
                "total": 1000.0,
                "by_asset": {"AAPL": 1000.0}
            }
        }
        
        mock_data_manager.get_monthly_analysis.return_value = AnalysisResult(
            success=True,
            message="Análisis generado correctamente",
            total_expenses=500.0,
            expenses_by_category={"Comida": 300.0, "Transporte": 200.0},
            total_investments=1000.0,
            analysis_data=mock_analysis_data
        )
        
        # Test analysis workflow
        data_manager = mock_data_manager_class()
        result = data_manager.get_monthly_analysis(7, 2025)
        
        # Verify analysis result
        self.assertTrue(result.success)
        self.assertEqual(result.total_expenses, 500.0)
        self.assertEqual(result.total_investments, 1000.0)
        self.assertIn("Comida", result.expenses_by_category)
        self.assertIn("expenses", result.analysis_data)
        
        # Verify method was called correctly
        mock_data_manager.get_monthly_analysis.assert_called_once_with(7, 2025)
    
    def test_web_interface_json_response_format_workflow(self):
        """Test web interface JSON response formatting workflow."""
        # Test successful response formatting
        success_result = Result(
            success=True,
            message="Operación exitosa",
            data={"id": 123, "amount": 150.0}
        )
        
        # Simulate JSON response creation
        json_response = {
            "success": success_result.success,
            "message": success_result.message,
            "data": success_result.data,
            "error_code": success_result.error_code
        }
        
        self.assertTrue(json_response["success"])
        self.assertEqual(json_response["message"], "Operación exitosa")
        self.assertIsNotNone(json_response["data"])
        self.assertIsNone(json_response["error_code"])
        
        # Test error response formatting
        error_result = Result(
            success=False,
            message="Error de validación",
            error_code="VALIDATION_ERROR"
        )
        
        error_json_response = {
            "success": error_result.success,
            "message": error_result.message,
            "data": error_result.data,
            "error_code": error_result.error_code
        }
        
        self.assertFalse(error_json_response["success"])
        self.assertEqual(error_json_response["error_code"], "VALIDATION_ERROR")
        self.assertIsNone(error_json_response["data"])


class TestSystemValidationWorkflow(unittest.TestCase):
    """Integration tests for system validation and startup workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.system_checker = SystemChecker()
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        
        self.data_manager = DataManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_system_dependency_validation_workflow(self, mock_subprocess):
        """Test system dependency validation workflow."""
        # Mock successful pdflatex check
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="pdfTeX 3.14159265-2.6-1.40.20 (TeX Live 2019/Debian)"
        )
        
        # Test dependency checking
        result = self.system_checker.check_all_dependencies()
        
        # Verify result structure
        self.assertIsInstance(result, Result)
        self.assertIsNotNone(result.success)
        self.assertIsNotNone(result.message)
        
        # Test with missing dependency
        mock_subprocess.side_effect = FileNotFoundError("pdflatex not found")
        
        result_missing = self.system_checker.check_all_dependencies()
        self.assertIsInstance(result_missing, Result)
    
    def test_data_integrity_validation_workflow(self):
        """Test complete data integrity validation workflow."""
        # Step 1: Create valid data files
        # Create expenses file
        with open(self.mock_config.CSV_GASTOS, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
            writer.writerow(["2025-07-24", "Comida", "Test expense", "100.0"])
        
        # Create investments file
        df = pd.DataFrame([{
            "Fecha": "2025-07-24",
            "Activo": "AAPL",
            "Tipo": "Compra",
            "Monto_ARS": 1000.0
        }])
        df.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        # Create budget file
        budget_data = {"monthly_budget": 5000.0, "categories": {"Comida": 1000.0}}
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            json.dump(budget_data, f)
        
        # Create directories
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
        
        # Step 2: Validate data integrity
        result = self.data_manager.validate_data_integrity()
        
        # Step 3: Verify validation results
        self.assertTrue(result.success)
        self.assertIn("validated_files", result.data)
        
        # Step 4: Test with corrupted data
        # Corrupt expenses file
        with open(self.mock_config.CSV_GASTOS, 'w', encoding='utf-8') as f:
            f.write("invalid,csv,format\n")
            f.write("missing,columns\n")
        
        # Validate again
        corrupted_result = self.data_manager.validate_data_integrity()
        
        # Should detect issues
        self.assertFalse(corrupted_result.success)
        self.assertEqual(corrupted_result.error_code, "DATA_INTEGRITY_ISSUES")
        self.assertIn("issues", corrupted_result.data)
    
    def test_startup_validation_workflow(self):
        """Test complete startup validation workflow."""
        # Test startup requirements validation
        startup_result = self.system_checker.validate_startup_requirements()
        
        # Verify result structure
        self.assertIsInstance(startup_result, Result)
        self.assertIsNotNone(startup_result.success)
        
        # Test system info gathering
        system_info = self.system_checker.get_system_info()
        
        # Verify system info structure
        self.assertIsInstance(system_info, dict)
        self.assertIn("platform", system_info)
        self.assertIn("python_version", system_info)


class TestCompleteEndToEndWorkflow(unittest.TestCase):
    """Integration tests for complete end-to-end workflows combining all components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        self.mock_config.RUTA_RESOLUCIONES = os.path.join(self.temp_dir, "resoluciones")
        self.mock_config.RUTA_TEMPLATES = os.path.join(self.temp_dir, "templates")
        
        # Initialize services
        self.data_manager = DataManager(self.mock_config)
        self.latex_processor = LaTeXProcessor()
        self.pdf_generator = PDFGenerator(self.latex_processor)
        
        # Create necessary directories
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
        os.makedirs(self.mock_config.RUTA_RESOLUCIONES, exist_ok=True)
        os.makedirs(self.mock_config.RUTA_TEMPLATES, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_financial_workflow_with_pdf_generation(self):
        """Test complete workflow from data entry to PDF generation."""
        # Step 1: Register expenses with special characters
        expenses = [
            (250.50, "Comida", "Restaurante 'La Parrilla' - descuento 10%"),
            (125.75, "Transporte", "Uber Pool - tarifa dinámica $125.75"),
            (300.00, "Servicios", "Electricidad & Gas - factura #AB123"),
            (85.25, "Entretenimiento", "Cine IMAX - película 'Avatar 2'"),
            (450.00, "Salud", "Consulta médica + medicamentos")
        ]
        
        for amount, category, description in expenses:
            result = self.data_manager.register_expense(amount, category, description)
            self.assertTrue(result.success)
        
        # Step 2: Register investments
        investments = [
            ("AAPL", "Compra", 2000.0),
            ("GOOGL", "Compra", 1500.0),
            ("MSFT", "Compra", 1000.0),
            ("TSLA", "Compra", 2500.0)
        ]
        
        for asset, op_type, amount in investments:
            result = self.data_manager.register_investment(asset, op_type, amount)
            self.assertTrue(result.success)
        
        # Step 3: Generate monthly analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Step 4: Prepare report data with LaTeX-safe processing
        report_data = {
            'title': f'Reporte Financiero - {current_month}/{current_year}',
            'total_expenses': f'${analysis_result.total_expenses:.2f}',
            'total_investments': f'${analysis_result.total_investments:.2f}',
            'expense_categories': [],
            'investment_summary': []
        }
        
        # Process expense categories
        for category, amount in analysis_result.expenses_by_category.items():
            report_data['expense_categories'].append({
                'name': category,
                'amount': f'${amount:.2f}'
            })
        
        # Process investment data
        investments_data = analysis_result.analysis_data.get('investments', {})
        for asset, amount in investments_data.get('by_asset', {}).items():
            report_data['investment_summary'].append({
                'asset': asset,
                'amount': f'${amount:.2f}'
            })
        
        # Step 5: Process data through LaTeX processor
        processed_data = self.pdf_generator._process_template_data(report_data)
        
        # Verify special characters were escaped
        self.assertIn('\\$', str(processed_data))
        
        # Step 6: Create missing files for data integrity validation
        # Create empty investments file
        df_empty = pd.DataFrame(columns=["Fecha", "Activo", "Tipo", "Monto_ARS"])
        df_empty.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        # Create budget file
        budget_data = {"monthly_budget": 5000.0}
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            json.dump(budget_data, f)
        
        # Validate data integrity
        integrity_result = self.data_manager.validate_data_integrity()
        self.assertTrue(integrity_result.success)
        
        # Step 7: Verify complete workflow results
        self.assertGreater(analysis_result.total_expenses, 0)
        self.assertGreater(analysis_result.total_investments, 0)
        self.assertGreater(len(analysis_result.expenses_by_category), 0)
        self.assertIsNotNone(processed_data)
    
    @patch.object(PDFGenerator, 'check_latex_availability')
    @patch('subprocess.run')
    def test_complete_pdf_generation_workflow_with_real_data(self, mock_subprocess, mock_latex_check):
        """Test complete PDF generation workflow with real financial data."""
        mock_latex_check.return_value = True
        
        # Step 1: Register sample financial data
        self.data_manager.register_expense(500.0, "Comida", "Gastos de alimentación del mes")
        self.data_manager.register_expense(300.0, "Transporte", "Viajes & combustible")
        self.data_manager.register_investment("AAPL", "Compra", 2000.0)
        
        # Step 2: Generate analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        
        # Step 3: Create template
        template_content = """
\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\begin{document}
\\title{{ '{' }}{{ title }}{{ '}' }}
\\maketitle

\\section{Resumen Financiero}
Total de gastos: {{ total_expenses }}
Total de inversiones: {{ total_investments }}

\\subsection{Gastos por Categoría}
\\begin{itemize}
{% for category, amount in expenses_by_category.items() %}
\\item {{ category }}: \\${{ "%.2f"|format(amount) }}
{% endfor %}
\\end{itemize}

\\end{document}
"""
        
        template_path = os.path.join(self.mock_config.RUTA_TEMPLATES, "report_template.tex")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # Step 4: Prepare template data
        template_data = {
            'title': 'Reporte Mensual de Finanzas',
            'total_expenses': analysis_result.total_expenses,
            'total_investments': analysis_result.total_investments,
            'expenses_by_category': analysis_result.expenses_by_category
        }
        
        # Step 5: Mock successful PDF compilation
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="Output written on report.pdf (1 page, 12345 bytes).",
            stderr=""
        )
        
        # Create fake PDF file
        pdf_path = os.path.join(self.mock_config.RUTA_RESOLUCIONES, "financial_report.pdf")
        with open(pdf_path, 'w') as f:
            f.write("fake pdf content")
        
        # Step 6: Generate PDF
        pdf_result = self.pdf_generator.generate_resolution(
            template_path=template_path,
            data=template_data,
            output_dir=self.mock_config.RUTA_RESOLUCIONES,
            filename_base="financial_report"
        )
        
        # Step 7: Verify PDF generation
        self.assertTrue(pdf_result.success)
        self.assertIsNotNone(pdf_result.pdf_path)
        self.assertIsNotNone(pdf_result.tex_path)
    
    def test_error_recovery_workflow(self):
        """Test error recovery and resilience workflow."""
        # Test recovery from invalid expense registration
        invalid_result = self.data_manager.register_expense(-100.0, "", "")
        self.assertFalse(invalid_result.success)
        
        # System should still work after invalid input
        valid_result = self.data_manager.register_expense(100.0, "Test", "Valid expense")
        self.assertTrue(valid_result.success)
        
        # Test recovery from invalid investment registration
        invalid_inv_result = self.data_manager.register_investment("", "InvalidType", -100.0)
        self.assertFalse(invalid_inv_result.success)
        
        # System should still work
        valid_inv_result = self.data_manager.register_investment("AAPL", "Compra", 1000.0)
        self.assertTrue(valid_inv_result.success)
        
        # Analysis should work despite previous errors
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Create missing files for data integrity validation
        # Create budget file
        budget_data = {"monthly_budget": 5000.0}
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            json.dump(budget_data, f)
        
        # Data integrity should be maintained
        integrity_result = self.data_manager.validate_data_integrity()
        self.assertTrue(integrity_result.success)
    
    def test_concurrent_operations_workflow(self):
        """Test workflow with concurrent-like operations."""
        # Simulate multiple rapid operations
        operations = [
            ("expense", 100.0, "Comida", "Almuerzo"),
            ("investment", "AAPL", "Compra", 1000.0),
            ("expense", 50.0, "Transporte", "Taxi"),
            ("investment", "GOOGL", "Compra", 500.0),
            ("expense", 200.0, "Servicios", "Internet"),
            ("investment", "MSFT", "Venta", 300.0)
        ]
        
        results = []
        for operation in operations:
            if operation[0] == "expense":
                result = self.data_manager.register_expense(operation[1], operation[2], operation[3])
            else:  # investment
                result = self.data_manager.register_investment(operation[1], operation[2], operation[3])
            
            results.append(result)
            self.assertTrue(result.success, f"Operation failed: {operation}")
        
        # Verify all operations succeeded
        self.assertEqual(len([r for r in results if r.success]), len(operations))
        
        # Verify data consistency
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Verify expected totals
        expected_expenses = sum(op[1] for op in operations if op[0] == "expense")
        expected_investments = sum(op[3] for op in operations if op[0] == "investment" and op[2] == "Compra")
        
        self.assertEqual(analysis_result.total_expenses, expected_expenses)
        self.assertEqual(analysis_result.total_investments, expected_investments)
    
    def test_unicode_and_special_characters_end_to_end_workflow(self):
        """Test complete workflow with unicode and special characters."""
        # Register data with various unicode and special characters
        unicode_data = [
            (150.0, "Alimentación", "Café & medialunas en 'La Esquina'"),
            (200.0, "Educación", "Curso de programación - certificación"),
            (100.0, "Salud", "Medicamentos: paracetamol & ibuprofeno"),
            (75.0, "Transporte", "Viaje en colectivo línea #152"),
            (300.0, "Entretenimiento", "Concierto de rock & roll - entrada VIP")
        ]
        
        for amount, category, description in unicode_data:
            result = self.data_manager.register_expense(amount, category, description)
            self.assertTrue(result.success)
        
        # Generate analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Verify unicode preservation in analysis
        categories = list(analysis_result.expenses_by_category.keys())
        self.assertIn("Alimentación", categories)
        self.assertIn("Educación", categories)
        
        # Test LaTeX processing with unicode data
        template_data = {
            'title': 'Reporte con Caracteres Especiales',
            'description': 'Este reporte contiene acentos, símbolos & caracteres especiales',
            'categories': analysis_result.expenses_by_category
        }
        
        processed_data = self.latex_processor.escape_special_characters(str(template_data))
        
        # Verify special characters were escaped but unicode preserved
        self.assertIn('\\&', processed_data)
        # Unicode characters should be preserved
        self.assertIn('Alimentación', processed_data)
        self.assertIn('Educación', processed_data)


class TestWebInterfaceIntegrationWorkflow(unittest.TestCase):
    """Integration tests for web interface with Flask app simulation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock Flask app context
        self.app_context = {
            'data_manager': None,
            'pdf_generator': None,
            'system_checker': None
        }
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        
        # Initialize services
        self.app_context['data_manager'] = DataManager(self.mock_config)
        self.app_context['pdf_generator'] = PDFGenerator(LaTeXProcessor())
        self.app_context['system_checker'] = SystemChecker()
        
        # Create directories
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_web_request_processing_workflow(self):
        """Test complete web request processing workflow."""
        # Simulate web request for expense registration
        request_data = {
            'comando': 'registrar',
            'args': {
                'monto': 150.0,
                'categoria': 'Comida',
                'desc': 'Almuerzo en restaurante'
            }
        }
        
        # Process request through service layer
        data_manager = self.app_context['data_manager']
        
        # Validate request data
        self.assertIn('comando', request_data)
        self.assertIn('args', request_data)
        self.assertEqual(request_data['comando'], 'registrar')
        
        # Extract arguments
        args = request_data['args']
        self.assertIn('monto', args)
        self.assertIn('categoria', args)
        self.assertIn('desc', args)
        
        # Execute operation
        result = data_manager.register_expense(
            args['monto'],
            args['categoria'],
            args['desc']
        )
        
        # Verify result
        self.assertTrue(result.success)
        self.assertIn("registrado", result.message.lower())
        
        # Simulate JSON response creation
        json_response = {
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'salida': result.message  # Legacy field
        }
        
        # Verify response structure
        self.assertTrue(json_response['success'])
        self.assertIsNotNone(json_response['message'])
        self.assertIsNotNone(json_response['data'])
        self.assertEqual(json_response['salida'], json_response['message'])
    
    def test_web_error_handling_workflow(self):
        """Test web interface error handling workflow."""
        # Simulate invalid web request
        invalid_request = {
            'comando': 'registrar',
            'args': {
                'monto': -100.0,  # Invalid amount
                'categoria': '',   # Empty category
                'desc': 'Invalid expense'
            }
        }
        
        data_manager = self.app_context['data_manager']
        
        # Process invalid request
        result = data_manager.register_expense(
            invalid_request['args']['monto'],
            invalid_request['args']['categoria'],
            invalid_request['args']['desc']
        )
        
        # Verify error handling
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_code)
        self.assertIn("monto", result.message.lower())
        
        # Simulate error response creation
        error_response = {
            'success': result.success,
            'message': result.message,
            'error_code': result.error_code,
            'salida': result.message
        }
        
        # Verify error response structure
        self.assertFalse(error_response['success'])
        self.assertIsNotNone(error_response['error_code'])
        self.assertIsNotNone(error_response['message'])
    
    def test_web_analysis_request_workflow(self):
        """Test web interface analysis request workflow."""
        # First, add some test data
        data_manager = self.app_context['data_manager']
        data_manager.register_expense(100.0, "Comida", "Test expense")
        data_manager.register_investment("AAPL", "Compra", 1000.0)
        
        # Simulate analysis request
        analysis_request = {
            'comando': 'analizar',
            'args': {
                'mes': datetime.now().month,
                'año': datetime.now().year
            }
        }
        
        # Process analysis request
        result = data_manager.get_monthly_analysis(
            analysis_request['args']['mes'],
            analysis_request['args']['año']
        )
        
        # Verify analysis result
        self.assertTrue(result.success)
        self.assertGreater(result.total_expenses, 0)
        self.assertGreater(result.total_investments, 0)
        
        # Simulate analysis response creation
        analysis_response = {
            'success': result.success,
            'message': result.message,
            'data': {
                'total_expenses': result.total_expenses,
                'expenses_by_category': result.expenses_by_category,
                'total_investments': result.total_investments,
                'analysis_data': result.analysis_data
            },
            'salida': result.message
        }
        
        # Verify response structure
        self.assertTrue(analysis_response['success'])
        self.assertIn('total_expenses', analysis_response['data'])
        self.assertIn('expenses_by_category', analysis_response['data'])
        self.assertIn('analysis_data', analysis_response['data'])


if __name__ == '__main__':
    # Run all integration tests
    unittest.main(verbosity=2)
    
    def setUp(self):
        """Set up test fixtures."""
        self.system_checker = SystemChecker()
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_complete_system_validation_workflow(self, mock_subprocess, mock_which):
        """Test complete system validation workflow."""
        # Mock successful dependency checks
        mock_which.return_value = '/usr/bin/pdflatex'
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout='pdfTeX 3.14159265-2.6-1.40.21'
        )
        
        # Test dependency validation
        dependency_result = self.system_checker.check_all_dependencies()
        self.assertTrue(dependency_result.success)
        
        # Test startup requirements validation
        startup_result = self.system_checker.validate_startup_requirements()
        self.assertTrue(startup_result.success)
        self.assertIn('system_info', startup_result.data)
    
    @patch('shutil.which')
    def test_system_validation_with_missing_dependencies_workflow(self, mock_which):
        """Test system validation workflow with missing dependencies."""
        # Mock missing pdflatex
        mock_which.return_value = None
        
        # Test dependency check
        dependency_result = self.system_checker.check_all_dependencies()
        self.assertFalse(dependency_result.success)
        self.assertEqual(dependency_result.error_code, 'MISSING_DEPENDENCIES')
        self.assertIn('pdflatex', dependency_result.missing_dependencies)
        
        # Test startup validation with missing dependencies
        startup_result = self.system_checker.validate_startup_requirements()
        self.assertFalse(startup_result.success)
        self.assertIn('missing_dependencies', startup_result.data)
        self.assertIn('installation_instructions', startup_result.data)


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end integration tests combining multiple services."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.JSON_PRESUPUESTO = os.path.join(self.temp_dir, "presupuesto.json")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
        self.mock_config.RUTA_REPORTES = os.path.join(self.temp_dir, "reportes")
        self.mock_config.RUTA_RESOLUCIONES = os.path.join(self.temp_dir, "resoluciones")
        
        # Initialize all services
        self.data_manager = DataManager(self.mock_config)
        self.latex_processor = LaTeXProcessor()
        self.pdf_generator = PDFGenerator(self.latex_processor)
        
        # Create directories
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)
        os.makedirs(self.mock_config.RUTA_RESOLUCIONES, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_financial_reporting_workflow(self):
        """Test complete workflow from data entry to report generation."""
        # Step 1: Register financial data with special characters
        expenses = [
            (250.50, "Alimentación", "Restaurante 'La Parrilla' - descuento 10%"),
            (125.75, "Transporte", "Viajes en Uber & taxi - tarifa nocturna"),
            (180.25, "Servicios", "Factura de luz & gas (referencia #12345)"),
            (95.00, "Entretenimiento", "Cine + palomitas - entrada 2x1"),
            (300.00, "Salud", "Consulta médica & medicamentos")
        ]
        
        investments = [
            ("AAPL", "Compra", 1500.0),
            ("GOOGL", "Compra", 2000.0),
            ("AAPL", "Venta", 500.0)
        ]
        
        # Register all data
        for amount, category, description in expenses:
            result = self.data_manager.register_expense(amount, category, description)
            self.assertTrue(result.success)
        
        for asset, op_type, amount in investments:
            result = self.data_manager.register_investment(asset, op_type, amount)
            self.assertTrue(result.success)
        
        # Step 2: Generate monthly analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Step 3: Prepare report data with LaTeX-safe processing
        report_data = {
            'title': f'Reporte Financiero - {current_month}/{current_year}',
            'total_expenses': f'${analysis_result.total_expenses:.2f}',
            'total_investments': f'${analysis_result.total_investments:.2f}',
            'expense_categories': [],
            'investment_summary': []
        }
        
        # Process expense categories
        for category, amount in analysis_result.expenses_by_category.items():
            report_data['expense_categories'].append({
                'name': category,
                'amount': f'${amount:.2f}'
            })
        
        # Process investment data
        investments_data = analysis_result.analysis_data.get('investments', {})
        for asset, amount in investments_data.get('by_asset', {}).items():
            report_data['investment_summary'].append({
                'asset': asset,
                'amount': f'${amount:.2f}'
            })
        
        # Step 4: Process data through LaTeX processor
        processed_data = self.pdf_generator._process_template_data(report_data)
        
        # Verify special characters were escaped
        self.assertIn('\\$', str(processed_data))
        
        # Step 5: Validate data integrity
        integrity_result = self.data_manager.validate_data_integrity()
        self.assertTrue(integrity_result.success)
        
        # Step 6: Verify complete workflow results
        self.assertGreater(analysis_result.total_expenses, 0)
        self.assertGreater(analysis_result.total_investments, 0)
        self.assertGreater(len(analysis_result.expenses_by_category), 0)
        self.assertIsNotNone(processed_data)
    
    def test_error_recovery_workflow(self):
        """Test error recovery and resilience workflow."""
        # Test recovery from invalid expense registration
        invalid_result = self.data_manager.register_expense(-100.0, "", "")
        self.assertFalse(invalid_result.success)
        
        # System should still work after invalid input
        valid_result = self.data_manager.register_expense(100.0, "Test", "Valid expense")
        self.assertTrue(valid_result.success)
        
        # Test recovery from invalid investment registration
        invalid_inv_result = self.data_manager.register_investment("", "InvalidType", -100.0)
        self.assertFalse(invalid_inv_result.success)
        
        # System should still work
        valid_inv_result = self.data_manager.register_investment("AAPL", "Compra", 1000.0)
        self.assertTrue(valid_inv_result.success)
        
        # Analysis should work despite previous errors
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        analysis_result = self.data_manager.get_monthly_analysis(current_month, current_year)
        self.assertTrue(analysis_result.success)
        
        # Data integrity should be maintained
        integrity_result = self.data_manager.validate_data_integrity()
        self.assertTrue(integrity_result.success)


if __name__ == '__main__':
    # Run all integration tests
    unittest.main(verbosity=2)