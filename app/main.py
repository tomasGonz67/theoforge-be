from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import asynccontextmanager
import os

from app.operations.user import UserService
from app.schemas.user import UserCreate, UserResponse
from app.database import Base, Database
from app.auth.dependencies import get_db
from app.routers import auth

# Get database URL from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    Database.initialize(database_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database is initialized
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    yield

app = FastAPI(title="TheoForge API", lifespan=lifespan)

# Include routers
app.include_router(auth.router)

# Keep existing engine for health check
engine = create_engine(database_url) if database_url else None

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    if engine:
        try:
            # Try to connect to the database
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    else:
        db_status = "no database configured"
    
    return {
        "status": "healthy",
        "database": db_status
    } 