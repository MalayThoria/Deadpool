#!/usr/bin/env python3
"""
Test script to verify OpenAI API connection and functionality
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from openai import OpenAI

async def test_openai_connection():
    """Test OpenAI API connection with the new key"""
    print("🔍 Testing OpenAI API Connection...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found in environment")
        return False
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        print("📡 Testing API connection...")
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, API connection successful!' in exactly those words."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        # Check response
        if response and response.choices:
            message = response.choices[0].message.content.strip()
            print(f"✅ API Response: {message}")
            
            # Verify the response contains expected text
            if "Hello, API connection successful!" in message:
                print("✅ OpenAI API connection is working perfectly!")
                return True
            else:
                print("⚠️  API responded but with unexpected content")
                return True  # Still working, just different response
        else:
            print("❌ No response from OpenAI API")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {str(e)}")
        return False

async def test_openai_models():
    """Test available OpenAI models"""
    print("\n🔍 Testing Available Models...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    try:
        client = OpenAI(api_key=api_key)
        
        # List available models
        models = client.models.list()
        
        # Filter for GPT models
        gpt_models = [model.id for model in models.data if 'gpt' in model.id.lower()]
        
        print(f"✅ Found {len(gpt_models)} GPT models:")
        for model in gpt_models[:5]:  # Show first 5
            print(f"   - {model}")
        
        if len(gpt_models) > 5:
            print(f"   ... and {len(gpt_models) - 5} more")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to list models: {str(e)}")
        return False

async def test_chat_functionality():
    """Test chat functionality specifically"""
    print("\n🔍 Testing Chat Functionality...")
    print("=" * 50)
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Test a medical-related query (relevant to the app)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant. Provide brief, accurate information."},
                {"role": "user", "content": "What is aspirin commonly used for? Give a brief answer."}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        if response and response.choices:
            message = response.choices[0].message.content.strip()
            print(f"✅ Medical Query Response: {message[:100]}...")
            print("✅ Chat functionality is working!")
            return True
        else:
            print("❌ No response from chat API")
            return False
            
    except Exception as e:
        print(f"❌ Chat functionality test failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🚀 OpenAI API Connection Test")
    print("=" * 50)
    
    # Run all tests
    connection_test = await test_openai_connection()
    models_test = await test_openai_models()
    chat_test = await test_chat_functionality()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Connection Test: {'✅ PASS' if connection_test else '❌ FAIL'}")
    print(f"   Models Test: {'✅ PASS' if models_test else '❌ FAIL'}")
    print(f"   Chat Test: {'✅ PASS' if chat_test else '❌ FAIL'}")
    
    all_passed = connection_test and models_test and chat_test
    
    if all_passed:
        print("\n🎉 All OpenAI API tests passed! The API key is working perfectly.")
        return True
    else:
        print("\n❌ Some OpenAI API tests failed. Please check the API key and connection.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)