import pytest
from datetime import timedelta
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from uuid import uuid4
from app.routers.dependencies import get_current_user, get_user_repository
from app.operations.jwt_service import create_access_token
from app.models.user import User, UserRole
from app.operations.user import UserRepository
from settings.config import settings
import asyncio

# --- Authentication Tests ---
@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Test retrieving current user with a valid token."""
    user_email = "test@example.com"
    role = UserRole.USER.name
    token_data = {"sub": user_email, "role": role}
    token = create_access_token(data=token_data)

    mock_repo = MagicMock(spec=UserRepository)
    mock_repo.get_by_email.return_value = User(id=uuid4(), email=user_email, role=UserRole.USER)

    with patch("app.routers.dependencies.decode_token", return_value=token_data), patch(
        "app.routers.dependencies.get_user_repository", return_value=mock_repo
    ):
        username = await get_current_user(token)  # Call without manually passing `user_repo`

    assert username == user_email

@pytest.mark.asyncio
async def test_get_current_user_no_token():
    """Test retrieving current user with no token."""
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(None)  # No manual `user_repo`

    assert excinfo.value.status_code == 401
    assert "Not authenticated" in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test retrieving current user with an invalid token."""
    invalid_token = "invalid.token.string"

    with patch("app.routers.dependencies.decode_token", return_value=None):
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(invalid_token)

    assert excinfo.value.status_code == 401
    assert "Invalid token" in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_missing_sub_claim():
    """Test retrieving current user with a token missing the 'sub' claim."""
    token_data = {"role": "USER"}
    token = create_access_token(data=token_data)

    with patch("app.routers.dependencies.decode_token", return_value=token_data):
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(token)

    assert excinfo.value.status_code == 401
    assert "Invalid token" in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """Test retrieving current user with an expired token."""
    user_email = "test@example.com"
    role = UserRole.USER.name
    token_data = {"sub": user_email, "role": role}
    expired_token = create_access_token(data=token_data, expires_delta=timedelta(seconds=-1))

    with patch("app.routers.dependencies.decode_token", return_value=None):
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(expired_token)

    assert excinfo.value.status_code == 401
    assert "Invalid token" in str(excinfo.value.detail)

# --- User Management Tests ---
@pytest.mark.asyncio
async def test_list_users():
    """Test listing all users."""
    mock_repo = MagicMock(spec=UserRepository)
    mock_repo.get_all_users.return_value = [
        User(id=uuid4(), email="user1@example.com", nickname="user1", role=UserRole.USER),
        User(id=uuid4(), email="user2@example.com", nickname="user2", role=UserRole.ADMIN),
    ]

    users = await mock_repo.get_all_users()
    assert len(users) == 2
    assert users[0].email == "user1@example.com"
    assert users[1].role == UserRole.ADMIN

@pytest.mark.asyncio
async def test_update_user():
    """Test updating a user."""
    user_id = uuid4()
    mock_repo = MagicMock(spec=UserRepository)
    mock_user = User(id=user_id, email="old@example.com", nickname="oldnick", role=UserRole.USER)

    mock_repo.get_by_id.return_value = mock_user
    mock_repo.save.return_value = mock_user

    update_data = {"email": "new@example.com", "nickname": "newnick"}
    for key, value in update_data.items():
        setattr(mock_user, key, value)

    updated_user = await mock_repo.save(mock_user)

    assert updated_user.email == "new@example.com"
    assert updated_user.nickname == "newnick"

@pytest.mark.asyncio
async def test_delete_user():
    """Test deleting a user."""
    user_id = uuid4()
    mock_repo = MagicMock(spec=UserRepository)
    mock_user = User(id=user_id, email="delete@example.com", nickname="todelete", role=UserRole.USER)

    mock_repo.get_by_id.return_value = mock_user
    await mock_repo.delete(mock_user)
    mock_repo.delete.assert_called_once_with(mock_user)
