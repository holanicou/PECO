# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for all service layer classes.
This test suite provides complete coverage of DataManager, LaTeXProcessor, and PDFGenerator.
"""

import unittest
import tempfile
import os
import csv
import json
import pandas as pd
import shutil
import subprocess
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from datetime import datetime
from io import StringIO

from services.data_manager import DataManager
from services.latex_processor import LaTeXProcessor
from services.pdf_generator import PDFGenerator, PDFResult, CompilationResult
from services.base import Result, AnalysisResult
from services.exceptions import LaTeXError, DataError, ConfigurationError


class TestDataManagerComprehensive(unittest.TestCase):
    """Comprehensive test cases for DataManager class."""
    
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
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_with_default_config(self):
        """Test DataManager initialization with default config module."""
        with patch('services.data_manager.config') as mock_config_module:
            mock_config_module.CSV_GASTOS = "test.csv"
            dm = DataManager()
            self.assertEqual(dm.csv_gastos, "test.csv")
    
    def test_register_expense_creates_directory_structure(self):
        """Test that expense registration creates necessary directories."""
        # Remove the temp directory to test creation
        shutil.rmtree(self.temp_dir)
        
        result = self.data_manager.register_expense(100.0, "Test", "Description")
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertTrue(os.path.exists(self.mock_config.CSV_GASTOS))
    
    def test_register_expense_appends_to_existing_file(self):
        """Test that expense registration appends to existing file."""
        # Create initial file with header and one record
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
            writer.writerow(["2025-07-01", "Existing", "Old record", "50.0"])
        
        result = self.data_manager.register_expense(100.0, "New", "New record")
        
        self.assertTrue(result.success)
        
        # Verify both records exist
        with open(self.mock_config.CSV_GASTOS, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 3)  # Header + 2 data rows
            self.assertEqual(rows[1][1], "Existing")
            self.assertEqual(rows[2][1], "New")
    
    def test_register_expense_handles_unicode_characters(self):
        """Test expense registration with unicode characters."""
        result = self.data_manager.register_expense(
            150.0, 
            "Comida", 
            "Café con leche y medialunas"
        )
        
        self.assertTrue(result.success)
        
        # Verify unicode characters are preserved
        with open(self.mock_config.CSV_GASTOS, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Café con leche", content)
    
    @patch('services.data_manager.datetime')
    def test_register_expense_uses_current_date(self, mock_datetime):
        """Test that expense registration uses current date."""
        mock_datetime.now.return_value.strftime.return_value = "2025-07-24"
        
        result = self.data_manager.register_expense(100.0, "Test", "Description")
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["fecha"], "2025-07-24")
    
    def test_register_expense_file_permission_error(self):
        """Test expense registration with file permission error."""
        # Create a read-only file
        with open(self.mock_config.CSV_GASTOS, 'w') as f:
            f.write("test")
        os.chmod(self.mock_config.CSV_GASTOS, 0o444)  # Read-only
        
        try:
            result = self.data_manager.register_expense(100.0, "Test", "Description")
            
            self.assertFalse(result.success)
            self.assertEqual(result.error_code, "EXPENSE_REGISTRATION_ERROR")
        finally:
            # Restore permissions for cleanup
            os.chmod(self.mock_config.CSV_GASTOS, 0o666)
    
    def test_register_investment_creates_new_excel_file(self):
        """Test investment registration creates new Excel file."""
        result = self.data_manager.register_investment("AAPL", "Compra", 1000.0)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(self.mock_config.XLSX_INVERSIONES))
        
        # Verify Excel file content
        df = pd.read_excel(self.mock_config.XLSX_INVERSIONES)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["Activo"], "AAPL")
    
    def test_register_investment_appends_to_existing_file(self):
        """Test investment registration appends to existing Excel file."""
        # Create initial Excel file
        initial_df = pd.DataFrame([{
            "Fecha": "2025-07-01",
            "Activo": "GOOGL",
            "Tipo": "Compra",
            "Monto_ARS": 500.0
        }])
        initial_df.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        result = self.data_manager.register_investment("AAPL", "Venta", 1000.0)
        
        self.assertTrue(result.success)
        
        # Verify both records exist
        df = pd.read_excel(self.mock_config.XLSX_INVERSIONES)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["Activo"], "GOOGL")
        self.assertEqual(df.iloc[1]["Activo"], "AAPL")
    
    def test_register_investment_validates_operation_types(self):
        """Test investment registration validates operation types."""
        valid_types = ["Compra", "Venta"]
        
        for op_type in valid_types:
            result = self.data_manager.register_investment("AAPL", op_type, 1000.0)
            self.assertTrue(result.success, f"Failed for valid type: {op_type}")
        
        # Test invalid type
        result = self.data_manager.register_investment("AAPL", "Invalid", 1000.0)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_OPERATION_TYPE")
    
    def test_get_monthly_analysis_filters_by_date_correctly(self):
        """Test monthly analysis filters data by date correctly."""
        # Create test data spanning multiple months
        expense_data = [
            ["Fecha", "Categoria", "Descripcion", "Monto_ARS"],
            ["2025-06-15", "Comida", "June expense", "100"],
            ["2025-07-15", "Comida", "July expense 1", "200"],
            ["2025-07-20", "Transporte", "July expense 2", "150"],
            ["2025-08-15", "Comida", "August expense", "300"]
        ]
        
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(expense_data)
        
        result = self.data_manager.get_monthly_analysis(7, 2025)
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_expenses, 350.0)  # Only July expenses
        self.assertEqual(len(result.analysis_data["expenses"]["records"]), 2)
    
    def test_get_monthly_analysis_handles_invalid_dates_in_data(self):
        """Test monthly analysis handles invalid dates in data gracefully."""
        # Create test data with invalid dates
        expense_data = [
            ["Fecha", "Categoria", "Descripcion", "Monto_ARS"],
            ["invalid-date", "Comida", "Invalid date", "100"],
            ["2025-07-15", "Comida", "Valid date", "200"],
            ["", "Transporte", "Empty date", "150"]
        ]
        
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(expense_data)
        
        result = self.data_manager.get_monthly_analysis(7, 2025)
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_expenses, 200.0)  # Only valid date record
    
    def test_get_monthly_analysis_calculates_investment_totals_correctly(self):
        """Test monthly analysis calculates investment totals correctly."""
        # Create investment data with purchases and sales
        investment_data = pd.DataFrame([
            {"Fecha": "2025-07-15", "Activo": "AAPL", "Tipo": "Compra", "Monto_ARS": 1000},
            {"Fecha": "2025-07-16", "Activo": "GOOGL", "Tipo": "Compra", "Monto_ARS": 2000},
            {"Fecha": "2025-07-17", "Activo": "AAPL", "Tipo": "Venta", "Monto_ARS": 500}
        ])
        investment_data.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        result = self.data_manager.get_monthly_analysis(7, 2025)
        
        self.assertTrue(result.success)
        investments = result.analysis_data["investments"]
        self.assertEqual(investments["total_compras"], 3000.0)
        self.assertEqual(investments["total_ventas"], 500.0)
        self.assertEqual(result.total_investments, 3000.0)  # Total purchases
    
    def test_validate_data_integrity_comprehensive_check(self):
        """Test comprehensive data integrity validation."""
        # Create valid files
        self._create_valid_test_files()
        
        result = self.data_manager.validate_data_integrity()
        
        self.assertTrue(result.success)
        self.assertIn("validated_files", result.data)
        self.assertEqual(len(result.data["validated_files"]), 4)
    
    def test_validate_data_integrity_detects_missing_columns(self):
        """Test data integrity validation detects missing columns."""
        # Create CSV with missing columns
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Monto_ARS"])  # Missing Categoria, Descripcion
        
        result = self.data_manager.validate_data_integrity()
        
        self.assertFalse(result.success)
        self.assertIn("issues", result.data)
        self.assertTrue(any("Columnas faltantes" in issue for issue in result.data["issues"]))
    
    def test_validate_data_integrity_detects_invalid_amounts(self):
        """Test data integrity validation detects invalid amounts."""
        # Create CSV with non-numeric amounts
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
            writer.writerow(["2025-07-15", "Test", "Description", "not_a_number"])
        
        result = self.data_manager.validate_data_integrity()
        
        self.assertFalse(result.success)
        self.assertTrue(any("Montos no numéricos" in issue for issue in result.data["issues"]))
    
    def test_validate_data_integrity_detects_invalid_investment_types(self):
        """Test data integrity validation detects invalid investment operation types."""
        # Create Excel with invalid operation types
        df = pd.DataFrame([{
            "Fecha": "2025-07-15",
            "Activo": "AAPL",
            "Tipo": "InvalidType",
            "Monto_ARS": 1000
        }])
        df.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        result = self.data_manager.validate_data_integrity()
        
        self.assertFalse(result.success)
        self.assertTrue(any("Tipos de operación inválidos" in issue for issue in result.data["issues"]))
    
    def test_validate_data_integrity_detects_invalid_json(self):
        """Test data integrity validation detects invalid JSON."""
        # Create invalid JSON file
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json content}')  # Invalid JSON
        
        result = self.data_manager.validate_data_integrity()
        
        self.assertFalse(result.success)
        self.assertTrue(any("Error de formato JSON" in issue for issue in result.data["issues"]))
    
    def _create_valid_test_files(self):
        """Helper method to create valid test files."""
        # Create valid expense file
        with open(self.mock_config.CSV_GASTOS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Categoria", "Descripcion", "Monto_ARS"])
            writer.writerow(["2025-07-15", "Comida", "Test", "100.0"])
        
        # Create valid investment file
        df = pd.DataFrame([{
            "Fecha": "2025-07-15",
            "Activo": "AAPL",
            "Tipo": "Compra",
            "Monto_ARS": 1000
        }])
        df.to_excel(self.mock_config.XLSX_INVERSIONES, index=False)
        
        # Create valid budget file
        with open(self.mock_config.JSON_PRESUPUESTO, 'w', encoding='utf-8') as f:
            json.dump({"Comida": 5000}, f)
        
        # Create reports directory
        os.makedirs(self.mock_config.RUTA_REPORTES, exist_ok=True)


class TestLaTeXProcessorComprehensive(unittest.TestCase):
    """Comprehensive test cases for LaTeXProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = LaTeXProcessor()
    
    def test_escape_special_characters_all_problematic_chars(self):
        """Test escaping of all problematic characters defined in LATEX_ESCAPE_MAP."""
        for char, expected_escape in self.processor.LATEX_ESCAPE_MAP.items():
            with self.subTest(char=char):
                result = self.processor.escape_special_characters(char)
                self.assertEqual(result, expected_escape)
    
    def test_escape_special_characters_backslash_handling(self):
        """Test proper backslash handling to avoid double-escaping."""
        test_cases = [
            ('\\', r'\textbackslash{}'),
            ('\\$', r'\textbackslash{}\$'),
            ('$\\%', r'\$\textbackslash{}\%'),
            ('\\\\', r'\textbackslash{}\textbackslash{}')
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_special_characters(input_text)
                self.assertEqual(result, expected)
    
    def test_escape_special_characters_complex_combinations(self):
        """Test escaping of complex character combinations."""
        test_cases = [
            # Financial expressions
            ('$1,234.56 @ 5% APR', r'\$1,234.56 @ 5\% APR'),
            ('R&D budget: $50,000', r'R\&D budget: \$50,000'),
            ('Cost: {$100 + $200} * 1.5', r'Cost: \{\$100 + \$200\} \textasteriskcentered{} 1.5'),
            
            # Technical expressions
            ('File: C:\\Users\\file.txt', r'File: C:\textbackslash{}Users\textbackslash{}file.txt'),
            ('Range: [0, 100] ~ 95%', r'Range: {[}0, 100{]} \textasciitilde{} 95\%'),
            ('Formula: x^2 + y^2', r'Formula: x\textasciicircum{}2 + y\textasciicircum{}2'),
            
            # Mixed content
            ('Email: user@domain.com #urgent', r'Email: user@domain.com \#urgent'),
            ('Tags: {important} & {urgent}', r'Tags: \{important\} \& \{urgent\}'),
            ('Comparison: A < B > C', r'Comparison: A \textless{} B \textgreater{} C')
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_special_characters(input_text)
                self.assertEqual(result, expected)
    
    def test_escape_special_characters_preserves_safe_content(self):
        """Test that safe content is preserved unchanged."""
        safe_texts = [
            'This is completely safe text',
            'Numbers 123456789 are safe',
            'Letters ABCDEFG are safe',
            'Spaces and punctuation like . , ; : are safe',
            'Parentheses () are safe',
            'Quotes " and \' are safe'
        ]
        
        for safe_text in safe_texts:
            with self.subTest(text=safe_text):
                result = self.processor.escape_special_characters(safe_text)
                self.assertEqual(result, safe_text)
    
    def test_escape_special_characters_error_handling(self):
        """Test error handling for invalid inputs."""
        invalid_inputs = [None, 123, [], {}, object()]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input=invalid_input):
                with self.assertRaises(LaTeXError):
                    self.processor.escape_special_characters(invalid_input)
    
    def test_escape_currency_amounts_patterns(self):
        """Test currency escaping with various patterns."""
        test_cases = [
            # Basic currency amounts
            ('$100', r'\$100'),
            ('$1,234', r'\$1,234'),
            ('$1,234.56', r'\$1,234.56'),
            ('$0.99', r'\$0.99'),
            ('$999,999.99', r'\$999,999.99'),
            
            # Multiple amounts
            ('$100 and $200', r'\$100 and \$200'),
            ('Total: $1,500 + $2,500 = $4,000', r'Total: \$1,500 + \$2,500 = \$4,000'),
            
            # Edge cases
            ('Just $ without number', 'Just $ without number'),  # Should not match
            ('$', '$'),  # Single $ should not match
            ('Price in USD$', 'Price in USD$'),  # $ at end without number
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_currency_amounts(input_text)
                self.assertEqual(result, expected)
    
    def test_process_description_comprehensive(self):
        """Test comprehensive description processing."""
        test_cases = [
            # Real-world expense descriptions
            ('Compra en supermercado por $125.50', 'Compra en supermercado por \\$125.50'),
            ('Pago de servicios: luz & gas $180.75', 'Pago de servicios: luz \\& gas \\$180.75'),
            ('Transferencia bancaria $2,500 (comisión 2%)', 'Transferencia bancaria \\$2,500 (comisión 2\\%)'),
            ('Inversión en ETF: $1,000 @ tasa ~3.5%', 'Inversión en ETF: \\$1,000 @ tasa \\textasciitilde{}3.5\\%'),
            
            # Technical descriptions
            ('Código de referencia: #PAY_2025_001', 'Código de referencia: \\#PAY\\_2025\\_001'),
            ('Archivo: C:\\Documents\\receipt.pdf', 'Archivo: C:\\textbackslash{}Documents\\textbackslash{}receipt.pdf'),
            ('Categoría: {Alimentación} - subcategoría: {Restaurantes}', 'Categoría: \\{Alimentación\\} - subcategoría: \\{Restaurantes\\}'),
            
            # Mathematical expressions
            ('Descuento: 15% sobre $200 = $30', 'Descuento: 15\\% sobre \\$200 = \\$30'),
            ('Interés: principal * tasa^tiempo', 'Interés: principal \\textasteriskcentered{} tasa\\textasciicircum{}tiempo'),
            ('Rango de precios: [$50, $100]', 'Rango de precios: {[}\\$50, \\$100{]}')
        ]
        
        for input_desc, expected in test_cases:
            with self.subTest(description=input_desc):
                result = self.processor.process_description(input_desc)
                self.assertEqual(result, expected)
    
    def test_process_description_empty_and_none(self):
        """Test description processing with empty and None inputs."""
        # Empty string should return empty string
        result = self.processor.process_description("")
        self.assertEqual(result, "")
        
        # None should return empty string
        result = self.processor.process_description(None)
        self.assertEqual(result, "")
    
    def test_validate_escaped_text_comprehensive(self):
        """Test comprehensive text validation."""
        # Properly escaped text should validate
        valid_texts = [
            r'This is \$ properly \% escaped \& text',
            r'Formula: x\textasciicircum{}2 + y\textasciicircum{}2',
            r'Path: C:\textbackslash{}Users\textbackslash{}file',
            r'Range: {[}0, 100{]} \textasciitilde{} 95\%',
            'This is completely safe text',
            ''  # Empty string
        ]
        
        for valid_text in valid_texts:
            with self.subTest(text=valid_text):
                self.assertTrue(self.processor.validate_escaped_text(valid_text))
        
        # Unescaped problematic text should not validate
        invalid_texts = [
            'This has $ unescaped dollar',
            'This has % unescaped percent',
            'This has & unescaped ampersand',
            'This has # unescaped hash',
            'This has _ unescaped underscore',
            'This has { unescaped brace',
            'This has } unescaped brace'
        ]
        
        for invalid_text in invalid_texts:
            with self.subTest(text=invalid_text):
                self.assertFalse(self.processor.validate_escaped_text(invalid_text))
    
    def test_performance_with_large_text(self):
        """Test processor performance with large text inputs."""
        # Create large text with various special characters
        large_text = ('Test with $100 & 50% discount ' * 1000)
        
        result = self.processor.escape_special_characters(large_text)
        
        # Verify escaping worked correctly
        self.assertIn(r'\$100', result)
        self.assertIn(r'\&', result)
        self.assertIn(r'50\%', result)
        
        # Verify length increased due to escaping
        self.assertGreater(len(result), len(large_text))


class TestPDFGeneratorComprehensive(unittest.TestCase):
    """Comprehensive test cases for PDFGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.latex_processor = LaTeXProcessor()
        self.pdf_generator = PDFGenerator(self.latex_processor)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_with_default_processor(self):
        """Test PDFGenerator initialization with default LaTeX processor."""
        generator = PDFGenerator()
        self.assertIsInstance(generator.latex_processor, LaTeXProcessor)
    
    def test_initialization_with_custom_processor(self):
        """Test PDFGenerator initialization with custom LaTeX processor."""
        custom_processor = LaTeXProcessor()
        generator = PDFGenerator(custom_processor)
        self.assertIs(generator.latex_processor, custom_processor)
    
    @patch('subprocess.run')
    def test_check_latex_availability_comprehensive(self, mock_run):
        """Test comprehensive LaTeX availability checking."""
        # Test successful check
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="pdfTeX 3.14159265-2.6-1.40.21 (TeX Live 2020)"
        )
        self.assertTrue(self.pdf_generator.check_latex_availability())
        
        # Test command not found
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.pdf_generator.check_latex_availability())
        
        # Test command fails
        mock_run.side_effect = None
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(self.pdf_generator.check_latex_availability())
        
        # Test timeout
        mock_run.side_effect = subprocess.TimeoutExpired('pdflatex', 10)
        self.assertFalse(self.pdf_generator.check_latex_availability())
    
    def test_process_template_data_nested_structures(self):
        """Test template data processing with deeply nested structures."""
        complex_data = {
            'title': 'Report with $ symbols',
            'sections': [
                {
                    'name': 'Expenses & Income',
                    'items': [
                        {'desc': 'Food: $100', 'amount': '$100.00'},
                        {'desc': 'Transport: $50', 'amount': '$50.00'}
                    ]
                },
                {
                    'name': 'Investments',
                    'items': [
                        {'desc': 'Stocks: $1,000', 'amount': '$1,000.00'}
                    ]
                }
            ],
            'metadata': {
                'currency': '$',
                'rate': '5%',
                'tags': ['#important', '#monthly']
            }
        }
        
        result = self.pdf_generator._process_template_data(complex_data)
        
        # Verify top-level escaping
        self.assertEqual(result['title'], 'Report with \\$ symbols')
        
        # Verify nested list escaping
        self.assertEqual(result['sections'][0]['name'], 'Expenses \\& Income')
        self.assertEqual(result['sections'][0]['items'][0]['desc'], 'Food: \\$100')
        
        # Verify deeply nested escaping
        self.assertEqual(result['metadata']['currency'], '\\$')
        self.assertEqual(result['metadata']['rate'], '5\\%')
        self.assertEqual(result['metadata']['tags'][0], '\\#important')
    
    def test_process_template_data_preserves_non_strings(self):
        """Test that template data processing preserves non-string values."""
        data = {
            'title': 'Test Report',
            'amount': 1234.56,  # Float
            'count': 42,  # Integer
            'active': True,  # Boolean
            'items': None,  # None
            'metadata': {
                'version': 1.0,
                'enabled': False
            }
        }
        
        result = self.pdf_generator._process_template_data(data)
        
        # Verify non-strings are preserved
        self.assertEqual(result['amount'], 1234.56)
        self.assertEqual(result['count'], 42)
        self.assertEqual(result['active'], True)
        self.assertEqual(result['items'], None)
        self.assertEqual(result['metadata']['version'], 1.0)
        self.assertEqual(result['metadata']['enabled'], False)
        
        # Verify strings are escaped
        self.assertEqual(result['title'], 'Test Report')  # No special chars, unchanged
    
    def test_process_template_comprehensive_validation(self):
        """Test comprehensive template processing validation."""
        # Create a comprehensive template
        template_content = """
\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\begin{document}
\\title{{ {{ title }} }}
\\author{{ {{ author }} }}
\\date{{ {{ date }} }}
\\maketitle

\\section{{ {{ section_title }} }}
{{ description }}

\\subsection{Expenses}
\\begin{itemize}
{% for expense in expenses %}
\\item {{ expense.description }}: {{ expense.amount }}
{% endfor %}
\\end{itemize}

\\subsection{Summary}
Total: {{ total_amount }}
Rate: {{ interest_rate }}
\\end{document}
"""
        
        template_path = os.path.join(self.temp_dir, 'comprehensive_template.tex')
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        data = {
            'title': 'Monthly Financial Report',
            'author': 'John Doe & Associates',
            'date': '2025-07-24',
            'section_title': 'Financial Analysis',
            'description': 'This report covers expenses & investments for July 2025.',
            'expenses': [
                {'description': 'Food & Dining', 'amount': '$250.50'},
                {'description': 'Transportation', 'amount': '$125.00'},
                {'description': 'Utilities (Gas & Electric)', 'amount': '$180.75'}
            ],
            'total_amount': '$556.25',
            'interest_rate': '3.5%'
        }
        
        result = self.pdf_generator.process_template(template_path, data)
        
        # Verify template was processed and special characters escaped
        self.assertIn('Monthly Financial Report', result)
        self.assertIn('John Doe \\& Associates', result)
        self.assertIn('expenses \\& investments', result)
        self.assertIn('Food \\& Dining', result)
        self.assertIn('\\$250.50', result)
        self.assertIn('Gas \\& Electric', result)
        self.assertIn('3.5\\%', result)
    
    def test_process_template_file_validation_comprehensive(self):
        """Test comprehensive template file validation."""
        # Test non-existent file
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.process_template('/nonexistent/template.tex', {})
        self.assertIn('Template file not found', str(context.exception))
        
        # Test directory instead of file
        dir_path = os.path.join(self.temp_dir, 'template_dir')
        os.makedirs(dir_path)
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.process_template(dir_path, {})
        self.assertIn('Template path is not a file', str(context.exception))
        
        # Test unreadable file (simulate permission error)
        template_path = os.path.join(self.temp_dir, 'unreadable.tex')
        with open(template_path, 'w') as f:
            f.write('test')
        
        with patch('os.access', return_value=False):
            with self.assertRaises(ConfigurationError) as context:
                self.pdf_generator.process_template(template_path, {})
            self.assertIn('Template file is not readable', str(context.exception))
    
    @patch.object(PDFGenerator, 'check_latex_availability')
    @patch('subprocess.run')
    def test_compile_to_pdf_comprehensive_scenarios(self, mock_run, mock_check):
        """Test comprehensive PDF compilation scenarios."""
        mock_check.return_value = True
        
        # Create test LaTeX file
        tex_content = """
\\documentclass{article}
\\begin{document}
Test document with special characters: \\$ \\% \\&
\\end{document}
"""
        tex_path = os.path.join(self.temp_dir, 'test.tex')
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        
        # Test successful compilation
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="This is pdfTeX, Version 3.14159265-2.6-1.40.21",
            stderr=""
        )
        
        # Create expected PDF file to simulate successful compilation
        pdf_path = os.path.join(self.temp_dir, 'test.pdf')
        with open(pdf_path, 'w') as f:
            f.write('fake pdf content')
        
        result = self.pdf_generator.compile_to_pdf(tex_path, self.temp_dir)
        
        self.assertTrue(result.success)
        self.assertTrue(result.pdf_created)
        self.assertEqual(result.return_code, 0)
        
        # Test compilation with warnings (return code 1 but PDF created)
        os.remove(pdf_path)  # Remove PDF first
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="LaTeX Warning: Some warning message",
            stderr=""
        )
        
        # Create PDF again to simulate successful compilation despite warnings
        with open(pdf_path, 'w') as f:
            f.write('fake pdf content')
        
        result = self.pdf_generator.compile_to_pdf(tex_path, self.temp_dir)
        
        self.assertTrue(result.success)  # Should succeed because PDF was created
        self.assertTrue(result.pdf_created)
        self.assertEqual(result.return_code, 1)
        
        # Test compilation failure (no PDF created)
        os.remove(pdf_path)  # Remove PDF
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="LaTeX Error: Something went wrong"
        )
        
        result = self.pdf_generator.compile_to_pdf(tex_path, self.temp_dir)
        
        self.assertFalse(result.success)  # Should fail because no PDF was created
        self.assertFalse(result.pdf_created)
        self.assertEqual(result.return_code, 1)
    
    @patch.object(PDFGenerator, 'check_latex_availability')
    def test_compile_to_pdf_error_scenarios(self, mock_check):
        """Test PDF compilation error scenarios."""
        mock_check.return_value = True
        
        # Test non-existent tex file
        with self.assertRaises(LaTeXError) as context:
            self.pdf_generator.compile_to_pdf('/nonexistent.tex', self.temp_dir)
        self.assertIn('LaTeX file not found', str(context.exception))
        
        # Test LaTeX not available
        mock_check.return_value = False
        tex_path = os.path.join(self.temp_dir, 'test.tex')
        with open(tex_path, 'w') as f:
            f.write('test')
        
        with self.assertRaises(LaTeXError) as context:
            self.pdf_generator.compile_to_pdf(tex_path, self.temp_dir)
        self.assertIn('pdflatex is not available', str(context.exception))
    
    def test_clean_temp_files_comprehensive(self):
        """Test comprehensive temporary file cleanup."""
        base_path = os.path.join(self.temp_dir, 'test_document')
        
        # Create various temporary files
        temp_extensions = ['.aux', '.log', '.fls', '.fdb_latexmk', '.synctex.gz']
        created_files = []
        
        for ext in temp_extensions:
            file_path = base_path + ext
            with open(file_path, 'w') as f:
                f.write(f'temporary content for {ext}')
            created_files.append(file_path)
        
        # Also create some files that shouldn't be cleaned
        keep_files = [base_path + '.tex', base_path + '.pdf']
        for file_path in keep_files:
            with open(file_path, 'w') as f:
                f.write('important content')
        
        # Clean temporary files
        result = self.pdf_generator.clean_temp_files(base_path)
        
        # Verify temporary files were removed
        for file_path in created_files:
            self.assertFalse(os.path.exists(file_path))
        
        # Verify important files were kept
        for file_path in keep_files:
            self.assertTrue(os.path.exists(file_path))
        
        # Verify cleanup result
        self.assertEqual(result['total_cleaned'], len(temp_extensions))
        self.assertEqual(result['total_failed'], 0)
        self.assertEqual(len(result['cleaned_files']), len(temp_extensions))
    
    def test_clean_temp_files_custom_extensions(self):
        """Test cleanup with custom file extensions."""
        base_path = os.path.join(self.temp_dir, 'custom_test')
        custom_extensions = ['.custom1', '.custom2', '.temp']
        
        # Create custom temporary files
        for ext in custom_extensions:
            file_path = base_path + ext
            with open(file_path, 'w') as f:
                f.write('custom temp content')
        
        # Clean with custom extensions
        result = self.pdf_generator.clean_temp_files(base_path, custom_extensions)
        
        # Verify all custom files were cleaned
        for ext in custom_extensions:
            self.assertFalse(os.path.exists(base_path + ext))
        
        self.assertEqual(result['total_cleaned'], len(custom_extensions))
    
    def test_clean_temp_files_permission_handling(self):
        """Test cleanup with permission errors."""
        base_path = os.path.join(self.temp_dir, 'permission_test')
        
        # Create a file and make it read-only
        readonly_file = base_path + '.aux'
        with open(readonly_file, 'w') as f:
            f.write('readonly content')
        
        # Make file read-only (this might not work on all systems)
        try:
            os.chmod(readonly_file, 0o444)
            
            result = self.pdf_generator.clean_temp_files(base_path)
            
            # Should report permission error
            self.assertGreater(result['total_failed'], 0)
            
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(readonly_file, 0o666)
            except:
                pass
    
    def test_ensure_directory_structure_comprehensive(self):
        """Test comprehensive directory structure validation."""
        # Test creating new directory
        new_dir = os.path.join(self.temp_dir, 'new', 'nested', 'directory')
        result = self.pdf_generator.ensure_directory_structure(new_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
        
        # Test validating existing directory
        result = self.pdf_generator.ensure_directory_structure(new_dir)
        self.assertTrue(result)
        
        # Test error when path is a file
        file_path = os.path.join(self.temp_dir, 'not_a_directory.txt')
        with open(file_path, 'w') as f:
            f.write('test')
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.ensure_directory_structure(file_path)
        self.assertIn('not a directory', str(context.exception))
    
    def test_copy_template_resources_comprehensive(self):
        """Test comprehensive template resource copying."""
        # Create template directory with resources
        template_dir = os.path.join(self.temp_dir, 'templates')
        os.makedirs(template_dir)
        
        # Create resource files
        resources = ['logo.png', 'firma.png']
        for resource in resources:
            resource_path = os.path.join(template_dir, resource)
            with open(resource_path, 'wb') as f:
                f.write(b'fake image content')
        
        template_path = os.path.join(template_dir, 'template.tex')
        with open(template_path, 'w') as f:
            f.write('template content')
        
        # Create output directory
        output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(output_dir)
        
        # Copy resources
        result = self.pdf_generator._copy_template_resources(template_path, output_dir)
        
        # Verify resources were copied
        for resource in resources:
            output_path = os.path.join(output_dir, resource)
            self.assertTrue(os.path.exists(output_path))
            
            # Also check subdirectory structure
            subdir_path = os.path.join(output_dir, '05_Templates_y_Recursos', resource)
            self.assertTrue(os.path.exists(subdir_path))
        
        # Verify result
        self.assertEqual(result['total_copied'], len(resources))
        self.assertEqual(result['total_failed'], 0)
        self.assertEqual(result['total_missing'], 0)
    
    def test_copy_template_resources_missing_files(self):
        """Test resource copying with missing files."""
        # Create template directory without resource files
        template_dir = os.path.join(self.temp_dir, 'templates')
        os.makedirs(template_dir)
        
        template_path = os.path.join(template_dir, 'template.tex')
        with open(template_path, 'w') as f:
            f.write('template content')
        
        output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(output_dir)
        
        # Copy resources (should handle missing files gracefully)
        result = self.pdf_generator._copy_template_resources(template_path, output_dir)
        
        # Verify missing files are reported
        self.assertEqual(result['total_copied'], 0)
        self.assertEqual(result['total_missing'], 2)  # logo.png and firma.png
        self.assertIn('logo.png', result['missing_files'])
        self.assertIn('firma.png', result['missing_files'])


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)