from builtins import Exception
from fastapi import HTTPException, Depends, status, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Database
from jose import JWTError
from jwt import PyJWTError, ExpiredSignatureError
from app.operations.jwt_service import decode_token
from settings.config import Settings
from sqlalchemy.exc import SQLAlchemyError

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Retrieve current user based on JWT
def get_current_user(access_token: str = Security(oauth2_scheme)):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_token(access_token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    except (JWTError, PyJWTError):
        raise HTTPException(status_code=401, detail="Invalid token")

def get_settings() -> Settings:
    """Return application settings."""
    return Settings()

# New service dependencies with imports inside the functions to avoid circular imports
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