import os
from typing import Optional
from fastapi import Depends, Request, HTTPException
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users import schemas
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.config import get_db
from pydantic import BaseModel
import uuid
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 3600  # 1 hour

from datetime import datetime

class UserRead(schemas.BaseUser[int]):
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None

class UserCreate(schemas.BaseUserCreate):
    role: str = "PATIENT"

class UserUpdate(schemas.BaseUserUpdate):
    role: Optional[str] = None

class UserManager(BaseUserManager[User, int]):
    reset_password_token_secret = SECRET_KEY
    verification_token_secret = SECRET_KEY

    def parse_id(self, value):
        """Parse user ID from string to integer"""
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid user ID: {value}")

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
        
        # Create user profile with medical history if provided
        if hasattr(request, 'json') and request:
            try:
                from database.models import UserProfile
                from database.config import get_db
                
                # Get the registration data from request
                registration_data = await request.json() if hasattr(request, 'json') else {}
                
                # Create user profile
                async for db in get_db():
                    profile = UserProfile(
                        user_id=user.id,
                        first_name=registration_data.get('first_name'),
                        last_name=registration_data.get('last_name'),
                        date_of_birth=registration_data.get('date_of_birth'),
                        gender=registration_data.get('gender'),
                        emergency_contact=registration_data.get('emergency_contact')
                    )
                    db.add(profile)
                    await db.commit()
                    break
            except Exception as e:
                print(f"Error creating user profile: {e}")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

    async def on_after_verify(
        self, user: User, request: Optional[Request] = None
    ):
        print(f"User {user.id} has been verified")

# Database adapter
async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)

# User manager dependency
def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

# Authentication backend
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET_KEY, lifetime_seconds=JWT_EXPIRATION_SECONDS)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Dependencies
current_active_user = fastapi_users.current_user(active=True)
current_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# OAuth2 Configuration
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
FACEBOOK_OAUTH_CLIENT_ID = os.getenv("FACEBOOK_OAUTH_CLIENT_ID")
FACEBOOK_OAUTH_CLIENT_SECRET = os.getenv("FACEBOOK_OAUTH_CLIENT_SECRET")

# Role-based access control
def require_role(required_role: str):
    def role_checker(current_user: User = Depends(current_active_user)):
        if current_user.role.value != required_role and current_user.role.value != "admin":
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Admin role dependency
require_admin = require_role("admin")

# Patient role dependency
require_patient = require_role("patient")

# Healthcare provider role dependency
require_healthcare_provider = require_role("healthcare_provider")