# Main FastAPI application entry point
from app.routers import users, auth
from fastapi import FastAPI
from app.database import Database
from settings.config import settings
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    Database.initialize(settings.database_url)
    yield
    # Shutdown: Add cleanup if needed
    pass

#initializes fastAPI
app = FastAPI(
    docs_url="/docs",
    title="User Management API",
    description="A simplified user management system",
    version="1.0.0",
    lifespan=lifespan
)

#root api. base backend is hit. it returns this message.
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app! This is a CI/CD test."}

app.include_router(users.router)
app.include_router(auth.router)


# TODO: Include routers
# TODO: Add middleware
# TODO: Add startup and shutdown events 