import requests
import os

def test_ocr_endpoint():
    """Test the OCR endpoint with a prescription image"""
    
    # Check if test image exists
    image_path = "test_prescription.jpg"
    if not os.path.exists(image_path):
        print(f"Test image {image_path} not found")
        return
    
    # API endpoint
    url = "http://localhost:8000/api/v1/ocr"
    
    try:
        # Open and send the image file
        with open(image_path, 'rb') as f:
            files = {'file': (image_path, f, 'image/jpeg')}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("\n✅ OCR Test Successful!")
                print(f"Extracted Text: {result.get('text', '')[:200]}...")
            else:
                print(f"\n❌ OCR Failed: {result.get('message')}")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_ocr_endpoint()