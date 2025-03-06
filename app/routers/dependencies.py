from builtins import Exception
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError
from app.database import Database
from app.operations.jwt_service import decode_token
from settings.config import Settings

# Create OAuth2PasswordBearer for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_db() -> AsyncSession:
    """Dependency that provides a database session for each request."""
    async_session_factory = Database.get_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        finally:
            await session.close()

# Retrieve current user from access_token in Authorization header
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Extract the current user from JWT in Authorization header."""
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        from app.operations.user import UserRepository
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user.email  # Return email to maintain compatibility with existing code (for now?)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_settings() -> Settings:
    """Return application settings."""
    return Settings()

# New service dependencies to avoid circular imports
def get_user_repository(db: AsyncSession = Depends(get_db)):
    """Dependency that provides a UserRepository instance."""
    from app.operations.user import UserRepository
    return UserRepository(db)

def get_registration_service(repository = Depends(get_user_repository)):
    """Dependency that provides a RegistrationService instance."""
    from app.operations.user import RegistrationService
    return RegistrationService(repository)

def get_auth_service(repository = Depends(get_user_repository)):
    """Dependency that provides an AuthenticationService instance."""
    from app.operations.user import AuthenticationService
    return AuthenticationService(repository)
