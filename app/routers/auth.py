from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.operations.user import UserService
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token_schema import TokenResponse
from app.operations.jwt_service import create_access_token
from dependencies import get_db
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
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    '''
    Method #1
    Login to create JSON response for immediate use by frontend and set cookie afterward

        - username: user@example.com
        - password: Secure*1234
    '''

    user = users_db.get(form_data.username)
    if not user or form_data.password != "Secure*1234":  # Replace with real hashing check
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"], "role": "user role example"},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Set cookie after creating JSON response and immediate frontend handling (second step of Method #1)
# Frontend can retrieve requests afterward by having ' credentials: "include" ' in fetch
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
            httponly=False,  # JavaScript cannot access this
            secure=False, # set to true in prod
            samesite=None
        )
        
    except Exception as e:
        print(f"Error in set_cookie: {str(e)}")  # Log the error for debugging
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    return {"message": "set-cookie test"}

# When protecting certain routes using JWT authentication with the cookie
@router.get("/auth")
async def auth_route(access_token: str = Cookie(None)):
    '''
    Authenticates user based on cookie

        - Uses encoded JWT in cookie for protected path check
    '''
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized: No access token found")

    return {"message": "You have access!", "access_token": access_token}

# Clears cookie when logging out
@router.post("/logout/cookie")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}