"""
Integration tests for protected routes.

These tests verify that the protected routes correctly:
- Enforce authentication for protected endpoints
- Grant access to authenticated users with valid tokens
- Deny access to unauthenticated users or users with invalid tokens
- Respect role-based access control when applicable
"""
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest_asyncio

from app.operations.jwt_service import create_access_token
from app.models.user import UserRole
from app.main import app


@pytest_asyncio.fixture
async def test_client():
    """Create a test client for the application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_user_token():
    """Create a valid token for a regular user."""
    return create_access_token(
        data={"sub": "user@example.com", "role": UserRole.USER.name}
    )


@pytest.fixture
def valid_admin_token():
    """Create a valid token for an admin user."""
    return create_access_token(
        data={"sub": "admin@example.com", "role": UserRole.ADMIN.name}
    )


@pytest.fixture
def expired_token():
    """Create an expired token for testing."""
    return create_access_token(
        data={"sub": "user@example.com", "role": UserRole.USER.name},
        expires_delta=timedelta(seconds=-1)
    )


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(test_client, valid_user_token):
    """Test accessing a protected route with a valid token."""
    # Use the existing protected auth route
    response = await test_client.get(
        "/auth/auth",
        cookies={"access_token": valid_user_token}
    )
    
    # The exact status code depends on whether the user exists in the database
    # But it should not be 401 Unauthorized or 403 Forbidden
    assert response.status_code not in (401, 403)


@pytest.mark.asyncio
async def test_protected_route_without_token(test_client):
    """Test accessing a protected route without a token."""
    response = await test_client.get("/auth/auth")
    
    assert response.status_code == 401
    assert "Not authenticated" in response.text


@pytest.mark.asyncio
async def test_protected_route_with_expired_token(test_client, expired_token):
    """Test accessing a protected route with an expired token."""
    response = await test_client.get(
        "/auth/auth",
        cookies={"access_token": expired_token}
    )
    
    assert response.status_code == 401
    assert "Invalid token" in response.text


@pytest.mark.asyncio
async def test_admin_route_with_admin_token(test_client, valid_admin_token):
    """Test accessing an admin route with an admin token."""
    # We don't have a specific admin-only route yet, so we'll test the token itself
    # by checking the response from a protected route
    response = await test_client.get(
        "/auth/auth",
        cookies={"access_token": valid_admin_token}
    )
    
    # Should be successful with the admin token
    assert response.status_code == 200
    
    # Verify the token is working
    data = response.json()
    assert "username" in data
    assert data["username"] == "admin@example.com"


@pytest.mark.asyncio
async def test_admin_route_with_user_token(test_client, valid_user_token):
    """Test accessing an admin route with a regular user token."""
    # Since we don't have a specific admin-only route, we'll just verify
    # that a user token can still access protected routes
    response = await test_client.get(
        "/auth/auth",
        cookies={"access_token": valid_user_token}
    )
    
    # Should be successful with a user token
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_public_route_with_token(test_client, valid_user_token):
    """Test accessing a public route with a token."""
    # For this test, we'll use the docs route which should be public
    response = await test_client.get(
        "/docs",
        cookies={"access_token": valid_user_token}
    )
    
    # Public routes should be accessible regardless of auth status
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_public_route_without_token(test_client):
    """Test accessing a public route without a token."""
    # For this test, we'll use the docs route which should be public
    response = await test_client.get("/docs")
    
    # Public routes should be accessible regardless of auth status
    assert response.status_code == 200 