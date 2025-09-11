import os
from dotenv import load_dotenv

print("=== Server Environment Debug ===")
print(f"Current working directory: {os.getcwd()}")

# Load environment variables in the same order as main.py
load_dotenv('.env')  # This should load from backend/.env
load_dotenv('../.env')  # This should load from root .env

api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"Loaded API key ending with: ...{api_key[-10:]}")
    print(f"Full key length: {len(api_key)}")
else:
    print("No API key found")

# Check all environment variables containing 'OPENAI'
print("\nAll OPENAI environment variables:")
for key, value in os.environ.items():
    if 'OPENAI' in key.upper():
        print(f"{key}: ...{value[-10:] if value else 'empty'}")

# Test GPT processor initialization
try:
    from utils.gpt import GPTProcessor
    processor = GPTProcessor()
    print(f"\nGPT Processor initialized successfully")
    print(f"Client API key ends with: ...{processor.client.api_key[-10:] if hasattr(processor.client, 'api_key') else 'unknown'}")
except Exception as e:
    print(f"\nError initializing GPT Processor: {e}")