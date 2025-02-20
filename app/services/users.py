# User service functions
from datetime import datetime, timezone
from typing import Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User, UserRole
from app.utils.security import hash_password, verify_password
from settings.config import settings
import logging

logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        """Execute a query with error handling."""
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email."""
        query = select(User).filter(User.email == email)
        result = await cls._execute_query(session, query)
        return result.scalar_one_or_none() if result else None

    @classmethod
    async def create_user(cls, session: AsyncSession, user_data: Dict) -> Optional[User]:
        """Create a new user."""
        try:
            # Hash the password
            hashed_password = hash_password(user_data.password)
            
            # Check if this is the first user (make them admin)
            user_count = await cls.count(session)
            role = UserRole.ADMIN if user_count == 0 else UserRole.USER

            # Create user instance
            user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                role=role,
                email_verified=True if role == UserRole.ADMIN else False
            )
            
            session.add(user)
            await session.commit()
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await session.rollback()
            return None

    @classmethod
    async def authenticate_user(cls, session: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = await cls.get_by_email(session, email)
        if not user:
            return None

        if user.is_locked:
            return None

        if verify_password(password, user.hashed_password):
            # Successful login
            user.failed_login_attempts = 0
            user.last_login_at = datetime.now(timezone.utc)
            session.add(user)
            await session.commit()
            return user
        else:
            # Failed login
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.is_locked = True
            session.add(user)
            await session.commit()
            return None

    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        """Check if a user account is locked."""
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """Get total number of users."""
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        return result.scalar()

# TODO: Get user by ID
# TODO: Update user
# TODO: Delete user
# TODO: List users 