"""
Unit tests for the UserRepository class.

These tests verify that the UserRepository correctly handles:
- Finding users by various attributes
- Saving user data
- Counting users
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.operations.user import UserRepository
from app.models.user import User, UserRole
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_get_by_id(db_session: AsyncSession, user):
    """Test retrieving a user by ID."""
    # Arrange
    repo = UserRepository(db_session)
    
    # Act
    result = await repo.get_by_id(user.id)
    
    # Assert
    assert result is not None
    assert result.id == user.id
    assert result.email == user.email

@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session: AsyncSession):
    """Test retrieving a user with a non-existent ID."""
    # Arrange
    repo = UserRepository(db_session)
    non_existent_id = uuid.uuid4()
    
    # Act
    result = await repo.get_by_id(non_existent_id)
    
    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_get_by_email(db_session: AsyncSession, user):
    """Test retrieving a user by email."""
    # Arrange
    repo = UserRepository(db_session)
    
    # Act
    result = await repo.get_by_email(user.email)
    
    # Assert
    assert result is not None
    assert result.email == user.email
    assert result.id == user.id

@pytest.mark.asyncio
async def test_get_by_email_not_found(db_session: AsyncSession):
    """Test retrieving a user with a non-existent email."""
    # Arrange
    repo = UserRepository(db_session)
    non_existent_email = "nonexistent@example.com"
    
    # Act
    result = await repo.get_by_email(non_existent_email)
    
    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_get_by_nickname(db_session: AsyncSession, user):
    """Test retrieving a user by nickname."""
    # Arrange
    repo = UserRepository(db_session)
    
    # Act
    result = await repo.get_by_nickname(user.nickname)
    
    # Assert
    assert result is not None
    assert result.nickname == user.nickname
    assert result.id == user.id

@pytest.mark.asyncio
async def test_get_by_nickname_not_found(db_session: AsyncSession):
    """Test retrieving a user with a non-existent nickname."""
    # Arrange
    repo = UserRepository(db_session)
    non_existent_nickname = "nonexistent_nickname"
    
    # Act
    result = await repo.get_by_nickname(non_existent_nickname)
    
    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_count(db_session: AsyncSession, users_with_same_role_50_users):
    """Test counting the number of users."""
    # Arrange
    repo = UserRepository(db_session)
    
    # Act
    count = await repo.count()
    
    # Assert - should be 50 users from the fixture
    assert count == 50

@pytest.mark.asyncio
async def test_save_new_user(db_session: AsyncSession):
    """Test saving a new user."""
    # Arrange
    repo = UserRepository(db_session)
    new_user = User(
        email="savetest@example.com",
        nickname="savetest",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER
    )
    
    # Act
    saved_user = await repo.save(new_user)
    
    # Assert
    assert saved_user.id is not None  # Should have an ID after saving
    assert saved_user.email == new_user.email
    
    # Verify in database
    fetched_user = await repo.get_by_email("savetest@example.com")
    assert fetched_user is not None
    assert fetched_user.id == saved_user.id

@pytest.mark.asyncio
async def test_save_existing_user(db_session: AsyncSession, user):
    """Test updating an existing user."""
    # Arrange
    repo = UserRepository(db_session)
    new_nickname = "updated_nickname"
    
    # Update user
    user.nickname = new_nickname
    
    # Act
    updated_user = await repo.save(user)
    
    # Assert
    assert updated_user.nickname == new_nickname
    
    # Verify in database
    fetched_user = await repo.get_by_id(user.id)
    assert fetched_user is not None
    assert fetched_user.nickname == new_nickname 