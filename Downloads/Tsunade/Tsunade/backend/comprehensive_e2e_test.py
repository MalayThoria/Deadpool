import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Health Check: PASSED")
            return True
        else:
            logger.error(f"❌ Health Check: FAILED - Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Health Check: FAILED - {str(e)}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if "message" in result:
                logger.info("✅ Root Endpoint: PASSED")
                return True
            else:
                logger.error("❌ Root Endpoint: FAILED - Invalid response format")
                return False
        else:
            logger.error(f"❌ Root Endpoint: FAILED - Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Root Endpoint: FAILED - {str(e)}")
        return False

def test_chat_functionality():
    """Test the chat endpoint with a simple query"""
    try:
        test_data = {
            "message": "What is aspirin used for?",
            "conversation_history": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "response" in result and len(result["response"]) > 20:
                logger.info("✅ Chat Functionality: PASSED")
                return True
            else:
                logger.error("❌ Chat Functionality: FAILED - Invalid response format")
                return False
        else:
            logger.error(f"❌ Chat Functionality: FAILED - Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Chat Functionality: FAILED - {str(e)}")
        return False

def test_medicine_extraction():
    """Test the medicine extraction endpoint"""
    try:
        test_data = {
            "prescription_text": "Take 2 tablets of Ibuprofen 200mg twice daily after meals. Also take 1 tablet of Metformin 500mg once daily before breakfast."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/extract-meds", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "medicines" in result and len(result["medicines"]) > 0:
                logger.info(f"✅ Medicine Extraction: PASSED - Found {len(result['medicines'])} medicines")
                return True
            else:
                logger.error("❌ Medicine Extraction: FAILED - No medicines extracted")
                return False
        else:
            logger.error(f"❌ Medicine Extraction: FAILED - Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Medicine Extraction: FAILED - {str(e)}")
        return False

def test_medicine_info_retrieval():
    """Test the medicine information endpoint"""
    try:
        test_data = {
            "medicines": ["Metformin"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/med-info", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "medicines_info" in result and len(result["medicines_info"]) > 0:
                medicine_info = result["medicines_info"][0]
                if "description" in medicine_info and len(medicine_info["description"]) > 50:
                    logger.info("✅ Medicine Information Retrieval: PASSED")
                    return True
                else:
                    logger.error("❌ Medicine Information Retrieval: FAILED - Insufficient detail")
                    return False
            else:
                logger.error("❌ Medicine Information Retrieval: FAILED - No medicine info returned")
                return False
        else:
            logger.error(f"❌ Medicine Information Retrieval: FAILED - Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Medicine Information Retrieval: FAILED - {str(e)}")
        return False

def test_ocr_endpoint():
    """Test the OCR endpoint availability (without actual image)"""
    try:
        # Just test if the endpoint exists and returns proper error for missing data
        response = requests.post(f"{BASE_URL}/api/v1/ocr", json={}, timeout=10)
        
        # We expect a 422 (validation error) since we're not sending proper data
        if response.status_code in [422, 400]:
            logger.info("✅ OCR Endpoint: PASSED - Endpoint is available")
            return True
        elif response.status_code == 404:
            logger.error("❌ OCR Endpoint: FAILED - Endpoint not found")
            return False
        else:
            logger.info(f"✅ OCR Endpoint: PASSED - Endpoint responded (status {response.status_code})")
            return True
    except Exception as e:
        logger.error(f"❌ OCR Endpoint: FAILED - {str(e)}")
        return False

def main():
    """Run all tests and report results"""
    logger.info("🚀 Starting Comprehensive E2E Testing...")
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Chat Functionality", test_chat_functionality),
        ("Medicine Extraction", test_medicine_extraction),
        ("Medicine Information Retrieval", test_medicine_info_retrieval),
        ("OCR Endpoint Availability", test_ocr_endpoint),
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                passed += 1
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Unexpected error: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    success_rate = (passed / total) * 100
    logger.info(f"\n🎯 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        logger.info("🎉 Great! Most functionality is working correctly.")
    elif success_rate >= 60:
        logger.info("⚠️ Good progress, but some issues need attention.")
    else:
        logger.info("🔧 Several issues detected. Review the failed tests.")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)