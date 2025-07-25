#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify enhanced error handling in the Flask application.
"""

import requests
import json
import sys

def test_error_handling():
    """Test various error scenarios to verify enhanced error handling."""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Enhanced Error Handling")
    print("=" * 50)
    
    # Test 1: Invalid JSON request
    print("\n1. Testing invalid JSON request...")
    try:
        response = requests.post(f"{base_url}/ejecutar", 
                               data="invalid json", 
                               headers={'Content-Type': 'application/json'})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Missing required fields
    print("\n2. Testing missing required fields...")
    try:
        response = requests.post(f"{base_url}/ejecutar", 
                               json={"comando": "registrar", "args": {"monto": "100"}})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Invalid numeric value
    print("\n3. Testing invalid numeric value...")
    try:
        response = requests.post(f"{base_url}/ejecutar", 
                               json={"comando": "registrar", 
                                   "args": {"monto": "invalid", "categoria": "test", "desc": "test"}})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Invalid investment type
    print("\n4. Testing invalid investment type...")
    try:
        response = requests.post(f"{base_url}/ejecutar", 
                               json={"comando": "invertir", 
                                   "args": {"activo": "SPY", "tipo": "Invalid", "monto": "100"}})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Unknown command
    print("\n5. Testing unknown command...")
    try:
        response = requests.post(f"{base_url}/ejecutar", 
                               json={"comando": "unknown_command", "args": {}})
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 6: System validation
    print("\n6. Testing system validation...")
    try:
        response = requests.get(f"{base_url}/validar-sistema")
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Error handling tests completed!")

if __name__ == "__main__":
    test_error_handling()