#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script for configuration validation and auto-creation functionality.
This demonstrates the implementation of task 7.2.
"""

import os
import sys
from services.system_checker import SystemChecker


def main():
    """Demonstrate configuration validation and auto-creation."""
    print("=" * 70)
    print("PECO CONFIGURATION VALIDATION AND AUTO-CREATION DEMO")
    print("=" * 70)
    
    # Create system checker instance
    checker = SystemChecker()
    
    print("\n1. PERFORMING COMPLETE SYSTEM VALIDATION")
    print("-" * 50)
    
    # Run complete system validation
    result = checker.validate_complete_system()
    
    print(f"Overall Success: {result.success}")
    print(f"Message: {result.message}")
    
    # Show dependency check results
    dep_check = result.data['dependency_check']
    print(f"\nDependency Check: {'✅ PASS' if dep_check['success'] else '❌ FAIL'}")
    print(f"  Message: {dep_check['message']}")
    
    if dep_check['missing_dependencies']:
        print(f"  Missing Dependencies: {dep_check['missing_dependencies']}")
        print("  Installation Instructions:")
        for dep, instruction in dep_check['installation_instructions'].items():
            print(f"    {dep}: {instruction}")
    
    # Show configuration check results
    config_check = result.data['configuration_check']
    print(f"\nConfiguration Check: {'✅ PASS' if config_check['success'] else '❌ FAIL'}")
    print(f"  Message: {config_check['message']}")
    
    if config_check['created_directories']:
        print(f"  Created Directories ({len(config_check['created_directories'])}):")
        for directory in config_check['created_directories']:
            print(f"    - {directory}")
    
    if config_check['created_files']:
        print(f"  Created Files ({len(config_check['created_files'])}):")
        for file_path in config_check['created_files']:
            print(f"    - {file_path}")
    
    if config_check['missing_files']:
        print(f"  Missing Files ({len(config_check['missing_files'])}):")
        for file_path in config_check['missing_files']:
            print(f"    - {file_path}")
    
    if config_check['validation_errors']:
        print(f"  Validation Errors ({len(config_check['validation_errors'])}):")
        for error in config_check['validation_errors']:
            print(f"    - {error}")
    
    print("\n2. TESTING INDIVIDUAL VALIDATION METHODS")
    print("-" * 50)
    
    # Test individual validators
    import config
    
    # Test JSON configuration validation
    if os.path.exists(config.RUTA_CONFIG_JSON):
        is_valid = checker._validate_config_mes_json(config.RUTA_CONFIG_JSON)
        print(f"config_mes.json validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    else:
        print("config_mes.json: ❌ FILE NOT FOUND")
    
    # Test budget configuration validation
    if os.path.exists(config.JSON_PRESUPUESTO):
        is_valid = checker._validate_presupuesto_json(config.JSON_PRESUPUESTO)
        print(f"presupuesto_base.json validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    else:
        print("presupuesto_base.json: ❌ FILE NOT FOUND")
    
    # Test CSV validation
    if os.path.exists(config.CSV_GASTOS):
        is_valid = checker._validate_csv_structure(config.CSV_GASTOS)
        print(f"gastos_mensuales.csv validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    else:
        print("gastos_mensuales.csv: ❌ FILE NOT FOUND")
    
    # Test Excel validation
    if os.path.exists(config.XLSX_INVERSIONES):
        is_valid = checker._validate_excel_structure(config.XLSX_INVERSIONES)
        print(f"inversiones.xlsx validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    else:
        print("inversiones.xlsx: ❌ FILE NOT FOUND")
    
    # Test LaTeX template validation
    template_path = os.path.join(config.RUTA_RECURSOS, config.NOMBRE_PLANTILLA_RESOLUCION)
    if os.path.exists(template_path):
        is_valid = checker._validate_latex_template(template_path)
        print(f"plantilla_resolucion.tex validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    else:
        print("plantilla_resolucion.tex: ❌ FILE NOT FOUND")
    
    print("\n3. SYSTEM INFORMATION")
    print("-" * 50)
    
    system_info = result.data['system_info']
    print(f"Platform: {system_info['platform']} {system_info['architecture']}")
    print(f"Python Version: {system_info['python_version']}")
    print(f"Python Executable: {system_info['python_executable']}")
    print(f"PATH Directories: {system_info['path_directories']}")
    
    print("\n" + "=" * 70)
    if result.success:
        print("🎉 SYSTEM VALIDATION COMPLETED SUCCESSFULLY!")
        print("All configuration files and dependencies are ready.")
    else:
        print("⚠️  SYSTEM VALIDATION FOUND ISSUES")
        print("Please review the results above and address any missing dependencies or configuration issues.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)