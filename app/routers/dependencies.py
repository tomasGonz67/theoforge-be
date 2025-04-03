from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError
from jose import JWTError


from app.database import Database, Neo4jService
from app.operations.jwt_service import decode_token
from settings.config import settings

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
from app.models.user import User
from app.operations.user import UserRepository

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Extract the current user from JWT in Authorization header and return the full user object."""
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user  # ✅ Now returning the full User object instead of just email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_settings():
    """Return application settings."""
    return settings

def get_relevant_context(query_embedding):
    query = """
    MATCH (n:Document)
    WITH n, gds.similarity.cosine(n.embedding, $queryEmbedding) AS similarity
    ORDER BY similarity DESC
    LIMIT 5
    RETURN n.text AS context
    """
    results = Neo4jService.execute_query(query, {"queryEmbedding": query_embedding})
    return " ".join([record["context"] for record in results])