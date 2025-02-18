# Main FastAPI application entry point
from routers import users
from fastapi import FastAPI
#initializes fastAPI
app = FastAPI(
    title="User Management API",
    description="A simplified user management system",
    version="1.0.0"
)
#root api. base backend is hit. it returns this message.
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app beast!"}

app.include_router(users.router)

# TODO: Include routers
# TODO: Add middleware
# TODO: Add startup and shutdown events 