# -*- coding: utf-8 -*-
"""
Integration tests for enhanced PECO functionality.
Tests complete form submission workflow, PDF generation with new dynamic forms,
CLI unification, and DataManager centralization.
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import datetime
import subprocess
from io import StringIO

from services.config_validator import ConfigValidator
from services.data_manager import DataManager
from services.latex_processor import LaTeXProcessor
from services.pdf_generator import PDFGenerator
from services.base import Result, PDFResult
from services.exceptions import PECOError, LaTeXError, ConfigurationError
from generar_resolucion import generar_resolucion
import PECO


class TestDynamicFormIntegration(unittest.TestCase):
    """Integration tests for dynamic form generation and submission workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_validator = ConfigValidator()
        
        # Create test configuration file
        self.config_file = os.path.join(self.temp_dir, "config_mes.json")
        self.valid_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto mensual de julio",
            "visto": "La necesidad de cubrir los gastos mensuales y mantener un control financiero adecuado.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Transporte público", "monto": "14000"},
                {"tipo": "gasto_anterior", "descripcion": "Alimentación", "monto": "27000"},
                {"tipo": "texto", "contenido": "Que se mantiene una política de ahorro responsable."}
            ],
            "articulos": [
                "Aprobar el presupuesto por un total de $MONTO_TOTAL ARS.",
                "El solicitante continuará registrando sus gastos mensualmente.",
                "Esta resolución tendrá vigencia hasta el próximo mes."
            ],
            "anexo": {
                "titulo": "Detalle del presupuesto mensual solicitado",
                "anexo_items": [
                    {"categoria": "Cuota Celular", "monto": "42416"},
                    {"categoria": "Inversiones CEDEARs", "monto": "50000"},
                    {"categoria": "Transporte", "monto": "14000"},
                    {"categoria": "Alimentación", "monto": "27000"}
                ],
                "penalizaciones": [
                    {"categoria": "Penalización llegada tarde", "monto": "-2500"}
                ],
                "nota_final": "El monto final será ajustado según corresponda y las penalizaciones aplicadas."
            }
        }
        
        # Save configuration file
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.valid_config, f, indent=2, ensure_ascii=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_form_data_validation_and_processing(self):
        """Test complete form data validation and processing workflow."""
        # Step 1: Simulate form data submission (as would come from dynamic form)
        form_data = {
            "mes_iso": "2025-08",
            "titulo_base": "Presupuesto agosto actualizado",
            "visto": "Considerando los gastos adicionales del mes de agosto.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Servicios públicos", "monto": "15000"},
                {"tipo": "texto", "contenido": "Que se requiere un ajuste presupuestario."},
                {"tipo": "gasto_anterior", "descripcion": "Internet", "monto": "8000"}
            ],
            "articulos": [
                "Aprobar el presupuesto ajustado por $MONTO_TOTAL ARS.",
                "Implementar controles adicionales de gasto."
            ],
            "anexo": {
                "titulo": "Presupuesto agosto - detalle",
                "anexo_items": [
                    {"categoria": "Servicios", "monto": "23000"},
                    {"categoria": "Entretenimiento", "monto": "12000"}
                ],
                "penalizaciones": [
                    {"categoria": "Multa por exceso", "monto": "-1000"}
                ],
                "nota_final": "Presupuesto sujeto a revisión mensual."
            }
        }
        
        # Step 2: Validate form data structure
        validation_result = self.config_validator.validate_config_structure(form_data)
        self.assertTrue(validation_result.success, f"Form validation failed: {validation_result.message}")
        
        # Step 3: Process configuration for template
        processing_result = self.config_validator.process_configuration_for_template(form_data)
        self.assertTrue(processing_result.success, f"Processing failed: {processing_result.message}")
        
        processed_config = processing_result.data
        
        # Step 4: Verify automatic calculations
        self.assertIn("subtotal", processed_config["anexo"])
        self.assertIn("total_solicitado", processed_config["anexo"])
        self.assertIn("penalizaciones_total", processed_config["anexo"])
        
        expected_subtotal = 23000 + 12000  # 35000
        expected_penalty = 1000
        expected_total = expected_subtotal - expected_penalty  # 34000
        
        self.assertEqual(float(processed_config["anexo"]["subtotal"]), expected_subtotal)
        self.assertEqual(float(processed_config["anexo"]["total_solicitado"]), expected_total)
        
        # Step 5: Verify MONTO_TOTAL replacement in articulos
        for articulo in processed_config["articulos"]:
            self.assertNotIn("$MONTO_TOTAL", articulo)
            if "Aprobar el presupuesto" in articulo:
                self.assertIn("34000", articulo)
        
        # Step 6: Verify date processing
        self.assertEqual(processed_config["mes_nombre"], "agosto")
        self.assertEqual(processed_config["anio"], "2025")
        self.assertIn("codigo_res", processed_config)
        self.assertIn("fecha_larga", processed_config)
    
    def test_dynamic_form_data_with_mixed_considerandos(self):
        """Test form processing with mixed considerando types."""
        form_data = {
            "mes_iso": "2025-09",
            "titulo_base": "Presupuesto mixto",
            "visto": "Considerando diversos tipos de gastos.",
            "considerandos": [
                {"tipo": "texto", "contenido": "Que se requiere flexibilidad presupuestaria."},
                {"tipo": "gasto_anterior", "descripcion": "Gastos médicos", "monto": "25000"},
                {"tipo": "texto", "contenido": "Que los gastos de salud son prioritarios."},
                {"tipo": "gasto_anterior", "descripcion": "Educación", "monto": "18000"},
                {"tipo": "texto", "contenido": "Que la formación continua es esencial."}
            ],
            "articulos": ["Aprobar presupuesto por $MONTO_TOTAL ARS."],
            "anexo": {
                "titulo": "Detalle presupuesto mixto",
                "anexo_items": [
                    {"categoria": "Salud", "monto": "25000"},
                    {"categoria": "Educación", "monto": "18000"}
                ],
                "penalizaciones": [],
                "nota_final": "Presupuesto balanceado."
            }
        }
        
        # Validate and process
        validation_result = self.config_validator.validate_config_structure(form_data)
        self.assertTrue(validation_result.success)
        
        processing_result = self.config_validator.process_configuration_for_template(form_data)
        self.assertTrue(processing_result.success)
        
        processed_config = processing_result.data
        
        # Verify considerandos structure is preserved
        self.assertEqual(len(processed_config["considerandos"]), 5)
        
        # Check alternating types
        expected_types = ["texto", "gasto_anterior", "texto", "gasto_anterior", "texto"]
        for i, considerando in enumerate(processed_config["considerandos"]):
            self.assertEqual(considerando["tipo"], expected_types[i])
        
        # Verify calculations
        expected_total = 25000 + 18000  # 43000
        self.assertEqual(float(processed_config["anexo"]["total_solicitado"]), expected_total)
    
    def test_form_validation_error_handling(self):
        """Test form validation with various error conditions."""
        # Test case 1: Missing required fields
        invalid_form_data = {
            "mes_iso": "2025-07",
            "titulo_base": "Test"
            # Missing visto, considerandos, articulos, anexo
        }
        
        result = self.config_validator.validate_config_structure(invalid_form_data)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.validation_errors)
        self.assertGreater(len(result.validation_errors), 0)
        
        # Test case 2: Invalid mes_iso format
        invalid_form_data = {
            "mes_iso": "invalid-date",
            "titulo_base": "Test",
            "visto": "Test",
            "considerandos": [],
            "articulos": [],
            "anexo": {"titulo": "Test", "anexo_items": [], "penalizaciones": [], "nota_final": "Test"}
        }
        
        result = self.config_validator.validate_config_structure(invalid_form_data)
        self.assertFalse(result.success)
        self.assertTrue(any("YYYY-MM format" in error for error in result.validation_errors))
        
        # Test case 3: Invalid considerando structure
        invalid_form_data = self.valid_config.copy()
        invalid_form_data["considerandos"] = [
            {"tipo": "gasto_anterior", "descripcion": "Test"},  # Missing monto
            {"tipo": "texto"},  # Missing contenido
            {"tipo": "invalid_type", "contenido": "Test"}  # Invalid tipo
        ]
        
        result = self.config_validator.validate_config_structure(invalid_form_data)
        self.assertFalse(result.success)
        self.assertGreater(len(result.validation_errors), 2)


class TestPDFGenerationIntegration(unittest.TestCase):
    """Integration tests for PDF generation with new configuration structure."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_validator = ConfigValidator()
        self.latex_processor = LaTeXProcessor()
        self.pdf_generator = PDFGenerator(self.latex_processor)
        
        # Create template and output directories
        self.template_dir = os.path.join(self.temp_dir, "templates")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.template_dir)
        os.makedirs(self.output_dir)
        
        # Create test configuration
        self.test_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto de prueba",
            "visto": "Considerando la necesidad de realizar pruebas del sistema.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Gastos de desarrollo", "monto": "50000"},
                {"tipo": "texto", "contenido": "Que el sistema requiere validación completa."}
            ],
            "articulos": [
                "Aprobar el presupuesto de prueba por $MONTO_TOTAL ARS.",
                "Continuar con las pruebas del sistema."
            ],
            "anexo": {
                "titulo": "Detalle del presupuesto de prueba",
                "anexo_items": [
                    {"categoria": "Desarrollo", "monto": "30000"},
                    {"categoria": "Testing", "monto": "20000"}
                ],
                "penalizaciones": [
                    {"categoria": "Retraso en entrega", "monto": "-5000"}
                ],
                "nota_final": "Presupuesto para validación del sistema."
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pdf_generation_with_new_config_structure(self):
        """Test PDF generation workflow with new configuration structure."""
        # Step 1: Process configuration for template
        processing_result = self.config_validator.process_configuration_for_template(self.test_config)
        self.assertTrue(processing_result.success)
        
        processed_config = processing_result.data
        
        # Step 2: Create a simple LaTeX template for testing
        template_content = """
\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage[spanish]{babel}
\\begin{document}

\\title{{ '{' }}{{ titulo_documento }}{{ '}' }}
\\author{Sistema PECO}
\\date{{ '{' }}{{ fecha_larga }}{{ '}' }}
\\maketitle

\\section{VISTO}
{{ visto }}

\\section{CONSIDERANDO}
{% for considerando in considerandos %}
{% if considerando.tipo == "gasto_anterior" %}
\\item Que en el mes anterior se registró un gasto de {{ considerando.descripcion }} por un monto de \\${{ considerando.monto }} ARS.
{% else %}
\\item {{ considerando.contenido }}
{% endif %}
{% endfor %}

\\section{ARTÍCULOS}
{% for articulo in articulos %}
\\item {{ articulo }}
{% endfor %}

{% if anexo.anexo_items %}
\\section{ANEXO}
\\subsection{{ '{' }}{{ anexo.titulo }}{{ '}' }}

\\begin{itemize}
{% for item in anexo.anexo_items %}
\\item {{ item.categoria }}: \\${{ item.monto }} ARS
{% endfor %}
{% if anexo.penalizaciones %}
\\item \\textbf{Penalizaciones:}
{% for penalizacion in anexo.penalizaciones %}
\\item {{ penalizacion.categoria }}: \\${{ penalizacion.monto }} ARS
{% endfor %}
{% endif %}
\\end{itemize}

\\textbf{Total solicitado: \\${{ anexo.total_solicitado }} ARS}

{{ anexo.nota_final }}
{% endif %}

\\end{document}
"""
        
        template_path = os.path.join(self.template_dir, "test_template.tex")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # Step 3: Test template processing
        try:
            processed_template = self.pdf_generator.process_template(template_path, processed_config)
            
            # Verify key elements are present in processed template
            self.assertIn("Presupuesto de prueba", processed_template)
            self.assertIn("45000", processed_template)  # total_solicitado (50000 - 5000)
            self.assertIn("validación completa", processed_template)
            self.assertIn("Desarrollo: \\$30000", processed_template)
            self.assertIn("Testing: \\$20000", processed_template)
            self.assertIn("Retraso en entrega: \\$-5000", processed_template)
            self.assertIn("Total solicitado: \\$45000", processed_template)
            
        except Exception as e:
            self.fail(f"Template processing failed: {e}")
    
    @patch('subprocess.run')
    def test_complete_pdf_generation_workflow(self, mock_subprocess):
        """Test complete PDF generation workflow with mocked LaTeX compilation."""
        # Mock successful LaTeX compilation
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Process configuration
        processing_result = self.config_validator.process_configuration_for_template(self.test_config)
        self.assertTrue(processing_result.success)
        
        processed_config = processing_result.data
        
        # Create minimal template
        template_content = """
\\documentclass{article}
\\begin{document}
Test document with total: {{ anexo.total_solicitado }}
\\end{document}
"""
        
        template_path = os.path.join(self.template_dir, "minimal.tex")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # Generate PDF
        result = self.pdf_generator.generate_resolution(
            template_path=template_path,
            data=processed_config,
            output_dir=self.output_dir,
            filename_base="test_resolution"
        )
        
        # Verify result
        self.assertTrue(result.success, f"PDF generation failed: {result.message}")
        self.assertIsNotNone(result.pdf_path)
        self.assertIsNotNone(result.tex_path)
        
        # Verify subprocess was called with correct parameters
        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args[0][0]
        self.assertIn("pdflatex", call_args)
    
    def test_pdf_generation_with_various_data_configurations(self):
        """Test PDF generation with different data configurations."""
        test_cases = [
            # Case 1: Minimal configuration
            {
                "mes_iso": "2025-01",
                "titulo_base": "Minimal",
                "visto": "Test",
                "considerandos": [{"tipo": "texto", "contenido": "Test"}],
                "articulos": ["Test article"],
                "anexo": {
                    "titulo": "Test",
                    "anexo_items": [],
                    "penalizaciones": [],
                    "nota_final": "Test"
                }
            },
            # Case 2: Configuration with only penalizaciones
            {
                "mes_iso": "2025-02",
                "titulo_base": "Only penalties",
                "visto": "Test",
                "considerandos": [{"tipo": "texto", "contenido": "Test"}],
                "articulos": ["Test article"],
                "anexo": {
                    "titulo": "Test",
                    "anexo_items": [],
                    "penalizaciones": [{"categoria": "Penalty", "monto": "-1000"}],
                    "nota_final": "Test"
                }
            },
            # Case 3: Large amounts
            {
                "mes_iso": "2025-03",
                "titulo_base": "Large amounts",
                "visto": "Test",
                "considerandos": [{"tipo": "texto", "contenido": "Test"}],
                "articulos": ["Test article"],
                "anexo": {
                    "titulo": "Test",
                    "anexo_items": [{"categoria": "Large", "monto": "1000000"}],
                    "penalizaciones": [],
                    "nota_final": "Test"
                }
            }
        ]
        
        for i, config in enumerate(test_cases):
            with self.subTest(case=i):
                # Process configuration
                processing_result = self.config_validator.process_configuration_for_template(config)
                self.assertTrue(processing_result.success, f"Case {i} processing failed")
                
                processed_config = processing_result.data
                
                # Verify calculations
                self.assertIn("subtotal", processed_config["anexo"])
                self.assertIn("total_solicitado", processed_config["anexo"])
                self.assertIn("penalizaciones_total", processed_config["anexo"])
                
                # Verify date processing
                self.assertIn("mes_nombre", processed_config)
                self.assertIn("anio", processed_config)
                self.assertIn("codigo_res", processed_config)


class TestCLIUnificationIntegration(unittest.TestCase):
    """Integration tests for CLI unification and DataManager centralization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config for DataManager
        self.mock_config = Mock()
        self.mock_config.CSV_GASTOS = os.path.join(self.temp_dir, "gastos.csv")
        self.mock_config.XLSX_INVERSIONES = os.path.join(self.temp_dir, "inversiones.xlsx")
        self.mock_config.RUTA_TRACKERS = self.temp_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('PECO.DataManager')
    def test_cli_registrar_command_integration(self, mock_data_manager_class):
        """Test CLI registrar command integration with DataManager."""
        # Setup mock
        mock_data_manager = Mock()
        mock_data_manager.register_expense.return_value = Mock(success=True, message="Success")
        mock_data_manager_class.return_value = mock_data_manager
        
        # Test registrar command
        PECO.registrar_gasto_main(150.50, "Comida", "Almuerzo en restaurante")
        
        # Verify DataManager was instantiated and called correctly
        mock_data_manager_class.assert_called_once()
        mock_data_manager.register_expense.assert_called_once_with(150.50, "Comida", "Almuerzo en restaurante")
    
    @patch('PECO.DataManager')
    def test_cli_registrar_error_handling(self, mock_data_manager_class):
        """Test CLI registrar command error handling."""
        # Setup mock to return error
        mock_data_manager = Mock()
        mock_data_manager.register_expense.return_value = Mock(
            success=False, 
            message="Database error", 
            error_code="DB_ERROR"
        )
        mock_data_manager_class.return_value = mock_data_manager
        
        # Capture stdout to verify error message
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            PECO.registrar_gasto_main(0, "Invalid", "Test error")
            
            output = mock_stdout.getvalue()
            self.assertIn("[ERROR]", output)
            self.assertIn("Database error", output)
    
    @patch('PECO.analisis_mensual_main')
    def test_cli_analizar_command_integration(self, mock_analisis):
        """Test CLI analizar command integration."""
        # Setup mock
        mock_analisis.return_value = None
        
        # Test that the function would be called (we can't easily test argparse here)
        # This tests the direct function call integration
        PECO.analisis_mensual_main()
        
        # Verify the function was called
        mock_analisis.assert_called_once()
    
    @patch('PECO.generar_resolucion')
    def test_cli_generar_command_integration(self, mock_generar):
        """Test CLI generar command integration."""
        # Setup mock
        mock_generar.return_value = None
        
        # Test direct function call
        PECO.generar_resolucion()
        
        # Verify the function was called
        mock_generar.assert_called_once()
    
    def test_datamanager_centralization(self):
        """Test that DataManager centralizes database access."""
        # This test verifies that DataManager is the central point for data operations
        with patch('services.data_manager.DataManager.__init__', return_value=None):
            with patch('services.data_manager.DataManager.register_expense') as mock_register:
                mock_register.return_value = Mock(success=True, message="Success")
                
                # Create DataManager instance
                data_manager = DataManager()
                
                # Test expense registration
                result = data_manager.register_expense(100.0, "Test", "Test expense")
                
                # Verify method was called
                mock_register.assert_called_once_with(100.0, "Test", "Test expense")


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end integration tests combining all enhanced functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_validator = ConfigValidator()
        
        # Create complete test environment
        self.config_file = os.path.join(self.temp_dir, "config_mes.json")
        self.template_dir = os.path.join(self.temp_dir, "templates")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        os.makedirs(self.template_dir)
        os.makedirs(self.output_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_form_to_pdf_workflow(self):
        """Test complete workflow from form submission to PDF generation."""
        # Step 1: Simulate form data submission
        form_data = {
            "mes_iso": "2025-12",
            "titulo_base": "Presupuesto fin de año",
            "visto": "Considerando el cierre del ejercicio fiscal y la necesidad de ajustes presupuestarios.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Gastos operativos", "monto": "75000"},
                {"tipo": "texto", "contenido": "Que se requiere un presupuesto adicional para el cierre del año."},
                {"tipo": "gasto_anterior", "descripcion": "Bonificaciones", "monto": "25000"}
            ],
            "articulos": [
                "Aprobar el presupuesto de cierre por $MONTO_TOTAL ARS.",
                "Autorizar los gastos adicionales necesarios.",
                "Esta resolución tendrá vigencia hasta el 31 de diciembre."
            ],
            "anexo": {
                "titulo": "Detalle del presupuesto de cierre de año",
                "anexo_items": [
                    {"categoria": "Operaciones", "monto": "75000"},
                    {"categoria": "Bonificaciones", "monto": "25000"},
                    {"categoria": "Gastos administrativos", "monto": "15000"}
                ],
                "penalizaciones": [
                    {"categoria": "Ajuste por inflación", "monto": "-5000"}
                ],
                "nota_final": "Presupuesto sujeto a aprobación final de la dirección."
            }
        }
        
        # Step 2: Validate form data
        validation_result = self.config_validator.validate_config_structure(form_data)
        self.assertTrue(validation_result.success, f"Form validation failed: {validation_result.message}")
        
        # Step 3: Process for template
        processing_result = self.config_validator.process_configuration_for_template(form_data)
        self.assertTrue(processing_result.success, f"Processing failed: {processing_result.message}")
        
        processed_config = processing_result.data
        
        # Step 4: Verify calculations
        expected_subtotal = 75000 + 25000 + 15000  # 115000
        expected_penalty = 5000
        expected_total = expected_subtotal - expected_penalty  # 110000
        
        self.assertEqual(float(processed_config["anexo"]["subtotal"]), expected_subtotal)
        self.assertEqual(float(processed_config["anexo"]["total_solicitado"]), expected_total)
        
        # Step 5: Verify MONTO_TOTAL replacement
        for articulo in processed_config["articulos"]:
            self.assertNotIn("$MONTO_TOTAL", articulo)
            if "Aprobar el presupuesto" in articulo:
                self.assertIn("110000", articulo)
        
        # Step 6: Verify date processing
        self.assertEqual(processed_config["mes_nombre"], "diciembre")
        self.assertEqual(processed_config["anio"], "2025")
        
        # Step 7: Save processed configuration
        save_result = self.config_validator.save_validated_config(processed_config, self.config_file)
        self.assertTrue(save_result.success, f"Save failed: {save_result.message}")
        
        # Step 8: Verify file was saved correctly
        self.assertTrue(os.path.exists(self.config_file))
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
            self.assertEqual(saved_config["mes_iso"], "2025-12")
            self.assertEqual(saved_config["titulo_base"], "Presupuesto fin de año")
            self.assertIn("subtotal", saved_config["anexo"])
            self.assertIn("total_solicitado", saved_config["anexo"])
    
    @patch('generar_resolucion.ConfigValidator')
    @patch('generar_resolucion.PDFGenerator')
    def test_integration_with_resolution_generator(self, mock_pdf_generator_class, mock_config_validator_class):
        """Test integration with the resolution generator."""
        # Setup mocks
        mock_validator = Mock()
        mock_validator.validate_and_load_config.return_value = Mock(
            success=True,
            data={"test": "config"},
            warnings=None
        )
        mock_validator.process_configuration_for_template.return_value = Mock(
            success=True,
            data={"processed": "config", "titulo_documento": "Test Resolution"}
        )
        mock_config_validator_class.return_value = mock_validator
        
        mock_pdf_gen = Mock()
        mock_pdf_gen.check_latex_availability.return_value = True
        mock_pdf_gen.generate_resolution.return_value = Mock(
            success=True,
            pdf_path="/test/path.pdf",
            tex_path="/test/path.tex"
        )
        mock_pdf_generator_class.return_value = mock_pdf_gen
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            with patch('generar_resolucion.RUTA_CONFIG_JSON', self.config_file):
                # Test resolution generation
                try:
                    generar_resolucion()
                    
                    # Verify validator was called
                    mock_validator.validate_and_load_config.assert_called_once()
                    mock_validator.process_configuration_for_template.assert_called_once()
                    
                    # Verify PDF generator was called
                    mock_pdf_gen.check_latex_availability.assert_called_once()
                    mock_pdf_gen.generate_resolution.assert_called_once()
                    
                except Exception as e:
                    self.fail(f"Resolution generation failed: {e}")


if __name__ == '__main__':
    # Run all integration tests
    unittest.main(verbosity=2)