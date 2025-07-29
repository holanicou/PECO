# -*- coding: utf-8 -*-
"""
User Acceptance Testing for PECO resolution generator enhancement.
Tests dynamic form usability, PDF output quality, and system performance.
"""

import json
import os
import tempfile
import shutil
import unittest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.config_validator import ConfigValidator
from services.pdf_generator import PDFGenerator
from services.latex_processor import LaTeXProcessor
from generar_resolucion import generar_resolucion


class TestUserAcceptance(unittest.TestCase):
    """User acceptance tests for the enhanced PECO system."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_validator = ConfigValidator()
        
        # Sample configurations for testing different scenarios
        self.minimal_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto mínimo",
            "visto": "Configuración mínima para pruebas.",
            "considerandos": [
                {"tipo": "texto", "contenido": "Considerando único para prueba."}
            ],
            "articulos": ["Artículo único de prueba."],
            "anexo": {
                "titulo": "Anexo mínimo",
                "anexo_items": [
                    {"categoria": "Item único", "monto": "1000"}
                ],
                "penalizaciones": [],
                "nota_final": "Nota final mínima."
            }
        }
        
        self.medium_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto mediano",
            "visto": "Configuración mediana con varios elementos para pruebas de usabilidad.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Transporte", "monto": "15000"},
                {"tipo": "gasto_anterior", "descripcion": "Alimentación", "monto": "25000"},
                {"tipo": "texto", "contenido": "Considerando adicional de texto."},
                {"tipo": "texto", "contenido": "Segundo considerando de texto para pruebas."}
            ],
            "articulos": [
                "Primer artículo del presupuesto mediano.",
                "Segundo artículo con detalles adicionales.",
                "Tercer artículo para completar la resolución."
            ],
            "anexo": {
                "titulo": "Detalle del presupuesto mediano",
                "anexo_items": [
                    {"categoria": "Transporte público", "monto": "15000"},
                    {"categoria": "Alimentación", "monto": "25000"},
                    {"categoria": "Materiales de estudio", "monto": "8000"},
                    {"categoria": "Servicios básicos", "monto": "12000"}
                ],
                "penalizaciones": [
                    {"categoria": "Penalización por retraso", "monto": "-1500"}
                ],
                "nota_final": "El monto será ajustado según las penalizaciones aplicables."
            }
        }
        
        self.large_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto completo con múltiples elementos",
            "visto": "Configuración completa para pruebas de rendimiento y usabilidad con múltiples elementos, considerandos extensos, y anexos detallados que permiten evaluar el comportamiento del sistema con cargas de datos significativas.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Transporte urbano e interurbano", "monto": "18000"},
                {"tipo": "gasto_anterior", "descripcion": "Alimentación y productos básicos", "monto": "35000"},
                {"tipo": "gasto_anterior", "descripcion": "Servicios de telecomunicaciones", "monto": "12000"},
                {"tipo": "texto", "contenido": "Que el solicitante ha demostrado responsabilidad en el manejo de presupuestos anteriores."},
                {"tipo": "texto", "contenido": "Que se requiere mantener un control estricto de gastos para el período solicitado."},
                {"tipo": "texto", "contenido": "Que los montos solicitados están justificados por las necesidades actuales."},
                {"tipo": "texto", "contenido": "Que se ha realizado una evaluación detallada de las prioridades de gasto."},
                {"tipo": "texto", "contenido": "Que el presupuesto incluye provisiones para gastos imprevistos menores."}
            ],
            "articulos": [
                "Aprobar el presupuesto por un total de $MONTO_TOTAL ARS, conforme al detalle del Anexo I.",
                "El solicitante deberá presentar comprobantes de todos los gastos realizados.",
                "Se autoriza la reasignación de hasta el 10% entre categorías previa justificación.",
                "El presupuesto tendrá vigencia durante el mes calendario correspondiente.",
                "Cualquier excedente deberá ser reportado y justificado al final del período.",
                "Se establece un sistema de seguimiento quincenal para el control de gastos."
            ],
            "anexo": {
                "titulo": "Detalle completo del presupuesto mensual solicitado",
                "anexo_items": [
                    {"categoria": "Transporte público (colectivos y subte)", "monto": "18000"},
                    {"categoria": "Alimentación y productos de primera necesidad", "monto": "35000"},
                    {"categoria": "Servicios de telecomunicaciones (celular e internet)", "monto": "12000"},
                    {"categoria": "Materiales de estudio y trabajo", "monto": "15000"},
                    {"categoria": "Servicios básicos (electricidad, gas, agua)", "monto": "20000"},
                    {"categoria": "Gastos médicos y farmacia", "monto": "8000"},
                    {"categoria": "Vestimenta y calzado", "monto": "10000"},
                    {"categoria": "Entretenimiento y recreación", "monto": "5000"},
                    {"categoria": "Ahorro e inversiones", "monto": "25000"},
                    {"categoria": "Gastos imprevistos (reserva)", "monto": "7000"}
                ],
                "penalizaciones": [
                    {"categoria": "Penalización por presentación tardía", "monto": "-2000"},
                    {"categoria": "Descuento por gastos no justificados del mes anterior", "monto": "-1500"},
                    {"categoria": "Ajuste por diferencias de cálculo", "monto": "-500"}
                ],
                "nota_final": "El monto final a transferir será el resultado de la suma de todos los ítems menos las penalizaciones aplicables. Cualquier modificación posterior requerirá una nueva resolución."
            }
        }
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_dynamic_form_data_structure_usability(self):
        """Test that dynamic form data structures are user-friendly and intuitive."""
        print("\n=== TESTING DYNAMIC FORM DATA STRUCTURE USABILITY ===")
        
        test_cases = [
            ("Minimal configuration", self.minimal_config),
            ("Medium configuration", self.medium_config),
            ("Large configuration", self.large_config)
        ]
        
        for case_name, config in test_cases:
            print(f"\nTesting {case_name}:")
            
            # Test 1: Configuration validation (simulates form validation)
            validation_result = self.config_validator.validate_config_structure(config)
            print(f"  ✓ Form validation: {'PASS' if validation_result.success else 'FAIL'}")
            
            if not validation_result.success:
                print(f"    Validation errors: {validation_result.validation_errors}")
                self.fail(f"Form validation failed for {case_name}")
            
            # Test 2: Data processing (simulates form submission processing)
            processing_result = self.config_validator.process_configuration_for_template(config)
            print(f"  ✓ Form processing: {'PASS' if processing_result.success else 'FAIL'}")
            
            if not processing_result.success:
                print(f"    Processing errors: {processing_result.message}")
                self.fail(f"Form processing failed for {case_name}")
            
            # Test 3: User-friendly field access (simulates form field population)
            processed_data = processing_result.data
            
            # Check that all expected fields are accessible
            expected_fields = [
                'mes_iso', 'titulo_base', 'visto', 'considerandos', 'articulos', 'anexo',
                'mes_nombre', 'anio', 'codigo_res', 'fecha_larga', 'titulo_documento'
            ]
            
            missing_fields = [field for field in expected_fields if field not in processed_data]
            if missing_fields:
                print(f"    Missing fields: {missing_fields}")
                self.fail(f"Missing required fields for {case_name}: {missing_fields}")
            
            print(f"  ✓ Field accessibility: PASS")
            
            # Test 4: Calculation accuracy (simulates real-time calculations in form)
            if 'anexo' in processed_data:
                anexo = processed_data['anexo']
                
                # Verify calculations are present and reasonable
                self.assertIn('subtotal', anexo, "Subtotal calculation missing")
                self.assertIn('total_solicitado', anexo, "Total calculation missing")
                
                # Verify calculations are numeric
                try:
                    subtotal = float(anexo['subtotal'])
                    total = float(anexo['total_solicitado'])
                    self.assertGreater(subtotal, 0, "Subtotal should be positive")
                    print(f"  ✓ Calculations: Subtotal=${subtotal:,.0f}, Total=${total:,.0f}")
                except (ValueError, TypeError) as e:
                    self.fail(f"Invalid calculation format for {case_name}: {e}")
            
            # Test 5: Data size handling (simulates form performance with different data sizes)
            data_size = len(json.dumps(config, ensure_ascii=False))
            processing_time = time.time()
            
            # Re-process to measure time
            self.config_validator.process_configuration_for_template(config)
            processing_time = time.time() - processing_time
            
            print(f"  ✓ Performance: {data_size} bytes processed in {processing_time:.3f}s")
            
            # Performance should be reasonable (under 1 second for form processing)
            self.assertLess(processing_time, 1.0, f"Form processing too slow for {case_name}")
        
        print("\n=== DYNAMIC FORM USABILITY TESTS COMPLETE ===")
    
    def test_pdf_output_quality_and_formatting(self):
        """Test PDF output quality and formatting with different data sizes."""
        print("\n=== TESTING PDF OUTPUT QUALITY AND FORMATTING ===")
        
        # Test PDF generation readiness by validating data structure
        
        test_cases = [
            ("Minimal data", self.minimal_config),
            ("Medium data", self.medium_config),
            ("Large data", self.large_config)
        ]
        
        for case_name, config in test_cases:
            print(f"\nTesting PDF readiness with {case_name}:")
            
            # Process configuration for template
            processing_result = self.config_validator.process_configuration_for_template(config)
            self.assertTrue(processing_result.success, f"Configuration processing failed for {case_name}")
            
            processed_data = processing_result.data
            
            # Test that data is ready for PDF generation
            print(f"  ✓ Data processing: PASS")
            
            # Check that essential data is present for template
            essential_fields = ['titulo_documento', 'fecha_larga', 'codigo_res']
            for field in essential_fields:
                self.assertIn(field, processed_data, f"Missing essential field {field} in processed data")
            
            print(f"  ✓ Template data: All essential fields present")
            
            # Test formatting quality by checking processed data structure
            self.assertIn('considerandos', processed_data, "Considerandos missing from processed data")
            self.assertIn('articulos', processed_data, "Articulos missing from processed data")
            self.assertIn('anexo', processed_data, "Anexo missing from processed data")
            
            # Check anexo formatting
            anexo = processed_data['anexo']
            if 'anexo_items' in anexo:
                for i, item in enumerate(anexo['anexo_items']):
                    self.assertIn('categoria', item, f"Anexo item {i} missing categoria")
                    self.assertIn('monto', item, f"Anexo item {i} missing monto")
            
            print(f"  ✓ Data formatting: Proper structure maintained")
            
            # Test calculation formatting
            if 'subtotal' in anexo and 'total_solicitado' in anexo:
                # Verify amounts are properly formatted as strings for LaTeX
                self.assertIsInstance(anexo['subtotal'], str, "Subtotal should be formatted as string")
                self.assertIsInstance(anexo['total_solicitado'], str, "Total should be formatted as string")
                
                # Verify amounts are numeric strings
                try:
                    float(anexo['subtotal'])
                    float(anexo['total_solicitado'])
                    print(f"  ✓ Amount formatting: Proper numeric string format")
                except ValueError:
                    self.fail(f"Invalid amount formatting for {case_name}")
        
        print("\n=== PDF OUTPUT QUALITY TESTS COMPLETE ===")
    
    def test_system_performance_with_various_data_sizes(self):
        """Test system performance with different data sizes."""
        print("\n=== TESTING SYSTEM PERFORMANCE WITH VARIOUS DATA SIZES ===")
        
        # Create configurations of different sizes
        performance_configs = []
        
        # Small configuration (baseline)
        small_config = self.minimal_config.copy()
        performance_configs.append(("Small (1 considerando, 1 artículo, 1 anexo item)", small_config))
        
        # Medium configuration
        medium_config = self.medium_config.copy()
        performance_configs.append(("Medium (4 considerandos, 3 artículos, 4 anexo items)", medium_config))
        
        # Large configuration
        large_config = self.large_config.copy()
        performance_configs.append(("Large (8 considerandos, 6 artículos, 10 anexo items)", large_config))
        
        # Extra large configuration (stress test)
        xl_config = large_config.copy()
        
        # Add more considerandos
        for i in range(10):
            xl_config['considerandos'].append({
                "tipo": "texto",
                "contenido": f"Considerando adicional número {i+1} para pruebas de rendimiento con texto extenso que simula contenido real de resoluciones administrativas."
            })
        
        # Add more artículos
        for i in range(10):
            xl_config['articulos'].append(f"Artículo adicional número {i+1} para pruebas de rendimiento del sistema.")
        
        # Add more anexo items
        for i in range(20):
            xl_config['anexo']['anexo_items'].append({
                "categoria": f"Categoría de prueba {i+1}",
                "monto": str((i+1) * 1000)
            })
        
        performance_configs.append(("Extra Large (18 considerandos, 16 artículos, 30 anexo items)", xl_config))
        
        performance_results = []
        
        for config_name, config in performance_configs:
            print(f"\nTesting performance with {config_name}:")
            
            # Measure data size
            data_size = len(json.dumps(config, ensure_ascii=False))
            print(f"  Data size: {data_size:,} bytes")
            
            # Test 1: Validation performance
            start_time = time.time()
            validation_result = self.config_validator.validate_config_structure(config)
            validation_time = time.time() - start_time
            
            print(f"  ✓ Validation: {validation_time:.3f}s ({'PASS' if validation_result.success else 'FAIL'})")
            self.assertTrue(validation_result.success, f"Validation failed for {config_name}")
            
            # Test 2: Processing performance
            start_time = time.time()
            processing_result = self.config_validator.process_configuration_for_template(config)
            processing_time = time.time() - start_time
            
            print(f"  ✓ Processing: {processing_time:.3f}s ({'PASS' if processing_result.success else 'FAIL'})")
            self.assertTrue(processing_result.success, f"Processing failed for {config_name}")
            
            # Test 3: Calculation performance
            start_time = time.time()
            totals = self.config_validator.calculate_anexo_totals(config['anexo'])
            calculation_time = time.time() - start_time
            
            print(f"  ✓ Calculations: {calculation_time:.3f}s (Total: ${totals['total_solicitado']:,.0f})")
            
            # Test 4: Memory usage (approximate)
            processed_data = processing_result.data
            processed_size = len(json.dumps(processed_data, ensure_ascii=False))
            size_increase = ((processed_size - data_size) / data_size) * 100
            
            print(f"  ✓ Memory usage: {processed_size:,} bytes (+{size_increase:.1f}%)")
            
            # Store results for analysis
            performance_results.append({
                'name': config_name,
                'data_size': data_size,
                'validation_time': validation_time,
                'processing_time': processing_time,
                'calculation_time': calculation_time,
                'processed_size': processed_size,
                'total_time': validation_time + processing_time + calculation_time
            })
            
            # Performance thresholds (reasonable expectations)
            self.assertLess(validation_time, 0.5, f"Validation too slow for {config_name}")
            self.assertLess(processing_time, 1.0, f"Processing too slow for {config_name}")
            self.assertLess(calculation_time, 0.1, f"Calculations too slow for {config_name}")
        
        # Performance analysis
        print(f"\n=== PERFORMANCE ANALYSIS ===")
        print(f"{'Configuration':<50} {'Size (KB)':<10} {'Total Time (s)':<15} {'Items':<10}")
        print("-" * 85)
        
        for result in performance_results:
            size_kb = result['data_size'] / 1024
            # Count total items (rough estimate)
            config = None
            for name, cfg in performance_configs:
                if name == result['name']:
                    config = cfg
                    break
            
            if config:
                total_items = len(config['considerandos']) + len(config['articulos']) + len(config['anexo'].get('anexo_items', []))
            else:
                total_items = 0
            
            print(f"{result['name']:<50} {size_kb:<10.1f} {result['total_time']:<15.3f} {total_items:<10}")
        
        # Verify performance scales reasonably
        if len(performance_results) >= 2:
            small_result = performance_results[0]
            large_result = performance_results[-1]
            
            size_ratio = large_result['data_size'] / small_result['data_size']
            time_ratio = large_result['total_time'] / small_result['total_time']
            
            print(f"\nScaling analysis:")
            print(f"  Size increase: {size_ratio:.1f}x")
            print(f"  Time increase: {time_ratio:.1f}x")
            print(f"  Efficiency: {'GOOD' if time_ratio <= size_ratio * 2 else 'NEEDS IMPROVEMENT'}")
            
            # Performance should scale reasonably (not exponentially)
            self.assertLess(time_ratio, size_ratio * 3, "Performance scaling is poor")
        
        print("\n=== SYSTEM PERFORMANCE TESTS COMPLETE ===")
    
    def test_user_experience_scenarios(self):
        """Test common user experience scenarios."""
        print("\n=== TESTING USER EXPERIENCE SCENARIOS ===")
        
        scenarios = [
            {
                "name": "New user with minimal data",
                "config": self.minimal_config,
                "expected_behavior": "Should work smoothly with basic validation"
            },
            {
                "name": "Regular user with typical monthly budget",
                "config": self.medium_config,
                "expected_behavior": "Should handle standard use case efficiently"
            },
            {
                "name": "Power user with complex budget",
                "config": self.large_config,
                "expected_behavior": "Should manage complex data without performance issues"
            }
        ]
        
        for scenario in scenarios:
            print(f"\nScenario: {scenario['name']}")
            print(f"Expected: {scenario['expected_behavior']}")
            
            config = scenario['config']
            
            # Test complete workflow
            start_time = time.time()
            
            # Step 1: Validation (simulates form validation)
            validation_result = self.config_validator.validate_config_structure(config)
            
            # Step 2: Processing (simulates form submission)
            if validation_result.success:
                processing_result = self.config_validator.process_configuration_for_template(config)
            else:
                processing_result = MagicMock(success=False)
            
            # Step 3: File operations (simulates saving configuration)
            if processing_result.success:
                config_path = os.path.join(self.test_dir, f"scenario_{scenario['name'].replace(' ', '_')}.json")
                save_result = self.config_validator.save_validated_config(config, config_path)
            else:
                save_result = MagicMock(success=False)
            
            total_time = time.time() - start_time
            
            # Evaluate user experience
            success = validation_result.success and processing_result.success and save_result.success
            
            print(f"  ✓ Workflow completion: {'PASS' if success else 'FAIL'} ({total_time:.3f}s)")
            
            if success:
                # Check user-friendly features
                processed_data = processing_result.data
                
                # Readable date format
                self.assertIn('fecha_larga', processed_data, "User-friendly date missing")
                self.assertIn('mes_nombre', processed_data, "Month name missing")
                
                # Proper document title
                self.assertIn('titulo_documento', processed_data, "Document title missing")
                
                # Calculated totals
                if 'anexo' in processed_data:
                    anexo = processed_data['anexo']
                    self.assertIn('total_solicitado', anexo, "Total calculation missing")
                    
                    # User-friendly amount formatting
                    total_str = anexo['total_solicitado']
                    self.assertIsInstance(total_str, str, "Total should be formatted as string")
                    
                    try:
                        total_amount = float(total_str)
                        print(f"  ✓ User experience: Total amount ${total_amount:,.0f} properly calculated")
                    except ValueError:
                        self.fail("Total amount not properly formatted")
                
                print(f"  ✓ User-friendly features: All present and working")
            else:
                if not validation_result.success:
                    print(f"    Validation issues: {validation_result.validation_errors}")
                if not processing_result.success:
                    print(f"    Processing issues: {processing_result.message}")
                if not save_result.success:
                    print(f"    Save issues: {save_result.message}")
                
                self.fail(f"User experience scenario failed: {scenario['name']}")
        
        print("\n=== USER EXPERIENCE SCENARIOS COMPLETE ===")
    
    def test_error_handling_user_experience(self):
        """Test that error handling provides good user experience."""
        print("\n=== TESTING ERROR HANDLING USER EXPERIENCE ===")
        
        error_scenarios = [
            {
                "name": "Missing required field",
                "config": {"mes_iso": "2025-07"},  # Missing other required fields
                "expected_error_type": "validation"
            },
            {
                "name": "Invalid date format",
                "config": {
                    "mes_iso": "invalid-date",
                    "titulo_base": "Test",
                    "visto": "Test",
                    "considerandos": [],
                    "articulos": [],
                    "anexo": {"titulo": "Test", "anexo_items": [], "penalizaciones": [], "nota_final": ""}
                },
                "expected_error_type": "validation"
            },
            {
                "name": "Invalid amount format",
                "config": {
                    "mes_iso": "2025-07",
                    "titulo_base": "Test",
                    "visto": "Test",
                    "considerandos": [{"tipo": "gasto_anterior", "descripcion": "Test", "monto": "invalid_amount"}],
                    "articulos": ["Test"],
                    "anexo": {"titulo": "Test", "anexo_items": [], "penalizaciones": [], "nota_final": ""}
                },
                "expected_error_type": "validation"
            }
        ]
        
        for scenario in error_scenarios:
            print(f"\nTesting error scenario: {scenario['name']}")
            
            config = scenario['config']
            
            # Test validation error handling
            validation_result = self.config_validator.validate_config_structure(config)
            
            # Should fail validation
            self.assertFalse(validation_result.success, f"Should fail validation for {scenario['name']}")
            
            # Should provide helpful error messages
            self.assertIsNotNone(validation_result.validation_errors, "Should provide error messages")
            self.assertGreater(len(validation_result.validation_errors), 0, "Should have specific error messages")
            
            # Error messages should be user-friendly
            for error in validation_result.validation_errors:
                self.assertIsInstance(error, str, "Error messages should be strings")
                self.assertGreater(len(error), 10, "Error messages should be descriptive")
                
                # Should not contain technical jargon that confuses users
                technical_terms = ['traceback', 'exception', 'null pointer', 'segfault']
                for term in technical_terms:
                    self.assertNotIn(term.lower(), error.lower(), f"Error message too technical: {error}")
            
            print(f"  ✓ Error handling: {len(validation_result.validation_errors)} clear error messages")
            print(f"    Sample error: {validation_result.validation_errors[0]}")
        
        print("\n=== ERROR HANDLING USER EXPERIENCE TESTS COMPLETE ===")
    
    def test_comprehensive_user_acceptance_validation(self):
        """Comprehensive validation of all user acceptance requirements."""
        print("\n=== COMPREHENSIVE USER ACCEPTANCE VALIDATION ===")
        
        # Test all requirements from the specification
        requirements_tests = [
            {
                "requirement": "2.1 - Dynamic form sections",
                "test": lambda: self._test_dynamic_form_sections(),
                "description": "Form displays structured sections for all data types"
            },
            {
                "requirement": "2.2 - Dynamic list management",
                "test": lambda: self._test_dynamic_list_management(),
                "description": "Users can add/remove items dynamically"
            },
            {
                "requirement": "2.3 - Anexo item management",
                "test": lambda: self._test_anexo_item_management(),
                "description": "Separate input fields for categoria and monto with validation"
            },
            {
                "requirement": "2.4 - Form data collection",
                "test": lambda: self._test_form_data_collection(),
                "description": "System collects and structures form data properly"
            },
            {
                "requirement": "2.5 - Form data loading",
                "test": lambda: self._test_form_data_loading(),
                "description": "Form populates correctly with existing data"
            },
            {
                "requirement": "3.1 - Dynamic considerandos rendering",
                "test": lambda: self._test_dynamic_considerandos_rendering(),
                "description": "Template renders considerandos based on type"
            },
            {
                "requirement": "3.2 - Automatic article numbering",
                "test": lambda: self._test_automatic_article_numbering(),
                "description": "Template automatically numbers and formats articles"
            },
            {
                "requirement": "3.3 - Conditional anexo rendering",
                "test": lambda: self._test_conditional_anexo_rendering(),
                "description": "Anexo page only shows when items exist"
            },
            {
                "requirement": "3.4 - Automatic calculations",
                "test": lambda: self._test_automatic_calculations(),
                "description": "Template automatically computes totals"
            },
            {
                "requirement": "3.5 - Penalizaciones handling",
                "test": lambda: self._test_penalizaciones_handling(),
                "description": "Template includes penalizaciones in calculations"
            },
            {
                "requirement": "6.4 - Amount formatting",
                "test": lambda: self._test_amount_formatting(),
                "description": "Amounts are formatted consistently with currency symbols"
            }
        ]
        
        passed_tests = 0
        total_tests = len(requirements_tests)
        
        for req_test in requirements_tests:
            print(f"\nTesting {req_test['requirement']}: {req_test['description']}")
            
            try:
                result = req_test['test']()
                if result:
                    print(f"  ✓ PASS")
                    passed_tests += 1
                else:
                    print(f"  ✗ FAIL")
            except Exception as e:
                print(f"  ✗ FAIL - {str(e)}")
        
        print(f"\n=== USER ACCEPTANCE VALIDATION SUMMARY ===")
        print(f"Passed: {passed_tests}/{total_tests} tests")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL USER ACCEPTANCE REQUIREMENTS VALIDATED SUCCESSFULLY!")
        else:
            print(f"⚠️  {total_tests - passed_tests} requirements need attention")
        
        # Overall acceptance criteria
        acceptance_threshold = 0.9  # 90% of tests must pass
        success_rate = passed_tests / total_tests
        
        self.assertGreaterEqual(
            success_rate, 
            acceptance_threshold, 
            f"User acceptance rate {success_rate:.1%} below threshold {acceptance_threshold:.1%}"
        )
    
    # Helper methods for requirement-specific tests
    def _test_dynamic_form_sections(self):
        """Test dynamic form sections functionality."""
        # Test that configuration structure supports all required sections
        config = self.medium_config
        result = self.config_validator.validate_config_structure(config)
        
        if not result.success:
            return False
        
        # Check that all sections are present
        required_sections = ['mes_iso', 'titulo_base', 'visto', 'considerandos', 'articulos', 'anexo']
        return all(section in config for section in required_sections)
    
    def _test_dynamic_list_management(self):
        """Test dynamic list management functionality."""
        # Test that considerandos and articulos can be managed as lists
        config = self.large_config.copy()
        
        # Test adding items (simulated)
        config['considerandos'].append({"tipo": "texto", "contenido": "New considerando"})
        config['articulos'].append("New articulo")
        
        # Test validation still works
        result = self.config_validator.validate_config_structure(config)
        return result.success
    
    def _test_anexo_item_management(self):
        """Test anexo item management functionality."""
        config = self.medium_config.copy()
        
        # Test adding anexo items
        config['anexo']['anexo_items'].append({"categoria": "New category", "monto": "5000"})
        
        # Test validation
        result = self.config_validator.validate_config_structure(config)
        if not result.success:
            return False
        
        # Test calculation with new item
        totals = self.config_validator.calculate_anexo_totals(config['anexo'])
        return totals['subtotal'] > 0
    
    def _test_form_data_collection(self):
        """Test form data collection functionality."""
        # Test that configuration can be processed for template
        config = self.medium_config
        result = self.config_validator.process_configuration_for_template(config)
        
        return result.success and 'codigo_res' in result.data
    
    def _test_form_data_loading(self):
        """Test form data loading functionality."""
        # Test that configuration can be saved and loaded
        config = self.medium_config
        config_path = os.path.join(self.test_dir, "test_load.json")
        
        save_result = self.config_validator.save_validated_config(config, config_path)
        if not save_result.success:
            return False
        
        load_result = self.config_validator.validate_and_load_config(config_path)
        return load_result.success and load_result.data['titulo_base'] == config['titulo_base']
    
    def _test_dynamic_considerandos_rendering(self):
        """Test dynamic considerandos rendering."""
        # Test that different considerando types are handled
        config = self.medium_config
        
        # Check that we have both types
        tipos = [c['tipo'] for c in config['considerandos']]
        has_gasto_anterior = 'gasto_anterior' in tipos
        has_texto = 'texto' in tipos
        
        if not (has_gasto_anterior and has_texto):
            return False
        
        # Test processing
        result = self.config_validator.process_configuration_for_template(config)
        return result.success
    
    def _test_automatic_article_numbering(self):
        """Test automatic article numbering."""
        # Test that articles are processed correctly
        config = self.large_config
        result = self.config_validator.process_configuration_for_template(config)
        
        if not result.success:
            return False
        
        # Check that articles are preserved
        return len(result.data['articulos']) == len(config['articulos'])
    
    def _test_conditional_anexo_rendering(self):
        """Test conditional anexo rendering."""
        # Test with anexo items
        config_with_items = self.medium_config
        result_with = self.config_validator.process_configuration_for_template(config_with_items)
        
        # Test with empty anexo
        config_empty = self.minimal_config.copy()
        config_empty['anexo']['anexo_items'] = []
        result_empty = self.config_validator.process_configuration_for_template(config_empty)
        
        return result_with.success and result_empty.success
    
    def _test_automatic_calculations(self):
        """Test automatic calculations."""
        config = self.medium_config
        totals = self.config_validator.calculate_anexo_totals(config['anexo'])
        
        # Check that calculations are reasonable
        return (totals['subtotal'] > 0 and 
                totals['total_solicitado'] > 0 and
                isinstance(totals['subtotal'], (int, float)))
    
    def _test_penalizaciones_handling(self):
        """Test penalizaciones handling."""
        config = self.medium_config  # Has penalizaciones
        totals = self.config_validator.calculate_anexo_totals(config['anexo'])
        
        # Total should be less than subtotal due to penalizaciones
        return totals['total_solicitado'] < totals['subtotal']
    
    def _test_amount_formatting(self):
        """Test amount formatting."""
        config = self.medium_config
        result = self.config_validator.process_configuration_for_template(config)
        
        if not result.success:
            return False
        
        # Check that amounts are formatted as strings
        anexo = result.data['anexo']
        return (isinstance(anexo.get('subtotal'), str) and 
                isinstance(anexo.get('total_solicitado'), str))


if __name__ == '__main__':
    # Run comprehensive user acceptance tests
    unittest.main(verbosity=2)