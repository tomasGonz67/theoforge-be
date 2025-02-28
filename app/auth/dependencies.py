from builtins import Exception
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Database
from jose import JWTError
from app.services.jwt_service import decode_token

async def get_db() -> AsyncSession:
    """Dependency that provides a database session for each request."""
    async_session_factory = Database.get_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await session.close()

# Retrieve current user based on access_token via cookie
def get_current_user(access_token: str = Cookie(None)):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(access_token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
