# test_users.py

import pytest
from sqlalchemy import select

from app.models.user import User, UserRole
from app.utils.security import verify_password

@pytest.mark.asyncio
async def test_user_creation(db_session, verified_user):
    """Test that a user is correctly created and stored in the database."""
    result = await db_session.execute(select(User).filter_by(email=verified_user.email))
    stored_user = result.scalars().first()
    assert stored_user is not None
    assert stored_user.email == verified_user.email
    assert verify_password("testpassword123", stored_user.hashed_password)

@pytest.mark.asyncio
async def test_locked_user(db_session, locked_user):
    """Test that a locked user is correctly identified."""
    result = await db_session.execute(select(User).filter_by(email=locked_user.email))
    stored_user = result.scalars().first()
    assert stored_user is not None
    assert stored_user.is_locked is True

@pytest.mark.asyncio
async def test_verified_user(db_session, verified_user):
    """Test that a verified user is correctly identified."""
    result = await db_session.execute(select(User).filter_by(email=verified_user.email))
    stored_user = result.scalars().first()
    assert stored_user is not None
    assert stored_user.email_verified is True

@pytest.mark.asyncio
async def test_user_role(db_session, admin_user):
    """Test that user roles are correctly assigned."""
    result = await db_session.execute(select(User).filter_by(email=admin_user.email))
    stored_user = result.scalars().first()
    assert stored_user is not None
    assert stored_user.role == UserRole.ADMIN

@pytest.mark.asyncio
async def test_bulk_user_creation(db_session, multiple_users):
    """Test that multiple users are correctly created."""
    result = await db_session.execute(select(User).filter_by(role=UserRole.USER))
    stored_users = result.scalars().all()
    assert len(stored_users) == 3  # We create 3 users in the fixture

@pytest.mark.asyncio
async def test_password_hashing(regular_user):
    """Test that password hashing works correctly."""
    assert verify_password("testpassword123", regular_user.hashed_password)

@pytest.mark.asyncio
async def test_user_unlock(db_session, locked_user):
    """Test that a user can be unlocked."""
    locked_user.unlock_account()
    await db_session.commit()
    await db_session.refresh(locked_user)
    assert locked_user.is_locked is False

@pytest.mark.asyncio
async def test_user_lock(db_session, regular_user):
    """Test that a user can be locked."""
    regular_user.lock_account()
    await db_session.commit()
    await db_session.refresh(regular_user)
    assert regular_user.is_locked is True

@pytest.mark.asyncio
async def test_email_verification(db_session, regular_user):
    """Test that email verification works correctly."""
    regular_user.verify_email()
    await db_session.commit()
    await db_session.refresh(regular_user)
    assert regular_user.email_verified is True 