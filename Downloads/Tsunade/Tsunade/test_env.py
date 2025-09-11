import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# Check what API key is loaded
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"API Key loaded: {api_key[:20]}...{api_key[-10:]}")
    print(f"API Key ends with: {api_key[-10:]}")
else:
    print("No API key found in environment")

# Also check from backend directory
os.chdir('backend')
load_dotenv('.env')
api_key2 = os.getenv('OPENAI_API_KEY')
if api_key2:
    print(f"Backend API Key loaded: {api_key2[:20]}...{api_key2[-10:]}")
    print(f"Backend API Key ends with: {api_key2[-10:]}")
else:
    print("No backend API key found in environment")