from fastapi import FastAPI
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import Base, Database
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

origins=[
    "http://localhost:5173",
    "localhost:5173",
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8000/set-cookie",
    "http://127.0.0.1:8000/auth",
    "http://127.0.0.1:8000/simple-cookie-test",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow frontend origin
    allow_credentials=True,  # Required for cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],
)

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