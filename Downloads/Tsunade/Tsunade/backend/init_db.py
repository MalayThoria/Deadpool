#!/usr/bin/env python3
"""
Database initialization script for SQLite development environment.
This script creates all necessary tables for the LP Assistant application.
"""

import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.config import Base
from database.models import *  # Import all models

async def init_database():
    """
    Initialize the database by creating all tables.
    """
    try:
        print("Creating database tables...")
        
        # Create async engine for table creation
        engine = create_async_engine("sqlite+aiosqlite:///./lp_assistant_dev.db")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully!")
        print(f"Database file: lp_assistant_dev.db")
        
        # Test the connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful!")
        
        await engine.dispose()
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_database())