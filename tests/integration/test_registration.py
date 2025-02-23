import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_successful_registration(async_client: AsyncClient):
    """Test successful user registration with valid data."""
    # First create an admin user
    admin_data = {
        "email": "admin@example.com",
        "password": "SecurePass123!",
        "first_name": "Admin",
        "last_name": "User"
    }
    await async_client.post("/auth/register", json=admin_data)
    
    # Now test regular user registration
    user_data = {
        "email": "new.user@example.com",
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User"
    }
    response = await async_client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "role" in data
    assert "nickname" in data  # Auto-generated from email
    assert data["email_verified"] is False

@pytest.mark.asyncio
async def test_first_user_gets_admin_role(async_client: AsyncClient):
    """Test that the first registered user gets admin role."""
    first_user_data = {
        "email": "admin@example.com",
        "password": "SecurePass123!",
        "first_name": "Admin",
        "last_name": "User"
    }
    first_response = await async_client.post("/auth/register", json=first_user_data)
    assert first_response.status_code == 201
    assert first_response.json()["role"] == UserRole.ADMIN.value

    # Second user should get USER role
    second_user_data = {
        "email": "regular@example.com",
        "password": "SecurePass123!",
        "first_name": "Regular",
        "last_name": "User"
    }
    second_response = await async_client.post("/auth/register", json=second_user_data)
    assert second_response.status_code == 201
    assert second_response.json()["role"] == UserRole.USER.value

@pytest.mark.asyncio
async def test_duplicate_email_registration(async_client: AsyncClient, db_session: AsyncSession):
    """Test that registration with an existing email is rejected."""
    # Create a user first
    existing_user = User(
        email="exists@example.com",
        nickname="existing_user",
        hashed_password=hash_password("SecurePass123!"),
        role=UserRole.USER
    )
    db_session.add(existing_user)
    await db_session.commit()

    # Try to register with the same email
    user_data = {
        "email": "exists@example.com",
        "password": "DifferentPass123!",
        "first_name": "Another",
        "last_name": "User"
    }
    response = await async_client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_invalid_password_registration(async_client: AsyncClient):
    """Test registration with invalid password formats."""
    test_cases = [
        ("short", "Password must be at least 8 characters long"),
        ("nouppercase123!", "Password must contain at least one uppercase letter"),
        ("NOLOWERCASE123!", "Password must contain at least one lowercase letter"),
        ("NoSpecialChar123", "Password must contain at least one special character"),
        ("NoNumber!", "Password must contain at least one number")
    ]

    for password, expected_error in test_cases:
        user_data = {
            "email": "test@example.com",
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }
        response = await async_client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(expected_error in error["msg"] for error in errors)

@pytest.mark.asyncio
async def test_invalid_email_registration(async_client: AsyncClient):
    """Test registration with invalid email formats."""
    invalid_emails = [
        "not_an_email",
        "missing@tld",
        "@nodomain.com",
        "spaces in@email.com"
    ]

    for email in invalid_emails:
        user_data = {
            "email": email,
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = await async_client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("email" in error["loc"] for error in errors)

@pytest.mark.asyncio
async def test_registration_with_optional_fields(async_client: AsyncClient):
    """Test registration with and without optional fields."""
    # Test with minimal required fields
    minimal_data = {
        "email": "minimal@example.com",
        "password": "SecurePass123!"
    }
    minimal_response = await async_client.post("/auth/register", json=minimal_data)
    assert minimal_response.status_code == 201
    assert minimal_response.json()["email"] == minimal_data["email"]
    assert minimal_response.json()["first_name"] is None
    assert minimal_response.json()["last_name"] is None

    # Test with all fields
    full_data = {
        "email": "full@example.com",
        "password": "SecurePass123!",
        "first_name": "Full",
        "last_name": "User",
        "nickname": "full_user"
    }
    full_response = await async_client.post("/auth/register", json=full_data)
    assert full_response.status_code == 201
    assert full_response.json()["email"] == full_data["email"]
    assert full_response.json()["first_name"] == full_data["first_name"]
    assert full_response.json()["last_name"] == full_data["last_name"]
    assert full_response.json()["nickname"] == full_data["nickname"]

@pytest.mark.asyncio
async def test_registration_response_format(async_client: AsyncClient):
    """Test that registration response contains all required fields in correct format."""
    user_data = {
        "email": "response@example.com",
        "password": "SecurePass123!",
        "first_name": "Response",
        "last_name": "Test"
    }
    response = await async_client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    
    # Check all required fields are present
    required_fields = {
        "id", "email", "nickname", "role", "email_verified",
        "first_name", "last_name", "created_at", "updated_at"
    }
    assert all(field in data for field in required_fields)
    
    # Check field types
    assert isinstance(data["id"], str)  # UUID as string
    assert isinstance(data["email"], str)
    assert isinstance(data["nickname"], str)
    assert isinstance(data["role"], str)
    assert isinstance(data["email_verified"], bool)
    assert isinstance(data["created_at"], str)  # datetime as ISO string
    assert isinstance(data["updated_at"], str)  # datetime as ISO string

@pytest.mark.asyncio
async def test_successful_registration_with_provided_nickname(async_client: AsyncClient):
    """Test successful user registration with a provided nickname."""
    # First create an admin user
    admin_data = {
        "email": "admin@example.com",
        "password": "SecurePass123!",
        "first_name": "Admin",
        "last_name": "User"
    }
    await async_client.post("/auth/register", json=admin_data)
    
    # Now test regular user registration with nickname
    user_data = {
        "email": "new.user@example.com",
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User",
        "nickname": "custom_nickname"
    }
    response = await async_client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["nickname"] == user_data["nickname"]  # Should use provided nickname
    assert "id" in data
    assert "role" in data
    assert data["email_verified"] is False

@pytest.mark.asyncio
async def test_successful_registration_with_auto_nickname(async_client: AsyncClient):
    """Test successful user registration with auto-generated nickname."""
    # First create an admin user
    admin_data = {
        "email": "admin@example.com",
        "password": "SecurePass123!",
        "first_name": "Admin",
        "last_name": "User"
    }
    await async_client.post("/auth/register", json=admin_data)
    
    # Now test regular user registration with auto nickname
    user_data = {
        "email": "new.user@example.com",
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User"
    }
    response = await async_client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["nickname"] == "newuser"  # Should be generated from email
    assert "id" in data
    assert "role" in data
    assert data["email_verified"] is False

@pytest.mark.asyncio
async def test_invalid_nickname_registration(async_client: AsyncClient):
    """Test registration with invalid nickname formats."""
    test_cases = [
        ("a", "ensure this value has at least 3 characters"),  # Too short
        ("user@123", "string does not match regex"),  # Invalid character @
        ("user 123", "string does not match regex"),  # Space not allowed
        ("user#123", "string does not match regex"),  # Special character not allowed
        ("verylongnicknamethatexceedsthelimit" * 2, "ensure this value has at most 50 characters")  # Too long
    ]

    for nickname, expected_error in test_cases:
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "nickname": nickname
        }
        response = await async_client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(expected_error.lower() in error["msg"].lower() for error in errors)

