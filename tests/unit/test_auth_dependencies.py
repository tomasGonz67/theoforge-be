"""
Unit tests for authentication dependencies.

These tests verify that the authentication dependencies correctly:
- Validate JWT tokens
- Extract user information from tokens
- Handle authentication errors
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException
import jwt
from jwt import PyJWTError, ExpiredSignatureError
from unittest.mock import patch, MagicMock

from app.routers.dependencies import get_current_user
from app.operations.jwt_service import create_access_token
from app.models.user import UserRole
from settings.config import settings


def test_get_current_user_valid_token():
    """Test retrieving current user with a valid token."""
    # Arrange
    user_email = "test@example.com"
    role = UserRole.USER.name
    token_data = {"sub": user_email, "role": role}
    token = create_access_token(data=token_data)
    
    # Act
    with patch('app.routers.dependencies.decode_token') as mock_decode:
        # Mock the decode_token function to return our payload
        mock_decode.return_value = token_data
        username = get_current_user(token)
    
    # Assert
    assert username == user_email
    mock_decode.assert_called_once_with(token)


def test_get_current_user_no_token():
    """Test retrieving current user with no token."""
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        get_current_user(None)
    
    # Verify the exception details
    assert excinfo.value.status_code == 401
    assert "Not authenticated" in str(excinfo.value.detail)


def test_get_current_user_invalid_token():
    """Test retrieving current user with an invalid token."""
    # Arrange
    invalid_token = "invalid.token.string"
    
    # Act & Assert
    with patch('app.routers.dependencies.decode_token', return_value={}):
        with pytest.raises(HTTPException) as excinfo:
            try:
                get_current_user(invalid_token)
            except AttributeError:
                pytest.fail("AttributeError: 'NoneType' object has no attribute 'get'. The implementation should handle this case.")
    
    # This test passes if get_current_user raises an HTTPException
    # If it doesn't handle the None case properly, it will raise an AttributeError
    # which we catch and convert to a test failure


def test_get_current_user_missing_sub_claim():
    """Test retrieving current user with a token missing the 'sub' claim."""
    # Arrange
    token_data = {"role": "USER"}  # Missing 'sub' claim
    token = create_access_token(data=token_data)
    
    # Act & Assert
    with patch('app.routers.dependencies.decode_token') as mock_decode:
        # Mock the decode_token function to return payload without 'sub'
        mock_decode.return_value = token_data
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token)
    
    # Verify the exception details
    assert excinfo.value.status_code == 401
    assert "Invalid token" in str(excinfo.value.detail)


def test_get_current_user_jwt_error():
    """Test retrieving current user when a JWT error occurs."""
    # Arrange
    token = "some.valid.looking.token"

    # Act & Assert
    with patch('app.routers.dependencies.decode_token') as mock_decode:
        # Mock the decode_token function to raise a JWT error
        mock_decode.side_effect = PyJWTError("Token invalid")

        with pytest.raises(HTTPException) as excinfo:
            get_current_user(token)
    
    # Verify the exception details
    assert excinfo.value.status_code == 401
    assert "Invalid token" in str(excinfo.value.detail)


def test_get_current_user_expired_token():
    """Test retrieving current user with an expired token."""
    # Arrange
    user_email = "test@example.com"
    role = UserRole.USER.name
    token_data = {"sub": user_email, "role": role}
    # Create a token that's already expired
    expired_token = create_access_token(data=token_data, expires_delta=timedelta(seconds=-1))
    
    # Act & Assert
    # When a token is expired, the implementation should decode it but find it's expired
    # We'll simulate that scenario by returning None from decode_token
    with patch('app.routers.dependencies.decode_token') as mock_decode:
        mock_decode.side_effect = ExpiredSignatureError("Token has expired")

        with pytest.raises(HTTPException) as excinfo:
            try:
                get_current_user(expired_token)
            except AttributeError:
                pytest.fail("AttributeError: 'NoneType' object has no attribute 'get'. The implementation should handle this case.")
    
    # This test passes if get_current_user raises an HTTPException when decode_token returns None 