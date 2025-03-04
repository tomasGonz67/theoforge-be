from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from uuid import UUID
from typing import List

from app.schemas.user import UserCreate, UserResponse
from app.schemas.token_schema import TokenResponse
from app.operations.jwt_service import create_access_token
from app.routers.dependencies import get_db, get_registration_service, get_auth_service, get_current_user, get_user_repository
from settings.config import settings
from app.models.user import User
from app.operations.user import UserRepository

# Create a router for auth endpoints
router = APIRouter(prefix="/auth", tags=["Authentication & User"])

# --- Cookie Management Routes ---
@router.post("/set-cookie")
async def set_cookie(token_data: TokenResponse, response: Response):
    '''
    Set a cookie from TokenResponse
    '''
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
async def auth_route(username: str = Depends(get_current_user)):
    '''
    Authenticates user based on cookie
    '''
    return {"message": "You have access!", "username": username}

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

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    auth_service = Depends(get_auth_service)
):
    '''
    Login to create JSON response for immediate use by frontend and to set cookie afterward
    '''
    user = await auth_service.login_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username/password")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# --- User CRUD Routes ---
@router.get("/users", response_model=List[UserResponse])
async def list_users(user_repo: UserRepository = Depends(get_user_repository)):
    """
    List all users.
    """
    users = await user_repo.get_all_users()
    return users

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    updated_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update user details.
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    
    updated_user = await user_repo.save(user)
    return updated_user

@router.delete("/users/{user_id}")
async def delete_user(user_id: UUID, user_repo: UserRepository = Depends(get_user_repository)):
    """
    Delete a user.
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await user_repo.delete(user)
    return {"message": "User deleted successfully"}