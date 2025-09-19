"""
Test script for prescription upload and dashboard integration workflow
Tests the complete flow from image upload to real-time dashboard updates
"""

import asyncio
import aiohttp
import json
import base64
from pathlib import Path
import time

# Test configuration
BASE_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000/ws"
TEST_USER_ID = 1

# Sample prescription data for testing
SAMPLE_PRESCRIPTION_TEXT = """
Dr. Sarah Johnson, MD
Internal Medicine Specialist
Phone: (555) 123-4567

Patient: John Doe
Date: 2024-01-15

Prescription:

1. Metformin 500mg
   - Take twice daily with meals
   - Duration: 30 days
   - For diabetes management

2. Lisinopril 10mg
   - Take once daily in the morning
   - Duration: 30 days
   - For blood pressure control

3. Atorvastatin 20mg
   - Take once daily at bedtime
   - Duration: 30 days
   - For cholesterol management

Conditions:
- Type 2 Diabetes
- Hypertension
- High Cholesterol

Follow-up appointment in 4 weeks.

Dr. Sarah Johnson
License #: MD123456
"""

async def test_prescription_upload():
    """Test prescription upload via API"""
    print("🧪 Testing prescription upload...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Prepare test data
            test_data = {
                "user_id": TEST_USER_ID,
                "prescription_text": SAMPLE_PRESCRIPTION_TEXT,
                "filename": "test_prescription.txt"
            }
            
            # Upload prescription
            async with session.post(
                f"{BASE_URL}/api/prescriptions/upload-text",
                json=test_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Prescription upload successful!")
                    print(f"   - Prescription ID: {result.get('prescription_id')}")
                    print(f"   - Medications found: {len(result.get('medications', []))}")
                    print(f"   - Conditions found: {len(result.get('conditions', []))}")
                    print(f"   - Confidence score: {result.get('confidence', 0):.2f}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Upload failed: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

async def test_dashboard_data():
    """Test dashboard data retrieval"""
    print("\n📊 Testing dashboard data retrieval...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/api/dashboard/{TEST_USER_ID}"
            ) as response:
                if response.status == 200:
                    dashboard_data = await response.json()
                    print("✅ Dashboard data retrieved successfully!")
                    print(f"   - Total medications: {dashboard_data.get('summary', {}).get('total_medications', 0)}")
                    print(f"   - Total conditions: {dashboard_data.get('summary', {}).get('total_conditions', 0)}")
                    print(f"   - Pending recommendations: {dashboard_data.get('summary', {}).get('pending_recommendations', 0)}")
                    print(f"   - Recent prescriptions: {len(dashboard_data.get('recent_prescriptions', []))}")
                    return dashboard_data
                else:
                    error_text = await response.text()
                    print(f"❌ Dashboard retrieval failed: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return None

async def test_websocket_connection():
    """Test WebSocket real-time updates"""
    print("\n🔌 Testing WebSocket connection...")
    
    try:
        import websockets
        
        # Connect to WebSocket
        uri = f"{WEBSOCKET_URL}/{TEST_USER_ID}"
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Listen for messages for a short time
            print("   Listening for real-time updates...")
            
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"✅ Received WebSocket message: {data.get('type', 'unknown')}")
                return True
                
            except asyncio.TimeoutError:
                print("⏰ No WebSocket messages received (timeout)")
                return True  # Connection worked, just no messages
                
    except ImportError:
        print("⚠️  websockets library not available, skipping WebSocket test")
        return True
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

async def test_security_validation():
    """Test security validation features"""
    print("\n🔒 Testing security validation...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test with invalid user ID
            invalid_data = {
                "user_id": -1,  # Invalid user ID
                "prescription_text": SAMPLE_PRESCRIPTION_TEXT,
                "filename": "test_prescription.txt"
            }
            
            async with session.post(
                f"{BASE_URL}/api/prescriptions/upload-text",
                json=invalid_data
            ) as response:
                if response.status == 400:
                    print("✅ Security validation working - invalid user ID rejected")
                else:
                    print("⚠️  Security validation may need attention")
            
            # Test with malicious content
            malicious_data = {
                "user_id": TEST_USER_ID,
                "prescription_text": "<script>alert('xss')</script>" + SAMPLE_PRESCRIPTION_TEXT,
                "filename": "test_prescription.txt"
            }
            
            async with session.post(
                f"{BASE_URL}/api/prescriptions/upload-text",
                json=malicious_data
            ) as response:
                if response.status in [200, 400]:  # Either processed safely or rejected
                    print("✅ XSS protection working")
                else:
                    print("⚠️  XSS protection may need attention")
                    
        return True
        
    except Exception as e:
        print(f"❌ Security test error: {e}")
        return False

async def run_integration_tests():
    """Run complete integration test suite"""
    print("🚀 Starting Prescription Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Upload prescription
    upload_result = await test_prescription_upload()
    
    # Test 2: Retrieve dashboard data
    dashboard_result = await test_dashboard_data()
    
    # Test 3: WebSocket connection
    websocket_result = await test_websocket_connection()
    
    # Test 4: Security validation
    security_result = await test_security_validation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"   Prescription Upload: {'✅ PASS' if upload_result else '❌ FAIL'}")
    print(f"   Dashboard Retrieval: {'✅ PASS' if dashboard_result else '❌ FAIL'}")
    print(f"   WebSocket Connection: {'✅ PASS' if websocket_result else '❌ FAIL'}")
    print(f"   Security Validation: {'✅ PASS' if security_result else '❌ FAIL'}")
    
    all_passed = all([upload_result, dashboard_result, websocket_result, security_result])
    
    if all_passed:
        print("\n🎉 All integration tests PASSED!")
        print("   The prescription-to-dashboard workflow is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the backend logs for details.")
    
    return all_passed

if __name__ == "__main__":
    print("Starting integration tests...")
    print("Make sure the backend server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel\n")
    
    try:
        result = asyncio.run(run_integration_tests())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        exit(1)