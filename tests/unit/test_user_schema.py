import uuid
import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.user import UserBase, UserCreate, UserResponse, ErrorResponse
from app.models.user import UserRole

@pytest.fixture
def valid_user_data():
    return {
        "email": "john.doe@example.com",
        "nickname": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "role": UserRole.USER
    }

@pytest.fixture
def valid_registration_data():
    return {
        "email": "john.doe@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }

# Test UserCreate Schema
def test_valid_user_registration(valid_registration_data):
    """Test that valid registration data is accepted."""
    user = UserCreate(**valid_registration_data)
    assert user.email == valid_registration_data["email"]
    assert user.password == valid_registration_data["password"]

@pytest.mark.parametrize("invalid_password", [
    "short",  # Too short
    "nouppercase123!",  # No uppercase
    "NOLOWERCASE123!",  # No lowercase
    "NoSpecialChar123",  # No special character
    "NoNumber!",  # No number
])
def test_invalid_password_validation(invalid_password, valid_registration_data):
    """Test that invalid passwords are rejected."""
    data = valid_registration_data.copy()
    data["password"] = invalid_password
    with pytest.raises(ValidationError):
        UserCreate(**data)

@pytest.mark.parametrize("invalid_email", [
    "not_an_email",
    "missing@tld",
    "@nodomain.com",
    "spaces in@email.com",
])
def test_invalid_email_validation(invalid_email, valid_registration_data):
    """Test that invalid email formats are rejected."""
    data = valid_registration_data.copy()
    data["email"] = invalid_email
    with pytest.raises(ValidationError):
        UserCreate(**data)

def test_nickname_generation(valid_registration_data):
    """Test that nickname is automatically generated from email if not provided."""
    user = UserCreate(**valid_registration_data)
    assert user.nickname == "johndoe"  # Based on the email john.doe@example.com

@pytest.mark.parametrize("valid_nickname", [
    "user123",
    "test_user",
    "test-user",
    "testuser",
])
def test_valid_nickname_formats(valid_nickname, valid_registration_data):
    """Test that valid nickname formats are accepted."""
    data = valid_registration_data.copy()
    data["nickname"] = valid_nickname
    user = UserCreate(**data)
    assert user.nickname == valid_nickname

@pytest.mark.parametrize("invalid_nickname", [
    "u",  # Too short
    "user@123",  # Invalid character
    "user 123",  # Space not allowed
    "user#123",  # Special character not allowed
])
def test_invalid_nickname_formats(invalid_nickname, valid_registration_data):
    """Test that invalid nickname formats are rejected."""
    data = valid_registration_data.copy()
    data["nickname"] = invalid_nickname
    with pytest.raises(ValidationError):
        UserCreate(**data)

# Test UserResponse Schema
def test_valid_user_response():
    """Test that UserResponse correctly handles all fields."""
    data = {
        "id": uuid.uuid4(),
        "email": "john.doe@example.com",
        "nickname": "john_doe",
        "first_name": "John",
        "last_name": "Doe",
        "role": UserRole.USER,
        "email_verified": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    response = UserResponse(**data)
    assert response.id == data["id"]
    assert response.email == data["email"]
    assert response.nickname == data["nickname"]
    assert response.role == data["role"]
    assert response.email_verified == data["email_verified"]

# Test ErrorResponse Schema
def test_error_response():
    """Test that ErrorResponse correctly handles error messages."""
    data = {
        "error": "Email already exists",
        "details": "The provided email address is already registered"
    }
    error = ErrorResponse(**data)
    assert error.error == data["error"]
    assert error.details == data["details"]
