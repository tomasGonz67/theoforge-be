from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.schemas.user import UserCreate, UserResponse
from app.operations.jwt_service import create_access_token
from app.routers.dependencies import get_registration_service, get_auth_service, get_current_user
from settings.config import settings

# Create a router for auth endpoints
router = APIRouter(prefix="/auth", tags=["auth"])

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
    
    - Validates user data using UserCreate schema
    - Checks for email uniqueness
    - Creates user with hashed password
    - First user gets ADMIN role, others get USER role
    """
    try:
        user = await registration_service.register_user(user_create.model_dump())
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 

# Login endpoint that returns JWT token
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    auth_service = Depends(get_auth_service)
):
    '''
    Login to get an access token for authenticated API requests
    
    - username: user@example.com
    - password: SecurePass123!
    
    Returns a JWT token that should be included in the Authorization header
    for subsequent requests as: "Bearer {token}"
    '''
    user = await auth_service.login_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username/password")

    # Creating access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Protected route that requires authentication
@router.get("/auth")
async def auth_route(username: str = Depends(get_current_user)):
    '''
    Authenticates user based on JWT token in Authorization header
    
    - Requires a valid JWT token in the Authorization header as "Bearer {token}"
    - Returns user information if authentication is successful
    '''
    return {"message": "You have access!", "username": username}

# Simple logout endpoint (note: actual token invalidation would be handled by the frontend)
@router.post("/logout")
async def logout():
    '''
    Logout endpoint
    
    Note: Since we're using JWT tokens, actual token management is handled by the frontend.
    The backend doesn't maintain session state, so this endpoint is provided for API completeness.
    '''
    return {"message": "Logged out successfully"}