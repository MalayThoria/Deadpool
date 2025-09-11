#!/usr/bin/env python3
"""
Comprehensive Railway Deployment Test Script
Tests OCR, ChatGPT, and all API endpoints
"""

import requests
import sys
import json
from pathlib import Path
import base64
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image():
    """Create a test prescription image for OCR testing"""
    # Create a simple prescription image
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a default font, fallback to basic if not available
        font_large = ImageFont.truetype("arial.ttf", 16)
        font_medium = ImageFont.truetype("arial.ttf", 12)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw prescription content
    draw.text((50, 30), "MEDICAL PRESCRIPTION", fill='black', font=font_large)
    draw.text((50, 70), "Dr. John Smith, MD", fill='black', font=font_medium)
    draw.text((50, 90), "Internal Medicine Specialist", fill='black', font=font_small)
    
    draw.text((50, 120), "Patient: Jane Doe", fill='black', font=font_medium)
    draw.text((50, 140), "DOB: 01/15/1980", fill='black', font=font_small)
    
    draw.text((50, 170), "Rx:", fill='black', font=font_medium)
    draw.text((50, 200), "1. Amoxicillin 500mg", fill='black', font=font_medium)
    draw.text((70, 220), "Take 1 tablet twice daily for 7 days", fill='black', font=font_small)
    
    draw.text((50, 250), "2. Ibuprofen 400mg", fill='black', font=font_medium)
    draw.text((70, 270), "Take 1 tablet as needed for pain", fill='black', font=font_small)
    
    draw.text((50, 300), "3. Vitamin D3 1000 IU", fill='black', font=font_medium)
    draw.text((70, 320), "Take 1 tablet daily with food", fill='black', font=font_small)
    
    draw.text((50, 360), "Date: 12/15/2024", fill='black', font=font_small)
    draw.text((350, 360), "Dr. Signature: _______________", fill='black', font=font_small)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr.getvalue()

def test_health_endpoint(base_url):
    """Test the health endpoint"""
    print("\n🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('status', 'Unknown')}")
            if 'tesseract_available' in data:
                print(f"   Tesseract available: {data['tesseract_available']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_ocr_endpoint(base_url):
    """Test the OCR endpoint with a test image"""
    print("\n🖼️ Testing OCR Endpoint...")
    try:
        # Create test image
        test_image = create_test_image()
        
        files = {'file': ('test_prescription.png', test_image, 'image/png')}
        response = requests.post(f"{base_url}/api/v1/ocr", files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            extracted_text = data.get('extracted_text', '')
            print(f"✅ OCR extraction successful")
            print(f"   Extracted text length: {len(extracted_text)} characters")
            if 'Amoxicillin' in extracted_text or 'prescription' in extracted_text.lower():
                print("   ✅ Text extraction appears accurate")
            else:
                print("   ⚠️ Text extraction may need improvement")
            print(f"   Sample text: {extracted_text[:100]}...")
            return True, extracted_text
        else:
            print(f"❌ OCR failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return False, None

def test_medicine_extraction(base_url, prescription_text=None):
    """Test the medicine extraction endpoint"""
    print("\n💊 Testing Medicine Extraction...")
    try:
        if not prescription_text:
            prescription_text = """Patient: Jane Doe
            Rx:
            1. Amoxicillin 500mg - Take 1 tablet twice daily for 7 days
            2. Ibuprofen 400mg - Take 1 tablet as needed for pain
            3. Vitamin D3 1000 IU - Take 1 tablet daily with food
            """
        
        payload = {"prescription_text": prescription_text}
        response = requests.post(f"{base_url}/api/v1/extract-meds", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            medicines = data.get('medicines', [])
            print(f"✅ Medicine extraction successful")
            print(f"   Found {len(medicines)} medicines:")
            for i, medicine in enumerate(medicines, 1):
                print(f"   {i}. {medicine}")
            return True
        else:
            print(f"❌ Medicine extraction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Medicine extraction error: {e}")
        return False

def test_chat_endpoint(base_url):
    """Test the chat endpoint"""
    print("\n💬 Testing Chat Endpoint...")
    try:
        payload = {
            "message": "What is Amoxicillin used for?",
            "context": "Patient is asking about antibiotic medication"
        }
        response = requests.post(f"{base_url}/api/v1/chat", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat response successful")
            print(f"   Response length: {len(data.get('response', ''))} characters")
            print(f"   Sample response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def test_docs_endpoint(base_url):
    """Test if API documentation is accessible"""
    print("\n📚 Testing API Documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API documentation accessible")
            return True
        else:
            print(f"❌ API docs not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test-railway-deployment.py <railway_url>")
        print("Example: python test-railway-deployment.py https://deadpool-production.up.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    print(f"🚀 Testing Railway deployment at: {base_url}")
    print("=" * 60)
    
    results = {
        'health': False,
        'ocr': False,
        'medicine_extraction': False,
        'chat': False,
        'docs': False
    }
    
    # Test all endpoints
    results['health'] = test_health_endpoint(base_url)
    
    ocr_success, extracted_text = test_ocr_endpoint(base_url)
    results['ocr'] = ocr_success
    
    # Use extracted text for medicine extraction if available
    results['medicine_extraction'] = test_medicine_extraction(base_url, extracted_text)
    
    results['chat'] = test_chat_endpoint(base_url)
    results['docs'] = test_docs_endpoint(base_url)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Railway deployment is fully functional.")
        exit_code = 0
    elif passed >= total * 0.7:  # 70% pass rate
        print("⚠️ Most tests passed. Check failed tests and environment variables.")
        exit_code = 1
    else:
        print("❌ Multiple tests failed. Check your deployment and configuration.")
        exit_code = 2
    
    print("\n🔧 Next steps:")
    if not results['medicine_extraction'] or not results['chat']:
        print("   - Set OPENAI_API_KEY in Railway environment variables")
    if not results['ocr']:
        print("   - Verify Tesseract installation in Docker container")
    if not results['docs']:
        print("   - Check if FastAPI docs are enabled in production")
    
    print(f"\n📖 For detailed setup instructions, see: RAILWAY_ENV_CONFIG.md")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()