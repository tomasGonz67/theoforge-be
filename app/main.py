from fastapi import FastAPI
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import importlib
import pkgutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, Database, DbService
from app.routers import auth, guest

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend origin
    allow_credentials=True,  # Required for auth headers
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(guest.router)

@app.get("/")
async def root():
    return {"message": "Hello World test"}

@app.get("/health")
async def health():
    """
    Health check endpoint that verifies application and database health asynchronously.
    Uses the same async database connection pattern as the rest of the application.
    """
    db_status = "not checked"
    
    if database_url:
        # Create a session for this request
        async_session_factory = Database.get_session_factory()
        async with async_session_factory() as session:
            try:
                # use async query execution
                result = await DbService.execute_query(session, text("SELECT 1"))
                row = result.fetchone()
                if row and row[0] == 1:
                    db_status = "connected"
                else:
                    db_status = "error: unexpected query result"
            except SQLAlchemyError as e:
                db_status = f"error: {str(e)}"
            finally:
                await session.close()
    else:
        db_status = "no database configured"
    
    return {
        "status": "healthy",
        "database": db_status
    }
