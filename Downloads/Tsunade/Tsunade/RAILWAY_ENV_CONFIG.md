# Railway Environment Configuration Guide

## 🔧 Required Environment Variables

To make your deployed Railway application fully functional with Tesseract OCR and ChatGPT integrations, you need to configure the following environment variables in your Railway project dashboard.

### 🚀 Access Railway Dashboard
1. Go to: https://railway.com/project/6aef17ec-3be6-4494-aedf-605e3e9ce4ca
2. Select your service (Deadpool)
3. Go to **Variables** tab

### 📝 Required Variables

#### Core API Configuration
```bash
# OpenAI API Key (CRITICAL - Required for ChatGPT functionality)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Application Environment
ENVIRONMENT=production
DEBUG=false

# Port Configuration (Railway sets this automatically)
PORT=8000
```

#### CORS Configuration
```bash
# Allow frontend domains to access the API
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://your-frontend-domain.netlify.app,http://localhost:3000
```

#### JWT Configuration (if using authentication)
```bash
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Database Configuration (Optional)
```bash
# PostgreSQL (if using Railway's PostgreSQL addon)
DATABASE_URL=postgresql://username:password@host:port/database

# Redis (if using Railway's Redis addon)
REDIS_URL=redis://username:password@host:port

# MongoDB (if using external MongoDB)
MONGO_URL=mongodb://username:password@host:port/database
```

#### Tesseract OCR Configuration
```bash
# Tesseract data path (automatically set in Docker)
TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/
```

#### Error Tracking (Optional)
```bash
# Sentry DSN for error tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

## 🔑 Getting Your OpenAI API Key

1. **Sign up/Login** to OpenAI: https://platform.openai.com/
2. **Navigate** to API Keys: https://platform.openai.com/account/api-keys
3. **Create** a new secret key
4. **Copy** the key (starts with `sk-`)
5. **Add** it to Railway as `OPENAI_API_KEY`

⚠️ **Important**: Never share your API key publicly or commit it to version control!

## 🚀 Setting Variables in Railway

### Method 1: Railway Dashboard (Recommended)
1. Go to your Railway project dashboard
2. Select your service
3. Click **Variables** tab
4. Click **New Variable**
5. Enter variable name and value
6. Click **Add**
7. Your service will automatically redeploy

### Method 2: Railway CLI (if working)
```bash
# Set individual variables
railway variables set OPENAI_API_KEY=sk-your-key-here
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false

# Set multiple variables from file
railway variables set --from-file .env.production
```

## 🧪 Testing After Configuration

After setting the environment variables, test your deployment:

```bash
# Test health endpoint
curl https://deadpool-production.up.railway.app/health

# Test OCR endpoint (requires image upload)
# Use the test script:
python test-railway-deployment.py https://deadpool-production.up.railway.app
```

## 🔍 Troubleshooting

### Common Issues:

1. **OpenAI API Key Not Working**
   - Verify the key starts with `sk-`
   - Check you have credits in your OpenAI account
   - Ensure the key has the correct permissions

2. **OCR Not Working**
   - Check Tesseract is installed in Docker (should be automatic with updated Dockerfile)
   - Verify image format is supported (JPEG, PNG)
   - Check image quality and text clarity

3. **CORS Errors**
   - Add your frontend domain to `CORS_ORIGINS`
   - Ensure the format is correct (comma-separated, no spaces)
   - Include both production and development URLs

4. **Service Not Starting**
   - Check Railway logs for error messages
   - Verify all required environment variables are set
   - Ensure no syntax errors in variable values

## 📊 Monitoring

### Railway Dashboard
- **Logs**: View real-time application logs
- **Metrics**: Monitor CPU, memory, and network usage
- **Deployments**: Track deployment history and status

### Health Check
Your application includes a health endpoint that reports:
- Service status
- Tesseract availability
- Basic system information

Access it at: `https://your-service.up.railway.app/health`

## 🔄 Redeployment

After updating environment variables:
1. Railway automatically redeploys your service
2. Wait for deployment to complete (check Deployments tab)
3. Test the endpoints to verify functionality
4. Monitor logs for any errors

---

**Next Steps:**
1. Set the `OPENAI_API_KEY` variable
2. Configure CORS origins for your frontend
3. Test all endpoints
4. Update frontend configuration to use Railway backend
5. Deploy frontend and test end-to-end integration