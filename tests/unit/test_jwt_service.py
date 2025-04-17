"""
Unit tests for the JWT service.

These tests verify that the JWT service correctly handles:
- Token creation
- Token decoding
- Token expiration
- Role handling
"""
import pytest
from datetime import datetime, timedelta
import jwt
import time

from app.operations.jwt_service import create_access_token, decode_token
from app.models.user import UserRole
from settings.config import settings


def test_create_access_token_with_role():
    """Test creating a token with user role."""
    # Arrange
    user_id = "test-user-id"
    role = UserRole.USER.name
    test_data = {"sub": user_id, "role": role}
    
    # Act
    token = create_access_token(data=test_data)
    
    # Assert
    assert token is not None
    # Verify token can be decoded with the secret key
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["sub"] == user_id
    assert decoded["role"] == role.upper()  # Role should be uppercase
    assert "exp" in decoded  # Expiration should be set


def test_create_access_token_with_custom_expiry():
    """Test creating a token with custom expiration time."""
    # Arrange
    test_data = {"sub": "test-user-id"}
    expires_delta = timedelta(minutes=30)
    
    # Act
    token = create_access_token(data=test_data, expires_delta=expires_delta)
    
    # Assert
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert "exp" in decoded
    
    # Verify expiration time is roughly 30 minutes from now
    # Allow for small test execution time differences (~2 seconds)
    expected_exp = datetime.utcnow() + expires_delta
    actual_exp = datetime.utcfromtimestamp(decoded["exp"])
    time_diff = abs((expected_exp - actual_exp).total_seconds())
    assert time_diff < 2


def test_create_access_token_with_default_expiry():
    """Test creating a token with default expiration time."""
    # Arrange
    test_data = {"sub": "test-user-id"}
    
    # Act
    token = create_access_token(data=test_data)
    
    # Assert
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert "exp" in decoded
    
    # Verify expiration time is roughly default minutes from now
    expected_exp = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    actual_exp = datetime.utcfromtimestamp(decoded["exp"])
    time_diff = abs((expected_exp - actual_exp).total_seconds())
    assert time_diff < 2


def test_decode_token_valid():
    """Test decoding a valid token."""
    # Arrange
    test_data = {"sub": "test-user-id", "role": UserRole.USER.name}
    token = create_access_token(data=test_data)
    
    # Act
    decoded = decode_token(token)
    
    # Assert
    assert decoded is not None
    assert decoded["sub"] == test_data["sub"]
    assert decoded["role"] == test_data["role"].upper()


def test_decode_token_invalid():
    """Test decoding an invalid token."""
    # Arrange
    invalid_token = "invalid.token.string"
    
    # Act
    decoded = decode_token(invalid_token)
    
    # Assert
    assert decoded is None


def test_decode_token_expired():
    """Test decoding an expired token."""
    # Arrange
    test_data = {"sub": "test-user-id"}
    # Create a token that's already expired
    expires_delta = timedelta(seconds=-1)
    expired_token = create_access_token(data=test_data, expires_delta=expires_delta)
    
    # Act
    decoded = decode_token(expired_token)
    
    # Assert
    assert decoded is None


def test_create_token_with_additional_data():
    """Test creating a token with additional custom data."""
    # Arrange
    test_data = {
        "sub": "test-user-id",
        "role": UserRole.ADMIN.name,
        "nickname": "testuser",
        "email": "test@example.com"
    }
    
    # Act
    token = create_access_token(data=test_data)
    
    # Assert
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["sub"] == test_data["sub"]
    assert decoded["role"] == test_data["role"].upper()
    assert decoded["nickname"] == test_data["nickname"]
    assert decoded["email"] == test_data["email"] 