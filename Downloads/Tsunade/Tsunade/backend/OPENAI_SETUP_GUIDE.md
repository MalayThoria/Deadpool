# OpenAI API Setup Guide

## 🚨 Current Issue
The OpenAI verification is currently unavailable because the API key is not properly configured. The system is using a placeholder value instead of a real API key.

## 🔍 Root Cause Analysis

### 1. **Placeholder API Key**
- **Current Value**: `sk-your-actual-openai-api-key-here`
- **Issue**: This is a template placeholder, not a real API key
- **Location**: `backend/.env` file, line 37

### 2. **GPT Processor Validation**
The system correctly detects invalid API keys and sets `client = None`, which triggers fallback responses.

## 🛠️ Step-by-Step Solution

### Step 1: Obtain a Valid OpenAI API Key

1. **Visit OpenAI Platform**: Go to [platform.openai.com](https://platform.openai.com) <mcreference link="https://medium.com/@duncanrogoff/how-to-get-your-openai-api-key-in-2024-the-complete-guide-6b52d82c7362" index="5">5</mcreference>
   - **Note**: Do NOT use chatgpt.com - use the developer platform

2. **Sign Up/Login**: Create an account or log in to your existing OpenAI account

3. **Navigate to API Keys**: Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys) <mcreference link="https://platform.openai.com/api-keys" index="3">3</mcreference>

4. **Create New API Key**:
   - Click "Create new secret key"
   - Give it a descriptive name (e.g., "RX Assistant App")
   - Copy the key immediately (you won't be able to see it again)

5. **Set Up Billing**: Ensure you have billing configured in your OpenAI account
   - Go to Settings > Billing
   - Add a payment method
   - Consider setting usage limits

### Step 2: Update Configuration

1. **Edit the .env file**:
   ```bash
   # Replace this line in backend/.env:
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   
   # With your real API key:
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

2. **Verify API Key Format**:
   - Must start with `sk-`
   - Should be approximately 51 characters long
   - Contains alphanumeric characters and hyphens

### Step 3: Test the Configuration

1. **Run the diagnostic script**:
   ```bash
   cd backend
   python test_openai_connection.py
   ```

2. **Expected successful output**:
   ```
   🔍 OpenAI API Connection Diagnostics
   ==================================================
   1. API Key Status:
      ✅ API Key found: sk-proj-xx...xxxx
   2. OpenAI Library:
      ✅ OpenAI library imported successfully
   3. Client Initialization:
      ✅ OpenAI client created successfully
   4. API Connection Test:
      ✅ Successfully connected to OpenAI API
      📋 Available models: gpt-4, gpt-3.5-turbo, ...
   ```

### Step 4: Restart the Server

1. **Stop the current server** (if running):
   - Press `Ctrl+C` in the terminal running the server

2. **Restart the server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Verify successful initialization**:
   Look for this message in the server logs:
   ```
   OpenAI client initialized successfully
   ```

## 🔧 Troubleshooting Common Issues

### Issue 1: Authentication Error
**Error**: `Authentication failed` or `Unauthorized`
**Solution**: 
- Verify the API key is correct
- Check if the key has been revoked
- Ensure no extra spaces or characters

### Issue 2: Billing/Quota Error
**Error**: `You exceeded your current quota`
**Solution**:
- Add billing information to your OpenAI account
- Check usage limits and increase if needed
- Verify payment method is valid

### Issue 3: Network Connection Error
**Error**: `Connection failed` or `Network error`
**Solution**:
- Check internet connectivity
- Verify firewall settings
- Try again after a few minutes

## 🧪 Testing After Setup

### 1. Test Individual Endpoints
```bash
# Test medicine information
curl -X POST "http://localhost:8000/api/v1/med-info" \
  -H "Content-Type: application/json" \
  -d '{"medicines": ["Paracetamol"]}'

# Test chat functionality
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the side effects of aspirin?"}'
```

### 2. Test via Frontend
1. Open http://localhost:3000
2. Upload a prescription image
3. Try asking questions in the chat
4. Verify you get AI-powered responses instead of fallback messages

## 🔒 Security Best Practices

1. **Keep API Key Secret**: <mcreference link="https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety" index="1">1</mcreference>
   - Never commit API keys to version control
   - Use environment variables
   - Rotate keys regularly

2. **Set Usage Limits**:
   - Configure monthly spending limits
   - Monitor usage regularly
   - Set up billing alerts

3. **Restrict API Key Permissions**:
   - Only grant necessary permissions
   - Consider using project-specific keys

## 📊 Expected Behavior After Fix

### Before Fix (Current State):
- Chat returns: "I'm sorry, but I'm currently unable to process your question..."
- Medicine info returns: "I apologize, but I'm currently unable to process..."
- OCR works but AI features are disabled

### After Fix:
- Chat provides intelligent responses about medications
- Medicine info returns detailed information and recommendations
- Full AI-powered prescription analysis
- Exercise and dietary recommendations work

## 🆘 Need Help?

If you continue to experience issues:

1. **Check the diagnostic script output** for specific error messages
2. **Verify your OpenAI account status** at platform.openai.com
3. **Review server logs** for detailed error information
4. **Ensure all dependencies are installed** with `pip install -r requirements.txt`

The system is designed to gracefully handle missing API keys with fallback responses, so the application will continue to work with basic functionality even without OpenAI integration.