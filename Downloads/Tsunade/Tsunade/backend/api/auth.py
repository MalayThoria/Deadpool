from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from database.config import get_sync_db
from database.models import User, UserRole, AuditLog
from auth.auth import (
    fastapi_users,
    auth_backend,
    current_active_user,
    UserCreate,
    UserRead,
    UserUpdate
)
from auth.oauth import (
    get_oauth_handler,
    OAuthUserManager,
    OAUTH_PROVIDERS
)
import secrets
import hashlib
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Pydantic models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class OAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None

class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    emergency_contact: Optional[str] = None
    consent_given: bool = True

class LoginResponse(BaseModel):
    user: UserRead
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access"):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

async def log_auth_event(
    db: Session,
    user_id: Optional[int],
    action: str,
    details: Dict[str, Any],
    request: Request
):
    """Log authentication events for audit"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource="authentication",
        new_values=details,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        data_classification="personal"
    )
    db.add(audit_log)
    db.commit()

# Include FastAPI Users routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/register",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/reset",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/verify",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)

# Custom registration endpoint
@router.post("/register-with-profile", response_model=UserRead)
async def register_with_profile(
    registration_data: UserRegistration,
    request: Request = None,
    db: Session = Depends(get_sync_db)
):
    """Custom registration endpoint that creates both User and UserProfile"""
    from database.models import UserProfile, Gender
    from fastapi_users.password import PasswordHelper
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == registration_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Hash password
    password_helper = PasswordHelper()
    hashed_password = password_helper.hash(registration_data.password)
    
    try:
        # Create user
        user = User(
            email=registration_data.email,
            hashed_password=hashed_password,
            role=UserRole.PATIENT,
            is_active=True,
            is_verified=False,
            consent_given=registration_data.consent_given,
            consent_date=datetime.utcnow() if registration_data.consent_given else None
        )
        db.add(user)
        db.flush()  # Get user ID without committing
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            emergency_contact=registration_data.emergency_contact
        )
        
        # Handle gender enum
        if registration_data.gender:
            try:
                profile.gender = Gender(registration_data.gender.lower())
            except ValueError:
                profile.gender = Gender.PREFER_NOT_TO_SAY
        
        # Handle date of birth
        if registration_data.date_of_birth:
            try:
                from datetime import datetime as dt
                profile.age = dt.now().year - dt.strptime(registration_data.date_of_birth, "%Y-%m-%d").year
            except ValueError:
                pass  # Skip if date format is invalid
        
        db.add(profile)
        db.commit()
        
        # Log registration event
        await log_auth_event(
            db, user.id, "REGISTRATION", 
            {"email": user.email, "method": "email_password"},
            request
        )
        
        return UserRead(
            id=user.id,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# Custom authentication endpoints
@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_sync_db)
):
    """Custom login endpoint with enhanced response"""
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        await log_auth_event(
            db, None, "LOGIN_FAILED", 
            {"email": form_data.username, "reason": "invalid_credentials"},
            request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        await log_auth_event(
            db, user.id, "LOGIN_FAILED", 
            {"reason": "account_inactive"},
            request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Log successful login
    await log_auth_event(
        db, user.id, "LOGIN_SUCCESS", 
        {"login_method": "password"},
        request
    )
    
    return LoginResponse(
        user=UserRead.from_orm(user),
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request = None,
    db: Session = Depends(get_sync_db)
):
    """Refresh access token using refresh token"""
    payload = verify_token(token_data.refresh_token, "refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Log token refresh
    await log_auth_event(
        db, user.id, "TOKEN_REFRESH", {},
        request
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(current_active_user),
    request: Request = None,
    db: Session = Depends(get_sync_db)
):
    """Change user password"""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    # Log password change
    await log_auth_event(
        db, current_user.id, "PASSWORD_CHANGE", {},
        request
    )
    
    return {"message": "Password changed successfully"}

# OAuth endpoints
@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(provider: str):
    """Get OAuth authorization URL"""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    oauth_handler = get_oauth_handler(provider)
    state = secrets.token_urlsafe(32)
    authorization_url = await oauth_handler.get_authorization_url(state)
    
    return {
        "authorization_url": authorization_url,
        "state": state
    }

@router.post("/oauth/{provider}/callback", response_model=LoginResponse)
async def oauth_callback(
    provider: str,
    callback_data: OAuthCallback,
    request: Request = None,
    db: Session = Depends(get_sync_db)
):
    """Handle OAuth callback"""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    try:
        oauth_handler = get_oauth_handler(provider)
        
        # Exchange code for access token
        access_token = await oauth_handler.get_access_token(callback_data.code)
        
        # Get user info
        user_info = await oauth_handler.get_user_info(access_token)
        
        # Get or create user
        user = await OAuthUserManager.get_or_create_oauth_user(
            db=db,
            email=user_info["email"],
            oauth_provider=provider,
            oauth_id=user_info["id"],
            user_info=user_info
        )
        
        # Create JWT tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Log OAuth login
        await log_auth_event(
            db, user.id, "OAUTH_LOGIN", 
            {"provider": provider, "oauth_id": user_info["id"]},
            request
        )
        
        return LoginResponse(
            user=UserRead.from_orm(user),
            access_token=jwt_access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        await log_auth_event(
            db, None, "OAUTH_LOGIN_FAILED", 
            {"provider": provider, "error": str(e)},
            request
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(current_active_user),
    request: Request = None,
    db: Session = Depends(get_sync_db)
):
    """Logout user (mainly for logging purposes)"""
    # Log logout event
    await log_auth_event(
        db, current_user.id, "LOGOUT", {},
        request
    )
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserRead)
async def get_current_user(current_user: User = Depends(current_active_user)):
    """Get current authenticated user"""
    return current_user

@router.delete("/me")
async def delete_account(
    current_user: User = Depends(current_active_user),
    request: Request = None,
    db: Session = Depends(get_sync_db)
):
    """Delete user account (GDPR compliance)"""
    # Log account deletion
    await log_auth_event(
        db, current_user.id, "ACCOUNT_DELETE", 
        {"user_email": current_user.email},
        request
    )
    
    # Delete user (cascade will handle related data)
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}