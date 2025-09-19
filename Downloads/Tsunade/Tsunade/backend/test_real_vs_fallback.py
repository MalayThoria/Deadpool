#!/usr/bin/env python3
"""
Test script to verify that real OpenAI responses are being used instead of fallback mechanisms
"""

import requests
import json
import time

def test_chat_response_quality():
    """Test if chat responses are from OpenAI or fallback"""
    print("🔍 Testing Chat Response Quality...")
    print("=" * 50)
    
    url = "http://localhost:8000/api/v1/chat"
    
    # Test with a specific medical question that would have different responses
    test_data = {
        "message": "What are the side effects of ibuprofen?",
        "conversation_id": "test_fallback_check"
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            print(f"✅ Response received (Status: {response.status_code})")
            print(f"📝 Response preview: {data.get('response', '')[:100]}...")
            
            # Check for fallback indicators
            fallback_indicators = [
                "i'm currently operating in fallback mode",
                "fallback response",
                "api is not available",
                "placeholder response",
                "hello there! i'm here to help"
            ]
            
            is_fallback = any(indicator in response_text for indicator in fallback_indicators)
            
            if is_fallback:
                print("⚠️  FALLBACK DETECTED: Response appears to be from fallback mechanism")
                return False
            else:
                print("✅ REAL API: Response appears to be from OpenAI API")
                return True
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_medicine_extraction_quality():
    """Test if medicine extraction is using real OpenAI or fallback"""
    print("\n🔍 Testing Medicine Extraction Quality...")
    print("=" * 50)
    
    url = "http://localhost:8000/api/v1/extract-meds"
    
    # Test with a complex prescription that would challenge fallback
    test_data = {
        "prescription_text": "Patient should take Metformin 500mg twice daily with meals, and Lisinopril 10mg once daily in the morning"
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            medicines = data.get('medicines', [])
            
            print(f"✅ Response received (Status: {response.status_code})")
            print(f"📊 Extracted {len(medicines)} medicines")
            
            # Check quality of extraction
            if len(medicines) >= 2:  # Should extract both medicines
                print("✅ REAL API: Successfully extracted multiple medicines")
                for med in medicines:
                    print(f"   - {med.get('original')} → {med.get('corrected')}")
                return True
            else:
                print("⚠️  FALLBACK SUSPECTED: Limited extraction capability")
                return False
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_medicine_info_quality():
    """Test if medicine information is using real OpenAI or fallback"""
    print("\n🔍 Testing Medicine Information Quality...")
    print("=" * 50)
    
    url = "http://localhost:8000/api/v1/med-info"
    
    # Test with a specific medicine (correct format)
    test_data = {
        "medicines": ["Metformin"]
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            medicines_info = data.get('medicines_info', [])
            
            print(f"✅ Response received (Status: {response.status_code})")
            print(f"📊 Extracted {len(medicines_info)} medicine info entries")
            
            # Check quality of information
            if medicines_info and len(medicines_info) > 0:
                med_info = medicines_info[0]
                has_detailed_info = (
                    med_info.get('description') and 
                    med_info.get('side_effects') and 
                    med_info.get('dosage') and
                    len(med_info.get('description', '')) > 50  # Detailed description
                )
                
                if has_detailed_info:
                    print("✅ REAL API: Detailed medicine information provided")
                    print(f"   Name: {med_info.get('name')}")
                    print(f"   Description: {med_info.get('description', '')[:50]}...")
                    return True
                else:
                    print("⚠️  FALLBACK SUSPECTED: Limited information provided")
                    return False
            else:
                print("⚠️  FALLBACK SUSPECTED: No medicine information returned")
                return False
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Real vs Fallback Response Test")
    print("=" * 50)
    
    # Run all tests
    chat_real = test_chat_response_quality()
    extraction_real = test_medicine_extraction_quality()
    info_real = test_medicine_info_quality()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Chat API: {'✅ REAL' if chat_real else '⚠️  FALLBACK'}")
    print(f"   Medicine Extraction: {'✅ REAL' if extraction_real else '⚠️  FALLBACK'}")
    print(f"   Medicine Information: {'✅ REAL' if info_real else '⚠️  FALLBACK'}")
    
    real_count = sum([chat_real, extraction_real, info_real])
    
    print(f"\n📈 Real API Usage: {real_count}/3 endpoints ({real_count/3*100:.1f}%)")
    
    if real_count == 3:
        print("🎉 All endpoints are using real OpenAI API!")
        return True
    elif real_count >= 2:
        print("✅ Most endpoints are using real OpenAI API")
        return True
    else:
        print("⚠️  Most endpoints are still using fallback mechanisms")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)