from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Database
from app.services.auth import decode_token
from settings.config import settings 

def get_settings():
    """Return application settings."""
    return settings

# Database dependency
async def get_db() -> AsyncSession:
    """Provides a database session for each request."""
    async_session_factory = Database.get_session()
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# User authentication dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates JWT token and returns current user info."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    user_role: str = payload.get("role")
    if user_id is None or user_role is None:
        raise credentials_exception
        
    return {"user_id": user_id, "role": user_role}

# Role-based access control dependency
def require_role(allowed_roles: list[str]):
    """Checks if current user has required role."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail="Operation not permitted"
            )
        return current_user
    return role_checker

"""
Not included from user_management:
- email service dependency
- template manager
- get_email_service() function

Changes from original:
- Changed OAuth2 tokenUrl to '/token'
- Made role_checker async
- Modified require_role to accept list of roles

The dependencies.py focuses solely on:
- Database session management
- JWT token validation
- Role-based access control
"""