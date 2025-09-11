# Frontend Configuration Update Script for Railway Integration
# This script updates the frontend to connect to Railway backend

param(
    [Parameter(Mandatory=$false)]
    [string]$RailwayUrl
)

Write-Host "🚀 Frontend Railway Integration Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Railway URL is provided
if (-not $RailwayUrl) {
    Write-Host "Please enter your Railway backend URL:" -ForegroundColor Yellow
    Write-Host "Example: https://your-app-name.railway.app" -ForegroundColor Gray
    $RailwayUrl = Read-Host "Railway URL"
}

# Validate URL format
if (-not $RailwayUrl.StartsWith("https://")) {
    Write-Host "❌ Error: URL must start with https://" -ForegroundColor Red
    exit 1
}

# Remove trailing slash if present
$RailwayUrl = $RailwayUrl.TrimEnd('/')

Write-Host "🔧 Configuring frontend for Railway backend..." -ForegroundColor Green
Write-Host "Backend URL: $RailwayUrl" -ForegroundColor Yellow
Write-Host ""

# Create frontend directory if it doesn't exist
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Error: frontend directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Create .env.local file for local development
$envLocalContent = @"
REACT_APP_API_URL=$RailwayUrl/api/v1
REACT_APP_API_BASE_URL=$RailwayUrl
REACT_APP_BACKEND_URL=$RailwayUrl
"@

$envLocalContent | Out-File -FilePath "frontend\.env.local" -Encoding UTF8
Write-Host "✅ Created frontend/.env.local" -ForegroundColor Green

# Create .env.production file for production builds
$envProdContent = @"
REACT_APP_API_URL=$RailwayUrl/api/v1
REACT_APP_API_BASE_URL=$RailwayUrl
REACT_APP_BACKEND_URL=$RailwayUrl
"@

$envProdContent | Out-File -FilePath "frontend\.env.production" -Encoding UTF8
Write-Host "✅ Created frontend/.env.production" -ForegroundColor Green

# Update package.json to remove localhost proxy (backup first)
if (Test-Path "frontend\package.json") {
    # Create backup
    Copy-Item "frontend\package.json" "frontend\package.json.backup" -Force
    Write-Host "✅ Backed up package.json" -ForegroundColor Green
    
    # Read and update package.json
    $packageJson = Get-Content "frontend\package.json" -Raw | ConvertFrom-Json
    
    # Remove proxy if it exists
    if ($packageJson.PSObject.Properties.Name -contains "proxy") {
        $packageJson.PSObject.Properties.Remove("proxy")
        $packageJson | ConvertTo-Json -Depth 10 | Out-File "frontend\package.json" -Encoding UTF8
        Write-Host "✅ Removed localhost proxy from package.json" -ForegroundColor Green
    }
}

# Create deployment configuration file
$deployConfig = @"
# Railway Frontend Integration Configuration
# Generated on $(Get-Date)

## Backend Configuration
RAILWAY_BACKEND_URL=$RailwayUrl
API_ENDPOINTS:
  - OCR: $RailwayUrl/api/v1/ocr
  - Extract Medicines: $RailwayUrl/api/v1/extract-meds
  - Medicine Info: $RailwayUrl/api/v1/med-info
  - Chat: $RailwayUrl/api/v1/chat
  - Health Check: $RailwayUrl/health

## Frontend Deployment
For Vercel deployment, set these environment variables:
  REACT_APP_API_URL=$RailwayUrl/api/v1
  REACT_APP_API_BASE_URL=$RailwayUrl
  REACT_APP_BACKEND_URL=$RailwayUrl

## CORS Configuration
Ensure your Railway backend includes these origins:
  - https://your-frontend-domain.vercel.app
  - http://localhost:3000
  - https://localhost:3000
"@

$deployConfig | Out-File -FilePath "RAILWAY_FRONTEND_CONFIG.txt" -Encoding UTF8
Write-Host "✅ Created RAILWAY_FRONTEND_CONFIG.txt" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Frontend configuration completed!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Configuration Summary:" -ForegroundColor Cyan
Write-Host "  Backend URL: $RailwayUrl" -ForegroundColor White
Write-Host "  API Base: $RailwayUrl/api/v1" -ForegroundColor White
Write-Host "  Environment files created: .env.local, .env.production" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Test locally:" -ForegroundColor White
Write-Host "     cd frontend" -ForegroundColor Gray
Write-Host "     npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Deploy to Vercel/Netlify:" -ForegroundColor White
Write-Host "     - Set environment variables from .env.production" -ForegroundColor Gray
Write-Host "     - Deploy from frontend directory" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Update Railway backend CORS:" -ForegroundColor White
Write-Host "     - Add your frontend domain to ALLOWED_ORIGINS" -ForegroundColor Gray
Write-Host "     - Include: https://your-app.vercel.app" -ForegroundColor Gray
Write-Host ""
Write-Host "🧪 Test Endpoints:" -ForegroundColor Cyan
Write-Host "  Health Check: $RailwayUrl/health" -ForegroundColor White
Write-Host "  API Docs: $RailwayUrl/docs" -ForegroundColor White
Write-Host "  OCR Test: $RailwayUrl/api/v1/ocr" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Important:" -ForegroundColor Yellow
Write-Host "  - Ensure your Railway backend is deployed and running" -ForegroundColor White
Write-Host "  - Update CORS settings in Railway environment variables" -ForegroundColor White
Write-Host "  - Test all endpoints before deploying frontend" -ForegroundColor White
Write-Host ""

# Offer to test the connection
$testConnection = Read-Host "Would you like to test the Railway backend connection? (y/n)"
if ($testConnection -eq "y" -or $testConnection -eq "Y") {
    Write-Host ""
    Write-Host "🔍 Testing Railway backend connection..." -ForegroundColor Cyan
    
    try {
        $healthResponse = Invoke-RestMethod -Uri "$RailwayUrl/health" -Method GET -TimeoutSec 10
        Write-Host "✅ Health check successful!" -ForegroundColor Green
        Write-Host "   Response: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Health check failed!" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Please ensure your Railway backend is deployed and running." -ForegroundColor Yellow
    }
    
    try {
        $docsResponse = Invoke-WebRequest -Uri "$RailwayUrl/docs" -Method GET -TimeoutSec 10
        if ($docsResponse.StatusCode -eq 200) {
            Write-Host "✅ API documentation accessible!" -ForegroundColor Green
            Write-Host "   Visit: $RailwayUrl/docs" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "⚠️  API docs check failed (this might be normal)" -ForegroundColor Yellow
        Write-Host "   Visit: $RailwayUrl/docs to verify manually" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "✨ Configuration complete! Your frontend is ready for Railway integration." -ForegroundColor Green