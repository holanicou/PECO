# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for new configuration handling functionality.
Tests configuration validation, loading, saving, and automatic calculation functions.
"""

import unittest
import json
import tempfile
import os
import shutil
from unittest.mock import patch, mock_open
from datetime import datetime

from services.config_validator import ConfigValidator, ValidationResult
from services.exceptions import ConfigurationError


class TestConfigurationHandling(unittest.TestCase):
    """Comprehensive test cases for configuration handling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ConfigValidator()
        self.temp_dir = tempfile.mkdtemp()
        
        # Valid configuration with new standardized structure
        self.valid_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto mensual",
            "visto": "La necesidad de cubrir los gastos mensuales y mantener un control financiero.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Transporte", "monto": "14000"},
                {"tipo": "gasto_anterior", "descripcion": "Comida", "monto": "27000"},
                {"tipo": "texto", "contenido": "Que se mantiene una política de ahorro."}
            ],
            "articulos": [
                "Aprobar el presupuesto por un total de $MONTO_TOTAL ARS.",
                "El solicitante continuará registrando sus gastos."
            ],
            "anexo": {
                "titulo": "Detalle del presupuesto mensual solicitado",
                "anexo_items": [
                    {"categoria": "Cuota Celular", "monto": "42416"},
                    {"categoria": "Inversiones CEDEARs", "monto": "50000"},
                    {"categoria": "Transporte", "monto": "14000"}
                ],
                "penalizaciones": [
                    {"categoria": "Penalización llegada tarde", "monto": "-2500"}
                ],
                "nota_final": "El monto final será ajustado según corresponda."
            }
        }
        
        # Configuration with backward compatibility (presupuesto instead of anexo_items)
        self.backward_compatible_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto mensual",
            "visto": "Test visto",
            "considerandos": [
                {"tipo": "texto", "contenido": "Test considerando"}
            ],
            "articulos": ["Test articulo"],
            "anexo": {
                "titulo": "Test anexo",
                "presupuesto": [  # Old field name
                    {"categoria": "Test item", "monto": "1000"}
                ],
                "penalizaciones": [],
                "nota_final": "Test nota"
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # ========================================================================
    # Configuration Structure Validation Tests
    # ========================================================================
    
    def test_validate_complete_valid_config(self):
        """Test validation of complete valid configuration."""
        result = self.validator.validate_config_structure(self.valid_config)
        
        self.assertTrue(result.success)
        self.assertIsNone(result.validation_errors)
        self.assertIn("Configuration structure validation passed", result.message)
    
    def test_validate_missing_required_fields(self):
        """Test validation fails when required top-level fields are missing."""
        test_cases = [
            ("mes_iso", {"titulo_base": "test", "visto": "test", "considerandos": [], "articulos": [], "anexo": {}}),
            ("titulo_base", {"mes_iso": "2025-07", "visto": "test", "considerandos": [], "articulos": [], "anexo": {}}),
            ("visto", {"mes_iso": "2025-07", "titulo_base": "test", "considerandos": [], "articulos": [], "anexo": {}}),
            ("considerandos", {"mes_iso": "2025-07", "titulo_base": "test", "visto": "test", "articulos": [], "anexo": {}}),
            ("articulos", {"mes_iso": "2025-07", "titulo_base": "test", "visto": "test", "considerandos": [], "anexo": {}}),
            ("anexo", {"mes_iso": "2025-07", "titulo_base": "test", "visto": "test", "considerandos": [], "articulos": []})
        ]
        
        for missing_field, config in test_cases:
            with self.subTest(missing_field=missing_field):
                result = self.validator.validate_config_structure(config)
                
                self.assertFalse(result.success)
                self.assertIsNotNone(result.validation_errors)
                self.assertTrue(any(f"Missing required field: {missing_field}" in error 
                                 for error in result.validation_errors))
    
    def test_validate_null_fields(self):
        """Test validation fails when required fields are null."""
        config = self.valid_config.copy()
        config["mes_iso"] = None
        
        result = self.validator.validate_config_structure(config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("Field cannot be null: mes_iso" in error 
                           for error in result.validation_errors))
    
    # ========================================================================
    # mes_iso Validation Tests
    # ========================================================================
    
    def test_validate_mes_iso_valid_formats(self):
        """Test mes_iso validation with valid formats."""
        valid_dates = ["2025-01", "2025-12", "2024-06", "2023-07"]
        
        for date_str in valid_dates:
            with self.subTest(date=date_str):
                config = self.valid_config.copy()
                config["mes_iso"] = date_str
                
                result = self.validator.validate_config_structure(config)
                self.assertTrue(result.success, f"Failed for date: {date_str}")
    
    def test_validate_mes_iso_invalid_formats(self):
        """Test mes_iso validation with invalid formats."""
        invalid_dates = [
            "2025/07",      # Wrong separator
            "25-07",        # Wrong year format
            "2025-7",       # Missing zero padding
            "2025-07-01",   # Too specific
            "July 2025",    # Text format
            "2025",         # Missing month
            ""              # Empty string
        ]
        
        for date_str in invalid_dates:
            with self.subTest(date=date_str):
                config = self.valid_config.copy()
                config["mes_iso"] = date_str
                
                result = self.validator.validate_config_structure(config)
                self.assertFalse(result.success, f"Should fail for date: {date_str}")
                self.assertTrue(any("YYYY-MM format" in error 
                               for error in result.validation_errors))
    
    def test_validate_mes_iso_invalid_months(self):
        """Test mes_iso validation with invalid month values."""
        invalid_months = ["2025-00", "2025-13", "2025-99"]
        
        for date_str in invalid_months:
            with self.subTest(date=date_str):
                config = self.valid_config.copy()
                config["mes_iso"] = date_str
                
                result = self.validator.validate_config_structure(config)
                self.assertFalse(result.success)
                self.assertTrue(any("month" in error and "invalid" in error 
                               for error in result.validation_errors))
    
    def test_validate_mes_iso_unusual_years(self):
        """Test mes_iso validation with unusual but valid years generates warnings."""
        unusual_years = ["2019-07", "2031-07"]  # Outside typical range
        
        for date_str in unusual_years:
            with self.subTest(date=date_str):
                config = self.valid_config.copy()
                config["mes_iso"] = date_str
                
                result = self.validator.validate_config_structure(config)
                # Should still be valid but with warnings
                self.assertTrue(result.success)
                self.assertIsNotNone(result.warnings)
                self.assertTrue(any("seems unusual" in warning 
                               for warning in result.warnings))
    
    # ========================================================================
    # Considerandos Validation Tests
    # ========================================================================
    
    def test_validate_considerandos_gasto_anterior_complete(self):
        """Test validation of complete gasto_anterior considerando."""
        config = self.valid_config.copy()
        config["considerandos"] = [
            {"tipo": "gasto_anterior", "descripcion": "Test expense", "monto": "1000"}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)
    
    def test_validate_considerandos_gasto_anterior_missing_fields(self):
        """Test validation fails for gasto_anterior with missing fields."""
        test_cases = [
            {"tipo": "gasto_anterior", "monto": "1000"},  # Missing descripcion
            {"tipo": "gasto_anterior", "descripcion": "Test"},  # Missing monto
            {"tipo": "gasto_anterior"}  # Missing both
        ]
        
        for considerando in test_cases:
            with self.subTest(considerando=considerando):
                config = self.valid_config.copy()
                config["considerandos"] = [considerando]
                
                result = self.validator.validate_config_structure(config)
                self.assertFalse(result.success)
    
    def test_validate_considerandos_texto_complete(self):
        """Test validation of complete texto considerando."""
        config = self.valid_config.copy()
        config["considerandos"] = [
            {"tipo": "texto", "contenido": "Test content"}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)
    
    def test_validate_considerandos_texto_missing_contenido(self):
        """Test validation fails for texto considerando without contenido."""
        config = self.valid_config.copy()
        config["considerandos"] = [
            {"tipo": "texto"}  # Missing contenido
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertFalse(result.success)
        self.assertTrue(any("missing 'contenido'" in error 
                           for error in result.validation_errors))
    
    def test_validate_considerandos_invalid_tipo(self):
        """Test validation fails for invalid considerando tipo."""
        config = self.valid_config.copy()
        config["considerandos"] = [
            {"tipo": "invalid_type", "contenido": "Test"}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertFalse(result.success)
        self.assertTrue(any("tipo must be 'gasto_anterior' or 'texto'" in error 
                           for error in result.validation_errors))
    
    def test_validate_considerandos_mixed_types(self):
        """Test validation of mixed considerando types."""
        config = self.valid_config.copy()
        config["considerandos"] = [
            {"tipo": "gasto_anterior", "descripcion": "Expense", "monto": "1000"},
            {"tipo": "texto", "contenido": "Text content"},
            {"tipo": "gasto_anterior", "descripcion": "Another expense", "monto": "2000"}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)
    
    def test_validate_considerandos_empty_array(self):
        """Test validation with empty considerandos array generates warning."""
        config = self.valid_config.copy()
        config["considerandos"] = []
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)  # Should still be valid
        self.assertIsNotNone(result.warnings)
        self.assertTrue(any("considerandos array is empty" in warning 
                           for warning in result.warnings))
    
    # ========================================================================
    # Anexo Validation Tests
    # ========================================================================
    
    def test_validate_anexo_complete_structure(self):
        """Test validation of complete anexo structure."""
        result = self.validator.validate_config_structure(self.valid_config)
        self.assertTrue(result.success)
    
    def test_validate_anexo_backward_compatibility(self):
        """Test validation supports backward compatibility with 'presupuesto' field."""
        result = self.validator.validate_config_structure(self.backward_compatible_config)
        self.assertTrue(result.success)
        
        # Should generate warning about both fields present
        config_with_both = self.valid_config.copy()
        config_with_both["anexo"]["presupuesto"] = [{"categoria": "Test", "monto": "1000"}]
        
        result_both = self.validator.validate_config_structure(config_with_both)
        self.assertTrue(result_both.success)
        self.assertIsNotNone(result_both.warnings)
        self.assertTrue(any("both 'anexo_items' and 'presupuesto'" in warning 
                           for warning in result_both.warnings))
    
    def test_validate_anexo_missing_required_fields(self):
        """Test validation fails when anexo missing required fields."""
        config = self.valid_config.copy()
        config["anexo"] = {"titulo": "Test"}  # Missing other required fields
        
        result = self.validator.validate_config_structure(config)
        self.assertFalse(result.success)
        
        required_fields = ["penalizaciones", "nota_final"]
        for field in required_fields:
            self.assertTrue(any(f"anexo missing required field: {field}" in error 
                               for error in result.validation_errors))
    
    def test_validate_anexo_items_structure(self):
        """Test validation of anexo items structure."""
        config = self.valid_config.copy()
        config["anexo"]["anexo_items"] = [
            {"categoria": "Valid item", "monto": "1000"},
            {"categoria": "Another item", "monto": "2000.50"}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)
    
    def test_validate_anexo_items_invalid_structure(self):
        """Test validation fails for invalid anexo items."""
        config = self.valid_config.copy()
        config["anexo"]["anexo_items"] = [
            {"categoria": "Missing monto"},  # Missing monto
            {"monto": "1000"},  # Missing categoria
            {"categoria": "", "monto": "1000"},  # Empty categoria
            {"categoria": "Invalid amount", "monto": "not_a_number"}  # Invalid monto
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertFalse(result.success)
        self.assertGreater(len(result.validation_errors), 0)
    
    def test_validate_penalizaciones_structure(self):
        """Test validation of penalizaciones structure."""
        config = self.valid_config.copy()
        config["anexo"]["penalizaciones"] = [
            {"categoria": "Late penalty", "monto": "-500"},
            {"categoria": "Other penalty", "monto": "-1000"}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)
    
    def test_validate_penalizaciones_positive_amounts_warning(self):
        """Test validation warns for positive penalizacion amounts."""
        config = self.valid_config.copy()
        config["anexo"]["penalizaciones"] = [
            {"categoria": "Positive penalty", "monto": "500"}  # Should be negative
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)  # Still valid
        self.assertIsNotNone(result.warnings)
        self.assertTrue(any("penalizaciones are typically negative" in warning 
                           for warning in result.warnings))
    
    # ========================================================================
    # Amount Validation Tests
    # ========================================================================
    
    def test_is_valid_amount_valid_formats(self):
        """Test amount validation with valid formats."""
        valid_amounts = [
            "1000", "1000.50", "-500", "0", "0.00",
            "1,000", "1,000.50", "10000", "-2500.75"
        ]
        
        for amount in valid_amounts:
            with self.subTest(amount=amount):
                self.assertTrue(self.validator._is_valid_amount(amount))
    
    def test_is_valid_amount_invalid_formats(self):
        """Test amount validation with invalid formats."""
        invalid_amounts = [
            "not_a_number", "", "abc", "1000abc", 
            None, 1000, [], {}, "1.2.3", "1,000,000.50.25"
        ]
        
        for amount in invalid_amounts:
            with self.subTest(amount=amount):
                self.assertFalse(self.validator._is_valid_amount(amount))
    
    # ========================================================================
    # Automatic Calculation Tests
    # ========================================================================
    
    def test_calculate_anexo_totals_basic(self):
        """Test basic anexo totals calculation."""
        anexo = {
            "anexo_items": [
                {"categoria": "Item 1", "monto": "1000"},
                {"categoria": "Item 2", "monto": "2000"}
            ],
            "penalizaciones": [
                {"categoria": "Penalty", "monto": "-500"}
            ]
        }
        
        totals = self.validator.calculate_anexo_totals(anexo)
        
        self.assertEqual(totals["subtotal"], 3000.0)
        self.assertEqual(totals["penalizaciones_total"], 500.0)  # Absolute value
        self.assertEqual(totals["total_solicitado"], 2500.0)
    
    def test_calculate_anexo_totals_backward_compatibility(self):
        """Test anexo totals calculation with backward compatible 'presupuesto' field."""
        anexo = {
            "presupuesto": [  # Old field name
                {"categoria": "Item 1", "monto": "1000"},
                {"categoria": "Item 2", "monto": "1500"}
            ],
            "penalizaciones": []
        }
        
        totals = self.validator.calculate_anexo_totals(anexo)
        
        self.assertEqual(totals["subtotal"], 2500.0)
        self.assertEqual(totals["penalizaciones_total"], 0.0)
        self.assertEqual(totals["total_solicitado"], 2500.0)
    
    def test_calculate_anexo_totals_with_formatting(self):
        """Test anexo totals calculation with formatted amounts."""
        anexo = {
            "anexo_items": [
                {"categoria": "Item 1", "monto": "1,000"},
                {"categoria": "Item 2", "monto": "2,500.50"},
                {"categoria": "Item 3", "monto": " 1500 "}  # With spaces
            ],
            "penalizaciones": [
                {"categoria": "Penalty", "monto": "-1,000.25"}
            ]
        }
        
        totals = self.validator.calculate_anexo_totals(anexo)
        
        self.assertEqual(totals["subtotal"], 5000.5)
        self.assertEqual(totals["penalizaciones_total"], 1000.25)
        self.assertEqual(totals["total_solicitado"], 4000.25)
    
    def test_calculate_anexo_totals_invalid_amounts(self):
        """Test anexo totals calculation handles invalid amounts gracefully."""
        anexo = {
            "anexo_items": [
                {"categoria": "Valid item", "monto": "1000"},
                {"categoria": "Invalid item", "monto": "not_a_number"},
                {"categoria": "Another valid", "monto": "500"}
            ],
            "penalizaciones": [
                {"categoria": "Invalid penalty", "monto": "invalid"}
            ]
        }
        
        # Should calculate only valid amounts
        totals = self.validator.calculate_anexo_totals(anexo)
        
        self.assertEqual(totals["subtotal"], 1500.0)  # Only valid amounts
        self.assertEqual(totals["penalizaciones_total"], 0.0)  # Invalid penalty ignored
        self.assertEqual(totals["total_solicitado"], 1500.0)
    
    def test_calculate_anexo_totals_empty_arrays(self):
        """Test anexo totals calculation with empty arrays."""
        anexo = {
            "anexo_items": [],
            "penalizaciones": []
        }
        
        totals = self.validator.calculate_anexo_totals(anexo)
        
        self.assertEqual(totals["subtotal"], 0.0)
        self.assertEqual(totals["penalizaciones_total"], 0.0)
        self.assertEqual(totals["total_solicitado"], 0.0)
    
    def test_calculate_anexo_totals_missing_fields(self):
        """Test anexo totals calculation with missing fields."""
        anexo = {}  # No items or penalizaciones
        
        totals = self.validator.calculate_anexo_totals(anexo)
        
        self.assertEqual(totals["subtotal"], 0.0)
        self.assertEqual(totals["penalizaciones_total"], 0.0)
        self.assertEqual(totals["total_solicitado"], 0.0)
    
    def test_calculate_anexo_totals_penalizacion_handling(self):
        """Test proper handling of penalizacion amounts (both positive and negative strings)."""
        anexo = {
            "anexo_items": [
                {"categoria": "Item 1", "monto": "1000"}
            ],
            "penalizaciones": [
                {"categoria": "Negative penalty", "monto": "-500"},
                {"categoria": "Positive penalty", "monto": "300"}  # Should still be subtracted
            ]
        }
        
        totals = self.validator.calculate_anexo_totals(anexo)
        
        self.assertEqual(totals["subtotal"], 1000.0)
        self.assertEqual(totals["penalizaciones_total"], 800.0)  # 500 + 300
        self.assertEqual(totals["total_solicitado"], 200.0)  # 1000 - 800
    
    # ========================================================================
    # File Operations Tests
    # ========================================================================
    
    def test_validate_and_load_config_success(self):
        """Test successful configuration loading and validation."""
        config_file = os.path.join(self.temp_dir, "test_config.json")
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.valid_config, f)
        
        result = self.validator.validate_and_load_config(config_file)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data["mes_iso"], "2025-07")
        
        # Check that totals were calculated and added
        self.assertIn("subtotal", result.data["anexo"])
        self.assertIn("total_solicitado", result.data["anexo"])
        self.assertIn("penalizaciones_total", result.data["anexo"])
    
    def test_validate_and_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        result = self.validator.validate_and_load_config("non_existent_file.json")
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message)
        self.assertIsNotNone(result.validation_errors)
    
    def test_validate_and_load_config_invalid_json(self):
        """Test loading file with invalid JSON."""
        config_file = os.path.join(self.temp_dir, "invalid.json")
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}')  # Invalid JSON
        
        result = self.validator.validate_and_load_config(config_file)
        
        self.assertFalse(result.success)
        self.assertIn("Invalid JSON", result.message)
        self.assertIsNotNone(result.validation_errors)
    
    def test_save_validated_config_success(self):
        """Test successful configuration validation and saving."""
        config_file = os.path.join(self.temp_dir, "saved_config.json")
        
        result = self.validator.save_validated_config(self.valid_config, config_file)
        
        self.assertTrue(result.success)
        self.assertIn("validated and saved successfully", result.message)
        
        # Verify file was created and contains valid JSON
        self.assertTrue(os.path.exists(config_file))
        with open(config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
            self.assertEqual(saved_config["mes_iso"], self.valid_config["mes_iso"])
            
            # Check that totals were calculated and added
            self.assertIn("subtotal", saved_config["anexo"])
            self.assertIn("total_solicitado", saved_config["anexo"])
    
    def test_save_validated_config_invalid_structure(self):
        """Test saving configuration with invalid structure fails."""
        invalid_config = {"mes_iso": "invalid_format"}  # Missing required fields
        config_file = os.path.join(self.temp_dir, "invalid_config.json")
        
        result = self.validator.save_validated_config(invalid_config, config_file)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.validation_errors)
        
        # File should not be created
        self.assertFalse(os.path.exists(config_file))
    
    def test_save_validated_config_creates_directory(self):
        """Test saving configuration creates directory if it doesn't exist."""
        nested_dir = os.path.join(self.temp_dir, "nested", "directory")
        config_file = os.path.join(nested_dir, "config.json")
        
        result = self.validator.save_validated_config(self.valid_config, config_file)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(config_file))
        self.assertTrue(os.path.exists(nested_dir))
    
    # ========================================================================
    # Template Processing Tests
    # ========================================================================
    
    def test_process_configuration_for_template(self):
        """Test configuration processing for template rendering."""
        result = self.validator.process_configuration_for_template(self.valid_config)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)
        
        processed_config = result.data
        
        # Check date processing
        self.assertIn("mes_nombre", processed_config)
        self.assertIn("anio", processed_config)
        self.assertEqual(processed_config["mes_nombre"], "julio")
        self.assertEqual(processed_config["anio"], "2025")
        
        # Check resolution code generation
        self.assertIn("codigo_res", processed_config)
        self.assertIn("fecha_larga", processed_config)
        self.assertIn("titulo_documento", processed_config)
        
        # Check anexo totals are calculated and formatted
        self.assertIn("subtotal", processed_config["anexo"])
        self.assertIn("total_solicitado", processed_config["anexo"])
        self.assertIsInstance(processed_config["anexo"]["subtotal"], str)
        self.assertIsInstance(processed_config["anexo"]["total_solicitado"], str)
        
        # Check MONTO_TOTAL replacement in articulos
        for articulo in processed_config["articulos"]:
            self.assertNotIn("$MONTO_TOTAL", articulo)
    
    def test_process_configuration_invalid_mes_iso(self):
        """Test template processing with invalid mes_iso."""
        config = self.valid_config.copy()
        config["mes_iso"] = "invalid-date"
        
        result = self.validator.process_configuration_for_template(config)
        
        # Should still succeed but with default values
        self.assertTrue(result.success)
        processed_config = result.data
        self.assertEqual(processed_config["mes_nombre"], "mes")
        self.assertEqual(processed_config["anio"], "año")
    
    def test_normalize_configuration_structure(self):
        """Test configuration structure normalization."""
        # Test with old 'presupuesto' field
        config_with_presupuesto = {
            "mes_iso": "2025-07",
            "titulo_base": "Test",
            "visto": "Test",
            "considerandos": [],
            "articulos": [],
            "anexo": {
                "titulo": "Test",
                "presupuesto": [{"categoria": "Test", "monto": "1000"}],
                "penalizaciones": [],
                "nota_final": "Test"
            }
        }
        
        result = self.validator.normalize_configuration_structure(config_with_presupuesto)
        
        self.assertTrue(result.success)
        normalized_config = result.data
        
        # Should have converted 'presupuesto' to 'anexo_items'
        self.assertIn("anexo_items", normalized_config["anexo"])
        self.assertNotIn("presupuesto", normalized_config["anexo"])
        self.assertEqual(len(normalized_config["anexo"]["anexo_items"]), 1)
    
    def test_month_name_generation(self):
        """Test month name generation for different months."""
        month_tests = [
            ("2025-01", "enero"),
            ("2025-02", "febrero"),
            ("2025-03", "marzo"),
            ("2025-04", "abril"),
            ("2025-05", "mayo"),
            ("2025-06", "junio"),
            ("2025-07", "julio"),
            ("2025-08", "agosto"),
            ("2025-09", "septiembre"),
            ("2025-10", "octubre"),
            ("2025-11", "noviembre"),
            ("2025-12", "diciembre")
        ]
        
        for mes_iso, expected_name in month_tests:
            with self.subTest(mes_iso=mes_iso):
                config = self.valid_config.copy()
                config["mes_iso"] = mes_iso
                
                result = self.validator.process_configuration_for_template(config)
                
                self.assertTrue(result.success)
                self.assertEqual(result.data["mes_nombre"], expected_name)
                self.assertEqual(result.data["anio"], "2025")
    
    # ========================================================================
    # Edge Cases and Error Handling Tests
    # ========================================================================
    
    def test_validation_with_unicode_content(self):
        """Test validation handles Unicode content properly."""
        config = self.valid_config.copy()
        config["visto"] = "Considerando la situación económica actual y la necesidad de mantener un equilibrio financiero."
        config["considerandos"] = [
            {"tipo": "texto", "contenido": "Que el solicitante mantiene un compromiso de pago por el celular POCO X6 Pro 5G."}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)
    
    def test_validation_with_large_amounts(self):
        """Test validation handles large monetary amounts."""
        config = self.valid_config.copy()
        config["anexo"]["anexo_items"] = [
            {"categoria": "Large amount", "monto": "1000000"},
            {"categoria": "Very large amount", "monto": "999999999.99"}
        ]
        
        result = self.validator.validate_config_structure(config)
        self.assertTrue(result.success)
        
        totals = self.validator.calculate_anexo_totals(config["anexo"])
        self.assertEqual(totals["subtotal"], 1000999999.99)
    
    def test_validation_with_empty_strings(self):
        """Test validation properly handles empty strings."""
        config = self.valid_config.copy()
        config["titulo_base"] = ""
        config["visto"] = "   "  # Only whitespace
        
        result = self.validator.validate_config_structure(config)
        self.assertFalse(result.success)
        
        # Should have errors for empty fields
        self.assertTrue(any("cannot be empty" in error for error in result.validation_errors))
    
    def test_validation_result_structure(self):
        """Test ValidationResult structure and properties."""
        result = self.validator.validate_config_structure(self.valid_config)
        
        # Check ValidationResult properties
        self.assertIsInstance(result, ValidationResult)
        self.assertIsInstance(result.success, bool)
        self.assertIsInstance(result.message, str)
        
        # For successful validation
        self.assertTrue(result.success)
        self.assertIsNone(result.validation_errors)
        
        # Test with invalid config
        invalid_config = {"mes_iso": "invalid"}
        result_invalid = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result_invalid.success)
        self.assertIsNotNone(result_invalid.validation_errors)
        self.assertIsInstance(result_invalid.validation_errors, list)
        self.assertGreater(len(result_invalid.validation_errors), 0)


if __name__ == '__main__':
    unittest.main()