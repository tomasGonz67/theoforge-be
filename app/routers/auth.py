from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from uuid import UUID
from typing import List

from app.schemas.user import UserCreate, UserResponse
from app.operations.jwt_service import create_access_token
from app.routers.dependencies import get_registration_service, get_auth_service, get_current_user
from settings.config import settings
from app.models.user import User
from app.operations.user import UserRepository, ProfileUpdateService

# Create a router for auth endpoints
router = APIRouter(prefix="/auth", tags=["Authentication & User"])

# --- Cookie Management Routes ---
@router.post("/set-cookie")
async def set_cookie(token_data: TokenResponse, response: Response):
    """
    Set a cookie from TokenResponse
    """
    try:
        access_token = token_data.access_token
        if not access_token:
            raise HTTPException(status_code=400, detail="Missing token")

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="Lax"
        )
    except Exception as e:
        print(f"Error in set_cookie: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    return {"message": "set-cookie test"}

@router.get("/auth")
async def auth_route(current_user: User = Depends(get_current_user)):
    """
    Authenticates user based on cookie
    """
    return {"message": "You have access!", "username": current_user.email}

@router.post("/logout/cookie")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

# --- User Authentication and Management Routes ---
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
    user_create: UserCreate,
    registration_service = Depends(get_registration_service)
):
    """
    Register a new user.
    """
    try:
        user = await registration_service.register_user(user_create.model_dump())
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 

# Simulated user database for FastAPI example
# DELETE THIS
# TODO: Use database for user login
users_db = {
    "user@example.com": {
        "username": "user@example.com",
        "password": "Secure*1234",
    }
}

# Creating a JSON Response (to then set a HTTP-only cookie after immediate use by frontend)
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    auth_service = Depends(get_auth_service)
):
    """
    Login to create JSON response for immediate use by frontend and to set cookie afterward
    """
    user = await auth_service.login_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username/password")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# When protecting certain routes using JWT authentication with the cookie
@router.get("/auth")
async def auth_route(username: str = Depends(get_current_user)):
    '''
    Authenticates user based on cookie

        - Uses encoded JWT in cookie for protected path check
        - Validates token through get_current_user dependency
    '''
    
    return {"message": "You have access!", "username": username}

# Clears cookie when logging out
@router.post("/logout")
async def logout(response: Response):
    return {"message": "Logged out successfully"}