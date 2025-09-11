from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from backend directory
load_dotenv('.env')

# Initialize Sentry for error tracking (disabled for development)
# if os.getenv("SENTRY_DSN"):
#     sentry_sdk.init(
#         dsn=os.getenv("SENTRY_DSN"),
#         integrations=[FastApiIntegration()],
#         traces_sample_rate=1.0,
#         environment=os.getenv("ENVIRONMENT", "development")
#     )

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from database.config import init_redis, init_mongodb
    await init_redis()
    await init_mongodb()
    yield
    # Shutdown
    from database.config import close_redis, close_mongodb
    await close_redis()
    await close_mongodb()

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
from routes import ocr, extract_meds, med_info, chat, exercise_recommendations, calendar_integration

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

# Existing routes
app.include_router(ocr.router, prefix="/api/v1", tags=["OCR"])
app.include_router(extract_meds.router, prefix="/api/v1", tags=["Medicine Extraction"])
app.include_router(med_info.router, prefix="/api/v1", tags=["Medicine Information"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(exercise_recommendations.router, prefix="/api/v1", tags=["Exercise Recommendations"])
app.include_router(calendar_integration.router, prefix="/api/v1", tags=["Calendar Integration"])

@app.get("/")
async def root():
    return {"message": "Rx Assistant API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Rx Assistant API"}