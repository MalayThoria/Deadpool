import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from dotenv import load_dotenv
from typing import Generator, AsyncGenerator

# Load environment variables
load_dotenv()

# Database URLs from environment variables
# Use SQLite for development when PostgreSQL is not available
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./lp_assistant_dev.db"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "lp_assistant_nosql")

# Database setup with SQLAlchemy (supports both PostgreSQL and SQLite)
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration - convert to async URL
    async_database_url = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(
        async_database_url,
        connect_args={"check_same_thread": False},
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
    # Also create sync engine for init_db.py
    sync_engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    # PostgreSQL configuration
    async_database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        async_database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
    # Also create sync engine for compatibility
    sync_engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

# Async session maker
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Sync session maker for compatibility
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# SQLAlchemy Base
Base = declarative_base()

# Redis connection
redis_client = None

# Initialize Redis and MongoDB connections
redis_client = None
mongo_client = None
mongo_db = None

# Database session dependencies
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        yield session

def get_sync_db() -> Generator[Session, None, None]:
    """Dependency to get synchronous database session (for compatibility)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        # Test the connection
        await redis_client.ping()
        return redis_client
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None
        return None

async def init_mongodb():
    """Initialize MongoDB connection"""
    global mongo_client, mongo_db
    try:
        mongo_client = AsyncIOMotorClient(MONGO_URL)
        mongo_db = mongo_client[MONGO_DB_NAME]
        # Test the connection
        await mongo_client.admin.command('ping')
        return mongo_db
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        mongo_client = None
        mongo_db = None
        raise e

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()

async def close_mongodb():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()

# Helper functions for database operations
async def get_redis() -> redis.Redis:
    """Get Redis client"""
    global redis_client
    if not redis_client:
        await init_redis()
    return redis_client

async def get_mongodb():
    """Get MongoDB database"""
    global mongo_db
    if not mongo_db:
        await init_mongodb()
    return mongo_db

# Database initialization
async def init_databases():
    """Initialize all database connections"""
    await init_redis()
    await init_mongodb()
    print("✅ Database connections initialized")

async def close_databases():
    """Close all database connections"""
    await close_redis()
    await close_mongodb()
    print("✅ Database connections closed")