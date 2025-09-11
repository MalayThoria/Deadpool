# Frontend Railway Integration Guide

## Current Frontend Configuration

The frontend is configured to use environment variables for API endpoints:
- **API Base URL**: `process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'`
- **Proxy Configuration**: `"proxy": "http://localhost:8000"` in package.json

## Step 1: Update Environment Variables

### For Local Development
Create a `.env.local` file in the frontend directory:

```env
# Frontend Environment Variables
REACT_APP_API_URL=https://your-railway-app.railway.app/api/v1
REACT_APP_API_BASE_URL=https://your-railway-app.railway.app
```

### For Production Deployment (Vercel/Netlify)
Set these environment variables in your deployment platform:

```env
REACT_APP_API_URL=https://your-railway-app.railway.app/api/v1
REACT_APP_API_BASE_URL=https://your-railway-app.railway.app
```

## Step 2: Update Package.json (Optional)

For development, you may want to remove or update the proxy:

```json
{
  "name": "rx-assistant-frontend",
  "version": "1.0.0",
  "private": true,
  // Remove or comment out the proxy line for Railway deployment
  // "proxy": "http://localhost:8000"
}
```

## Step 3: Update CORS Configuration in Backend

Ensure your Railway backend includes your frontend domain in CORS settings:

```env
# In Railway backend environment variables
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000,https://your-railway-app.railway.app
```

## Step 4: Test API Endpoints

The frontend makes calls to these endpoints:

1. **OCR Endpoint**: `POST /api/v1/ocr`
   - Uploads prescription images
   - Extracts text using Tesseract

2. **Medicine Extraction**: `POST /api/v1/extract-meds`
   - Identifies medicines from extracted text
   - Provides corrections for misspelled medicine names

3. **Medicine Information**: `POST /api/v1/med-info`
   - Gets detailed information about medicines
   - Provides usage instructions and warnings

4. **Chat Endpoint**: `POST /api/v1/chat`
   - Handles general health-related questions
   - Provides AI-powered responses

## Step 5: Frontend Deployment Options

### Option A: Vercel (Recommended)

1. **Connect Repository**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set root directory to `frontend`

2. **Build Settings**:
   ```
   Framework Preset: Create React App
   Build Command: npm run build
   Output Directory: build
   Install Command: npm install
   Root Directory: frontend
   ```

3. **Environment Variables**:
   ```
   REACT_APP_API_URL=https://your-railway-app.railway.app/api/v1
   REACT_APP_API_BASE_URL=https://your-railway-app.railway.app
   ```

### Option B: Netlify

1. **Connect Repository**:
   - Go to [netlify.com](https://netlify.com)
   - Import your GitHub repository

2. **Build Settings**:
   ```
   Base Directory: frontend
   Build Command: npm run build
   Publish Directory: frontend/build
   ```

3. **Environment Variables**:
   ```
   REACT_APP_API_URL=https://your-railway-app.railway.app/api/v1
   REACT_APP_API_BASE_URL=https://your-railway-app.railway.app
   ```

## Step 6: Testing Integration

### Local Testing
1. Start your Railway backend
2. Update `.env.local` with Railway URL
3. Run `npm start` in frontend directory
4. Test all features:
   - File upload (OCR)
   - Medicine extraction
   - Chat functionality

### Production Testing
1. Deploy frontend with Railway backend URL
2. Test all API endpoints
3. Check browser console for CORS errors
4. Verify all features work end-to-end

## Step 7: Troubleshooting

### Common Issues:

1. **CORS Errors**:
   ```
   Access to XMLHttpRequest at 'https://railway-app.railway.app/api/v1/ocr' 
   from origin 'https://frontend-app.vercel.app' has been blocked by CORS policy
   ```
   **Solution**: Add frontend domain to backend CORS settings

2. **Environment Variables Not Loading**:
   ```
   API calls going to localhost instead of Railway URL
   ```
   **Solution**: Ensure variables start with `REACT_APP_` and restart dev server

3. **Build Failures**:
   ```
   Module not found errors during build
   ```
   **Solution**: Check all dependencies are in package.json

4. **API Endpoint 404 Errors**:
   ```
   POST https://railway-app.railway.app/api/v1/ocr 404 (Not Found)
   ```
   **Solution**: Verify Railway backend is deployed and endpoints are correct

## Step 8: Automated Update Script

Create a PowerShell script to update frontend configuration:

```powershell
# update-frontend-config.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$RailwayUrl
)

$envContent = @"
REACT_APP_API_URL=$RailwayUrl/api/v1
REACT_APP_API_BASE_URL=$RailwayUrl
"@

$envContent | Out-File -FilePath "frontend\.env.local" -Encoding UTF8

Write-Host "Frontend configuration updated!" -ForegroundColor Green
Write-Host "API URL: $RailwayUrl/api/v1" -ForegroundColor Yellow
Write-Host "Base URL: $RailwayUrl" -ForegroundColor Yellow
Write-Host "" 
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test locally: cd frontend && npm start"
Write-Host "2. Deploy to Vercel/Netlify with these environment variables"
Write-Host "3. Update backend CORS to include your frontend domain"
```

## Expected Results

After successful integration:

✅ **Frontend**: Deployed and accessible
✅ **Backend**: Railway deployment responding
✅ **API Integration**: All endpoints working
✅ **File Upload**: OCR functionality working
✅ **Medicine Extraction**: AI processing working
✅ **Chat**: AI chat responses working
✅ **CORS**: No cross-origin errors
✅ **Error Handling**: Proper error messages displayed

---

**Remember**: Replace `your-railway-app.railway.app` with your actual Railway deployment URL!