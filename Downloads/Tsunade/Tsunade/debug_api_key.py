import os
import sys
from pathlib import Path
from dotenv import load_dotenv

print("=== API Key Debug Information ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Check system environment
print("\n1. System Environment Variable:")
sys_key = os.environ.get('OPENAI_API_KEY')
if sys_key:
    print(f"   Found: ...{sys_key[-10:]}")
else:
    print("   Not found in system environment")

# Check without loading .env
print("\n2. Before loading .env:")
before_key = os.getenv('OPENAI_API_KEY')
if before_key:
    print(f"   Found: ...{before_key[-10:]}")
else:
    print("   Not found")

# Load root .env
print("\n3. Loading root .env:")
load_dotenv('.env')
root_key = os.getenv('OPENAI_API_KEY')
if root_key:
    print(f"   Found: ...{root_key[-10:]}")
else:
    print("   Not found")

# Load backend .env
print("\n4. Loading backend/.env:")
load_dotenv('backend/.env')
backend_key = os.getenv('OPENAI_API_KEY')
if backend_key:
    print(f"   Found: ...{backend_key[-10:]}")
else:
    print("   Not found")

# Check .env file contents directly
print("\n5. Direct file contents:")
try:
    with open('.env', 'r') as f:
        content = f.read()
        for line in content.split('\n'):
            if 'OPENAI_API_KEY' in line:
                key_part = line.split('=')[1] if '=' in line else ''
                print(f"   Root .env: ...{key_part[-10:] if key_part else 'empty'}")
except Exception as e:
    print(f"   Error reading root .env: {e}")

try:
    with open('backend/.env', 'r') as f:
        content = f.read()
        for line in content.split('\n'):
            if 'OPENAI_API_KEY' in line:
                key_part = line.split('=')[1] if '=' in line else ''
                print(f"   Backend .env: ...{key_part[-10:] if key_part else 'empty'}")
except Exception as e:
    print(f"   Error reading backend .env: {e}")

# Check if there are any .env.* files
print("\n6. Other .env files:")
for env_file in Path('.').glob('.env*'):
    print(f"   Found: {env_file}")
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if 'OPENAI_API_KEY' in line:
                    key_part = line.split('=')[1] if '=' in line else ''
                    print(f"     Contains API key: ...{key_part[-10:] if key_part else 'empty'}")
    except Exception as e:
        print(f"     Error reading {env_file}: {e}")