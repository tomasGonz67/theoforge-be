from builtins import Exception, bool, classmethod, int, str
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import warnings
from datetime import timezone

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, ErrorResponse
from app.core.security import hash_password, verify_password
from settings.config import Settings  

settings = Settings()  
logger = logging.getLogger(__name__)

# Base repository for data access
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def _execute_query(self, query):
        """Execute a query with error handling and transaction management."""
        try:
            result = await self.session.execute(query)
            await self.session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await self.session.rollback()
            return None
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by their ID."""
        query = select(User).filter_by(id=user_id)
        result = await self._execute_query(query)
        return result.scalars().first() if result else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Check if user exists with given email."""
        query = select(User).filter_by(email=email)
        result = await self._execute_query(query)
        return result.scalars().first() if result else None
    
    async def get_by_nickname(self, nickname: str) -> Optional[User]:
        """Check if user exists with given nickname."""
        query = select(User).filter_by(nickname=nickname)
        result = await self._execute_query(query)
        return result.scalars().first() if result else None
    
    async def count(self) -> int:
        """Count total number of users. Used to determine if first user (admin)."""
        query = select(func.count()).select_from(User)
        result = await self.session.execute(query)
        return result.scalar()
    
    async def save(self, user: User) -> User:
        """Save user to database."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

# Registration service
class RegistrationService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def register_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """Register a new user with the provided data."""
        try:
            # Validate user data
            validated_data = UserCreate(**user_data).model_dump()
            
            # Check for existing user
            existing_user = await self.repository.get_by_email(validated_data['email'])
            if existing_user:
                logger.error("User with given email already exists.")
                return None
            
            # Hash password and remove plain password
            validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            
            # Check if this is the first user
            user_count = await self.repository.count()
            role = UserRole.ADMIN if user_count == 0 else UserRole.USER
            
            # Create new user instance with determined role and verification
            new_user = User(
                **validated_data,
                role=role,
                email_verified=(role == UserRole.ADMIN)  # True for admin, False for regular users
            )
            
            return await self.repository.save(new_user)
            
        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e}")
            return None

# Authentication service
class AuthenticationService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def login_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = await self.repository.get_by_email(email)
        if user:
            if user.email_verified is False:
                return None
            if verify_password(password, user.hashed_password):
                return await self.repository.save(user)
        return None

# The UserService class has been removed as it's no longer needed.
# All functionality has been moved to the specialized service classes above.

"""
Changes made for service extension implementation:
1. Separated concerns into three main classes:
   - UserRepository: Handles database operations
   - RegistrationService: Manages user registration
   - AuthenticationService: Handles login and authentication
   
2. Each class has clear responsibilities:
   - Repository: Data access and persistence
   - Services: Business logic
   
3. Complete migration from monolithic UserService:
   - UserService class completely removed
   - All functionality moved to specialized services
   
4. Benefits:
   - Clear separation of concerns
   - Testability through dependency injection
   - More maintainable and extensible code
"""
