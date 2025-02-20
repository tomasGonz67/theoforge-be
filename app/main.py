# Main FastAPI application entry point
from routers import users
from fastapi import FastAPI
from settings.config import settings
from app.database import Database

#initializes fastAPI
app = FastAPI(
    title="User Management API",
    description="A simplified user management system",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    Database.initialize(settings.database_url)

#root api. base backend is hit. it returns this message.
@app.get("/API")
def read_root():
    return {"message": "Welcome to the FastAPI app! This is a CI/CD test."}

app.include_router(users.router)

# TODO: Include routers
# TODO: Add middleware
# TODO: Add startup and shutdown events 