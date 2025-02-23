from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import asynccontextmanager
import os

from app.operations.user import UserService
from app.schemas.user import UserCreate, UserResponse
from app.database import Base, Database
from app.auth.dependencies import get_db

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

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"]
)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - Validates user data using UserCreate schema
    - Checks for email uniqueness
    - Creates user with hashed password
    - First user gets ADMIN role, others get USER role
    """
    user = await UserService.register_user(db, user_create.model_dump())
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email already exists"
    ) 