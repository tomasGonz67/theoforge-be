from builtins import Exception, bool, classmethod, int, str
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, ErrorResponse
from app.core.security import hash_password

logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by their ID."""
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        """Check if user exists with given email."""
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        """Check if user exists with given nickname."""
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str]) -> Optional[User]:
        """Create a new user with the provided data."""
        try:
            validated_data = UserCreate(**user_data).model_dump()
            existing_user = await cls.get_by_email(session, validated_data['email'])
            if existing_user:
                logger.error("User with given email already exists.")
                return None

            # Hash password and remove plain password
            validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            
            # Create new user instance
            new_user = User(**validated_data)
            
            # Set role based on if first user
            user_count = await cls.count(session)
            new_user.role = UserRole.ADMIN if user_count == 0 else UserRole.USER
            
            # First user (admin) gets auto-verified
            new_user.email_verified = new_user.role == UserRole.ADMIN
            
            session.add(new_user)
            await session.commit()
            return new_user

        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e}")
            return None

    @classmethod
    async def register_user(cls, session: AsyncSession, user_data: Dict[str, str]) -> Optional[User]:
        """Register a new user. This is the main method to be used for registration."""
        return await cls.create(session, user_data)

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """Count total number of users. Used to determine if first user (admin)."""
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        return result.scalar()

"""
Changes made for registration implementation:
1. Core registration methods:
   - create(): Main user creation with validation and password hashing
   - register_user(): Public wrapper for user registration
   - get_by_email(), get_by_nickname(): Duplicate checking
   - count(): For first user = admin logic

2. Registration features:
   - Email uniqueness validation
   - Password hashing
   - Automatic role assignment (first user = admin)
   - Admin auto-verification
   - Basic error handling and logging

3. Removed non-registration functionality:
   - Login and session management
   - Account locking and password reset
   - Email verification (kept only verified flag)
   - Profile updates and deletion
"""
