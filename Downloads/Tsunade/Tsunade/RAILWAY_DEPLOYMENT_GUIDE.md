# Railway Deployment Guide for Tsunade Backend

## Prerequisites
1. Railway account (sign up at https://railway.app)
2. GitHub repository with your code
3. Railway CLI installed (optional but recommended)

## Step 1: Prepare for Deployment

### 1.1 Verify Files
Ensure these files are in your project root:
- `Dockerfile` ✅ (configured for backend deployment)
- `railway.json` ✅ (updated with correct start command)
- `requirements.txt` ✅ (in root directory)
- `backend/` directory with all backend code ✅

### 1.2 Environment Variables Required
You'll need to set these in Railway:

**Essential Variables:**
```
OPENAI_API_KEY=your-openai-api-key
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
ENCRYPTION_KEY=DFxCMUpIP1afscKsU9YXelMfbr3biWez2IVCCq0QVh8=
```

**Database Variables (Railway will provide these):**
```
REDIS_URL=redis://railway-provided-url
MONGODB_URL=mongodb://railway-provided-url
MONGODB_DB_NAME=tsunade_production
```

**CORS Configuration:**
```
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://your-railway-backend.railway.app
```

## Step 2: Deploy to Railway

### Method 1: Web Interface (Recommended)

1. **Create New Project**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account if not already connected
   - Select your repository

2. **Configure Deployment**
   - Railway will automatically detect the Dockerfile
   - The `railway.json` configuration will be applied automatically
   - Wait for initial build to complete

3. **Add Environment Variables**
   - Go to your project dashboard
   - Click on "Variables" tab
   - Add all the environment variables listed above
   - **Important**: Update `OPENAI_API_KEY` with your actual key

4. **Add Database Services**
   - Click "New Service" → "Database" → "Redis"
   - Click "New Service" → "Database" → "MongoDB"
   - Railway will automatically provide connection URLs
   - Copy these URLs to your environment variables

### Method 2: Railway CLI

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set OPENAI_API_KEY=your-key
   railway variables set ENVIRONMENT=production
   # ... add other variables
   ```

## Step 3: Verify Deployment

1. **Check Deployment Status**
   - In Railway dashboard, verify the service is "Active"
   - Check logs for any errors
   - Note the public URL (e.g., `https://your-app.railway.app`)

2. **Test API Endpoints**
   ```bash
   # Health check
   curl https://your-app.railway.app/health
   
   # Test OCR endpoint
   curl -X POST https://your-app.railway.app/ocr/extract \
     -F "file=@test_prescription.jpg"
   
   # Test chat endpoint
   curl -X POST https://your-app.railway.app/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, test message"}'
   ```

## Step 4: Update Frontend Configuration

Update your frontend to use the Railway backend URL:

1. **Update API Base URL**
   - Replace `http://localhost:8000` with `https://your-app.railway.app`
   - Update in your frontend configuration files

2. **Update CORS Settings**
   - Add your frontend domain to `ALLOWED_ORIGINS` in Railway environment variables

## Step 5: Domain Configuration (Optional)

1. **Custom Domain**
   - In Railway dashboard, go to "Settings" → "Domains"
   - Add your custom domain
   - Update DNS records as instructed

## Troubleshooting

### Common Issues:

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify requirements.txt is in root directory
   - Check Railway build logs

2. **Runtime Errors**
   - Verify all environment variables are set
   - Check application logs in Railway dashboard
   - Ensure database connections are working

3. **API Not Accessible**
   - Verify the service is running
   - Check if PORT environment variable is properly used
   - Ensure firewall/security settings allow traffic

### Monitoring:
- Use Railway dashboard to monitor:
  - CPU and memory usage
  - Request logs
  - Error rates
  - Database connections

## Security Checklist

- [ ] Updated JWT_SECRET_KEY for production
- [ ] Set DEBUG=false
- [ ] Updated OPENAI_API_KEY with valid key
- [ ] Configured proper CORS origins
- [ ] Database connections use secure URLs
- [ ] No sensitive data in logs

## Next Steps

After successful deployment:
1. Test all API endpoints thoroughly
2. Update frontend to use Railway backend URL
3. Test complete frontend-backend integration
4. Set up monitoring and alerts
5. Configure backup strategies for databases

---

**Your Railway backend URL will be:** `https://[your-project-name].railway.app`

Save this URL as you'll need it to configure your frontend!