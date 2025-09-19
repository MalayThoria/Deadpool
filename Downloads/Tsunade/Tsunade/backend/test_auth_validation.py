#!/usr/bin/env python3
"""
Test script to validate authentication system and token generation
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import jwt
import requests

# Load environment variables
load_dotenv('.env')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.auth import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_SECONDS

async def test_auth_system():
    """Test the authentication system"""
    
    print("=== Authentication System Test ===")
    print(f"Secret Key: {SECRET_KEY}")
    print(f"JWT Algorithm: {JWT_ALGORITHM}")
    print(f"JWT Expiration: {JWT_EXPIRATION_SECONDS} seconds")
    
    # Test 1: Generate token using same method as auth system
    print("\n1. Testing Token Generation:")
    
    payload = {
        "sub": "1",  # User ID as string (FastAPI Users format)
        "aud": ["fastapi-users:auth"],  # FastAPI Users audience
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION_SECONDS)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    print(f"Generated token: {token}")
    
    # Test 2: Validate token
    print("\n2. Testing Token Validation:")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM], audience=["fastapi-users:auth"])
        print(f"Token validation successful: {decoded}")
    except Exception as e:
        print(f"Token validation failed: {e}")
    
    # Test 3: Test login endpoint
    print("\n3. Testing Login Endpoint:")
    try:
        response = requests.post(
            "http://localhost:8000/auth/jwt/login",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text}")
    except Exception as e:
        print(f"Login test failed: {e}")
    
    # Test 4: Test protected endpoint with generated token
    print("\n4. Testing Protected Endpoint:")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/analyze-prescription",
            json={
                "prescription_text": "Test prescription",
                "auto_update_profile": False
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        print(f"Protected endpoint status: {response.status_code}")
        print(f"Protected endpoint response: {response.text}")
    except Exception as e:
        print(f"Protected endpoint test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_system())