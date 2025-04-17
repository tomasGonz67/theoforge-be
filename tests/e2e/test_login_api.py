"""
Integration tests for the login API endpoints.

These tests verify that the login API:
- Validates credentials correctly
- Returns proper tokens
- Handles invalid credentials appropriately
"""
import pytest
import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.operations.user import UserRepository, AuthenticationService
from app.core.security import hash_password
from settings.config import settings

@pytest.mark.asyncio
async def test_login_valid_credentials(async_client: AsyncClient, user):
    """Test successful login with valid credentials."""
    # Arrange
    login_data = {
        "username": user.email,
        "password": "SecurePass123!"  # This is the password set in the user fixture
    }
    
    # Act
    response = await async_client.post("/auth/login", data=login_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify token contents
    token = data["access_token"]
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["sub"] == user.email
    assert decoded["role"] == user.role.name.upper()
    assert "exp" in decoded


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient, user):
    """Test login with invalid credentials."""
    # Arrange
    login_data = {
        "username": user.email,
        "password": "WrongPassword123!"
    }
    
    # Act
    response = await async_client.post("/auth/login", data=login_data)
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid username/password" in data["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with non-existent user."""
    # Arrange
    login_data = {
        "username": "nonexistent@example.com",
        "password": "AnyPassword123!"
    }
    
    # Act
    response = await async_client.post("/auth/login", data=login_data)
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid username/password" in data["detail"]


@pytest.mark.asyncio
async def test_login_unverified_email(async_client: AsyncClient, db_session: AsyncSession):
    """Test login with unverified email."""
    # Arrange - create an unverified user
    user_data = {
        "nickname": "unverified_user",
        "email": "unverified@example.com",
        "hashed_password": hash_password("SecurePass123!"),
        "role": UserRole.USER,
        "email_verified": False
    }
    unverified_user = User(**user_data)
    db_session.add(unverified_user)
    await db_session.commit()
    
    login_data = {
        "username": "unverified@example.com",
        "password": "SecurePass123!"
    }
    
    # Act
    response = await async_client.post("/auth/login", data=login_data)
    
    # Assert
    if settings.require_email_verification:
        # If email verification is required, login should fail
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid username/password" in data["detail"]
        # Note: We're returning the same error message for security reasons to not leak information
    else:
        # If email verification is not required, login should succeed
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_admin_user(async_client: AsyncClient, admin_user):
    """Test login with admin user."""
    # Arrange
    login_data = {
        "username": admin_user.email,
        "password": "SecurePass123!"  # This is the password set in the admin_user fixture
    }
    
    # Act
    response = await async_client.post("/auth/login", data=login_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # Verify token contents contains ADMIN role
    token = data["access_token"]
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["role"] == "ADMIN" 