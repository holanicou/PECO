#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for configuration handling unit tests.
Runs comprehensive tests for the new configuration handling functionality.
"""

import unittest
import sys
import os

def run_configuration_tests():
    """Run all configuration handling unit tests."""
    print("=" * 70)
    print("PECO Configuration Handling Unit Tests")
    print("=" * 70)
    print()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_configuration_handling_unit')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    
    return success

if __name__ == '__main__':
    success = run_configuration_tests()
    sys.exit(0 if success else 1)