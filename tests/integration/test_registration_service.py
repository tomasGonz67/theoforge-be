"""
Integration tests for the RegistrationService.

These tests verify the RegistrationService works correctly with:
- The real database
- Actual database constraints
- Service integration
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from app.operations.user import RegistrationService, UserRepository
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_registration_service_end_to_end(db_session: AsyncSession, registration_service: RegistrationService, user_repository: UserRepository):
    """Test the complete registration flow using the service directly."""
    # Arrange
    email = "servicetest@example.com"
    user_data = UserCreate(
        email=email,
        password="SecurePass123!",
        first_name="Service",
        last_name="Test",
        nickname="servicetest"
    )
    
    # Act
    user = await registration_service.register_user(user_data.model_dump())
    
    # Assert
    assert user is not None
    assert user.email == email
    
    # Verify user was saved to database
    db_user = await user_repository.get_by_email(email)
    assert db_user is not None
    assert db_user.id == user.id

@pytest.mark.asyncio
async def test_registration_service_admin_role_assignment(db_session: AsyncSession, registration_service: RegistrationService):
    """Test that the first user registered gets admin role."""
    # Arrange - ensure database is empty
    count = await UserRepository(db_session).count()
    if count > 0:
        pytest.skip("Database already has users, can't test first user role assignment")
    
    # Act
    first_user_data = UserCreate(
        email="firstadmin@example.com",
        password="SecurePass123!",
        first_name="First",
        last_name="Admin"
    )
    
    user = await registration_service.register_user(first_user_data.model_dump())
    
    # Assert
    assert user is not None
    assert user.role == UserRole.ADMIN
    
    # Register a second user and verify they get USER role
    second_user_data = UserCreate(
        email="seconduser@example.com",
        password="SecurePass123!",
        first_name="Second",
        last_name="User",
        nickname="seconduser"
    )
    
    second_user = await registration_service.register_user(second_user_data.model_dump())
    assert second_user is not None
    assert second_user.role == UserRole.USER

@pytest.mark.asyncio
async def test_registration_service_duplicate_email(db_session: AsyncSession, registration_service: RegistrationService, user):
    """Test that the service properly handles duplicate emails."""
    # Arrange - user fixture already creates a user
    
    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        duplicate_user_data = UserCreate(
            email=user.email,  # Same email as existing user
            password="SecurePass123!",
            first_name="Duplicate",
            last_name="User"
        )
        
        await registration_service.register_user(duplicate_user_data.model_dump())
    
    # Verify error message
    assert "already exists" in str(excinfo.value) 