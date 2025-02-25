from builtins import str
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token_schema import TokenResponse
from app.services.users import UserService
from app.services.jwt_service import create_access_token
from app.dependencies import get_settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
settings = get_settings()

# Register
@router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Login and Registration"])
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_db)):
    user = await UserService.register_user(session, user_data.model_dump())
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

# Login
@router.post("/login/", response_model=TokenResponse, tags=["Login and Registration"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    if await UserService.is_account_locked(session, form_data.username):
        raise HTTPException(status_code=400, detail="Account locked due to too many failed login attempts.")

    user = await UserService.login_user(session, form_data.username, form_data.password)
    if user:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)

        access_token = create_access_token(
            data={"sub": user.email, "role": str(user.role.name)},
            expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect email or password.")