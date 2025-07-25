#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit test runner for PECO service layer.
Runs all unit tests for DataManager, LaTeXProcessor, and PDFGenerator.
"""

import unittest
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_unit_tests():
    """Run all unit tests for the service layer."""
    
    # Discover and load all test modules
    loader = unittest.TestLoader()
    
    # Load test suites
    test_modules = [
        'test_data_manager_unit',
        'test_latex_processor_unit', 
        'test_pdf_generator_unit'
    ]
    
    suite = unittest.TestSuite()
    
    for module_name in test_modules:
        try:
            module_suite = loader.loadTestsFromName(module_name)
            suite.addTest(module_suite)
            print(f"✓ Loaded tests from {module_name}")
        except Exception as e:
            print(f"✗ Failed to load tests from {module_name}: {e}")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("UNIT TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    success = run_unit_tests()
    sys.exit(0 if success else 1)