# Main FastAPI application entry point
from routers import users, auth
from fastapi import FastAPI

#initializes fastAPI
app = FastAPI(
    title="User Management API",
    description="A simplified user management system",
    version="1.0.0"
)

#initializes database
"""
@app.on_event("startup")
async def startup():
    Database.initialize(settings.database_url)
"""


#root api. base backend is hit. it returns this message.
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app! This is a CI/CD test."}

app.include_router(users.router)
app.include_router(auth.router)

# TODO: Include routers
# TODO: Add middleware
# TODO: Add startup and shutdown events 