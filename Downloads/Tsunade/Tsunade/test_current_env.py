import os
from dotenv import load_dotenv

# Test current environment loading
print("=== Testing Environment Loading ===")
print(f"Current working directory: {os.getcwd()}")

# Test loading from different locations
print("\n1. Before loading any .env:")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT_SET')[-10:] if os.getenv('OPENAI_API_KEY') else 'NOT_SET'}")

# Load from root
load_dotenv('.env')
print("\n2. After loading root .env:")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT_SET')[-10:] if os.getenv('OPENAI_API_KEY') else 'NOT_SET'}")

# Load from backend
load_dotenv('backend/.env')
print("\n3. After loading backend/.env:")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT_SET')[-10:] if os.getenv('OPENAI_API_KEY') else 'NOT_SET'}")

# Test GPT processor initialization
print("\n=== Testing GPT Processor ===")
try:
    from backend.utils.gpt import GPTProcessor
    processor = GPTProcessor()
    print("✅ GPT Processor initialized successfully")
except Exception as e:
    print(f"❌ GPT Processor failed: {e}")