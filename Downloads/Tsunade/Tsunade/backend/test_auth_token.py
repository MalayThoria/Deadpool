#!/usr/bin/env python3
"""
Test script to generate a test authentication token for endpoint testing
"""
import os
import sys
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# JWT Configuration (same as in auth.py)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

def generate_test_token():
    """Generate a test JWT token for API testing"""
    
    # Test user payload
    payload = {
        "sub": "1",  # User ID
        "email": "test@example.com",
        "role": "PATIENT",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24)  # 24 hour expiration
    }
    
    # Generate token
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    print("=== Test Authentication Token ===")
    print(f"Token: {token}")
    print(f"Secret Key: {SECRET_KEY}")
    print(f"Algorithm: {JWT_ALGORITHM}")
    print(f"Expires: {payload['exp']}")
    print("\nTo use this token, add the following header to your requests:")
    print(f"Authorization: Bearer {token}")
    
    return token

if __name__ == "__main__":
    generate_test_token()