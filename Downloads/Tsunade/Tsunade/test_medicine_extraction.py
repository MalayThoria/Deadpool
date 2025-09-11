import requests
import json

def test_medicine_extraction():
    """Test the medicine extraction endpoint"""
    
    # Sample prescription text (from OCR result)
    prescription_text = """Test Prescription
Patient: John Doe
Medication: Amoxicillin 500mg
Take 1 tablet 3 times daily
Dr. Smith"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/extract-meds"
    
    try:
        # Send the prescription text
        payload = {"text": prescription_text}
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Medicine Extraction Test Successful!")
            print(f"Extracted Medicines: {result}")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Request failed: {str(e)}")

def test_medicine_info():
    """Test the medicine information endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/med-info"
    
    try:
        # Request info for Amoxicillin
        payload = {"medicines": ["Amoxicillin"]}
        response = requests.post(url, json=payload)
        
        print(f"\nMedicine Info Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Medicine Info Test Successful!")
            print(f"Medicine Information: {result}")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Request failed: {str(e)}")

if __name__ == "__main__":
    print("Testing Medicine Extraction...")
    test_medicine_extraction()
    
    print("\n" + "="*50)
    print("Testing Medicine Information...")
    test_medicine_info()