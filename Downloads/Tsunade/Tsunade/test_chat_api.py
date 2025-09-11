import requests
import json

def test_chat_api():
    """Test the ChatGPT API endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/chat"
    
    try:
        # Send a test message
        payload = {
            "message": "Hello, can you help me with my medication?",
            "conversation_id": "test-123"
        }
        
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ ChatGPT API Test Successful!")
            print(f"Response: {result}")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error Details: {error_detail}")
            except:
                print(f"Error Text: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Request failed: {str(e)}")

if __name__ == "__main__":
    print("Testing ChatGPT API...")
    test_chat_api()