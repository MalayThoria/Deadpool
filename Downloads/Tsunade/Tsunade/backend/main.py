from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from backend directory
load_dotenv('.env')

# Initialize Sentry for error tracking (disabled for development)
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and sentry_dsn.strip() and sentry_dsn.startswith(("http://", "https://")):
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0,
        )
        print("✅ Sentry initialized")
    else:
        print("⚠️ Sentry DSN not configured or invalid (continuing without error tracking)")
except ImportError:
    print("⚠️ Sentry not available (continuing without error tracking)")
except Exception as e:
    print(f"⚠️ Sentry initialization failed (continuing without error tracking): {e}")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting LP Assistant API...")
    
    # Try to initialize external services but don't fail if they're not available
    try:
        from database.config import init_redis, init_mongodb
        try:
            await init_redis()
            print("✅ Redis connected successfully")
        except Exception as e:
            print(f"⚠️ Redis connection failed (continuing without Redis): {e}")
        
        try:
            await init_mongodb()
            print("✅ MongoDB connected successfully")
        except Exception as e:
            print(f"⚠️ MongoDB connection failed (continuing without MongoDB): {e}")
    except ImportError as e:
        print(f"⚠️ Database config not available (continuing without external databases): {e}")
    
    print("✅ API startup completed")
    yield
    
    # Shutdown
    print("🔄 Shutting down LP Assistant API...")
    try:
        from database.config import close_redis, close_mongodb
        try:
            await close_redis()
        except Exception as e:
            print(f"⚠️ Redis close failed: {e}")
        
        try:
            await close_mongodb()
        except Exception as e:
            print(f"⚠️ MongoDB close failed: {e}")
    except ImportError:
        print("⚠️ Database config not available for cleanup")
    
    print("✅ API shutdown completed")

app = FastAPI(
    title="LP Assistant Healthcare API",
    description="AI-powered healthcare assistant with prescription OCR, exercise recommendations, and health tracking",
    version="2.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import authentication and new routes
from auth.auth import auth_backend, current_active_user, fastapi_users, UserRead, UserCreate, UserUpdate
from api import auth, profiles
from api.insights import router as insights_router
from api.calendar import router as calendar_router
from api.admin import router as admin_router
from api.privacy import router as privacy_router
from api.exercise_tracking import router as exercise_router
from api.health_insights import router as health_insights_router
from routers.health_analysis import router as health_analysis_router
from routes import ocr, extract_meds, med_info, chat, exercise_recommendations, calendar_integration, health_recommendations, prescription_analysis, prescription_integration, websocket_routes

# Authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/v1/auth/jwt",
    tags=["Authentication"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/v1/auth",
    tags=["Authentication"]
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/api/v1/auth",
    tags=["Authentication"]
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/api/v1/auth",
    tags=["Authentication"]
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/v1/users",
    tags=["Users"]
)

# Custom authentication routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Profile management routes
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Profiles"])

# New API routes
app.include_router(insights_router, prefix="/api/insights", tags=["insights"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["calendar"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(privacy_router, prefix="/api/privacy", tags=["Privacy & Compliance"])
app.include_router(exercise_router, prefix="/api/exercise", tags=["Exercise Tracking"])
app.include_router(health_insights_router, prefix="/api/health-insights", tags=["Health Insights"])
app.include_router(health_analysis_router, prefix="/api/v1", tags=["Health Analysis"])

# Existing routes
app.include_router(ocr.router, prefix="/api/v1", tags=["OCR"])
app.include_router(extract_meds.router, prefix="/api/v1", tags=["Medicine Extraction"])
app.include_router(med_info.router, prefix="/api/v1", tags=["Medicine Information"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(exercise_recommendations.router, prefix="/api/v1", tags=["Exercise Recommendations"])
app.include_router(calendar_integration.router, prefix="/api/v1", tags=["Calendar Integration"])
app.include_router(health_recommendations.router, prefix="/api/v1", tags=["Health Recommendations"])
app.include_router(prescription_analysis.router, prefix="/api/v1", tags=["Prescription Analysis"])
app.include_router(prescription_integration.router, tags=["Prescription Integration"])
app.include_router(websocket_routes.router, tags=["WebSocket"])

@app.get("/")
async def root():
    return {"message": "Rx Assistant API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Rx Assistant API"}