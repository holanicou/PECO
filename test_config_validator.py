# -*- coding: utf-8 -*-
"""
Unit tests for the configuration validator module.
Tests the standardized data structure validation and integrity checks.
"""

import unittest
import json
import tempfile
import os
from unittest.mock import patch

from services.config_validator import ConfigValidator, ValidationResult


class TestConfigValidator(unittest.TestCase):
    """Test cases for ConfigValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ConfigValidator()
        
        # Valid configuration for testing
        self.valid_config = {
            "mes_iso": "2025-07",
            "titulo_base": "Presupuesto mensual",
            "visto": "La necesidad de cubrir los gastos mensuales y mantener un control financiero.",
            "considerandos": [
                {"tipo": "gasto_anterior", "descripcion": "Transporte", "monto": "14000"},
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
                    {"categoria": "Transporte", "monto": "14000"}
                ],
                "penalizaciones": [
                    {"categoria": "Penalización", "monto": "-2500"}
                ],
                "nota_final": "El monto final será ajustado según corresponda."
            }
        }
    
    def test_validate_valid_config_structure(self):
        """Test validation of a valid configuration structure."""
        result = self.validator.validate_config_structure(self.valid_config)
        
        self.assertTrue(result.success)
        self.assertIsNone(result.validation_errors)
        self.assertIn("Configuration structure validation passed", result.message)
    
    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        invalid_config = {"mes_iso": "2025-07"}  # Missing other required fields
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.validation_errors)
        self.assertIn("Missing required field", result.validation_errors[0])
    
    def test_validate_mes_iso_format(self):
        """Test mes_iso format validation."""
        # Test invalid format
        invalid_config = self.valid_config.copy()
        invalid_config["mes_iso"] = "2025/07"  # Wrong format
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("YYYY-MM format" in error for error in result.validation_errors))
    
    def test_validate_mes_iso_invalid_month(self):
        """Test mes_iso validation with invalid month."""
        invalid_config = self.valid_config.copy()
        invalid_config["mes_iso"] = "2025-13"  # Invalid month
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("month" in error and "invalid" in error for error in result.validation_errors))
    
    def test_validate_considerandos_structure(self):
        """Test considerandos structure validation."""
        # Test invalid considerando type
        invalid_config = self.valid_config.copy()
        invalid_config["considerandos"] = [
            {"tipo": "invalid_type", "descripcion": "Test"}
        ]
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("tipo must be" in error for error in result.validation_errors))
    
    def test_validate_considerandos_gasto_anterior(self):
        """Test gasto_anterior considerando validation."""
        # Test missing descripcion
        invalid_config = self.valid_config.copy()
        invalid_config["considerandos"] = [
            {"tipo": "gasto_anterior", "monto": "1000"}  # Missing descripcion
        ]
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("missing 'descripcion'" in error for error in result.validation_errors))
    
    def test_validate_considerandos_texto(self):
        """Test texto considerando validation."""
        # Test missing contenido
        invalid_config = self.valid_config.copy()
        invalid_config["considerandos"] = [
            {"tipo": "texto"}  # Missing contenido
        ]
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("missing 'contenido'" in error for error in result.validation_errors))
    
    def test_validate_articulos_structure(self):
        """Test articulos structure validation."""
        # Test non-array articulos
        invalid_config = self.valid_config.copy()
        invalid_config["articulos"] = "not an array"
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("articulos must be an array" in error for error in result.validation_errors))
    
    def test_validate_anexo_structure(self):
        """Test anexo structure validation."""
        # Test missing required anexo fields
        invalid_config = self.valid_config.copy()
        invalid_config["anexo"] = {"titulo": "Test"}  # Missing other required fields
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("anexo missing required field" in error for error in result.validation_errors))
    
    def test_validate_anexo_items(self):
        """Test anexo items validation."""
        # Test invalid item structure
        invalid_config = self.valid_config.copy()
        invalid_config["anexo"]["anexo_items"] = [
            {"categoria": "Test"}  # Missing monto
        ]
        
        result = self.validator.validate_config_structure(invalid_config)
        
        self.assertFalse(result.success)
        self.assertTrue(any("missing required field 'monto'" in error for error in result.validation_errors))
    
    def test_calculate_anexo_totals(self):
        """Test anexo totals calculation."""
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
    
    def test_validate_and_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        result = self.validator.validate_and_load_config("non_existent_file.json")
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message)
    
    def test_validate_and_load_config_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            temp_file = f.name
        
        try:
            result = self.validator.validate_and_load_config(temp_file)
            
            self.assertFalse(result.success)
            self.assertIn("Invalid JSON", result.message)
        finally:
            os.unlink(temp_file)
    
    def test_validate_and_load_valid_config(self):
        """Test loading valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_file = f.name
        
        try:
            result = self.validator.validate_and_load_config(temp_file)
            
            self.assertTrue(result.success)
            self.assertIsNotNone(result.data)
            self.assertIn("loaded and validated successfully", result.message)
            
            # Check that totals were calculated
            self.assertIn("subtotal", result.data["anexo"])
            self.assertIn("total_solicitado", result.data["anexo"])
        finally:
            os.unlink(temp_file)
    
    def test_save_validated_config(self):
        """Test saving validated configuration."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            result = self.validator.save_validated_config(self.valid_config, temp_file)
            
            self.assertTrue(result.success)
            self.assertIn("validated and saved successfully", result.message)
            
            # Verify file was created and contains valid JSON
            self.assertTrue(os.path.exists(temp_file))
            with open(temp_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                self.assertEqual(saved_config["mes_iso"], self.valid_config["mes_iso"])
                # Check that totals were added
                self.assertIn("subtotal", saved_config["anexo"])
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_is_valid_amount(self):
        """Test amount validation helper method."""
        # Valid amounts
        self.assertTrue(self.validator._is_valid_amount("1000"))
        self.assertTrue(self.validator._is_valid_amount("1000.50"))
        self.assertTrue(self.validator._is_valid_amount("-500"))
        self.assertTrue(self.validator._is_valid_amount("1,000"))
        
        # Invalid amounts
        self.assertFalse(self.validator._is_valid_amount("not_a_number"))
        self.assertFalse(self.validator._is_valid_amount(""))
        self.assertFalse(self.validator._is_valid_amount(None))
        self.assertFalse(self.validator._is_valid_amount(1000))  # Not a string


if __name__ == '__main__':
    unittest.main()
if _
_name__ == '__main__':
    unittest.main()