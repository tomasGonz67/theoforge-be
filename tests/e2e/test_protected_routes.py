import pytest
from datetime import timedelta
from httpx import AsyncClient
import pytest_asyncio
from app.operations.jwt_service import create_access_token
from app.models.user import User, UserRole
from app.main import app
from app.core.security import hash_password
from app.database import Database
from sqlalchemy.future import select

@pytest_asyncio.fixture
async def test_client():
    """Create a test client for the application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def setup_users():
    """Ensure test users exist in the database before running tests."""
    async with Database.get_session_factory()() as session:
        for user_data in [
            {"email": "user@example.com", "nickname": "test_user", "role": UserRole.USER},
            {"email": "admin@example.com", "nickname": "admin_user", "role": UserRole.ADMIN}
        ]:
            result = await session.execute(select(User).filter_by(email=user_data["email"]))
            user = result.scalars().first()
            if not user:
                user = User(
                    email=user_data["email"],
                    nickname=user_data["nickname"],
                    hashed_password=hash_password("SecurePass123!"),
                    role=user_data["role"],
                    email_verified=True
                )
                session.add(user)
        await session.commit()

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
async def test_protected_route_with_valid_token(test_client, valid_user_token, setup_users):
    """Test accessing a protected route with a valid token."""
    response = await test_client.get(
        "/auth/auth",
        headers={"Authorization": f"Bearer {valid_user_token}"}
    )
    assert response.status_code == 200, f"Unexpected response: {response.json()}"

@pytest.mark.asyncio
async def test_protected_route_without_token(test_client):
    """Test accessing a protected route without a token."""
    response = await test_client.get("/auth/auth")
    assert response.status_code == 401
    assert "Not authenticated" in response.text

@pytest.mark.asyncio
async def test_protected_route_with_expired_token(test_client, expired_token, setup_users):
    """Test accessing a protected route with an expired token."""
    response = await test_client.get(
        "/auth/auth",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401, f"Unexpected response: {response.json()}"
    assert "Invalid token" in response.text or "Not authenticated" in response.text

@pytest.mark.asyncio
async def test_admin_route_with_admin_token(test_client, valid_admin_token, setup_users):
    """Test accessing an admin route with an admin token."""
    response = await test_client.get(
        "/auth/auth",
        headers={"Authorization": f"Bearer {valid_admin_token}"}
    )
    assert response.status_code == 200, f"Unexpected response: {response.json()}"
    data = response.json()
    assert "username" in data
    assert data["username"] == "admin@example.com"

@pytest.mark.asyncio
async def test_admin_route_with_user_token(test_client, valid_user_token, setup_users):
    """Test accessing an admin route with a regular user token."""
    response = await test_client.get(
        "/auth/auth", 
        headers={"Authorization": f"Bearer {valid_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == "user@example.com"

@pytest.mark.asyncio
async def test_public_route_with_token(test_client, valid_user_token):
    """Test accessing a public route with a token."""
    response = await test_client.get(
        "/docs",
        headers={"Authorization": f"Bearer {valid_user_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_public_route_without_token(test_client):
    """Test accessing a public route without a token."""
    response = await test_client.get("/docs")
    assert response.status_code == 200
