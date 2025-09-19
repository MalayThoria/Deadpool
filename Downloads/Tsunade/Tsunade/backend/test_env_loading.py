#!/usr/bin/env python3
"""
Test script to verify environment variable loading and OpenAI API key configuration
"""

import os
import sys
from dotenv import load_dotenv

def test_env_loading():
    """Test if environment variables are loaded correctly"""
    print("🔍 Testing Environment Variable Loading...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if OpenAI API key is loaded
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"📋 Environment Variables Status:")
    print(f"   OPENAI_API_KEY: {'✅ Loaded' if openai_key else '❌ Not Found'}")
    
    if openai_key:
        # Mask the key for security (show first 10 and last 4 characters)
        masked_key = f"{openai_key[:10]}...{openai_key[-4:]}" if len(openai_key) > 14 else "***"
        print(f"   Key Preview: {masked_key}")
        print(f"   Key Length: {len(openai_key)} characters")
        
        # Check if it's the placeholder key
        if "placeholder" in openai_key.lower():
            print("   ⚠️  WARNING: Still using placeholder key!")
            return False
        else:
            print("   ✅ Real API key detected")
            return True
    else:
        print("   ❌ OpenAI API key not found in environment")
        return False

def test_other_env_vars():
    """Test other important environment variables"""
    print("\n🔍 Testing Other Environment Variables...")
    print("=" * 50)
    
    important_vars = [
        'JWT_SECRET_KEY',
        'DB_HOST',
        'ENVIRONMENT',
        'DEBUG'
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        status = "✅ Loaded" if value else "❌ Not Found"
        print(f"   {var}: {status}")

if __name__ == "__main__":
    print("🚀 Environment Loading Test")
    print("=" * 50)
    
    # Test environment loading
    env_success = test_env_loading()
    test_other_env_vars()
    
    print("\n" + "=" * 50)
    if env_success:
        print("✅ Environment configuration is ready!")
        sys.exit(0)
    else:
        print("❌ Environment configuration has issues!")
        sys.exit(1)