import os
from typing import Optional, Dict, Any
from fastapi import HTTPException
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.facebook import FacebookOAuth2
from fastapi_users.authentication import AuthenticationBackend
from fastapi_users.authentication.transport.bearer import BearerTransport
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from database.models import User, UserRole
from database.config import get_db
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import secrets
import hashlib

load_dotenv()

# OAuth2 Configuration
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
FACEBOOK_OAUTH_CLIENT_ID = os.getenv("FACEBOOK_OAUTH_CLIENT_ID")
FACEBOOK_OAUTH_CLIENT_SECRET = os.getenv("FACEBOOK_OAUTH_CLIENT_SECRET")
OAUTH_REDIRECT_URL = os.getenv("OAUTH_REDIRECT_URL", "http://localhost:3000/auth/callback")

# OAuth2 Clients
google_oauth_client = GoogleOAuth2(
    client_id=GOOGLE_OAUTH_CLIENT_ID,
    client_secret=GOOGLE_OAUTH_CLIENT_SECRET,
) if GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET else None

facebook_oauth_client = FacebookOAuth2(
    client_id=FACEBOOK_OAUTH_CLIENT_ID,
    client_secret=FACEBOOK_OAUTH_CLIENT_SECRET,
) if FACEBOOK_OAUTH_CLIENT_ID and FACEBOOK_OAUTH_CLIENT_SECRET else None

class OAuthUserManager:
    """Manager for OAuth user operations"""
    
    @staticmethod
    def generate_random_password() -> str:
        """Generate a random password for OAuth users"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    async def get_or_create_oauth_user(
        db: Session,
        email: str,
        oauth_provider: str,
        oauth_id: str,
        user_info: Dict[str, Any]
    ) -> User:
        """Get existing OAuth user or create new one"""
        
        # Check if user exists with this email
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            # Update OAuth ID if not set
            if oauth_provider == "google" and not existing_user.google_id:
                existing_user.google_id = oauth_id
            elif oauth_provider == "facebook" and not existing_user.facebook_id:
                existing_user.facebook_id = oauth_id
            
            # Check if user has a profile, create one if missing
            from database.models import UserProfile
            existing_profile = db.query(UserProfile).filter(UserProfile.user_id == existing_user.id).first()
            if not existing_profile:
                profile = UserProfile(
                    user_id=existing_user.id,
                    first_name=user_info.get('given_name') or user_info.get('first_name'),
                    last_name=user_info.get('family_name') or user_info.get('last_name'),
                    # Set default values for required fields
                    fitness_level=None,  # Will use enum default
                    timezone="UTC",
                    language="en"
                )
                db.add(profile)
            
            db.commit()
            db.refresh(existing_user)
            return existing_user
        
        # Create new user
        random_password = OAuthUserManager.generate_random_password()
        hashed_password = OAuthUserManager.hash_password(random_password)
        
        new_user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "role": UserRole.PATIENT,
            "is_active": True,
            "is_verified": True,  # OAuth users are pre-verified
            "consent_given": True,
        }
        
        # Set OAuth ID based on provider
        if oauth_provider == "google":
            new_user_data["google_id"] = oauth_id
        elif oauth_provider == "facebook":
            new_user_data["facebook_id"] = oauth_id
        
        new_user = User(**new_user_data)
        db.add(new_user)
        db.flush()  # Get user ID without committing
        
        # Create user profile for OAuth users
        from database.models import UserProfile
        profile = UserProfile(
            user_id=new_user.id,
            first_name=user_info.get('given_name') or user_info.get('first_name'),
            last_name=user_info.get('family_name') or user_info.get('last_name'),
            # Set default values for required fields
            fitness_level=None,  # Will use enum default
            timezone="UTC",
            language="en"
        )
        db.add(profile)
        db.commit()
        db.refresh(new_user)
        
        return new_user

class GoogleOAuthHandler:
    """Handler for Google OAuth operations"""
    
    @staticmethod
    async def get_authorization_url(state: str = None) -> str:
        """Get Google OAuth authorization URL"""
        if not google_oauth_client:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured"
            )
        
        authorization_url = await google_oauth_client.get_authorization_url(
            redirect_uri=f"{OAUTH_REDIRECT_URL}/google",
            state=state,
            scope=["openid", "email", "profile"]
        )
        return authorization_url
    
    @staticmethod
    async def get_access_token(authorization_code: str) -> str:
        """Exchange authorization code for access token"""
        if not google_oauth_client:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured"
            )
        
        access_token = await google_oauth_client.get_access_token(
            authorization_code,
            redirect_uri=f"{OAUTH_REDIRECT_URL}/google"
        )
        return access_token
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        if not google_oauth_client:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured"
            )
        
        user_id, user_email = await google_oauth_client.get_id_email(
            access_token["access_token"]
        )
        
        return {
            "id": user_id,
            "email": user_email,
            "provider": "google"
        }

class FacebookOAuthHandler:
    """Handler for Facebook OAuth operations"""
    
    @staticmethod
    async def get_authorization_url(state: str = None) -> str:
        """Get Facebook OAuth authorization URL"""
        if not facebook_oauth_client:
            raise HTTPException(
                status_code=500,
                detail="Facebook OAuth not configured"
            )
        
        authorization_url = await facebook_oauth_client.get_authorization_url(
            redirect_uri=f"{OAUTH_REDIRECT_URL}/facebook",
            state=state,
            scope=["email"]
        )
        return authorization_url
    
    @staticmethod
    async def get_access_token(authorization_code: str) -> str:
        """Exchange authorization code for access token"""
        if not facebook_oauth_client:
            raise HTTPException(
                status_code=500,
                detail="Facebook OAuth not configured"
            )
        
        access_token = await facebook_oauth_client.get_access_token(
            authorization_code,
            redirect_uri=f"{OAUTH_REDIRECT_URL}/facebook"
        )
        return access_token
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """Get user information from Facebook"""
        if not facebook_oauth_client:
            raise HTTPException(
                status_code=500,
                detail="Facebook OAuth not configured"
            )
        
        user_id, user_email = await facebook_oauth_client.get_id_email(
            access_token["access_token"]
        )
        
        return {
            "id": user_id,
            "email": user_email,
            "provider": "facebook"
        }

# OAuth provider mapping
OAUTH_PROVIDERS = {
    "google": GoogleOAuthHandler,
    "facebook": FacebookOAuthHandler,
}

def get_oauth_handler(provider: str):
    """Get OAuth handler for specified provider"""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    return OAUTH_PROVIDERS[provider]