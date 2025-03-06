import uuid
import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.user import UserCreate, UserUpdate, UserResponse, ErrorResponse
from app.models.user import UserRole, SubscriptionPlan

@pytest.fixture
def valid_registration_data():
    return {
        "email": "john.doe@example.com",
        "password": "SecurePass123!",
        "nickname": "john_doe",
        "first_name": "John",
        "last_name": "Doe"
    }

@pytest.fixture
def valid_update_data():
    return {
        "phone_number": "123-456-7890",
        "address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "card_number": "4111111111111111",
        "ccv": "123",
        "security_code": "456",
        "subscription_plan": "PREMIUM"
    }

# Test UserCreate Schema
def test_valid_user_registration(valid_registration_data):
    """Test that valid registration data is accepted."""
    user = UserCreate(**valid_registration_data)
    assert user.email == valid_registration_data["email"]
    assert user.password == valid_registration_data["password"]

@pytest.mark.parametrize("invalid_password", [
    "short",
    "nouppercase123!",
    "NOLOWERCASE123!",
    "NoSpecialChar123",
    "NoNumber!"
])
def test_invalid_password_validation(invalid_password, valid_registration_data):
    """Test that invalid passwords are rejected."""
    data = valid_registration_data.copy()
    data["password"] = invalid_password
    with pytest.raises(ValidationError, match="Password"):
        UserCreate(**data)

@pytest.mark.parametrize("invalid_subscription_plan", [
    "INVALID_PLAN",
    "123",
    "",
])
def test_invalid_subscription_plan(invalid_subscription_plan, valid_update_data):
    """Test that invalid subscription plans are rejected."""
    data = valid_update_data.copy()
    data["subscription_plan"] = invalid_subscription_plan
    with pytest.raises(ValidationError, match="Invalid subscription plan"):
        UserUpdate(**data)

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
