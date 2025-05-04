from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from app.core.security import hash_password  # ✅ Correct import
from prometheus_client import Counter # Add Prometheus Counter import

from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserGeneralUpdate
from app.operations.jwt_service import create_access_token
from app.routers.dependencies import get_current_user, get_db
from app.operations.user import UserRepository, RegistrationService, AuthenticationService
from settings.config import settings
from app.models.user import User, SubscriptionPlan

# Define Prometheus counters
REGISTRATIONS_TOTAL = Counter('user_registrations_total', 'Total number of user registrations')
LOGINS_TOTAL = Counter('user_logins_total', 'Total number of user logins')

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
    try:
        user_repo = UserRepository(db)
        registration_service = RegistrationService(user_repo)
        
        user = await registration_service.register_user(user_create.model_dump())
        REGISTRATIONS_TOTAL.inc() # Increment registration counter
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 

# Login endpoint that returns JWT token
@router.post("/login")
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    '''
    Login to get an access token for authenticated API requests
    
    - username: testuser@example.com
    - password: SecurePass123!
    
    Returns a JWT token that should be included in the Authorization header
    for subsequent requests as: "Bearer {token}"
    '''
    user_repo = UserRepository(db)
    auth_service = AuthenticationService(user_repo)
    
    user = await auth_service.login_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username/password")

    # Creating access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name},
        expires_delta=access_token_expires
    )

    LOGINS_TOTAL.inc() # Increment login counter
    return {"access_token": access_token, "token_type": "bearer"}

# Simple logout endpoint (MOVED TO AFTER LOGIN)
@router.post("/logout")
async def logout():
    '''
    Logout endpoint
    
    Note: Since we're using JWT tokens, actual token management is handled by the frontend.
    The backend doesn't maintain session state, so this endpoint is provided for API completeness.
    '''
    return {"message": "Logged out successfully"}

# Protected route that requires authentication
@router.get("/auth")
async def auth_route(username: str = Depends(get_current_user)):
    '''
    Authenticates user based on JWT token in Authorization header
    
    - Requires a valid JWT token in the Authorization header as "Bearer {token}"
    - Returns user information if authentication is successful
    '''
    return {"message": "You have access!", "username": username}

# List all users
@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    """
    Retrieve a list of all users.
    """
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

# Update general user information

@router.put("/update", response_model=UserResponse)
async def update_user(
    user_update: UserGeneralUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update general user information like first name, last name, email, nickname, and password.
    """
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Update fields if provided
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name

    # ✅ Email update requires uniqueness check
    if user_update.email is not None and user_update.email != user.email:
        email_check = await db.execute(select(User).where(User.email == user_update.email))
        if email_check.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_update.email
        user.email_verified = False  # Reset email verification

    # ✅ Nickname update requires uniqueness check
    if user_update.nickname is not None and user_update.nickname != user.nickname:
        nickname_check = await db.execute(select(User).where(User.nickname == user_update.nickname))
        if nickname_check.scalars().first():
            raise HTTPException(status_code=400, detail="Nickname already taken")
        user.nickname = user_update.nickname

    # ✅ Password update requires hashing
    if user_update.password is not None:
        user.hashed_password = hash_password(user_update.password)  

    # ✅ Save changes
    await db.commit()
    await db.refresh(user)

    # ✅ Generate a new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name},
        expires_delta=access_token_expires
    )

    # ✅ Return properly formatted response
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        nickname=user.nickname,
        role=user.role.name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# Update user profile
@router.put("/update-profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Ensure this works
):
    """
    Update user profile details including phone number, address, payment info, and subscription plan.

    - Requires authentication.
    """
    if not current_user:  # ✅ Ensure user is authenticated
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Retrieve user from the database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(current_user.id)  # ✅ Use repository to fetch user

    if not user:  # ✅ Ensure user exists in the DB
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Update fields if provided
    if user_update.phone_number is not None:
        user.phone_number = user_update.phone_number
    if user_update.address is not None:
        user.address = user_update.address
    if user_update.city is not None:
        user.city = user_update.city
    if user_update.state is not None:
        user.state = user_update.state
    if user_update.zip_code is not None:
        user.zip_code = user_update.zip_code
    if user_update.card_number is not None:
        user.card_number = user_update.card_number
    if user_update.ccv is not None:
        user.ccv = user_update.ccv
    if user_update.security_code is not None:
        user.security_code = user_update.security_code
    if user_update.subscription_plan is not None:
        try:
            user.subscription_plan = SubscriptionPlan[user_update.subscription_plan.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid subscription plan")

    # ✅ Save changes
    await db.commit()
    await db.refresh(user)

    return user  # ✅ Return updated user


# Delete user
@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_user(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete user account.

    - Requires authentication.
    - Deletes the authenticated user's account permanently.
    - Returns a success message.
    """
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)  # ✅ Remove user from database
    await db.commit()  # ✅ Commit changes to persist deletion

    return {"message": "User deleted successfully"}  # ✅ Now returns a JSON response


    