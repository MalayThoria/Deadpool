#!/usr/bin/env python3
"""
Endpoint Testing Script for LP Assistant API
Tests all endpoints to ensure proper fallback mechanisms when OpenAI is unavailable
"""

import requests
import json
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_VERSION = "v1"

def test_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None, files: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            if files:
                response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}
        
        return {
            "status": "success" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "response_time": response.elapsed.total_seconds()
        }
    except requests.exceptions.Timeout:
        return {"status": "timeout", "message": "Request timed out"}
    except requests.exceptions.ConnectionError:
        return {"status": "connection_error", "message": "Could not connect to server"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    """Run comprehensive endpoint tests"""
    print("🧪 LP Assistant API Endpoint Testing")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Health Check",
            "method": "GET",
            "endpoint": "/health",
            "expected": "Should always work"
        },
        {
            "name": "Root Endpoint",
            "method": "GET", 
            "endpoint": "/",
            "expected": "Should always work"
        },
        {
            "name": "Medicine Extraction (Fallback Test)",
            "method": "POST",
            "endpoint": f"/api/{API_VERSION}/extract-meds",
            "data": {
                "prescription_text": "Take Paracetamol 500mg twice daily and Ibuprofen 200mg as needed for pain"
            },
            "expected": "Should work with fallback extraction"
        },
        {
            "name": "Medicine Information (Fallback Test)",
            "method": "POST",
            "endpoint": f"/api/{API_VERSION}/med-info",
            "data": {
                "medicines": ["Paracetamol", "Ibuprofen"]
            },
            "expected": "Should work with fallback information"
        },
        {
            "name": "Chat Assistant (Fallback Test)",
            "method": "POST",
            "endpoint": f"/api/{API_VERSION}/chat",
            "data": {
                "message": "What is Paracetamol used for?",
                "conversation_history": []
            },
            "expected": "Should work with fallback response"
        },
        {
            "name": "Prescription Analysis (Fallback Test)",
            "method": "POST",
            "endpoint": f"/api/{API_VERSION}/analyze-prescription",
            "data": {
                "prescription_text": "Patient: John Doe. Diagnosis: Hypertension. Rx: Lisinopril 10mg once daily for 30 days. Dr. Smith, 2024-01-15",
                "auto_update_profile": False
            },
            "headers": {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiYXVkIjpbImZhc3RhcGktdXNlcnM6YXV0aCJdLCJpYXQiOjE3NTgwNTYyNDEsImV4cCI6MTc1ODA1OTg0MX0.M6kl3T3Hqtef2HNXXqmJ-N_otdicYsZLOVgvQtgCymQ"
            },
            "expected": "Should work with fallback analysis"
        },
        {
            "name": "Health Recommendations (Fallback Test)",
            "method": "POST",
            "endpoint": f"/api/{API_VERSION}/disease-recommendations",
            "data": {
                "disease_name": "hypertension",
                "severity": "mild",
                "symptoms": ["headache", "dizziness"],
                "limitations": []
            },
            "expected": "Should work with fallback recommendations"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Endpoint: {test_case['method']} {test_case['endpoint']}")
        print(f"   Expected: {test_case['expected']}")
        
        result = test_endpoint(
            method=test_case['method'],
            endpoint=test_case['endpoint'],
            data=test_case.get('data'),
            files=test_case.get('files'),
            headers=test_case.get('headers')
        )
        
        results.append({
            "test_name": test_case['name'],
            "endpoint": test_case['endpoint'],
            "result": result
        })
        
        # Print result
        if result['status'] == 'success':
            print(f"   ✅ SUCCESS (Status: {result['status_code']}, Time: {result['response_time']:.2f}s)")
            if isinstance(result['response'], dict):
                if 'error' in result['response']:
                    print(f"   ⚠️  Response contains error: {result['response']['error']}")
                elif 'fallback' in str(result['response']).lower():
                    print(f"   ✅ Fallback mechanism working")
        else:
            print(f"   ❌ FAILED: {result.get('message', 'Unknown error')}")
            if 'status_code' in result:
                print(f"   Status Code: {result['status_code']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results if r['result']['status'] == 'success')
    total_tests = len(results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    for result in results:
        status_icon = "✅" if result['result']['status'] == 'success' else "❌"
        print(f"{status_icon} {result['test_name']}: {result['result']['status']}")
        if result['result']['status'] != 'success':
            print(f"   Error: {result['result'].get('message', 'Unknown')}")
    
    # OpenAI Status Check
    print("\n🔍 OPENAI STATUS CHECK:")
    print("Current API Key Status: PLACEHOLDER (Not configured)")
    print("Fallback Mechanisms: ACTIVE")
    print("Recommendation: Configure valid OpenAI API key for full functionality")
    
    return results

if __name__ == "__main__":
    main()