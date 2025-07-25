#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify chart generation improvements and error handling.
"""

import sys
import os
import tempfile
import shutil

# Add services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from analisis_mensual import validate_chart_data, validate_matplotlib_availability, create_fallback_chart

def test_data_validation():
    """Test the improved data validation function."""
    print("Testing data validation improvements...")
    
    # Test case 1: Normal data
    normal_data = {"Comida": 1000, "Transporte": 500, "Ocio": 300}
    is_valid, cleaned, message = validate_chart_data(normal_data)
    assert is_valid, f"Normal data should be valid: {message}"
    print(f"✓ Normal data validation: {message}")
    
    # Test case 2: Extreme values
    extreme_data = {"Normal": 1000, "Extreme": 50_000_000}
    is_valid, cleaned, message = validate_chart_data(extreme_data)
    assert is_valid, f"Extreme data should be valid but capped: {message}"
    assert "Advertencias" in message, "Should contain warnings for extreme values"
    print(f"✓ Extreme data validation: {message}")
    
    # Test case 3: Invalid data types
    invalid_data = {"Valid": 1000, "Invalid": "not_a_number", "Negative": -500}
    is_valid, cleaned, message = validate_chart_data(invalid_data)
    assert is_valid, f"Should be valid after cleaning: {message}"
    assert len(cleaned) == 1, "Should only contain valid data"
    print(f"✓ Invalid data validation: {message}")
    
    # Test case 4: Empty data
    empty_data = {}
    is_valid, cleaned, message = validate_chart_data(empty_data)
    assert not is_valid, "Empty data should be invalid"
    print(f"✓ Empty data validation: {message}")
    
    # Test case 5: All zero/negative data
    zero_data = {"Zero": 0, "Negative": -100}
    is_valid, cleaned, message = validate_chart_data(zero_data)
    assert not is_valid, "Zero/negative data should be invalid"
    print(f"✓ Zero/negative data validation: {message}")
    
    print("All data validation tests passed!\n")


def test_matplotlib_validation():
    """Test matplotlib availability validation."""
    print("Testing matplotlib validation...")
    
    is_available, error_msg = validate_matplotlib_availability()
    
    if is_available:
        print("✓ Matplotlib is available and working")
    else:
        print(f"✗ Matplotlib validation failed: {error_msg}")
    
    print("Matplotlib validation test completed!\n")


def test_fallback_chart_generation():
    """Test fallback chart generation with various scenarios."""
    print("Testing fallback chart generation...")
    
    # Create temporary directory for test charts
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test case 1: Normal data
        normal_data = {"Comida": 1000, "Transporte": 500, "Ocio": 300}
        chart_path = os.path.join(temp_dir, "test_normal.png")
        result = create_fallback_chart(normal_data, 7, 2025, chart_path)
        
        if result and os.path.exists(result):
            print("✓ Normal fallback chart generated successfully")
        else:
            print("✗ Normal fallback chart generation failed")
        
        # Test case 2: Many categories
        many_categories = {f"Category_{i}": 100 + i*50 for i in range(12)}
        chart_path = os.path.join(temp_dir, "test_many.png")
        result = create_fallback_chart(many_categories, 7, 2025, chart_path)
        
        if result and os.path.exists(result):
            print("✓ Many categories fallback chart generated successfully")
        else:
            print("✗ Many categories fallback chart generation failed")
        
        # Test case 3: Large amounts
        large_amounts = {"Small": 100, "Medium": 10000, "Large": 1000000}
        chart_path = os.path.join(temp_dir, "test_large.png")
        result = create_fallback_chart(large_amounts, 7, 2025, chart_path)
        
        if result and os.path.exists(result):
            print("✓ Large amounts fallback chart generated successfully")
        else:
            print("✗ Large amounts fallback chart generation failed")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("Fallback chart generation tests completed!\n")


def main():
    """Run all chart improvement tests."""
    print("=== Testing Chart Generation Improvements ===\n")
    
    try:
        test_data_validation()
        test_matplotlib_validation()
        test_fallback_chart_generation()
        
        print("=== All Chart Improvement Tests Completed Successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())