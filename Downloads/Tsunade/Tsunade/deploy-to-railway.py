#!/usr/bin/env python3
"""
Railway Deployment Script
Deploys the backend to Railway using the provided token and project information.
"""

import os
import requests
import json
import subprocess
import sys
from pathlib import Path

# Railway project information
RAILWAY_TOKEN = "2c0a4ab3-5ab2-43f3-9020-2f0c4f8d2df5"
PROJECT_ID = "6aef17ec-3be6-4494-aedf-605e3e9ce4ca"
PROJECT_NAME = "charismatic-light"
INVITE_URL = "https://railway.com/invite/Oj4C7QjMvRR"

# Railway API endpoints
RAILWAY_API_BASE = "https://backboard.railway.app/graphql"

def check_railway_cli():
    """Check if Railway CLI is installed and working"""
    try:
        result = subprocess.run(["railway", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Railway CLI installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Railway CLI not working properly")
            return False
    except FileNotFoundError:
        print("❌ Railway CLI not found")
        return False

def deploy_with_cli():
    """Attempt to deploy using Railway CLI"""
    print("\n🚀 Attempting deployment with Railway CLI...")
    
    # Set environment variable
    os.environ["RAILWAY_TOKEN"] = RAILWAY_TOKEN
    
    try:
        # Try to deploy directly
        print("Deploying to Railway...")
        result = subprocess.run(
            ["railway", "up", "--detach"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Deployment successful!")
            print(result.stdout)
            return True
        else:
            print("❌ Deployment failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ CLI deployment error: {e}")
        return False

def create_railway_toml():
    """Create railway.toml configuration file"""
    railway_config = {
        "build": {
            "builder": "DOCKERFILE",
            "dockerfilePath": "Dockerfile"
        },
        "deploy": {
            "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "healthcheckPath": "/health",
            "healthcheckTimeout": 100,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    with open("railway.toml", "w") as f:
        # Convert to TOML format manually
        f.write("[build]\n")
        f.write('builder = "DOCKERFILE"\n')
        f.write('dockerfilePath = "Dockerfile"\n\n')
        f.write("[deploy]\n")
        f.write('startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"\n')
        f.write('healthcheckPath = "/health"\n')
        f.write('healthcheckTimeout = 100\n')
        f.write('restartPolicyType = "ON_FAILURE"\n')
        f.write('restartPolicyMaxRetries = 10\n')
    
    print("✅ Created railway.toml configuration")

def print_manual_instructions():
    """Print manual deployment instructions"""
    print("\n" + "="*60)
    print("📋 MANUAL DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    print(f"\n🔗 Project Information:")
    print(f"   Name: {PROJECT_NAME}")
    print(f"   ID: {PROJECT_ID}")
    print(f"   Invite URL: {INVITE_URL}")
    print(f"   Token: {RAILWAY_TOKEN}")
    
    print(f"\n🌐 Web Interface Deployment:")
    print(f"   1. Visit: {INVITE_URL}")
    print(f"   2. Accept the invitation to join the project")
    print(f"   3. Go to Railway dashboard")
    print(f"   4. Select the '{PROJECT_NAME}' project")
    print(f"   5. Click 'New Service' → 'GitHub Repo'")
    print(f"   6. Connect your repository")
    print(f"   7. Set Root Directory: '/' (project root)")
    print(f"   8. Railway will auto-detect the Dockerfile")
    
    print(f"\n⚙️ Environment Variables to Set:")
    env_vars = [
        "OPENAI_API_KEY=your-openai-api-key",
        "JWT_SECRET_KEY=your-super-secret-jwt-key",
        "JWT_ALGORITHM=HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30",
        "ENVIRONMENT=production",
        "DEBUG=false",
        "DATABASE_URL=postgresql://...",
        "REDIS_URL=redis://...",
        "MONGO_URL=mongodb://..."
    ]
    
    for var in env_vars:
        print(f"   {var}")
    
    print(f"\n🚀 Alternative CLI Commands (if authentication works):")
    print(f"   export RAILWAY_TOKEN={RAILWAY_TOKEN}")
    print(f"   railway link {PROJECT_ID}")
    print(f"   railway up")
    
    print(f"\n📊 Testing Deployment:")
    print(f"   Once deployed, your API will be available at:")
    print(f"   https://{PROJECT_NAME}-production.up.railway.app")
    print(f"   ")
    print(f"   Test endpoints:")
    print(f"   - GET /health")
    print(f"   - GET /docs")
    print(f"   - POST /api/v1/ocr")
    print(f"   - POST /api/v1/extract-meds")
    
    print("\n" + "="*60)

def main():
    """Main deployment function"""
    print("🚀 Railway Deployment Script")
    print(f"Project: {PROJECT_NAME} ({PROJECT_ID})")
    print(f"Token: {RAILWAY_TOKEN[:8]}...")
    
    # Check if we're in the right directory
    if not Path("Dockerfile").exists():
        print("❌ Dockerfile not found. Make sure you're in the project root.")
        return False
    
    # Create railway configuration
    create_railway_toml()
    
    # Check Railway CLI
    cli_available = check_railway_cli()
    
    if cli_available:
        # Try CLI deployment
        success = deploy_with_cli()
        if success:
            print("\n✅ Deployment completed successfully!")
            return True
    
    # If CLI fails, provide manual instructions
    print("\n⚠️ CLI deployment failed or unavailable.")
    print_manual_instructions()
    
    return False

if __name__ == "__main__":
    main()