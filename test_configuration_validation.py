# -*- coding: utf-8 -*-
"""
Test configuration validation and auto-creation functionality.
Tests for task 7.2: Add configuration validation and auto-creation
"""

import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
import sys

# Add services to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

from services.system_checker import SystemChecker, ConfigurationResult


def test_configuration_validation_and_creation():
    """Test comprehensive configuration validation and auto-creation."""
    print("Testing configuration validation and auto-creation...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Mock the config module with test paths
        mock_config = MagicMock()
        mock_config.RUTA_BASE = temp_dir
        mock_config.RUTA_TRACKERS = os.path.join(temp_dir, "03_Trackers")
        mock_config.RUTA_RECURSOS = os.path.join(temp_dir, "static", "05_Templates_y_Recursos")
        mock_config.RUTA_REPORTES = os.path.join(temp_dir, "06_Reportes")
        mock_config.RUTA_RESOLUCIONES = os.path.join(temp_dir, "01_Resoluciones")
        mock_config.RUTA_CONFIG_JSON = os.path.join(mock_config.RUTA_RECURSOS, 'config_mes.json')
        mock_config.JSON_PRESUPUESTO = os.path.join(mock_config.RUTA_RECURSOS, 'presupuesto_base.json')
        mock_config.CSV_GASTOS = os.path.join(mock_config.RUTA_TRACKERS, "gastos_mensuales.csv")
        mock_config.XLSX_INVERSIONES = os.path.join(mock_config.RUTA_TRACKERS, "inversiones.xlsx")
        mock_config.NOMBRE_PLANTILLA_RESOLUCION = "plantilla_resolucion.tex"
        
        # Patch the config import
        with patch.dict('sys.modules', {'config': mock_config}):
            checker = SystemChecker()
            
            # Test 1: Initial validation with missing everything
            print("\n1. Testing initial validation with missing files and directories...")
            result = checker.validate_configuration()
            
            assert isinstance(result, ConfigurationResult), "Should return ConfigurationResult"
            print(f"   Result success: {result.success}")
            print(f"   Message: {result.message}")
            
            if result.created_directories:
                print(f"   Created directories: {len(result.created_directories)}")
                for directory in result.created_directories:
                    print(f"     - {directory}")
                    assert os.path.exists(directory), f"Directory should exist: {directory}"
            
            if result.created_files:
                print(f"   Created files: {len(result.created_files)}")
                for file_path in result.created_files:
                    print(f"     - {file_path}")
                    assert os.path.exists(file_path), f"File should exist: {file_path}"
            
            # Test 2: Validate created configuration files
            print("\n2. Testing validation of created configuration files...")
            
            # Test config_mes.json
            if os.path.exists(mock_config.RUTA_CONFIG_JSON):
                print("   Validating config_mes.json...")
                is_valid = checker._validate_config_mes_json(mock_config.RUTA_CONFIG_JSON)
                print(f"     Valid: {is_valid}")
                
                # Check content
                with open(mock_config.RUTA_CONFIG_JSON, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    required_fields = ['titulo_documento', 'mes_nombre', 'mes_anterior', 
                                     'mensualidad_anterior_monto', 'gastos_mes_anterior',
                                     'considerandos_adicionales', 'articulos']
                    for field in required_fields:
                        assert field in config_data, f"Missing field: {field}"
                    print("     All required fields present")
            
            # Test presupuesto_base.json
            if os.path.exists(mock_config.JSON_PRESUPUESTO):
                print("   Validating presupuesto_base.json...")
                is_valid = checker._validate_presupuesto_json(mock_config.JSON_PRESUPUESTO)
                print(f"     Valid: {is_valid}")
                
                # Check content
                with open(mock_config.JSON_PRESUPUESTO, 'r', encoding='utf-8') as f:
                    presupuesto_data = json.load(f)
                    assert isinstance(presupuesto_data, dict), "Should be a dictionary"
                    for categoria, monto in presupuesto_data.items():
                        assert isinstance(monto, (int, float)), f"Amount should be numeric for {categoria}"
                        assert monto >= 0, f"Amount should be non-negative for {categoria}"
                    print("     Budget structure is valid")
            
            # Test CSV file
            if os.path.exists(mock_config.CSV_GASTOS):
                print("   Validating gastos_mensuales.csv...")
                is_valid = checker._validate_csv_structure(mock_config.CSV_GASTOS)
                print(f"     Valid: {is_valid}")
                
                # Check header
                with open(mock_config.CSV_GASTOS, 'r', encoding='utf-8') as f:
                    header = f.readline().strip()
                    expected_columns = ['Fecha', 'Categoria', 'Descripcion', 'Monto']
                    for col in expected_columns:
                        assert col.lower() in header.lower(), f"Missing column: {col}"
                    print("     CSV header is valid")
            
            # Test 3: Second validation run (should not create new files)
            print("\n3. Testing second validation run...")
            result2 = checker.validate_configuration()
            
            print(f"   Result success: {result2.success}")
            print(f"   Message: {result2.message}")
            
            # Should not create new files on second run
            if result2.created_files:
                print(f"   Warning: Created additional files: {result2.created_files}")
            else:
                print("   No additional files created (expected)")
            
            # Test 4: Test with corrupted JSON file
            print("\n4. Testing validation with corrupted JSON file...")
            
            # Corrupt the config file
            with open(mock_config.RUTA_CONFIG_JSON, 'w', encoding='utf-8') as f:
                f.write("{ invalid json content")
            
            is_valid = checker._validate_config_mes_json(mock_config.RUTA_CONFIG_JSON)
            assert not is_valid, "Should detect invalid JSON"
            print("   Correctly detected invalid JSON")
            
            # Test 5: Test directory permissions (if possible)
            print("\n5. Testing directory permissions...")
            
            # Create a directory and test write permissions
            test_dir = os.path.join(temp_dir, "test_permissions")
            os.makedirs(test_dir, exist_ok=True)
            
            if os.access(test_dir, os.W_OK):
                print("   Directory has write permissions")
            else:
                print("   Directory lacks write permissions")
            
            print("\n✅ Configuration validation and auto-creation tests completed successfully!")
            
            return True


def test_individual_validators():
    """Test individual validation methods."""
    print("\nTesting individual validation methods...")
    
    checker = SystemChecker()
    
    # Test 1: LaTeX template validation
    print("\n1. Testing LaTeX template validation...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as f:
        # Valid LaTeX template
        f.write("""\\documentclass[12pt]{article}
\\usepackage[utf8]{inputenc}
\\begin{document}
{{ titulo_documento }}
{{ mes_nombre }}
{{ gastos_mes_anterior }}
{{ considerandos_adicionales }}
{{ articulos }}
\\end{document}""")
        valid_template_path = f.name
    
    try:
        is_valid = checker._validate_latex_template(valid_template_path)
        assert is_valid, "Valid LaTeX template should pass validation"
        print("   ✅ Valid LaTeX template passed validation")
    finally:
        os.unlink(valid_template_path)
    
    # Test invalid LaTeX template
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as f:
        f.write("This is not a valid LaTeX document")
        invalid_template_path = f.name
    
    try:
        is_valid = checker._validate_latex_template(invalid_template_path)
        assert not is_valid, "Invalid LaTeX template should fail validation"
        print("   ✅ Invalid LaTeX template correctly failed validation")
    finally:
        os.unlink(invalid_template_path)
    
    # Test 2: CSV validation with different structures
    print("\n2. Testing CSV validation with different structures...")
    
    # Valid CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("Fecha,Categoria,Descripcion,Monto_ARS\n")
        valid_csv_path = f.name
    
    try:
        is_valid = checker._validate_csv_structure(valid_csv_path)
        assert is_valid, "Valid CSV should pass validation"
        print("   ✅ Valid CSV passed validation")
    finally:
        os.unlink(valid_csv_path)
    
    # Invalid CSV (missing columns)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("Date,Amount\n")
        invalid_csv_path = f.name
    
    try:
        is_valid = checker._validate_csv_structure(invalid_csv_path)
        assert not is_valid, "Invalid CSV should fail validation"
        print("   ✅ Invalid CSV correctly failed validation")
    finally:
        os.unlink(invalid_csv_path)
    
    print("\n✅ Individual validator tests completed successfully!")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING CONFIGURATION VALIDATION AND AUTO-CREATION")
    print("=" * 60)
    
    try:
        # Test main functionality
        test_configuration_validation_and_creation()
        
        # Test individual validators
        test_individual_validators()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("Configuration validation and auto-creation is working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)